# src/analysis_engine.py
"""
Pipeline phân tích chính: Audio → Transcript chunks → Keywords → Score từng chunk.

Luồng xử lý:
    uploaded_file (bytes)
        → SpeechToText.transcribe_chunks_from_bytes()   [chunk 10s]
        → _match_keywords_from_text()                   [quét keywords.json]
        → MultilabelPredictor.predict(keywords)
        → List[ChunkResult] lưu vào session_state["chunk_scores"]

Mỗi ChunkResult là dict:
    {
        "time_label": "00:10",   # start_sec format MM:SS  (dùng cho trục X chart)
        "time_end":   "00:20",   # end_sec format MM:SS
        "time_range": "00:10-00:20",
        "diem":       0.72,      # diem_nghi_ngo từ multilabel_predictor (0-1)
        "text":       "...",     # transcript câu thoại
        "keywords":   [...],     # keywords trích xuất
        "loai":       [...],     # loai_du_doan từ model
    }
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
import streamlit as st
from pathlib import Path
from typing import List, Dict

from .speech_to_text import SpeechToText, DEFAULT_CHUNK_DURATION
from .multilabel_predictor import MultilabelPredictor


# ── Singleton instances (khởi tạo lazy, dùng chung trong session) ──────────
_stt:         SpeechToText        | None = None
_predictor:   MultilabelPredictor | None = None
_predefined_keywords: List[str]   | None = None


def _get_stt() -> SpeechToText:
    global _stt
    if _stt is None:
        _stt = SpeechToText()
    return _stt


def _get_predictor() -> MultilabelPredictor:
    global _predictor
    if _predictor is None:
        _predictor = MultilabelPredictor()
        _predictor.load_models()
    return _predictor


def _load_predefined_keywords() -> List[str]:
    """
    Load và flatten toàn bộ từ khoá từ config/keywords.json.
    Kết quả được cache trong biến module-level để không đọc file lại.
    Sắp xếp theo độ dài giảm dần để ưu tiên khớp cụm dài trước.
    """
    global _predefined_keywords
    if _predefined_keywords is None:
        kw_path = Path(__file__).parent.parent / "config" / "keywords.json"
        with open(kw_path, "r", encoding="utf-8") as f:
            kw_dict = json.load(f)
        flat: List[str] = []
        for kw_list in kw_dict.values():
            flat.extend(kw_list)
        # Loại trùng, sắp xếp cụm dài trước để tránh khớp một phần
        _predefined_keywords = sorted(set(flat), key=len, reverse=True)
    return _predefined_keywords


def _match_keywords_from_text(text: str) -> List[str]:
    """
    Quét text và trả về những từ khoá CÓ TRONG danh sách keywords.json.
    Dùng word-boundary matching (không khớp giữa chừng một từ).
    """
    if not text:
        return []
    predefined = _load_predefined_keywords()
    text_lower = text.lower()
    matched: List[str] = []
    seen: set = set()
    for kw in predefined:
        kw_lower = kw.lower()
        # Dùng regex word-boundary để tránh khớp sai (vd: "an" trong "khan")
        pattern = r'(?<![a-zA-ZÀ-ỹ])' + re.escape(kw_lower) + r'(?![a-zA-ZÀ-ỹ])'
        if re.search(pattern, text_lower) and kw_lower not in seen:
            matched.append(kw)
            seen.add(kw_lower)
    return matched


# ── Helpers ─────────────────────────────────────────────────────────────────

def _fmt_time(sec: float) -> str:
    """Chuyển giây → chuỗi MM:SS."""
    sec = max(0, int(sec))
    return f"{sec // 60:02d}:{sec % 60:02d}"


def _score_chunk(text: str, predictor: MultilabelPredictor) -> Dict:
    """
    Từ transcript text của 1 chunk → trả về keywords + diem + loai.
    Nếu text rỗng → trả về diem = 0.

    Keywords được trích bằng cách quét trực tiếp transcript đối chiếu
    với danh sách từ khoá định sẵn trong config/keywords.json —
    KHÔNG dùng LLM để tránh trích từ khoá ngoài danh sách.
    LLM vẫn được gọi để lấy signals/scammer_quote (phục vụ giải thích).
    """
    if not text or not text.strip():
        return {"keywords": [], "diem": 0.0, "loai": []}

    # 1. Trích từ khoá bằng quét trực tiếp danh sách định sẵn (keywords.json)
    keywords: List[str] = _match_keywords_from_text(text)

    # 2. Multilabel predict → diem_nghi_ngo
    # Chuẩn hoá từ khoá về dạng gạch dưới TRƯỚC khi đưa vào TF-IDF
    # (TF-IDF được train trên "rửa_tiền", "tài_khoản", ... – không phải khoảng trắng)
    try:
        kw_text = " ".join(
            re.sub(r'\s+', '_', kw.lower().strip()) for kw in keywords
        )
        pred = predictor.predict(text=kw_text, keywords=keywords)
        diem  = float(pred.get("diem_nghi_ngo", 0.0))
        loai  = pred.get("loai_du_doan", [])
    except Exception:
        diem = 0.0
        loai = []

    return {"keywords": keywords, "diem": diem, "loai": loai}


# ── API chính ────────────────────────────────────────────────────────────────

def run_analysis(
    audio_bytes: bytes,
    filename: str,
    chunk_duration: int = DEFAULT_CHUNK_DURATION,
    progress_callback=None,
) -> List[Dict]:
    """
    Chạy toàn bộ pipeline phân tích cho 1 file audio.

    Args:
        audio_bytes:       Raw bytes của file audio (từ session_state["uploaded_file"].getvalue())
        filename:          Tên file gốc (để detect format cho pydub)
        chunk_duration:    Độ dài mỗi chunk tính bằng giây (mặc định 10s)
        progress_callback: Hàm nhận (done, total) để cập nhật progress bar (optional)

    Returns:
        List[ChunkResult] — đã được lưu vào st.session_state["chunk_scores"]
    """
    stt       = _get_stt()
    predictor = _get_predictor()

    chunk_scores: List[Dict] = []

    # Ước tính tổng số chunk để tính progress
    try:
        total_sec   = stt.get_audio_duration(audio_bytes, filename)
        total_chunks = max(1, int(total_sec // chunk_duration) + (1 if total_sec % chunk_duration else 0))
    except Exception:
        total_chunks = 1

    done = 0
    for chunk_idx, start_sec, end_sec, text, error in stt.transcribe_chunks_from_bytes(
        audio_bytes, filename, chunk_duration
    ):
        done += 1
        if progress_callback:
            progress_callback(done, total_chunks)

        if error:
            # Chunk lỗi → ghi nhận nhưng diem = 0
            chunk_scores.append({
                "time_label": _fmt_time(start_sec),
                "time_end":   _fmt_time(end_sec),
                "time_range": f"{_fmt_time(start_sec)}-{_fmt_time(end_sec)}",
                "diem":       0.0,
                "text":       f"[Lỗi chunk: {error}]",
                "keywords":   [],
                "loai":       [],
            })
            continue

        scored = _score_chunk(text, predictor)

        chunk_scores.append({
            "time_label": _fmt_time(start_sec),
            "time_end":   _fmt_time(end_sec),
            "time_range": f"{_fmt_time(start_sec)}-{_fmt_time(end_sec)}",
            "diem":       scored["diem"],
            "text":       text or "",
            "keywords":   scored["keywords"],
            "loai":       scored["loai"],
        })

    # Cache kết quả vào session_state để không chạy lại khi re-render
    st.session_state["chunk_scores"] = chunk_scores

    # ── Tính diem_nghi_ngo tổng thể: Weighted Temporal Aggregation ────────
    # Công thức:
    #   S = α·max(sᵢ) + β·Σ(wᵢ·sᵢ)/Σwᵢ + γ·|{i: sᵢ≥θ}|/N
    # Trong đó:
    #   α=0.40  → đỉnh nguy hiểm cao nhất (chunk kẻ lừa đảo đang "chốt")
    #   β=0.40  → mật độ trung bình có trọng số vị trí (Gaussian, tâm giữa)
    #   γ=0.20  → tỷ lệ chunk vượt ngưỡng (chống 1 chunk outlier kéo điểm giả)
    #   θ=0.40  → nhất quán với NGUONG_CANH_BAO của MultilabelPredictor
    #   wᵢ     → phân phối Gaussian: chunk giữa cuộc gọi có trọng số cao hơn
    if chunk_scores:
        ALPHA, BETA, GAMMA = 0.40, 0.40, 0.20
        THETA = 0.40   # khớp NGUONG_CANH_BAO trong multilabel_predictor.py

        scores = [c["diem"] for c in chunk_scores]
        N = len(scores)

        # Trọng số Gaussian theo vị trí: wᵢ = 1 + 0.5·exp(-(i-μ)²/(2σ²))
        mu    = (N - 1) / 2.0
        sigma = max(N / 4.0, 0.5)   # tránh chia 0 khi N=1
        weights = [
            1.0 + 0.5 * math.exp(-((i - mu) ** 2) / (2 * sigma ** 2))
            for i in range(N)
        ]

        s_max      = max(scores)
        w_sum      = sum(weights)
        s_weighted = sum(w * s for w, s in zip(weights, scores)) / w_sum
        coverage   = sum(1 for s in scores if s >= THETA) / N

        diem_tong = ALPHA * s_max + BETA * s_weighted + GAMMA * coverage
        diem_tong = min(diem_tong, 1.0)   # clip về [0, 1]
    else:
        diem_tong = 0.0
    st.session_state["diem_nghi_ngo"] = diem_tong

    # Tổng hợp keywords toàn cuộc gọi với tần suất (dùng cho kw-card)
    all_kw: List[str] = []
    for c in chunk_scores:
        all_kw.extend(c["keywords"])
    kw_counter = Counter(all_kw)
    # Sắp xếp theo tần suất giảm dần, giữ tối đa 20 từ
    st.session_state["keywords_count"] = kw_counter.most_common(20)

    return chunk_scores


def get_chunk_scores() -> List[Dict]:
    """Lấy chunk_scores từ session_state (đã tính sẵn)."""
    return st.session_state.get("chunk_scores", [])


def is_analysis_done() -> bool:
    """Kiểm tra pipeline đã chạy xong chưa."""
    return "chunk_scores" in st.session_state