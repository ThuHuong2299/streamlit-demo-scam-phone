# src/llm_client.py
"""LLM client for feature extraction and result explanation."""

import os
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

# ============== ĐỌC API KEY (Streamlit Cloud secrets ĐẦU, rồi .env) ==============
def _get_api_key() -> str:
    try:
        import streamlit as st
        return st.secrets.get("GROQ_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
    except Exception:
        return os.getenv("GROQ_API_KEY", "")

API_KEY = _get_api_key()


class LLMClient:
    """Client for interacting with Groq LLM API."""
    
    def __init__(self, api_key: Optional[str] = None, default_model: str = "llama-3.1-8b-instant"):
        self.api_key = api_key or API_KEY
        self.default_model = default_model
        self._client = None
        
        if not self.api_key:
            raise RuntimeError(
                "Missing GROQ_API_KEY. Please set API_KEY in llm_client.py"
            )
    
    @property
    def client(self):
        """Lazy initialization of Groq client."""
        if self._client is None:
            from groq import Groq
            self._client = Groq(api_key=self.api_key)
        return self._client
    
    @staticmethod
    def _safe_json_load(text: str) -> dict:
        """
        Safely parse JSON from LLM response.
        Handles cases where LLM adds extra text around JSON.
        """
        text = (text or "").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON object from text
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(text[start:end + 1])
            raise ValueError(f"Could not parse JSON from: {text[:100]}...")
    
    def extract_keywords(
        self, 
        transcript: str, 
        model: Optional[str] = None
    ) -> Dict:
        """
        Extract keywords, signals, and suspicious quotes from transcript.
        
        Args:
            transcript: Call transcript text
            model: LLM model name (optional)
            
        Returns:
            Dict with keys: keywords, signals, scammer_quote
        """
        model = model or self.default_model
        
        system_prompt = """Bạn là mô-đun trích xuất từ khóa cho hệ thống phát hiện cuộc gọi lừa đảo.
BẮT BUỘC: Trả về CHỈ JSON hợp lệ, không markdown, không giải thích ngoài JSON.
Format JSON:
{
  "keywords": ["cụm_từ"],
  "signals": ["nhãn_tín_hiệu"],
  "scammer_quote": "trích 1-2 câu đáng nghi nhất (nếu có), nếu không có để rỗng"
}
Yêu cầu:
- keywords: 8-20 cụm từ ngắn, ưu tiên lời người gọi/yêu cầu hành động.
- signals: OTP / chuyển tiền / link / giả danh / hối thúc / đe doạ / thông tin nhạy cảm...
- Không bịa."""

        user_msg = f"Hãy trả về JSON theo đúng format.\n\nTRANSCRIPT:\n{(transcript or '')[:15000]}"

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.2,
                max_tokens=900,
            )
            content = response.choices[0].message.content.strip()
            return self._safe_json_load(content)
        except Exception as e:
            print(f"⚠️ LLM extraction failed: {e}")
            return {"keywords": [], "signals": [], "scammer_quote": ""}
    
    def explain_result(
        self,
        transcript: str,
        ml_score: float,
        label: str,
        keywords: List[str],
        signals: List[str],
        scammer_quote: str = "",
        loai_lua_dao: List[str] = None,
        model: Optional[str] = None,
    ) -> Dict:
        """
        Giải thích kết quả + đề xuất lời khuyên.
        
        Args:
            transcript: Transcript cuộc gọi
            ml_score: Điểm nghi ngờ (0-1)
            label: Nhãn dự đoán
            keywords: Từ khóa trích xuất
            signals: Tín hiệu nguy hiểm
            scammer_quote: Trích dẫn đáng ngờ
            loai_lua_dao: Danh sách loại lừa đảo dự đoán (từ Mô hình 2)
            model: LLM model name
            
        Returns:
            Dict: summary, reason, recommendation, loai_lua_dao
        """
        model = model or self.default_model
        
        system_prompt = """Bạn là trợ lý AI giải thích kết quả phát hiện cuộc gọi lừa đảo.
BẮT BUỘC: Trả về CHỈ JSON hợp lệ, không markdown, không giải thích ngoài JSON.
Format JSON: { "summary": "string", "reason": "string", "recommendation": "string" }
Yêu cầu:
- summary: 1-3 câu tóm tắt kết quả phân tích (bao gồm loại lừa đảo nếu phát hiện).
- reason: giải thích TẠI SAO cuộc gọi bị nghi ngờ, dựa trên chủ đề ngữ nghĩa + từ khóa + trích dẫn.
- recommendation: lời khuyên CỤ THỂ, hành động cần làm ngay, bằng tiếng Việt, dễ hiểu.
- Không bịa."""

        # Xây dựng context
        loai_text = ', '.join(loai_lua_dao) if loai_lua_dao else '(chưa xác định)'
        
        user_prompt = f"""Hãy trả về JSON theo đúng format.

KẾT QUẢ PHÂN TÍCH:
- Điểm nghi ngờ: {ml_score:.0%}
- Loại lừa đảo phát hiện: {loai_text}

KEYWORDS: {', '.join(keywords) if keywords else '(không có)'}
TÍN HIỆU NGUY HIỂM: {', '.join(signals) if signals else '(không có)'}
TRÍCH DẪN NGHI NGỜ: {scammer_quote if scammer_quote else '(không có)'}

TRANSCRIPT:
{(transcript or '')[:15000]}"""

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=900,
            )
            content = response.choices[0].message.content.strip()
            result = self._safe_json_load(content)
            result["loai_lua_dao"] = loai_lua_dao or []
            return result
        except Exception as e:
            print(f"⚠️ LLM explanation failed: {e}")
            return {
                "summary": "Không thể tạo giải thích tự động.",
                "reason": f"Điểm nghi ngờ: {ml_score:.0%}. Loại: {loai_text}",
                "recommendation": "Vui lòng xác minh thủ công. Không cung cấp thông tin cá nhân qua điện thoại.",
                "loai_lua_dao": loai_lua_dao or []
            }


# Backward compatibility - keep old function names
_default_client = None

def get_client() -> LLMClient:
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client

def extract_keywords(transcript: str, model: str = "llama-3.1-8b-instant") -> Dict:
    """Legacy function for backward compatibility."""
    return get_client().extract_keywords(transcript, model)

def explain_result(
    transcript: str,
    ml_score: float,
    label: str,
    keywords: list,
    signals: list,
    scammer_quote: str = "",
    loai_lua_dao: list = None,
    model: str = "llama-3.1-8b-instant",
) -> Dict:
    """Legacy function for backward compatibility."""
    return get_client().explain_result(
        transcript, ml_score, label, keywords, signals, scammer_quote,
        loai_lua_dao, model
    )


if __name__ == "__main__":
    # Test the LLM client
    client = LLMClient()
    
    test_transcript = """
    Tôi là nhân viên ngân hàng, tài khoản của anh đang bị khóa.
    Anh cần cung cấp mã OTP để chúng tôi xác minh và mở khóa ngay.
    Nếu không làm trong 5 phút, tiền sẽ bị mất.
    """
    
    result = client.extract_keywords(test_transcript)
    print("Keywords:", result)