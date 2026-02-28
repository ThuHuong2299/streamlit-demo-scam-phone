# src/multilabel_predictor.py
"""
MÔ HÌNH 2: Phân loại Đa lớp + Nhị phân (NHÃN THẬT)

Vai trò trong hệ thống:
- Dự đoán LOẠI LỪA ĐẢO thật (16 loại từ nhãn ground truth)
- Đưa ra CẢNH BÁO dựa trên xác suất dự đoán
- Output: loại lừa đảo + xác suất + quyết định cảnh báo

THAY ĐỔI so với phiên bản cũ:
- Cũ: Dùng 6 chủ đề LDA (silver labeling) → Mới: Dùng 16 loại thật
- Cũ: Phụ thuộc Mô hình 1 (LDA) → Mới: ĐỘC LẬP
- Cũ: Rule-based (đếm từ khóa match) → Mới: ML models trên nhãn thật
"""

import re
import json
import sys
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional


# Ngưỡng cảnh báo mặc định
NGUONG_CANH_BAO = 0.4

# Ngưỡng tối thiểu từ khóa
NGUONG_TU_KHOA_TOI_THIEU = 3


# ── Định nghĩa lại MulticlassAsBinary GIỐNG HỆT notebook ─────────────────
# Cần để joblib.load() deserialize được mo_hinh_da_lop.pkl
# pkl lưu reference __main__.MulticlassAsBinary khi train trong notebook.
class MulticlassAsBinary:
    """Wrapper: trích xác suất 1 class từ multiclass model."""
    def __init__(self, model, class_idx):
        self.model     = model
        self.class_idx = class_idx
        self._map      = {c: i for i, c in enumerate(model.classes_)}

    def predict_proba(self, X):
        proba = self.model.predict_proba(X)
        p = (proba[:, self._map[self.class_idx]]
             if self.class_idx in self._map
             else np.zeros(X.shape[0]))
        return np.column_stack([1 - p, p])

    def predict(self, X):
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)


def _safe_load(path: Path):
    """
    Load pkl bằng joblib — đúng format cho cả tfidf và mo_hinh.

    Cả hai file đều được lưu bằng joblib (không phải pickle thuần),
    và mo_hinh_da_lop.pkl chứa XGBClassifier + MulticlassAsBinary.
    joblib tự xử lý numpy array embedded; ta chỉ cần inject
    MulticlassAsBinary vào sys.modules trước khi load.
    """
    # Inject MulticlassAsBinary vào __main__ để joblib tìm thấy
    # (pkl lưu dưới namespace __main__.MulticlassAsBinary)
    import __main__
    if not hasattr(__main__, "MulticlassAsBinary"):
        __main__.MulticlassAsBinary = MulticlassAsBinary

    # Đồng thời inject vào sys.modules['__main__'] để chắc chắn
    sys.modules["__main__"].MulticlassAsBinary = MulticlassAsBinary  # type: ignore

    return joblib.load(path)


class MultilabelPredictor:
    """
    Predictor Mô hình 2: Phân loại đa lớp trên nhãn thật.
    
    Load các mô hình đã train từ notebook Mo_hinh_2_Phan_loai_Da_lop_Nhi_phan.ipynb
    """
    
    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = models_dir or Path(__file__).parent.parent / "models"
        self.tfidf = None
        self.mo_hinh = None       # Dict {loai_id: {'model': ..., 'name': ..., 'loai_ten': ...}}
        self.id_to_loai = {}      # Mapping ID → tên loại
        self.loai_to_id = {}      # Mapping tên loại → ID
        self.so_loai = 0
        self.danh_sach_loai = []
        self.tu_khoa_dac_trung = {}  # {loai_ten: [từ khóa]}
        self._loaded = False
    
    def load_models(self) -> bool:
        """Load các mô hình đã train từ disk."""
        try:
            # 1. Load TF-IDF vectorizer
            tfidf_path = self.models_dir / "tfidf_vectorizer_v2.pkl"
            if tfidf_path.exists():
                self.tfidf = _safe_load(tfidf_path)
                print(f"  [OK] Loaded TF-IDF vectorizer")
            
            # 2. Load mô hình đa lớp (nhãn thật)
            model_path = self.models_dir / "mo_hinh_da_lop.pkl"
            if model_path.exists():
                self.mo_hinh = _safe_load(model_path)
                print(f"  [OK] Loaded {len(self.mo_hinh)} multi-label models")
            
            # 3. Load mapping loại
            mapping_path = self.models_dir / "mapping_loai.json"
            if mapping_path.exists():
                with open(mapping_path, 'r', encoding='utf-8') as f:
                    mapping = json.load(f)
                self.id_to_loai = {int(k): v for k, v in mapping.get('ID_TO_LOAI', {}).items()}
                self.loai_to_id = mapping.get('LOAI_TO_ID', {})
                self.so_loai = mapping.get('SO_LOAI', 0)
                self.danh_sach_loai = mapping.get('DANH_SACH_LOAI', [])
                print(f"  [OK] Loaded mapping: {self.so_loai} loai lua dao")
            
            # 4. Load từ khóa đặc trưng mỗi loại
            tk_path = self.models_dir / "tu_khoa_dac_trung_loai.json"
            if tk_path.exists():
                with open(tk_path, 'r', encoding='utf-8') as f:
                    self.tu_khoa_dac_trung = json.load(f)
                print(f"  [OK] Loaded tu khoa dac trung cho {len(self.tu_khoa_dac_trung)} loai")
            
            self._loaded = (self.tfidf is not None and self.mo_hinh is not None)
            
            if self._loaded:
                print(f"\n[OK] Multilabel Predictor san sang ({len(self.mo_hinh)} models)")
            else:
                print(f"\n[WARN] Chua co model files. Se dung rule-based fallback.")
            
            return self._loaded
            
        except Exception as e:
            print(f"[ERROR] Error loading models: {e}")
            return False
    
    def _chuan_hoa_tu_khoa(self, tu_khoa: str) -> str:
        """Chuẩn hóa từ khóa."""
        tu = str(tu_khoa).lower().strip()
        tu = re.sub(r'[^\w\s]', '', tu)
        tu = re.sub(r'\s+', '_', tu)
        return tu
    
    def _tach_tu_khoa(self, chuoi: str) -> List[str]:
        """Tách chuỗi từ khóa thành danh sách."""
        if not chuoi:
            return []
        cac_tu = [t.strip() for t in str(chuoi).split(',') if t.strip()]
        return [self._chuan_hoa_tu_khoa(tu) for tu in cac_tu if tu]
    
    def predict(
        self, 
        text: str = "",
        keywords: List[str] = None,
        nguong_canh_bao: float = NGUONG_CANH_BAO
    ) -> Dict:
        """
        Dự đoán loại lừa đảo và đưa ra cảnh báo.
        
        Args:
            text: Văn bản từ khóa (space-separated, cho TF-IDF)
            keywords: Danh sách từ khóa (optional)
            nguong_canh_bao: Ngưỡng xác suất để cảnh báo
            
        Returns:
            Dict:
                - canh_bao: bool (có cảnh báo hay không)
                - diem_nghi_ngo: float (0-1, điểm nghi ngờ)
                - loai_du_doan: List[str] (các loại lừa đảo dự đoán)
                - chi_tiet: List[Dict] (xác suất từng loại)
                - nguon: str ("ml_model" hoặc "rule_based")
        """
        # Kiểm tra đầu vào
        if not text and not keywords:
            return self._ket_qua_rong("Không có dữ liệu để phân tích")
        
        if keywords and len(keywords) < NGUONG_TU_KHOA_TOI_THIEU:
            warning = f"Chỉ có {len(keywords)} từ khóa (tối thiểu {NGUONG_TU_KHOA_TOI_THIEU}) - độ tin cậy THẤP"
        else:
            warning = None
        
        # Chuẩn bị text cho TF-IDF
        # Luôn build lại từ keywords đã chuẩn hoá để đảm bảo
        # format khớp với dữ liệu train (rửa_tiền, tài_khoản, ...)
        if keywords:
            text = ' '.join([self._chuan_hoa_tu_khoa(kw) for kw in keywords])
        elif not text:
            pass  # giữ text gốc nếu không có keywords
        
        # Nếu có ML model → dùng ML
        if self._loaded and self.mo_hinh and self.tfidf:
            result = self._predict_ml(text, nguong_canh_bao)
        else:
            # Fallback: rule-based dùng từ khóa đặc trưng
            result = self._predict_rule_based(keywords or [], nguong_canh_bao)
        
        if warning:
            result["warning"] = warning
        
        return result
    
    def _predict_ml(self, text: str, nguong_canh_bao: float) -> Dict:
        """Dự đoán bằng ML models (nhãn thật).

        Cấu trúc mỗi item trong self.mo_hinh:
            info = {
                'threshold':  float,   # ngưỡng xác suất riêng của loại
                'f1':         float,
                'loai_ten':   str,
                'best_model': str,     # 'RandomForest' | 'XGBoost' | 'DecisionTree'
                'models': {
                    'RandomForest': MulticlassAsBinary,
                    'XGBoost':      MulticlassAsBinary,
                    'DecisionTree': MulticlassAsBinary,
                }
            }
        """
        try:
            X = self.tfidf.transform([text])

            chi_tiet = []
            loai_du_doan = []
            xac_suat_max = 0.0

            for loai_id, info in self.mo_hinh.items():
                loai_id_int = int(loai_id)
                loai_ten    = info.get('loai_ten', self.id_to_loai.get(loai_id_int, f'Loại {loai_id}'))
                best_name   = info.get('best_model', 'RandomForest')
                # Ngưỡng riêng của loại này (đã tối ưu lúc train)
                threshold   = float(info.get('threshold', nguong_canh_bao))

                # Lấy model tốt nhất từ dict 'models'
                models_dict = info.get('models', {})
                model = models_dict.get(best_name)

                # Fallback nếu best_name không khớp key trong models_dict
                if model is None:
                    for fallback in ('RandomForest', 'XGBoost', 'DecisionTree'):
                        model = models_dict.get(fallback)
                        if model is not None:
                            best_name = fallback
                            break

                if model is None:
                    continue  # bỏ qua loại này nếu không có model

                # Xác suất
                if hasattr(model, 'predict_proba'):
                    proba = model.predict_proba(X)[0]
                    xac_suat = float(proba[1]) if len(proba) > 1 else float(proba[0])
                else:
                    xac_suat = float(model.predict(X)[0])

                # Quyết định dựa trên threshold riêng của loại
                du_doan = 1 if xac_suat >= threshold else 0

                chi_tiet.append({
                    "loai_id":   loai_id_int,
                    "loai_ten":  loai_ten,
                    "du_doan":   du_doan,
                    "xac_suat":  xac_suat,
                    "threshold": threshold,
                    "mo_hinh":   best_name,
                })

                if du_doan == 1:
                    loai_du_doan.append(loai_ten)

                xac_suat_max = max(xac_suat_max, xac_suat)

            # Sắp xếp theo xác suất giảm dần
            chi_tiet.sort(key=lambda x: x['xac_suat'], reverse=True)

            # Điểm nghi ngờ tổng thể
            if loai_du_doan:
                diem = max(ct['xac_suat'] for ct in chi_tiet if ct['du_doan'] == 1)
            else:
                diem = xac_suat_max

            canh_bao = len(loai_du_doan) > 0 or diem >= nguong_canh_bao

            return {
                "canh_bao":      canh_bao,
                "diem_nghi_ngo": float(diem),
                "loai_du_doan":  loai_du_doan,
                "so_loai":       len(loai_du_doan),
                "chi_tiet":      chi_tiet,
                "nguon":         "ml_model",
                "ghi_chu":       (f"Phát hiện {len(loai_du_doan)} loại lừa đảo"
                                  if loai_du_doan else "Không phát hiện lừa đảo rõ ràng"),
            }

        except Exception as e:
            print(f"[ERROR] ML prediction error: {e}")
            return self._ket_qua_rong(f"Loi du doan: {e}")
    
    def _predict_rule_based(
        self, 
        keywords: List[str],
        nguong_canh_bao: float
    ) -> Dict:
        """
        Fallback: Dự đoán bằng rule-based (đếm từ khóa match).
        Dùng khi chưa có ML model.
        """
        if not keywords or not self.tu_khoa_dac_trung:
            return self._ket_qua_rong("Không đủ dữ liệu cho rule-based")
        
        chi_tiet = []
        keywords_chuan = [self._chuan_hoa_tu_khoa(kw) for kw in keywords]
        
        for loai_ten, tk_list in self.tu_khoa_dac_trung.items():
            # Đếm match
            so_match = 0
            for kw in keywords_chuan:
                for tk in tk_list:
                    if kw in tk or tk in kw:
                        so_match += 1
                        break
            
            xac_suat = min(so_match / max(len(keywords), 5), 1.0)
            
            chi_tiet.append({
                "loai_ten": loai_ten,
                "du_doan": 1 if so_match >= 2 else 0,
                "xac_suat": xac_suat,
                "so_match": so_match,
                "mo_hinh": "rule_based"
            })
        
        chi_tiet.sort(key=lambda x: x['xac_suat'], reverse=True)
        
        loai_du_doan = [ct['loai_ten'] for ct in chi_tiet if ct['du_doan'] == 1]
        diem = chi_tiet[0]['xac_suat'] if chi_tiet else 0.0
        canh_bao = diem >= nguong_canh_bao or len(loai_du_doan) > 0
        
        return {
            "canh_bao": canh_bao,
            "diem_nghi_ngo": float(diem),
            "loai_du_doan": loai_du_doan,
            "so_loai": len(loai_du_doan),
            "chi_tiet": chi_tiet,
            "nguon": "rule_based",
            "ghi_chu": f"Rule-based: {len(loai_du_doan)} loại" if loai_du_doan else "Không match đủ từ khóa"
        }
    
    def _ket_qua_rong(self, ghi_chu: str) -> Dict:
        """Trả về kết quả rỗng."""
        return {
            "canh_bao": False,
            "diem_nghi_ngo": 0.0,
            "loai_du_doan": [],
            "so_loai": 0,
            "chi_tiet": [],
            "nguon": "empty",
            "ghi_chu": ghi_chu
        }
    
    def get_summary(self, result: Dict) -> str:
        """Tạo summary text từ kết quả."""
        if result["so_loai"] == 0:
            return "Không phát hiện loại lừa đảo cụ thể."
        elif result["so_loai"] == 1:
            return f"Nghi ngờ: **{result['loai_du_doan'][0]}** ({result['diem_nghi_ngo']:.0%})"
        else:
            return f"**CẢNH BÁO**: Phát hiện {result['so_loai']} loại lừa đảo: {', '.join(result['loai_du_doan'])}"


# ============================================
# SINGLETON & CONVENIENCE FUNCTIONS
# ============================================

_predictor: Optional[MultilabelPredictor] = None


def get_multilabel_predictor() -> MultilabelPredictor:
    """Lấy singleton predictor."""
    global _predictor
    if _predictor is None:
        _predictor = MultilabelPredictor()
        _predictor.load_models()
    return _predictor


def predict_loai_lua_dao(text: str = "", keywords: List[str] = None) -> Dict:
    """
    Hàm tiện ích: Dự đoán loại lừa đảo.
    
    Args:
        text: Văn bản từ khóa (cho TF-IDF)
        keywords: Danh sách từ khóa
        
    Returns:
        Dict kết quả với canh_bao, diem_nghi_ngo, loai_du_doan, chi_tiet
    """
    predictor = get_multilabel_predictor()
    return predictor.predict(text=text, keywords=keywords)


if __name__ == "__main__":
    # Test
    predictor = MultilabelPredictor()
    predictor.load_models()

    test_keywords = ["công an", "chuyển tiền", "khẩn cấp", "bắt giam", "vi phạm"]
    result = predictor.predict(keywords=test_keywords)

    print(f"\nTest keywords: {test_keywords}")
    print(f"Cảnh báo: {result['canh_bao']}")
    print(f"Điểm: {result['diem_nghi_ngo']:.2%}")
    print(f"Loại: {result['loai_du_doan']}")
    print(f"Nguồn: {result['nguon']}")