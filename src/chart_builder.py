# src/chart_builder.py
"""
Vẽ line chart SVG thuần (không cần thư viện JS) từ chunk_scores.

Màu sắc:
  - diem < 0.30  → xanh lá  #22c55e  (An toàn)
  - diem < 0.60  → vàng     #f59e0b  (Nghi ngờ)
  - diem >= 0.60 → đỏ       #ef4444  (Lừa đảo)

Kích thước chart cố định vừa với trend-card (width 849px, height 216px):
  padding: 20px title → chart area W=760, H=130
"""

from __future__ import annotations
from typing import List, Dict
import json


# ── Hằng số layout ──────────────────────────────────────────────────────────
CHART_W   = 760    # chiều rộng vùng vẽ (px)
CHART_H   = 128    # chiều cao vùng vẽ (px)
PAD_LEFT  = 36     # padding trái (chỗ label % trục Y)
PAD_RIGHT = 12
PAD_TOP   = 10
PAD_BOT   = 28     # padding dưới (chỗ label thời gian trục X)

# Màu theo ngưỡng
def _point_color(diem: float) -> str:
    if diem < 0.30:
        return "#22c55e"
    if diem < 0.60:
        return "#f59e0b"
    return "#ef4444"


def _segment_gradient_id(idx: int) -> str:
    return f"seg_grad_{idx}"


# ── Helpers tọa độ ───────────────────────────────────────────────────────────
def _coords(chunk_scores: List[Dict]):
    """Tính tọa độ SVG (x, y) cho mỗi điểm."""
    n = len(chunk_scores)
    if n == 0:
        return []
    draw_w = CHART_W - PAD_LEFT - PAD_RIGHT
    draw_h = CHART_H - PAD_TOP  - PAD_BOT
    coords = []
    for i, c in enumerate(chunk_scores):
        x = PAD_LEFT + (i / max(n - 1, 1)) * draw_w
        y = PAD_TOP  + (1.0 - c["diem"]) * draw_h
        coords.append((x, y))
    return coords


# ── Builder chính ────────────────────────────────────────────────────────────

def build_line_chart_html(chunk_scores: List[Dict]) -> str:
    """
    Nhận chunk_scores (List[Dict]) → trả về HTML string chứa SVG line chart.

    chunk_scores mỗi phần tử cần có:
        diem       : float 0-1
        time_label : str "MM:SS"
        text       : str  (câu thoại — hiện trong tooltip)
        loai       : List[str]
    """

    # ── Placeholder khi chưa có data ────────────────────────────────────────
    if not chunk_scores:
        return (
            '<div style="display:flex;align-items:center;justify-content:center;'
            'height:128px;color:#9b9797;font-size:13px;font-family:Poppins,sans-serif;">'
            '⏳ Chưa có dữ liệu — đang phân tích...</div>'
        )

    coords     = _coords(chunk_scores)
    n          = len(chunk_scores)
    draw_h     = CHART_H - PAD_TOP - PAD_BOT

    # ── Tính ngưỡng Y ───────────────────────────────────────────────────────
    y_30 = PAD_TOP + (1.0 - 0.30) * draw_h
    y_60 = PAD_TOP + (1.0 - 0.60) * draw_h

    # ── Polyline points string ──────────────────────────────────────────────
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)

    # ── Fill area (polygon đóng xuống đáy) ─────────────────────────────────
    fill_pts = pts
    fill_pts += f" {coords[-1][0]:.1f},{PAD_TOP + draw_h:.1f}"
    fill_pts += f" {coords[0][0]:.1f},{PAD_TOP + draw_h:.1f}"

    # ── Segments gradient: mỗi đoạn line tô màu riêng ──────────────────────
    # Vẽ fill polygon trước (mờ), sau đó vẽ các đoạn polyline màu đậm theo ngưỡng
    segment_lines = []
    for i in range(n - 1):
        c0, c1 = chunk_scores[i], chunk_scores[i + 1]
        avg_diem = (c0["diem"] + c1["diem"]) / 2
        color    = _point_color(avg_diem)
        x0, y0   = coords[i]
        x1, y1   = coords[i + 1]
        segment_lines.append(
            f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" '
            f'stroke="{color}" stroke-width="2.5" stroke-linecap="round"/>'
        )
    segments_svg = "\n    ".join(segment_lines)

    # ── Điểm tròn + tooltip data ─────────────────────────────────────────────
    dots_svg_parts = []
    # Chuẩn bị data JSON nhúng vào script để JS đọc
    tooltip_data = []
    for i, (c, (x, y)) in enumerate(zip(chunk_scores, coords)):
        color     = _point_color(c["diem"])
        pct_label = f"{c['diem']:.0%}"
        loai_str  = ", ".join(c.get("loai", [])) or "—"
        # Text câu thoại cắt ngắn 80 ký tự
        text_short = (c.get("text") or "")[:80].replace('"', '&quot;')
        dots_svg_parts.append(
            f'<circle class="lc-dot" cx="{x:.1f}" cy="{y:.1f}" r="4" '
            f'fill="{color}" stroke="#fff" stroke-width="1.5" '
            f'data-idx="{i}"/>'
        )
        tooltip_data.append({
            "time":  c.get("time_range", c.get("time_label", "")),
            "pct":   pct_label,
            "loai":  loai_str,
            "text":  text_short,
            "color": color,
        })
    dots_svg = "\n    ".join(dots_svg_parts)
    tooltip_json = json.dumps(tooltip_data, ensure_ascii=False)

    # ── Label trục Y (0%, 30%, 60%, 100%) ────────────────────────────────────
    y_labels = []
    for pct in [1.0, 0.6, 0.3, 0.0]:
        yl = PAD_TOP + (1.0 - pct) * draw_h
        y_labels.append(
            f'<text x="{PAD_LEFT - 4}" y="{yl + 4:.1f}" '
            f'text-anchor="end" font-size="10" fill="#9b9797" font-family="Lato,sans-serif">'
            f'{int(pct*100)}%</text>'
        )
    y_labels_svg = "\n    ".join(y_labels)

    # ── Label trục X (hiện tối đa 10 nhãn để không chật) ────────────────────
    x_labels = []
    step = max(1, n // 8)
    for i in range(0, n, step):
        x, _ = coords[i]
        lbl  = chunk_scores[i].get("time_label", "")
        x_labels.append(
            f'<text x="{x:.1f}" y="{CHART_H - 4}" '
            f'text-anchor="middle" font-size="10" fill="#9b9797" font-family="Lato,sans-serif">'
            f'{lbl}</text>'
        )
    x_labels_svg = "\n    ".join(x_labels)

    # ── Grid lines ngang (30% và 60%) ────────────────────────────────────────
    grid_right = CHART_W - PAD_RIGHT
    grids_svg = (
        f'<line x1="{PAD_LEFT}" y1="{y_30:.1f}" x2="{grid_right}" y2="{y_30:.1f}" '
        f'stroke="#f59e0b" stroke-width="1" stroke-dasharray="4,3" opacity="0.5"/>\n    '
        f'<line x1="{PAD_LEFT}" y1="{y_60:.1f}" x2="{grid_right}" y2="{y_60:.1f}" '
        f'stroke="#ef4444" stroke-width="1" stroke-dasharray="4,3" opacity="0.5"/>\n    '
        # Grid ngang 0% và 100%
        f'<line x1="{PAD_LEFT}" y1="{PAD_TOP:.1f}" x2="{grid_right}" y2="{PAD_TOP:.1f}" '
        f'stroke="#e5e7eb" stroke-width="0.5"/>\n    '
        f'<line x1="{PAD_LEFT}" y1="{PAD_TOP + draw_h:.1f}" x2="{grid_right}" y2="{PAD_TOP + draw_h:.1f}" '
        f'stroke="#e5e7eb" stroke-width="0.5"/>'
    )

    # ── Nhãn ngưỡng inline ───────────────────────────────────────────────────
    threshold_labels = (
        f'<text x="{grid_right + 2}" y="{y_30 + 4:.1f}" font-size="9" fill="#f59e0b" '
        f'font-family="Lato,sans-serif">30%</text>\n    '
        f'<text x="{grid_right + 2}" y="{y_60 + 4:.1f}" font-size="9" fill="#ef4444" '
        f'font-family="Lato,sans-serif">60%</text>'
    )

    # ── Fill area mờ ─────────────────────────────────────────────────────────
    fill_svg = (
        f'<polygon points="{fill_pts}" '
        f'fill="url(#lc_fill_grad)" opacity="0.18"/>'
    )

    # ── Assemble SVG ─────────────────────────────────────────────────────────
    svg = f"""<svg id="lc-svg" width="100%" height="auto" viewBox="0 0 {CHART_W} {CHART_H}" preserveAspectRatio="xMidYMid meet"
     xmlns="http://www.w3.org/2000/svg" style="overflow:visible;">
  <defs>
    <linearGradient id="lc_fill_grad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ef4444"/>
      <stop offset="50%" stop-color="#f59e0b"/>
      <stop offset="100%" stop-color="#22c55e"/>
    </linearGradient>
  </defs>
  <!-- Grid -->
  {grids_svg}
  {threshold_labels}
  <!-- Fill area -->
  {fill_svg}
  <!-- Segment lines -->
  {segments_svg}
  <!-- Dots -->
  {dots_svg}
  <!-- Trục Y labels -->
  {y_labels_svg}
  <!-- Trục X labels -->
  {x_labels_svg}
</svg>"""

    # ── Tooltip div + JS ──────────────────────────────────────────────────────
    tooltip_html = """<div id="lc-tooltip" style="
      display:none; position:fixed; z-index:9999;
      background:#1e293b; color:#f8fafc; border-radius:8px;
      padding:8px 12px; font-size:12px; font-family:Poppins,sans-serif;
      max-width:220px; pointer-events:none; line-height:1.5;
      box-shadow:0 4px 16px rgba(0,0,0,0.25);">
    </div>"""

    js = f"""<script>
(function() {{
  var DATA = {tooltip_json};
  var tip  = document.getElementById('lc-tooltip');
  document.querySelectorAll('.lc-dot').forEach(function(dot) {{
    dot.addEventListener('mouseenter', function(e) {{
      var d   = DATA[parseInt(dot.getAttribute('data-idx'))];
      var svg = document.getElementById('lc-svg');
      var pt  = svg.createSVGPoint();
      pt.x = parseFloat(dot.getAttribute('cx'));
      pt.y = parseFloat(dot.getAttribute('cy'));
      var pos = pt.matrixTransform(svg.getScreenCTM());
      tip.innerHTML =
        '<div style="font-weight:700;color:' + d.color + ';margin-bottom:3px;">' +
          d.time + ' &nbsp;' + d.pct +
        '</div>' +
        (d.loai !== '—' ? '<div style="color:#94a3b8;font-size:11px;">📌 ' + d.loai + '</div>' : '') +
        (d.text ? '<div style="margin-top:4px;color:#e2e8f0;font-size:11px;">' + d.text + '</div>' : '');
      tip.style.display = 'block';
      var tipW = tip.offsetWidth, tipH = tip.offsetHeight;
      var left = pos.x + 14;
      var top  = pos.y - tipH / 2;
      if (left + tipW > window.innerWidth - 8)  left = pos.x - tipW - 14;
      if (top < 8)                               top  = 8;
      if (top + tipH > window.innerHeight - 8)  top  = window.innerHeight - tipH - 8;
      tip.style.left = left + 'px';
      tip.style.top  = top  + 'px';
    }});
    dot.addEventListener('mouseleave', function() {{
      tip.style.display = 'none';
    }});
    dot.addEventListener('touchstart', function(e) {{
      e.preventDefault();
      dot.dispatchEvent(new MouseEvent('mouseenter'));
    }}, {{passive: false}});
    dot.addEventListener('touchend', function() {{
      setTimeout(function() {{ tip.style.display = 'none'; }}, 1800);
    }});
  }});
}})();
</script>"""

    return tooltip_html + '\n<div style="width:100%;min-width:0;overflow:hidden;">' + svg + '</div>' + js