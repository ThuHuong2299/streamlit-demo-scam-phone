"""
src/pages/home_page.py
────────────────────────────────────────────────────────────────
Trang 1 – Home: CSS, HTML và logic render.
────────────────────────────────────────────────────────────────
"""

import streamlit as st
from src.assets_loader import icon, deco
from src.upload_handler import render_upload_widget, get_upload_error

# ── CSS ───────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam:wght@400;500;600&display=swap');
*, *::before, *::after {
  box-sizing: border-box; margin: 0; padding: 0; border: none;
  text-decoration: none; background: none; -webkit-font-smoothing: antialiased;
}
menu, ol, ul { list-style-type: none; margin: 0; padding: 0; }

@keyframes gradientShift1 {
  0%   { background-position: 0% 0%; }
  25%  { background-position: 100% 0%; }
  50%  { background-position: 100% 100%; }
  75%  { background-position: 0% 100%; }
  100% { background-position: 0% 0%; }
}

@keyframes btnPulse {
  0%   { box-shadow: 0 0 0 0 rgba(44,109,238,0.6), 0 4px 15px rgba(44,109,238,0.4); }
  50%  { box-shadow: 0 0 0 10px rgba(44,109,238,0), 0 4px 25px rgba(44,109,238,0.6); }
  100% { box-shadow: 0 0 0 0 rgba(44,109,238,0), 0 4px 15px rgba(44,109,238,0.4); }
}
@keyframes btnLiveGlow {
  0%   { box-shadow: 0 0 8px rgba(0,63,255,0.25); }
  50%  { box-shadow: 0 0 20px rgba(0,63,255,0.5), 0 0 40px rgba(0,63,255,0.2); }
  100% { box-shadow: 0 0 8px rgba(0,63,255,0.25); }
}

.wireframe-1 {
  background: linear-gradient(135deg, #ffffff 0%, #a8d4f8 20%, #d6eeff 40%, #ffffff 55%, #b8daff 75%, #e0f0ff 90%, #ffffff 100%);
  background-size: 400% 400%;
  animation: gradientShift1 6s ease infinite;
  min-height: 100vh; position: relative; overflow: hidden; font-family: "Be Vietnam", sans-serif;
}
.frame-501 {
  display: flex; flex-direction: column; gap: clamp(32px, 5vw, 72px);
  align-items: center; justify-content: center;
  position: relative; width: 100%; padding: clamp(60px, 8vh, 120px) clamp(16px, 6vw, 186px);
  box-sizing: border-box;
}
.frame-500 {
  display: flex; flex-direction: column; gap: 16px;
  align-items: center; flex-shrink: 0; width: min(856px, 100%);
}
.heading {
  color: #02256f; text-align: center; font-size: clamp(24px, 4vw, 50px);
  line-height: 1.2; font-weight: 600; position: relative; align-self: stretch;
}
.subheading {
  color: #9b9797; text-align: center; font-size: clamp(14px, 1.5vw, 18px);
  line-height: 1.6; font-weight: 500; position: relative; align-self: stretch;
}
.frame-498 {
  display: flex; flex-direction: row; flex-wrap: wrap; gap: 12px;
  align-items: center; justify-content: center; flex-shrink: 0;
}
.btn-upload {
  background: #2c6dee; border-radius: 64px; padding: 12px 22px;
  display: flex; flex-direction: row; gap: 10px; align-items: center;
  justify-content: center; flex-shrink: 0; cursor: pointer;
  animation: btnPulse 2s ease-in-out infinite;
}
.frame-img { flex-shrink: 0; width: 24px; height: 24px; }
.upload-text { color: #ffffff; font-size: clamp(14px, 1.5vw, 18px); line-height: 1.4; font-weight: 600; }
.btn-live {
  background: #ffffff; border-radius: 64px; padding: 15px 24px;
  display: flex; flex-direction: row; gap: 10px; align-items: center;
  justify-content: center; flex-shrink: 0; cursor: pointer;
  animation: btnLiveGlow 2s ease-in-out infinite 1s;
}
.dot-wrap { flex-shrink: 0; width: 24px; height: 24px; position: relative; overflow: hidden; }
.dot {
  background: #ff1414; border-radius: 50%; width: 14.59px; height: 14.59px;
  position: absolute; left: 4.7px; top: 4.7px;
}
.live-text { color: #2c6dee; font-size: clamp(14px, 1.5vw, 18px); line-height: 1.4; font-weight: 600; }
.frame-499 {
  display: flex; flex-direction: row; flex-wrap: wrap; gap: 18px; align-items: stretch;
  align-self: stretch; flex-shrink: 0; justify-content: center;
}
.card {
  border-radius: 16px; padding: 25px; display: flex; flex-direction: column; gap: 24px;
  align-items: center; flex-shrink: 0; width: clamp(280px, 30vw, 344px); min-height: 260px;
  box-shadow: 0px 0px 14px 0px rgba(207,207,207,0.5); box-sizing: border-box;
}
.card-1 {
  background: #ece8f8;
}
.card-2 {
  background: #e2f4ec;
}
.card-3 {
  background: #fce8e9;
}
.card-header { display: flex; flex-direction: column; gap: 16px; align-items: flex-start; align-self: stretch; }
.card-title { color: #000; font-size: 20px; line-height: 55px; font-weight: 600; align-self: stretch; }
.card-desc { color: #9b9797; font-size: 16px; line-height: 25px; font-weight: 600; align-self: stretch; }
.card-img-wrap {
  width: 100%; flex: 1; display: flex; align-items: flex-end; justify-content: center;
  overflow: hidden; border-radius: 0 0 12px 12px;
}
.card-deco-img {
  max-width: 100%; max-height: 140px; width: auto; height: auto;
  object-fit: contain; display: block;
}
</style>
"""

# ── HTML template ─────────────────────────────────────────────────────────
HTML = """
{css}
<div class="wireframe-1">
  <div class="frame-501">
    <div class="frame-500">
      <div class="heading"> Dễ dàng theo dõi và phát hiện cuộc gọi đáng ngờ</div>
      <div class="subheading">Hệ thống được huấn luyện từ dữ liệu thực tế, nhận diện các phương thức lừa đảo mới, mang đến khả năng bảo vệ chủ động và thông minh.</div>
    </div>
    <div class="frame-498">
      <div class="btn-upload" onclick="triggerUpload()" style="cursor:pointer;">
        <img class="frame-img" src="{icon_upload}" />
        <div class="upload-text">Tải audio</div>
      </div>
      <script>
        function triggerUpload() {{
          var inputs = window.parent.document.querySelectorAll('input[type="file"]');
          if (inputs.length > 0) {{ inputs[0].click(); }}
        }}
      </script>
      <div class="btn-live">
        <div class="dot-wrap"><div class="dot"></div></div>
        <div class="live-text">Ghi âm</div>
      </div>
    </div>
    <div class="frame-499">
      <div class="card card-1">
        <div class="card-header">
          <div class="card-title">Phân tích nhanh</div>
          <div class="card-desc">Tự động phát hiện dấu hiệu bất thường ngay khi cuộc gọi bắt đầu.</div>
        </div>
        <div class="card-img-wrap">
          <img class="card-deco-img" src="{deco_purple}" />
        </div>
      </div>
      <div class="card card-2">
        <div class="card-header">
          <div class="card-title">Độ chính xác cao</div>
          <div class="card-desc">Phân tích giọng nói, nội dung và hành vi để đưa ra cảnh báo chính xác.</div>
        </div>
        <div class="card-img-wrap">
          <img class="card-deco-img" src="{deco_green}" />
        </div>
      </div>
      <div class="card card-3">
        <div class="card-header">
          <div class="card-title">Bảo mật tuyệt đối</div>
          <div class="card-desc">Dữ liệu được mã hóa và xử lý an toàn, đảm bảo quyền riêng tư của người dùng.</div>
        </div>
        <div class="card-img-wrap">
          <img class="card-deco-img" src="{deco_orange}" />
        </div>
      </div>
    </div>
  </div>
</div>
"""


# ── Render function ───────────────────────────────────────────────────────
def render_home():
    html = HTML.format(
        css=CSS,
        icon_upload=icon("icon_upload.svg"),
        deco_purple=deco("deco_purple.png", mime="image/png"),
        deco_green=deco("deco_green.png",   mime="image/png"),
        deco_orange=deco("deco_orange.png", mime="image/png"),
    )

    st.components.v1.html(html, height=900, scrolling=True)
    render_upload_widget()

    err = get_upload_error()
    if err:
        st.error(err)