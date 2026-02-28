"""
src/loading_screen.py
────────────────────────────────────────────────────────────────
Loading screen hiển thị trong khi run_analysis() xử lý chunks.

ROOT CAUSE CỦA LỖI RENDER THÀNH TEXT:
  Streamlit markdown() sanitizer XÓA toàn bộ <style> block.
  Kết quả: không có CSS → browser render HTML tags thành text thuần.

GIẢI PHÁP TRIỆT ĐỂ:
  - KHÔNG dùng <style> block ở bất kỳ đâu
  - 100% inline style="..." trên mỗi element
  - Keyframe animations nhúng qua <style> được inject bằng
    st.markdown() RIÊNG trước khi show loading screen
    (Streamlit cho phép inject <style> qua st.markdown một lần
     ở đầu app, khác với trong component HTML)
────────────────────────────────────────────────────────────────
"""

import math
import streamlit as st

_CIRCUMFERENCE = 2 * math.pi * 56  # r = 56


# ── Keyframe CSS inject một lần vào <head> của Streamlit ─────────────────
# st.markdown với unsafe_allow_html=True ở cấp app (không trong component)
# ĐƯỢC PHÉP chứa <style> — Streamlit chỉ strip style trong markdown content
_KEYFRAMES_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam:wght@400;500;600&display=swap');
@keyframes cld-float {
  0%,100% { transform: translate(0,0) scale(1); }
  20%      { transform: translate(28px,-40px) scale(1.08); }
  40%      { transform: translate(-20px,-65px) scale(1.15); }
  60%      { transform: translate(35px,-45px) scale(1.1); }
  80%      { transform: translate(-12px,-30px) scale(1.05); }
}
@keyframes cld-bpulse {
  0%,100% { transform:scale(0.8); opacity:0.25; }
  50%      { transform:scale(1.2); opacity:0.5; }
}
@keyframes cld-bounce {
  0%,80%,100% { transform:translateY(0); }
  40%          { transform:translateY(-15px); }
}
@keyframes cld-fadein {
  from { opacity:0; } to { opacity:1; }
}
.cld-bubble-inner {
  position:absolute; inset:8px; border-radius:50%; opacity:0.25;
  animation: cld-bpulse 2s ease-in-out infinite;
}
</style>"""


# ── 20 bong bóng với inline style hoàn toàn ────────────────────────────────
# Mỗi bong bóng: position/size/color/animation-delay đều inline
# Màu: tím=#c4b5fd / xanh=#93c5fd / hồng=#f9a8d4 xen kẽ

def _bubble(left, top, size, color, delay, duration, opacity=0.6, border_w=2):
    """Tạo 1 bong bóng với 100% inline style."""
    inner_color = color
    inner_size = max(0, size - 16)
    return (
        f'<div style="position:absolute;border-radius:50%;'
        f'left:{left};top:{top};width:{size}px;height:{size}px;'
        f'border:{border_w}px solid {color};opacity:{opacity};'
        f'animation:cld-float {duration}s ease-in-out infinite {delay}s;">'
        f'<div class="cld-bubble-inner" '
        f'style="background:{inner_color};'
        f'animation-delay:{delay}s;"></div>'
        f'</div>'
    )


def _build_bubbles():
    specs = [
        # (left, top, size, color,     delay, duration, opacity, border_w)
        # Góc trên trái
        ("3%",   "5%",  120, "#c4b5fd", 0.0,  5.0,  0.22, 3),
        ("9%",   "14%",  48, "#93c5fd", 0.6,  3.4,  0.45, 2),
        ("18%",  "4%",   22, "#f9a8d4", 1.2,  2.6,  0.60, 2),
        # Góc trên phải
        ("80%",  "3%",   90, "#f9a8d4", 0.3,  4.5,  0.25, 3),
        ("72%",  "12%",  36, "#c4b5fd", 0.9,  3.1,  0.45, 2),
        ("91%",  "18%",  16, "#93c5fd", 1.5,  2.3,  0.60, 2),
        # Rìa trái giữa
        ("1%",   "38%",  64, "#93c5fd", 0.5,  4.2,  0.30, 3),
        ("7%",   "55%",  28, "#f9a8d4", 1.1,  3.6,  0.50, 2),
        ("13%",  "70%",  14, "#c4b5fd", 1.8,  2.8,  0.60, 2),
        # Rìa phải giữa
        ("88%",  "42%",  72, "#c4b5fd", 0.2,  4.8,  0.28, 3),
        ("93%",  "58%",  32, "#93c5fd", 0.8,  3.3,  0.50, 2),
        ("82%",  "68%",  18, "#f9a8d4", 1.4,  2.5,  0.60, 2),
        # Phần dưới trái
        ("5%",   "80%", 100, "#f9a8d4", 0.4,  5.2,  0.22, 3),
        ("22%",  "88%",  42, "#c4b5fd", 1.0,  3.7,  0.45, 2),
        ("32%",  "78%",  20, "#93c5fd", 1.6,  2.9,  0.60, 2),
        # Phần dưới phải
        ("72%",  "82%",  80, "#93c5fd", 0.7,  4.6,  0.27, 3),
        ("84%",  "90%",  36, "#f9a8d4", 1.3,  3.0,  0.50, 2),
        ("60%",  "91%",  12, "#c4b5fd", 0.1,  2.4,  0.60, 2),
        # Trung tâm rải rác
        ("44%",  "8%",   54, "#f9a8d4", 0.9,  4.0,  0.30, 2),
        ("50%",  "88%",  26, "#93c5fd", 1.7,  3.5,  0.55, 2),
    ]
    return "".join(_bubble(*s) for s in specs)


def _build_html(percent: int, status_text: str) -> str:
    dashoffset = _CIRCUMFERENCE * (1 - percent / 100)

    bubbles = _build_bubbles()

    # SVG progress circle
    svg = (
        '<svg width="128" height="128" viewBox="0 0 128 128" '
        'style="transform:rotate(-90deg);display:block;">'
        '<defs>'
        '<linearGradient id="pg-grad-cld" x1="0%" y1="0%" x2="100%" y2="100%">'
        '<stop offset="0%" stop-color="#ec4899"/>'
        '<stop offset="100%" stop-color="#f472b6"/>'
        '</linearGradient>'
        '</defs>'
        '<circle cx="64" cy="64" r="56" stroke="#e0e0e0" stroke-width="4" fill="none" opacity="0.3"/>'
        f'<circle cx="64" cy="64" r="56"'
        f' stroke="url(#pg-grad-cld)" stroke-width="4" fill="none" stroke-linecap="round"'
        f' stroke-dasharray="{_CIRCUMFERENCE:.1f}"'
        f' stroke-dashoffset="{dashoffset:.1f}"'
        f' style="transition:stroke-dashoffset 0.4s ease;"/>'
        '</svg>'
    )

    # 3 dots bounce
    dots = (
        '<div style="display:flex;gap:8px;margin-top:8px;">'
        + "".join(
            f'<div style="width:12px;height:12px;border-radius:50%;background:#f472b6;'
            f'animation:cld-bounce 1.4s ease-in-out infinite {delay}s;"></div>'
            for delay in [0, 0.2, 0.4]
        )
        + "</div>"
    )

    # Overlay wrapper — 100% inline, không dùng class nào có CSS ngoài
    html = (
        '<div style="'
        'position:fixed;top:0;left:0;width:100vw;height:100vh;'
        'z-index:999999;'
        'background:linear-gradient(135deg,#dbeafe 0%,#ede9fe 50%,#fce7f3 100%);'
        'display:flex;align-items:center;justify-content:center;'
        'font-family:Be Vietnam,sans-serif;'
        'animation:cld-fadein 0.4s ease;'
        'overflow:hidden;">'
        + bubbles
        # Center card
        + '<div style="display:flex;flex-direction:column;align-items:center;'
        'gap:16px;position:relative;z-index:1;">'
        # SVG ring
        +   '<div style="position:relative;width:128px;height:128px;">'
        +     svg
        +     f'<div style="position:absolute;inset:0;display:flex;'
              f'align-items:center;justify-content:center;'
              f'font-size:28px;font-weight:700;color:#ec4899;">{percent}%</div>'
        +   '</div>'
        # Title
        +   '<div style="font-size:22px;font-weight:600;color:#374151;margin-top:4px;">'
              'Đang phân tích'
            '</div>'
        # Subtitle / status
        +   f'<div style="font-size:14px;color:#6b7280;'
              f'max-width:280px;text-align:center;line-height:1.5;">'
              f'{status_text}'
            '</div>'
        + dots
        + '</div>'  # end center
        + '</div>'  # end overlay
    )
    return html


class LoadingScreen:
    """
    Loading screen toàn màn hình — 100% inline style, không có <style> block.

    20 bong bóng kích thước 12px→120px, 3 màu xen kẽ (tím/xanh/hồng),
    phân bổ đều toàn màn hình theo layout Streamlit.
    """

    def __init__(self, total_chunks: int = 0):
        self.total_chunks = total_chunks
        self._placeholder = None
        self._keyframes_injected = False

    def _inject_keyframes(self):
        """Inject keyframe CSS một lần duy nhất vào app."""
        if not self._keyframes_injected:
            st.markdown(_KEYFRAMES_CSS, unsafe_allow_html=True)
            self._keyframes_injected = True

    def show(self, status_text: str = "Đang chuẩn bị xử lý..."):
        self._inject_keyframes()
        self._placeholder = st.empty()
        self._render(percent=0, status_text=status_text)

    def update(self, done: int, total: int = 0, status_text: str = ""):
        if self._placeholder is None:
            self.show()
            return

        real_total = total or self.total_chunks
        if real_total > 0:
            percent = min(int(done / real_total * 100), 99)
        else:
            percent = 99

        if not status_text:
            status_text = (
                f"Đang xử lý đoạn {done}/{real_total}..."
                if real_total > 0
                else f"Đã xử lý {done} đoạn..."
            )

        self._render(percent=percent, status_text=status_text)

    def done(self):
        if self._placeholder is not None:
            self._render(percent=100, status_text="Hoàn tất! Đang tải kết quả...")
            self._placeholder.empty()
            self._placeholder = None

    def _render(self, percent: int, status_text: str):
        html = _build_html(percent=percent, status_text=status_text)
        self._placeholder.markdown(html, unsafe_allow_html=True)


# ── Helper ─────────────────────────────────────────────────────────────────

def estimate_chunks(
    audio_bytes: bytes,
    filename: str = "audio.mp3",
    chunk_duration: int = 10,
) -> int:
    try:
        import io
        from pathlib import Path
        from pydub import AudioSegment

        ext = Path(filename).suffix.lower().lstrip(".")
        if ext == "m4a":
            ext = "mp4"
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=ext)
        return math.ceil(len(audio) / 1000 / chunk_duration)
    except Exception:
        return 0