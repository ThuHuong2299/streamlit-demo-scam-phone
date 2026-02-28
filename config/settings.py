# config/settings.py
"""Cấu hình cho hệ thống phân tích cuộc gọi lừa đảo (phiên bản mới)."""

from pathlib import Path

# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

# Data files
RAW_DATA_PATH = DATA_DIR / "data_scam_fix.csv"

# =========================
# MODEL FILES - Mô hình 2 (Đa lớp trên nhãn thật)
# =========================
MULTILABEL_MODEL_PATH = MODELS_DIR / "mo_hinh_da_lop.pkl"
TFIDF_PATH = MODELS_DIR / "tfidf_vectorizer_v2.pkl"
MAPPING_LOAI_PATH = MODELS_DIR / "mapping_loai.json"
TU_KHOA_DAC_TRUNG_LOAI_PATH = MODELS_DIR / "tu_khoa_dac_trung_loai.json"

# =========================
# LLM CONFIGURATION
# =========================
DEFAULT_LLM_MODEL = "llama-3.1-8b-instant"
LLM_TEMPERATURE_EXTRACT = 0.2
LLM_TEMPERATURE_EXPLAIN = 0.3
LLM_MAX_TOKENS = 900

# =========================
# MODEL PARAMETERS
# =========================
RANDOM_STATE = 42
NGUONG_CANH_BAO = 0.4  # Ngưỡng xác suất để cảnh báo

# =========================
# 14 LOẠI LỪA ĐẢO (NHÃN THẬT - Mô hình 2)
# =========================
LOAI_LUA_DAO = {
    1: "Giả danh cơ sở giáo dục",
    2: "Giả danh nhân viên bảo hiểm",
    3: "Giả mạo cơ quan xuất khẩu lao động",
    4: "Giả mạo cục viễn thông",
    5: "Giả mạo là công an",
    6: "Giả mạo người giao hàng",
    7: "Giả mạo nhà tuyển dụng",
    8: "Giả mạo đại sứ quán",
    9: "Lừa đảo liên quan sức khỏe",
    10: "Lừa đảo ngoại tình",
    11: "Lừa đảo phí điện nước",
    12: "Lừa đảo quà tặng",
    13: "Lừa đảo tài chính – ngân hàng",
    14: "Lừa đảo đe dọa"
}

# =========================
# 7 CHỦ ĐỀ LDA (Mô hình 1 - Giải thích ngữ nghĩa)
# =========================
SO_CHU_DE_LDA = 7
TEN_CHU_DE_LDA = {
    0: "Tuyển dụng hợp đồng",
    1: "Phúc lợi đăng ký",
    2: "Xác thực tài khoản",
    3: "Xác minh định danh",
    4: "Định danh số",
    5: "Tương tác trực tuyến",
    6: "Tác động áp lực"
}
