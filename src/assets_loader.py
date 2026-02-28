"""
src/assets_loader.py
────────────────────────────────────────────────────────────────
Load icon và deco assets dưới dạng base64 data URI
để nhúng trực tiếp vào HTML (tránh lỗi đường dẫn tương đối).
────────────────────────────────────────────────────────────────
"""

import base64
import os

# Thư mục assets ngang cấp với src/
# src/assets_loader.py → lên 1 cấp → project root → vào assets/
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")


def _load_b64(filepath: str, mime: str) -> str:
    """Đọc file và trả về data URI base64."""
    with open(filepath, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{data}"


def icon(filename: str, mime: str = "image/svg+xml") -> str:
    """Load icon từ thư mục assets/icons/."""
    path = os.path.join(ASSETS_DIR, "icons", filename)
    return _load_b64(path, mime)


def deco(filename: str, mime: str = "image/png") -> str:
    """Load decoration image từ thư mục assets/decorations/."""
    path = os.path.join(ASSETS_DIR, "decorations", filename)
    return _load_b64(path, mime)