"""
app.py – Entry point & Router
────────────────────────────────────────────────────────────────
Chỉ chứa:
  - Cấu hình Streamlit
  - Ẩn UI mặc định
  - Khởi tạo session state
  - Router điều hướng giữa các trang
────────────────────────────────────────────────────────────────
"""

import os
import sys
import streamlit as st

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from views.home_page     import render_home
from views.analysis_page import render_analysis

# ── Cấu hình trang ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Call Detection System",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Ẩn chrome mặc định của Streamlit ─────────────────────────────────────
st.markdown("""
<style>
  #MainMenu { visibility: hidden; }
  footer    { visibility: hidden; }
  header    { visibility: hidden; }
  .block-container { padding: 0 !important; max-width: 100% !important; }
  .stApp { background: white; }
</style>
""", unsafe_allow_html=True)

# ── Session state mặc định ────────────────────────────────────────────────
st.session_state.setdefault("page", "home")
st.session_state.setdefault("filename", "")

# ── Router ────────────────────────────────────────────────────────────────
if st.session_state.page == "home":
    render_home()
else:
    render_analysis()