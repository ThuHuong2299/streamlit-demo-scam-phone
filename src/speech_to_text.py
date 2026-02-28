# src/speech_to_text.py
"""
Module Speech-to-Text sử dụng Groq Whisper API.
Chức năng:
1. Transcribe file audio (mp3, wav, m4a)
2. Chia audio thành chunks để xử lý streaming
3. Hỗ trợ tiếng Việt
"""

import os
import io
import tempfile
from pathlib import Path
from typing import Optional, List, Generator, Tuple

# Groq client — import ở đây để property client() có thể dùng trực tiếp
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    Groq = None
    GROQ_AVAILABLE = False

# Check if pydub is available
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

# CẤU HÌNH
from dotenv import load_dotenv

load_dotenv()

# API Key — ưu tiên Streamlit secrets (Cloud), fallback về .env (local)
def _get_groq_key() -> str:
    try:
        import streamlit as st
        return st.secrets.get("GROQ_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
    except Exception:
        return os.getenv("GROQ_API_KEY", "")

GROQ_API_KEY = _get_groq_key()

# Model Whisper tốt nhất của Groq (học từ groq_whisperer)
WHISPER_MODEL = "whisper-large-v3"

# Không dùng prompt - chỉ transcribe thuần túy từ audio sang text
DEFAULT_PROMPT = ""

# Chunk duration cho streaming (giây)
DEFAULT_CHUNK_DURATION = 10  # 10 giây mỗi chunk


class SpeechToText:
    """
    Client Speech-to-Text sử dụng Groq Whisper API.
    
    Học hỏi từ groq_whisperer:
    - Cách khởi tạo Groq client
    - Cách gọi audio.transcriptions.create()
    - Các parameters quan trọng: model, prompt, response_format, language
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: str = WHISPER_MODEL,
        language: str = "vi",
        prompt: str = DEFAULT_PROMPT
    ):
        """
        Khởi tạo Speech-to-Text client.
        
        Args:
            api_key: Groq API key (mặc định lấy từ config)
            model: Whisper model name (mặc định: whisper-large-v3)
            language: Ngôn ngữ (mặc định: vi - tiếng Việt)
            prompt: Context prompt để cải thiện accuracy
        """
        self.api_key = api_key or GROQ_API_KEY
        self.model = model
        self.language = language
        self.prompt = prompt
        self._client = None
    
    @property
    def client(self):
        """Lazy initialization của Groq client."""
        if self._client is None:
            if not GROQ_AVAILABLE or Groq is None:
                raise RuntimeError(
                    "Thư viện groq chưa được cài. Chạy: pip install groq"
                )
            self._client = Groq(api_key=self.api_key)
        return self._client
    
    def transcribe_file(
        self, 
        audio_path: str,
        prompt: Optional[str] = None,
        language: Optional[str] = None
    ) -> str:
        """
        Transcribe toàn bộ file audio thành text.
        
        Học từ groq_whisperer:
        ```python
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(audio_file_path), file.read()),
            model="whisper-large-v3",
            response_format="text",
            language="en",
        )
        ```
        
        Args:
            audio_path: Đường dẫn file audio (mp3, wav, m4a)
            prompt: Context prompt (optional, override default)
            language: Ngôn ngữ (optional, override default)
            
        Returns:
            Transcript text
        """
        try:
            with open(audio_path, "rb") as file:
                # Gọi Groq Whisper API (pattern từ groq_whisperer)
                transcription = self.client.audio.transcriptions.create(
                    file=(os.path.basename(audio_path), file.read()),
                    model=self.model,
                    prompt=prompt or self.prompt,
                    response_format="text",
                    language=language or self.language,
                )
            return transcription
        except Exception as e:
            print(f"❌ Lỗi transcribe: {e}")
            return ""
    
    def transcribe_bytes(
        self,
        audio_bytes: bytes,
        filename: str = "audio.wav",
        prompt: Optional[str] = None,
        language: Optional[str] = None
    ) -> str:
        """
        Transcribe audio từ bytes (cho Streamlit file_uploader).
        
        Args:
            audio_bytes: Audio data dạng bytes
            filename: Tên file (để Groq nhận diện format)
            prompt: Context prompt (optional)
            language: Ngôn ngữ (optional)
            
        Returns:
            Transcript text
        """
        try:
            transcription = self.client.audio.transcriptions.create(
                file=(filename, audio_bytes),
                model=self.model,
                prompt=prompt or self.prompt,
                response_format="text",
                language=language or self.language,
            )
            return transcription
        except Exception as e:
            print(f"❌ Lỗi transcribe bytes: {e}")
            return ""
    
    def transcribe_chunks_generator(
        self,
        audio_path: str,
        chunk_duration: int = DEFAULT_CHUNK_DURATION,
        prompt: Optional[str] = None
    ) -> Generator[Tuple[int, float, float, str], None, None]:
        """
        Transcribe audio theo từng chunk (STREAMING MODE).
        
        Đây là phần MỚI - không có trong groq_whisperer.
        Cho phép xử lý real-time: mỗi chunk transcribe xong sẽ yield ngay.
        
        Args:
            audio_path: Đường dẫn file audio
            chunk_duration: Độ dài mỗi chunk (giây)
            prompt: Context prompt
            
        Yields:
            Tuple (chunk_index, start_time, end_time, transcript_text)
        """
        if not PYDUB_AVAILABLE:
            raise RuntimeError("Cần cài pydub để dùng streaming mode: pip install pydub")
        
        # Load audio
        audio = AudioSegment.from_file(audio_path)
        total_duration = len(audio) / 1000  # milliseconds to seconds
        chunk_ms = chunk_duration * 1000
        
        chunk_index = 0
        
        for start_ms in range(0, len(audio), chunk_ms):
            end_ms = min(start_ms + chunk_ms, len(audio))
            start_sec = start_ms / 1000
            end_sec = end_ms / 1000
            tmp_path = None
            
            try:
                chunk = audio[start_ms:end_ms]
                
                # Export chunk to temporary WAV file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    chunk.export(tmp.name, format="wav")
                    tmp_path = tmp.name
                
                # Transcribe chunk
                transcript = self.transcribe_file(tmp_path, prompt=prompt)
                
                yield (chunk_index, start_sec, end_sec, transcript, None)
                
            except Exception as e:
                # Trả về lỗi thay vì crash
                error_msg = str(e)
                yield (chunk_index, start_sec, end_sec, "", error_msg)
            finally:
                # Cleanup temp file
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                chunk_index += 1
    
    def transcribe_chunks_from_bytes(
        self,
        audio_bytes: bytes,
        filename: str = "audio.mp3",
        chunk_duration: int = DEFAULT_CHUNK_DURATION,
        prompt: Optional[str] = None
    ) -> Generator[Tuple[int, float, float, str], None, None]:
        """
        Transcribe audio bytes theo từng chunk (cho Streamlit upload).
        
        Args:
            audio_bytes: Audio data dạng bytes
            filename: Tên file gốc (để detect format)
            chunk_duration: Độ dài mỗi chunk (giây)
            prompt: Context prompt
            
        Yields:
            Tuple (chunk_index, start_time, end_time, transcript_text)
        """
        if not PYDUB_AVAILABLE:
            raise RuntimeError("Cần cài pydub để dùng streaming mode: pip install pydub")
        
        # Detect format from filename
        ext = Path(filename).suffix.lower().lstrip(".")
        if ext == "m4a":
            ext = "mp4"  # pydub uses mp4 for m4a
        
        # Load audio from bytes
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=ext)
        total_duration = len(audio) / 1000
        chunk_ms = chunk_duration * 1000
        
        chunk_index = 0
        
        for start_ms in range(0, len(audio), chunk_ms):
            end_ms = min(start_ms + chunk_ms, len(audio))
            start_sec = start_ms / 1000
            end_sec = end_ms / 1000
            tmp_path = None
            
            try:
                chunk = audio[start_ms:end_ms]
                
                # Export chunk to temporary WAV file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    chunk.export(tmp.name, format="wav")
                    tmp_path = tmp.name
                
                # Transcribe chunk
                transcript = self.transcribe_file(tmp_path, prompt=prompt)
                
                yield (chunk_index, start_sec, end_sec, transcript, None)
                
            except Exception as e:
                # Trả về lỗi thay vì crash
                error_msg = str(e)
                yield (chunk_index, start_sec, end_sec, "", error_msg)
            finally:
                # Cleanup temp file
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                chunk_index += 1
    
    def get_audio_duration(self, audio_bytes: bytes, filename: str = "audio.mp3") -> float:
        """Lấy tổng thời lượng audio (giây)."""
        if not PYDUB_AVAILABLE:
            return 0.0
        
        ext = Path(filename).suffix.lower().lstrip(".")
        if ext == "m4a":
            ext = "mp4"
        
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=ext)
        return len(audio) / 1000


# =========================
# HELPER FUNCTIONS
# =========================

# Singleton instance
_stt_instance: Optional[SpeechToText] = None


def get_stt_client() -> SpeechToText:
    """Lấy singleton instance của SpeechToText."""
    global _stt_instance
    if _stt_instance is None:
        _stt_instance = SpeechToText()
    return _stt_instance


def transcribe_audio(audio_path: str) -> str:
    """
    Helper function - Transcribe file audio.
    
    Args:
        audio_path: Đường dẫn file
        
    Returns:
        Transcript text
    """
    return get_stt_client().transcribe_file(audio_path)


def transcribe_audio_bytes(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    """
    Helper function - Transcribe audio bytes.
    
    Args:
        audio_bytes: Audio data
        filename: Tên file
        
    Returns:
        Transcript text
    """
    return get_stt_client().transcribe_bytes(audio_bytes, filename)


def transcribe_streaming(
    audio_bytes: bytes, 
    filename: str = "audio.mp3",
    chunk_duration: int = DEFAULT_CHUNK_DURATION
) -> Generator[Tuple[int, float, float, str], None, None]:
    """
    Helper function - Transcribe audio streaming theo chunks.
    
    Args:
        audio_bytes: Audio data
        filename: Tên file
        chunk_duration: Độ dài chunk (giây)
        
    Yields:
        Tuple (chunk_index, start_time, end_time, transcript)
    """
    yield from get_stt_client().transcribe_chunks_from_bytes(
        audio_bytes, filename, chunk_duration
    )


# =========================
# TEST
# =========================

if __name__ == "__main__":
    # Test basic transcription
    print("🎤 Speech-to-Text Module")
    print(f"   Model: {WHISPER_MODEL}")
    print(f"   Language: vi")
    print(f"   Chunk duration: {DEFAULT_CHUNK_DURATION}s")
    
    stt = SpeechToText()
    print(f"✅ Groq client initialized")