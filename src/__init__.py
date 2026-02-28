# src/__init__.py
"""
Source modules cho Phân tích Lừa đảo Demo.

Modules:
- multilabel_predictor: Mô hình - Multi-label Classification  
- llm_client: Trích xuất từ khóa và giải thích kết quả
- speech_to_text: Chuyển đổi audio thành text (Groq Whisper)
"""

from .multilabel_predictor import predict_multilabel
from .llm_client import extract_keywords, explain_result
from .analysis_engine import run_analysis, get_chunk_scores, is_analysis_done
from .chart_builder import build_line_chart_html
from .speech_to_text import (
    SpeechToText,
    transcribe_audio,
    transcribe_audio_bytes,
    transcribe_streaming,
    get_stt_client,
)

__all__ = [
    # Multi-label
    "predict_multilabel",
    # LLM
    "extract_keywords",
    "explain_result",
    # Speech-to-Text
    "SpeechToText",
    "transcribe_audio",
    "transcribe_audio_bytes",
    "transcribe_streaming",
    "get_stt_client",
]