"""
logic/upload_handler.py
────────────────────────────────────────────────────────────────
Xử lý toàn bộ logic liên quan đến việc upload file âm thanh.

Chức năng:
  - Các định dạng file được chấp nhận
  - Validate file (loại, kích thước)
  - Xử lý kết quả upload từ st.file_uploader
  - Lưu uploaded file vào thư mục tạm (nếu cần)
  - Cập nhật session_state và điều hướng sang trang phân tích
────────────────────────────────────────────────────────────────
"""

import os
import tempfile
import streamlit as st

# ── Cấu hình ──────────────────────────────────────────────────────────────
ALLOWED_EXTENSIONS = ["mp3", "wav", "m4a", "ogg", "mp4", "mpeg4"]
ALLOWED_MIME_TYPES = [
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
    "audio/m4a",
    "audio/x-m4a",
    "audio/ogg",
    "video/mp4",
    "audio/mp4",
]
MAX_FILE_SIZE_MB = 200
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


# ── Helpers ────────────────────────────────────────────────────────────────
def get_file_extension(filename: str) -> str:
    """Trả về đuôi file (không có dấu chấm), viết thường."""
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def is_allowed_extension(filename: str) -> bool:
    """Kiểm tra đuôi file có nằm trong danh sách cho phép không."""
    return get_file_extension(filename) in ALLOWED_EXTENSIONS


def is_allowed_size(file_bytes: int) -> bool:
    """Kiểm tra kích thước file có nằm trong giới hạn không."""
    return file_bytes <= MAX_FILE_SIZE_BYTES


def validate_uploaded_file(uploaded_file) -> tuple[bool, str]:
    """
    Validate file upload từ st.file_uploader.

    Returns:
        (True, "")           → file hợp lệ
        (False, error_msg)   → file không hợp lệ, kèm thông báo lỗi
    """
    if uploaded_file is None:
        return False, "Chưa có file nào được chọn."

    if not is_allowed_extension(uploaded_file.name):
        ext = get_file_extension(uploaded_file.name)
        allowed = ", ".join(f".{e}" for e in ALLOWED_EXTENSIONS)
        return False, (
            f"Định dạng file '.{ext}' không được hỗ trợ. "
            f"Vui lòng chọn file: {allowed}"
        )

    file_size = uploaded_file.size
    if not is_allowed_size(file_size):
        size_mb = file_size / (1024 * 1024)
        return False, (
            f"File quá lớn ({size_mb:.1f} MB). "
            f"Giới hạn tối đa là {MAX_FILE_SIZE_MB} MB."
        )

    return True, ""


def save_uploaded_file(uploaded_file, save_dir: str | None = None) -> str:
    """
    Lưu file upload ra đĩa (thư mục tạm hoặc save_dir chỉ định).

    Returns:
        Đường dẫn tuyệt đối đến file đã lưu.
    """
    if save_dir is None:
        save_dir = tempfile.mkdtemp(prefix="cds_upload_")

    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, uploaded_file.name)

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return file_path


# ── API chính dùng trong app.py ────────────────────────────────────────────
def render_upload_widget(uploader_key: str = "audio_uploader") -> None:
    """
    Render st.file_uploader ẩn hoàn toàn (dùng CSS display:none).
    Nút "Upload asset" trong HTML sẽ trigger nó qua JavaScript.

    Gọi hàm này ngay sau st.components.v1.html(html_p1, ...).
    Khi user chọn file, hàm tự cập nhật session_state và gọi st.rerun().
    """
    # CSS ẩn toàn bộ widget uploader mặc định của Streamlit
    st.markdown(
        """
        <style>
          /* Ẩn hoàn toàn file uploader gốc của Streamlit */
          [data-testid="stFileUploader"] {
              position: absolute !important;
              width: 1px !important;
              height: 1px !important;
              padding: 0 !important;
              margin: 0 !important;
              overflow: hidden !important;
              clip: rect(0,0,0,0) !important;
              white-space: nowrap !important;
              border: 0 !important;
              opacity: 0 !important;
              pointer-events: none !important;
          }
          /* Ẩn label của uploader */
          [data-testid="stFileUploaderDropzone"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        label="Upload file âm thanh",
        type=ALLOWED_EXTENSIONS,
        key=uploader_key,
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        is_valid, error_msg = validate_uploaded_file(uploaded_file)

        if not is_valid:
            st.session_state["upload_error"] = error_msg
            return

        # Lưu thông tin vào session_state
        st.session_state["upload_error"] = ""
        st.session_state["filename"] = uploaded_file.name
        st.session_state["uploaded_file"] = uploaded_file
        st.session_state["page"] = "analysis"
        st.rerun()


def get_upload_error() -> str:
    """Trả về thông báo lỗi upload nếu có."""
    return st.session_state.get("upload_error", "")


def clear_upload_state() -> None:
    """Xóa toàn bộ trạng thái upload (dùng khi quay về Home)."""
    for key in ("filename", "uploaded_file", "upload_error", "audio_uploader"):
        st.session_state.pop(key, None)