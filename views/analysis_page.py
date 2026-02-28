"""
src/pages/analysis_page.py
────────────────────────────────────────────────────────────────
Trang 2 – Kết quả phân tích: CSS, HTML và logic render.
────────────────────────────────────────────────────────────────
"""

import re
import base64
import streamlit as st

from src.assets_loader import icon
from src.analysis_engine import run_analysis, get_chunk_scores, is_analysis_done
from src.chart_builder import build_line_chart_html
from src.upload_handler import clear_upload_state
from src.loading_screen import LoadingScreen, estimate_chunks

# ── CSS ───────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Lato:wght@400;700&family=Inter:wght@600&display=swap');
:root { --layout-200:#dbdbdb; --layout-800:#222222; }
*, *::before, *::after { box-sizing:border-box; margin:0; padding:0; border:none; text-decoration:none; background:none; -webkit-font-smoothing:antialiased; }
menu, ol, ul { list-style-type: none; }
@keyframes gradientShift2 {
  0%{background-position:0% 0%} 25%{background-position:100% 0%}
  50%{background-position:100% 100%} 75%{background-position:0% 100%} 100%{background-position:0% 0%}
}
.desktop-2 {
  background: linear-gradient(135deg,#ffffff 0%,#a8d4f8 20%,#d6eeff 40%,#ffffff 55%,#b8daff 75%,#e0f0ff 90%,#ffffff 100%);
  background-size:400% 400%; animation:gradientShift2 6s ease infinite;
  min-height:100vh; position:relative; font-family:"Poppins",sans-serif; display:flex; flex-direction:column;
}
.topbar { padding:0 clamp(12px,2vw,21.5px); display:flex; flex-direction:row; align-items:center; gap:12px; flex-wrap:wrap; width:100%; position:sticky; top:0; z-index:100; min-height:62px; background:rgba(229,241,253,0.92); backdrop-filter:blur(8px); box-sizing:border-box; }
.topbar-left { display:flex; flex-direction:row; align-items:center; gap:12px; flex-shrink:0; width:auto; min-width:0; }
.brand { display:flex; align-items:center; justify-content:center; flex-shrink:0; cursor:pointer; width:44px; height:44px; border-radius:50%; background:rgba(255,255,255,0.85); box-shadow:0 2px 10px rgba(0,63,255,0.15); transition:box-shadow 0.2s; }
.brand:hover { box-shadow:0 4px 16px rgba(0,63,255,0.28); }
.fname { color:#02256f; font-size:clamp(12px,1.3vw,15px); font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:clamp(100px,20vw,300px); }
.audio-player-wrap { background:#ffffff; border-radius:18px; padding:0 20px; display:flex; flex-direction:row; gap:14px; align-items:center; flex:1; height:44px; box-shadow:0 2px 10px rgba(0,63,255,0.10); }
.ap-play-btn { flex-shrink:0; width:30px; height:30px; border-radius:50%; background:#2c6dee; border:none; cursor:pointer; display:flex; align-items:center; justify-content:center; }
.ap-play-btn svg { fill:#fff; }
.ap-track-wrap { flex:1; }
.ap-range { -webkit-appearance:none; appearance:none; width:100%; height:5px; border-radius:4px; outline:none; cursor:pointer; background:linear-gradient(to right,#2c6dee 0%,#2c6dee var(--prog,0%),#d1dff7 var(--prog,0%),#d1dff7 100%); }
.ap-range::-webkit-slider-thumb { -webkit-appearance:none; width:13px; height:13px; border-radius:50%; background:#2c6dee; cursor:pointer; }
.ap-range::-moz-range-thumb { width:13px; height:13px; border-radius:50%; background:#2c6dee; cursor:pointer; border:none; }
.ap-time { color:#02256f; font-size:13px; font-weight:500; white-space:nowrap; flex-shrink:0; min-width:80px; text-align:right; }
.stats-row { display:flex; flex-direction:row; flex-wrap:wrap; gap:12px; align-items:stretch; width:100%; padding:12px clamp(12px,2vw,21.5px) 0; box-sizing:border-box; }
.fraud-card { background:#ffffff; border-radius:16px; padding:20px 22px; display:flex; flex-direction:column; gap:12px; align-items:flex-start; flex-shrink:0; flex:1; min-width:260px; min-height:180px; box-sizing:border-box; overflow:hidden; }
.lato-title { color:#02256f; font-family:"Lato",sans-serif; font-size:16px; font-weight:700; align-self:stretch; flex-shrink:0; }
.fraud-body { display:flex; flex-direction:row; align-items:center; justify-content:space-between; align-self:stretch; flex:1; min-height:0; }
.fraud-left { display:flex; flex-direction:column; gap:10px; align-items:flex-start; flex-shrink:0; width:148px; }
.pct { font-size:clamp(36px,5vw,52px); line-height:1; font-weight:700; }
.fraud-badge { border-radius:32px; padding:7px 14px; display:inline-flex; align-items:center; justify-content:center; flex-shrink:0; }
.fraud-badge-txt { font-family:"Inter",sans-serif; font-size:13px; line-height:1; font-weight:600; white-space:nowrap; }
.fraud-legend { display:flex; flex-direction:column; gap:10px; align-items:flex-start; justify-content:center; flex-shrink:0; padding-right:4px; }
.legend-row { display:flex; flex-direction:row; gap:8px; align-items:center; }
.legend-dot { width:12px; height:12px; border-radius:50%; flex-shrink:0; }
.legend-txt { font-family:"Poppins",sans-serif; font-size:13px; font-weight:500; white-space:nowrap; }
.trend-card { background:#ffffff; border-radius:16px; padding:18px 22px 12px; display:flex; flex-direction:column; gap:12px; align-items:flex-start; flex-shrink:0; flex:2; min-width:300px; min-height:180px; box-sizing:border-box; }
.trend-chart-wrap { flex:1; width:100%; min-height:0; }
.bottom-left { display:flex; flex-direction:column; gap:12px; align-items:flex-start; flex:1; min-width:280px; }
.kw-card { background:#ffffff; border-radius:16px; padding:20px 22px; display:flex; flex-direction:column; gap:14px; align-items:flex-start; align-self:stretch; flex-shrink:0; box-sizing:border-box; }
.kw-tags-col { display:flex; flex-direction:row; flex-wrap:wrap; gap:10px; align-self:stretch; }
.kw-tag { background:#f7f4ff; border-radius:32px; border:1px solid #7c3aed; padding:7px 14px; display:inline-flex; flex-direction:row; gap:8px; align-items:center; flex-shrink:0; }
.kw-label { color:#562182; font-size:13px; font-weight:500; white-space:nowrap; font-family:"Poppins",sans-serif; }
.kw-count { background:#674ea0; border-radius:14px; min-width:26px; height:26px; padding:0 7px; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.kw-num { color:#ffffff; font-size:12px; font-weight:600; font-family:"Poppins",sans-serif; }
.kw-more { color:#02256f; text-align:center; font-size:13px; font-weight:600; align-self:stretch; font-family:"Poppins",sans-serif; cursor:pointer; }
.advice-card { background:#ffffff; border-radius:16px; padding:20px 22px; display:flex; flex-direction:column; gap:12px; align-items:flex-start; align-self:stretch; flex-shrink:0; max-height:400px; box-sizing:border-box; overflow:hidden; }
.poppins-title { color:#02256f; font-size:16px; font-weight:700; align-self:stretch; flex-shrink:0; font-family:"Poppins",sans-serif; }
.advice-scroll { display:flex; flex-direction:column; gap:10px; align-self:stretch; flex:1; min-height:0; overflow-y:auto; padding-right:4px; scrollbar-width:thin; scrollbar-color:#ffbcbc #fff0f0; }
.advice-scroll::-webkit-scrollbar { width:5px; }
.advice-scroll::-webkit-scrollbar-track { background:#fff0f0; border-radius:4px; }
.advice-scroll::-webkit-scrollbar-thumb { background:#ffbcbc; border-radius:4px; }
.advice-box { background:#fff5f5; border:1px solid #ffbcbc; border-radius:10px; padding:14px 16px; display:flex; flex-direction:column; gap:10px; flex-shrink:0; box-sizing:border-box; }
.advice-warning { display:flex; flex-direction:row; gap:8px; align-items:flex-start; flex-shrink:0; }
.advice-warning-icon { font-size:15px; flex-shrink:0; line-height:1.4; }
.advice-warning-txt { color:#c0392b; font-family:"Poppins",sans-serif; font-size:13px; font-weight:700; line-height:1.4; }
.advice-bullets { display:flex; flex-direction:column; gap:6px; padding-left:4px; }
.advice-bullet { display:flex; flex-direction:row; gap:8px; align-items:flex-start; }
.advice-bullet-dot { color:#c0392b; font-size:13px; line-height:1.5; flex-shrink:0; }
.advice-bullet-txt { color:#c0392b; font-family:"Poppins",sans-serif; font-size:13px; font-weight:400; line-height:1.5; }
.advice-rec-box { background:#fce8e8; border-radius:10px; padding:14px 16px; display:flex; flex-direction:column; gap:10px; flex-shrink:0; box-sizing:border-box; }
.advice-rec-title { color:#c0392b; font-family:"Poppins",sans-serif; font-size:13px; font-weight:700; line-height:1.4; }
.advice-rec-body { color:#c0392b; font-family:"Poppins",sans-serif; font-size:13px; font-weight:700; line-height:1.5; }
.advice-rec-why { color:#c0392b; font-family:"Poppins",sans-serif; font-size:13px; font-weight:700; line-height:1.5; margin-top:2px; }
.conv-card { background:#ffffff; border-radius:16px; padding:20px 22px; display:flex; flex-direction:column; gap:14px; flex:2; min-width:300px; box-sizing:border-box; }
.tbl { border-radius:8px; display:flex; flex-direction:column; align-self:stretch; overflow:hidden; border:1px solid #e8edf4; }
.tbl-hdr { background:#e3eefc; display:grid; grid-template-columns:130px 1fr; align-items:center; border-bottom:1px solid #d3e3f9; }
.th-cell { padding:11px 14px; color:#222222; font-size:14px; font-weight:600; font-family:"Poppins",sans-serif; }
.tbl-body { display:flex; flex-direction:column; max-height:460px; overflow-y:auto; scrollbar-width:thin; scrollbar-color:#c7d9f0 #f5f8fc; }
.tbl-body::-webkit-scrollbar { width:5px; }
.tbl-body::-webkit-scrollbar-track { background:#f5f8fc; }
.tbl-body::-webkit-scrollbar-thumb { background:#c7d9f0; border-radius:4px; }
.tr-row { display:grid; grid-template-columns:130px 1fr; align-items:baseline; border-top:1px solid #e8edf4; }
.tr-row:first-child { border-top:none; }
.td-time { padding:11px 14px; color:#2c6dee; font-size:13px; font-weight:500; font-family:"Poppins",sans-serif; white-space:nowrap; }
.td-content { padding:11px 14px 11px 0; color:#333333; font-size:13.5px; font-weight:400; font-family:"Poppins",sans-serif; line-height:1.55; }
.kw-hl { background:#ffd6cc; color:#c0392b; font-weight:600; border-radius:4px; padding:1px 4px; }
.bottom-row { display:flex; flex-direction:row; flex-wrap:wrap; gap:12px; width:100%; padding:12px clamp(12px,2vw,21.5px) 20px; box-sizing:border-box; align-items:flex-start; }
@media (max-width:900px) {
  .stats-row,.bottom-row { flex-direction:column; }
  .fraud-card,.trend-card,.bottom-left,.conv-card { flex:unset; width:100%; min-width:unset; }
  .topbar { flex-wrap:wrap; height:auto; padding:10px 16px; gap:8px; }
  .audio-player-wrap { flex:1; min-width:200px; }
  .topbar-left { flex-shrink:1; min-width:0; }
}
@media (max-width:600px) {
  .pct { font-size:36px; }
  .heading { font-size:22px !important; }
  .fraud-body { flex-direction:column; gap:16px; }
  .ap-time { display:none; }
  .tbl-hdr,.tr-row { grid-template-columns:90px 1fr; }
}
</style>
"""


# ── Helpers ───────────────────────────────────────────────────────────────
def _highlight_text(text, keywords):
    if not keywords or not text:
        return text or ""
    result = text
    for kw in sorted(keywords, key=len, reverse=True):
        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        result = pattern.sub(lambda m: f'<span class="kw-hl">{m.group(0)}</span>', result)
    return result


def _kw_tag(label, count, hidden=False):
    style = ' style="display:none;"' if hidden else ''
    cls   = 'kw-tag kw-extra' if hidden else 'kw-tag'
    return (
        f'<div class="{cls}"{style}>'
        f'<div class="kw-label">{label}</div>'
        f'<div class="kw-count"><div class="kw-num">{count}</div></div>'
        f'</div>'
    )


def _build_audio_src(uploaded_file, filename):
    if uploaded_file is None:
        return ""
    mime_map = {"mp3":"audio/mpeg","wav":"audio/wav","m4a":"audio/x-m4a",
                "ogg":"audio/ogg","mp4":"audio/mp4","mpeg4":"audio/mp4"}
    ext  = filename.rsplit(".", 1)[-1].lower() if "." in filename else "mp3"
    mime = mime_map.get(ext, "audio/mpeg")
    b64  = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def _badge_style(raw_score):
    if raw_score < 0.30:
        return "#22c55e", "#dcfce7", "#22c55e", "An toàn"
    elif raw_score < 0.60:
        return "#f59e0b", "#fef3c7", "#f59e0b", "Nghi ngờ"
    return "#f50000", "#ffd7d7", "#f50000", "Dấu hiệu lừa đảo"


# ── Render function ───────────────────────────────────────────────────────
def render_analysis():
    filename      = st.session_state.get("filename", "File name upload")
    uploaded_file = st.session_state.get("uploaded_file")
    icon_home     = icon("icon_home_heart.svg")

    # ── Bước 1: Hiện LoadingScreen rồi chạy analysis ────────────────────
    if not is_analysis_done() and uploaded_file is not None:
        audio_bytes  = uploaded_file.getvalue()
        total_chunks = estimate_chunks(audio_bytes, filename, chunk_duration=10)

        loader = LoadingScreen(total_chunks=total_chunks)
        loader.show(status_text=f"Đang chuẩn bị phân tích '{filename}'...")

        def _on_progress(done, total):
            loader.update(
                done=done,
                total=total,
                status_text=f"Đang xử lý đoạn {done}/{total}...",
            )

        run_analysis(
            audio_bytes=audio_bytes,
            filename=filename,
            progress_callback=_on_progress,
        )
        loader.done()
        st.rerun()

    # ── Bước 2: Đọc data ──────────────────────────────────────────────────
    chunk_scores = get_chunk_scores()
    raw_score    = st.session_state.get("diem_nghi_ngo", 0.0)
    kw_list      = st.session_state.get("keywords_count", [])

    transcript = [(c["time_range"], c["text"], c["keywords"][:5]) for c in chunk_scores]

    # ── Bước 3: Build các thành phần HTML ─────────────────────────────────
    audio_src   = _build_audio_src(uploaded_file, filename)
    pct_color, badge_bg, badge_color, badge_label = _badge_style(raw_score)
    pct_display = f"{raw_score:.0%}"
    chart_html  = build_line_chart_html(chunk_scores)

    VISIBLE_KW      = 5
    kw_tags_html    = "".join(_kw_tag(l, c) for l, c in kw_list[:VISIBLE_KW])
    kw_tags_html   += "".join(_kw_tag(l, c, hidden=True) for l, c in kw_list[VISIBLE_KW:])
    kw_hidden_count = max(0, len(kw_list) - VISIBLE_KW)
    kw_more_label   = f"Xem thêm {kw_hidden_count} từ khóa" if kw_hidden_count > 0 else ""

    rows_html = "".join(
        f'<div class="tr-row"><div class="td-time">{t}</div>'
        f'<div class="td-content">{_highlight_text(txt, kws)}</div></div>'
        for t, txt, kws in transcript
    )

    # TODO: thay bằng st.session_state.get("llm_advice", {...})
    advice_warning     = "Cảnh báo cao! Cuộc gọi này có nhiều dấu hiệu lừa đảo:"
    advice_bullets     = ["Mạo danh cơ quan công quyền (công an)", "Tạo áp lực khẩn cấp để nạn nhân không kịp suy nghĩ", "Yêu cầu chuyển tiền và cung cấp mã OTP", "Đe dọa bắt giữ nếu không hợp tác"]
    advice_rec_body    = "KHÔNG chuyển tiền, KHÔNG cung cấp mã OTP. Liên hệ trực tiếp cơ quan công an qua số 113 để xác minh."
    advice_rec_bullets = ["Cơ quan công an KHÔNG bao giờ yêu cầu chuyển tiền qua điện thoại", "Nếu có vấn đề pháp lý, họ sẽ gửi giấy tờ chính thức hoặc mời trực tiếp", "Tạo áp lực khẩn cấp là chiêu thức điển hình của tội phạm", "Kẻ lừa đảo sợ bạn có thời gian để xác minh thông tin họ"]

    def bullets_html(items):
        return "".join(f'<div class="advice-bullet"><span class="advice-bullet-dot">•</span><span class="advice-bullet-txt">{b}</span></div>' for b in items)

    kw_more_html = f'<div class="kw-more" id="kw-more-btn" onclick="toggleKwMore()">{kw_more_label}</div>' if kw_more_label else ""

    # ── Bước 4: Render HTML ───────────────────────────────────────────────
    html = f"""
{CSS}
<div class="desktop-2">
  <div class="topbar">
    <div class="topbar-left">
      <div class="brand" id="btn-home" onclick="goHome()" title="Quay lại trang chủ">
        <img src="{icon_home}" width="24" height="24" style="flex-shrink:0;" />
      </div>
      <script>
        function goHome() {{
          try {{
            // allow-same-origin sandbox → truy cập trực tiếp parent location
            var url = new URL(window.parent.location.href);
            url.searchParams.set("go_home", "1");
            window.parent.location.href = url.toString();
          }} catch(e) {{
            // fallback: reload trang hiện tại với param go_home
            window.location.href = window.location.origin + window.location.pathname + "?go_home=1";
          }}
        }}
      </script>
      <div class="fname">{filename}</div>
    </div>
    <div class="audio-player-wrap">
      <audio id="ap-audio" src="{audio_src}" preload="metadata"></audio>
      <button class="ap-play-btn" id="ap-btn" onclick="apToggle()">
        <svg id="ap-icon-play" width="12" height="14" viewBox="0 0 12 14"><path d="M0 0L12 7L0 14V0Z"/></svg>
        <svg id="ap-icon-pause" width="12" height="14" viewBox="0 0 12 14" style="display:none"><rect x="0" y="0" width="4" height="14"/><rect x="8" y="0" width="4" height="14"/></svg>
      </button>
      <div class="ap-track-wrap">
        <input class="ap-range" id="ap-range" type="range" min="0" max="100" value="0" step="0.1" oninput="apSeek(this.value)" />
      </div>
      <div class="ap-time" id="ap-time">0:00 / 0:00</div>
    </div>
    <script>
      (function() {{
        var audio=document.getElementById('ap-audio'),range=document.getElementById('ap-range'),
            timeEl=document.getElementById('ap-time'),
            iconPlay=document.getElementById('ap-icon-play'),iconPause=document.getElementById('ap-icon-pause');
        function fmt(s){{s=Math.floor(s||0);return Math.floor(s/60)+':'+String(s%60).padStart(2,'0');}}
        function upd(){{var p=audio.duration?(audio.currentTime/audio.duration*100):0;range.value=p;range.style.setProperty('--prog',p+'%');timeEl.textContent=fmt(audio.currentTime)+' / '+fmt(audio.duration);}}
        audio.addEventListener('timeupdate',upd);audio.addEventListener('loadedmetadata',upd);
        audio.addEventListener('ended',function(){{iconPlay.style.display='';iconPause.style.display='none';}});
        window.apToggle=function(){{if(audio.paused){{audio.play();iconPlay.style.display='none';iconPause.style.display='';}}else{{audio.pause();iconPlay.style.display='';iconPause.style.display='none';}}}};
        window.apSeek=function(v){{if(audio.duration)audio.currentTime=v/100*audio.duration;}};
      }})();
    </script>
  </div>
  <div class="stats-row">
    <div class="fraud-card">
      <div class="lato-title">Mức độ lừa đảo</div>
      <div class="fraud-body">
        <div class="fraud-left">
          <div class="pct" style="color:{pct_color};">{pct_display}</div>
          <div class="fraud-badge" style="background:{badge_bg};">
            <div class="fraud-badge-txt" style="color:{badge_color};">{badge_label}</div>
          </div>
        </div>
        <div class="fraud-legend">
          <div class="legend-row"><div class="legend-dot" style="background:#22c55e;"></div><div class="legend-txt">&lt; 30%: <span style="color:#22c55e;font-weight:700;">An toàn</span></div></div>
          <div class="legend-row"><div class="legend-dot" style="background:#f59e0b;"></div><div class="legend-txt">30% - 60%: <span style="color:#f59e0b;font-weight:700;">Nghi ngờ</span></div></div>
          <div class="legend-row"><div class="legend-dot" style="background:#ef4444;"></div><div class="legend-txt">&gt; 60%: <span style="color:#ef4444;font-weight:700;">Lừa đảo</span></div></div>
        </div>
      </div>
    </div>
    <div class="trend-card">
      <div class="lato-title">Diễn biến mức độ lừa đảo</div>
      <div class="trend-chart-wrap">{chart_html}</div>
    </div>
  </div>
  <div class="bottom-row">
    <div class="bottom-left">
      <div class="kw-card">
        <div class="lato-title">Từ khóa nghi ngờ</div>
        <div class="kw-tags-col">{kw_tags_html}</div>
        {kw_more_html}
        <script>
          function toggleKwMore() {{
            var extras=document.querySelectorAll('.kw-extra');
            var btn=document.getElementById('kw-more-btn');
            var hidden=extras[0]&&extras[0].style.display==='none';
            extras.forEach(function(el){{el.style.display=hidden?'inline-flex':'none';}});
            btn.textContent=hidden?'Ẩn bớt':'Xem thêm {kw_hidden_count} từ khóa';
          }}
        </script>
      </div>
      <div class="advice-card">
        <div class="poppins-title">💡 Lời khuyên</div>
        <div class="advice-scroll">
          <div class="advice-box">
            <div class="advice-warning">
              <span class="advice-warning-icon">⚠️</span>
              <span class="advice-warning-txt">{advice_warning}</span>
            </div>
            <div class="advice-bullets">{bullets_html(advice_bullets)}</div>
          </div>
          <div class="advice-rec-box">
            <div class="advice-rec-title">✓ Khuyến nghị:</div>
            <div class="advice-rec-body">{advice_rec_body}</div>
            <div class="advice-rec-why">Tại sao?</div>
            <div class="advice-bullets">{bullets_html(advice_rec_bullets)}</div>
          </div>
        </div>
      </div>
    </div>
    <div class="conv-card">
      <div class="poppins-title">🗒 Nội dung hội thoại (Transcript)</div>
      <div class="tbl">
        <div class="tbl-hdr">
          <div class="th-cell">Thời gian</div>
          <div class="th-cell">Nội dung</div>
        </div>
        <div class="tbl-body">{rows_html}</div>
      </div>
    </div>
  </div>
</div>
"""

    st.components.v1.html(html, height=900, scrolling=True)