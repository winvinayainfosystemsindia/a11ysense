"""
Visual Audit Report Generator
Converts audit_results.csv into an interactive, visually stunning HTML dashboard
with screenshot previews, tier filters, search, and element breakdowns.
"""

import csv
import os
import json
from pathlib import Path

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>A11ySense — Android Screen Visual Audit & Screenshot Mapper</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-primary: #0a0e17;
      --bg-secondary: #111827;
      --bg-card: #182234;
      --bg-card-hover: #1f2c42;
      --border-subtle: #253349;
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
      --accent-blue: #38bdf8;
      --accent-purple: #818cf8;
      --complex-badge: #f43f5e;
      --complex-bg: rgba(244, 63, 94, 0.12);
      --medium-badge: #f59e0b;
      --medium-bg: rgba(245, 158, 11, 0.12);
      --simple-badge: #10b981;
      --simple-bg: rgba(16, 185, 129, 0.12);
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: var(--bg-primary);
      color: var(--text-main);
      padding: 24px;
      line-height: 1.5;
    }

    .container {
      max-width: 1440px;
      margin: 0 auto;
    }

    header {
      background: linear-gradient(135deg, #111827 0%, #1e1b4b 100%);
      border: 1px solid var(--border-subtle);
      border-radius: 16px;
      padding: 28px 32px;
      margin-bottom: 24px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
    }

    .header-top {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 16px;
    }

    h1 {
      font-size: 26px;
      font-weight: 800;
      letter-spacing: -0.02em;
      background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 8px;
    }

    p.subtitle {
      color: var(--text-muted);
      font-size: 14px;
      max-width: 760px;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-top: 24px;
    }

    .stat-card {
      background: rgba(17, 24, 39, 0.7);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      padding: 16px;
      backdrop-filter: blur(8px);
    }

    .stat-card .label {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      font-weight: 600;
    }

    .stat-card .value {
      font-size: 24px;
      font-weight: 800;
      margin-top: 4px;
      font-family: 'JetBrains Mono', monospace;
    }

    .controls-panel {
      background: var(--bg-secondary);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      padding: 16px 20px;
      margin-bottom: 24px;
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      align-items: center;
      justify-content: space-between;
    }

    .search-box {
      flex: 1;
      min-width: 280px;
      position: relative;
    }

    .search-box input {
      width: 100%;
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      padding: 10px 14px;
      color: var(--text-main);
      font-size: 14px;
      outline: none;
      transition: all 0.2s ease;
    }

    .search-box input:focus {
      border-color: var(--accent-blue);
      box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2);
    }

    .filter-group {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .filter-btn {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      color: var(--text-muted);
      padding: 8px 14px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .filter-btn:hover, .filter-btn.active {
      background: var(--bg-card-hover);
      color: var(--text-main);
      border-color: var(--accent-blue);
    }

    .screens-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 20px;
    }

    .screen-card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 14px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    }

    .screen-card:hover {
      transform: translateY(-3px);
      box-shadow: 0 12px 28px rgba(0, 0, 0, 0.4);
      border-color: #3b5070;
    }

    .screen-preview-container {
      width: 100%;
      height: 230px;
      background: #0b111e;
      border-bottom: 1px solid var(--border-subtle);
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      overflow: hidden;
    }

    .screen-preview-img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      background-color: #000;
      cursor: pointer;
      transition: transform 0.3s ease;
    }

    .screen-preview-img:hover {
      transform: scale(1.03);
    }

    .placeholder-preview {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 20px;
      color: #64748b;
    }

    .placeholder-preview svg {
      width: 44px;
      height: 44px;
      stroke: #475569;
      margin-bottom: 8px;
    }

    .placeholder-preview span {
      font-size: 12px;
      font-weight: 500;
    }

    .card-body {
      padding: 18px;
      display: flex;
      flex-direction: column;
      flex: 1;
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 8px;
      gap: 12px;
    }

    .screen-title {
      font-size: 17px;
      font-weight: 700;
      color: #fff;
      line-height: 1.3;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-size: 11px;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 6px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      white-space: nowrap;
    }

    .badge-complex {
      background: var(--complex-bg);
      color: var(--complex-badge);
      border: 1px solid rgba(244, 63, 94, 0.3);
    }

    .badge-medium {
      background: var(--medium-bg);
      color: var(--medium-badge);
      border: 1px solid rgba(245, 158, 11, 0.3);
    }

    .badge-simple {
      background: var(--simple-bg);
      color: var(--simple-badge);
      border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .screen-raw-name {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      color: #64748b;
      word-break: break-all;
      margin-bottom: 12px;
    }

    .screen-type-tag {
      display: inline-block;
      font-size: 11px;
      background: rgba(56, 189, 248, 0.1);
      color: #38bdf8;
      border: 1px solid rgba(56, 189, 248, 0.2);
      border-radius: 4px;
      padding: 2px 6px;
      margin-bottom: 12px;
      font-weight: 600;
    }

    .rationale-box {
      background: rgba(15, 23, 42, 0.6);
      border: 1px dashed var(--border-subtle);
      border-radius: 6px;
      padding: 8px 10px;
      font-size: 12px;
      color: #cbd5e1;
      margin-bottom: 14px;
    }

    .metrics-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: auto;
      padding-top: 10px;
      border-top: 1px solid var(--border-subtle);
    }

    .metric-chip {
      font-size: 11px;
      font-family: 'JetBrains Mono', monospace;
      background: #0f172a;
      border: 1px solid #1e293b;
      padding: 3px 6px;
      border-radius: 4px;
      color: #94a3b8;
    }

    .metric-chip.highlight {
      color: #38bdf8;
      border-color: rgba(56, 189, 248, 0.3);
      background: rgba(56, 189, 248, 0.05);
    }

    .instructions-card {
      background: linear-gradient(135deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.8) 100%);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 24px;
    }

    .instructions-card h3 {
      font-size: 16px;
      margin-bottom: 8px;
      color: var(--accent-blue);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .instructions-card ol {
      margin-left: 20px;
      font-size: 13px;
      color: var(--text-muted);
      line-height: 1.8;
    }

    .instructions-card code {
      font-family: 'JetBrains Mono', monospace;
      background: #0f172a;
      padding: 2px 6px;
      border-radius: 4px;
      color: #38bdf8;
    }

    /* Lightbox Modal */
    .lightbox {
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.88);
      backdrop-filter: blur(8px);
      z-index: 9999;
      justify-content: center;
      align-items: center;
      padding: 20px;
    }

    .lightbox.active {
      display: flex;
    }

    .lightbox-content {
      max-width: 90%;
      max-height: 90%;
      border-radius: 12px;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.7);
      border: 1px solid rgba(255, 255, 255, 0.1);
      object-fit: contain;
    }

    .lightbox-close {
      position: absolute;
      top: 24px;
      right: 24px;
      font-size: 32px;
      color: #fff;
      cursor: pointer;
    }
  </style>
</head>
<body>

<div class="container">
  <header>
    <div class="header-top">
      <div>
        <h1>A11ySense — Android Screen Visual Audit & Screenshot Mapper</h1>
        <p class="subtitle">
          Visual correlation between Android layout / activity identifiers and human-readable screen titles.
          Screenshots are automatically linked from the <code>screenshots/</code> directory.
        </p>
      </div>
      <div>
        <a href="audit_results.csv" download class="filter-btn active" style="text-decoration: none; display: inline-block;">
          Download CSV
        </a>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="label">Total Audited Screens</div>
        <div class="value">__TOTAL_SCREENS__</div>
      </div>
      <div class="stat-card">
        <div class="label">Total Effort</div>
        <div class="value">__TOTAL_HOURS__ hrs</div>
      </div>
      <div class="stat-card" style="border-color: rgba(244, 63, 94, 0.3);">
        <div class="label" style="color: var(--complex-badge);">Complex (5.5h)</div>
        <div class="value" style="color: var(--complex-badge);">__COMPLEX_COUNT__</div>
      </div>
      <div class="stat-card" style="border-color: rgba(245, 158, 11, 0.3);">
        <div class="label" style="color: var(--medium-badge);">Medium (2.5h)</div>
        <div class="value" style="color: var(--medium-badge);">__MEDIUM_COUNT__</div>
      </div>
      <div class="stat-card" style="border-color: rgba(16, 185, 129, 0.3);">
        <div class="label" style="color: var(--simple-badge);">Simple (1.0h)</div>
        <div class="value" style="color: var(--simple-badge);">__SIMPLE_COUNT__</div>
      </div>
      <div class="stat-card">
        <div class="label">Screenshots Linked</div>
        <div class="value" id="capturedCount">__CAPTURED_COUNT__ / __TOTAL_SCREENS__</div>
      </div>
    </div>
  </header>

  <div class="instructions-card">
    <h3>
      <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
      How to Automatically Capture & View Screenshots for These Screens
    </h3>
    <ol>
      <li>Connect your Android phone (with USB debugging) or start an Android Emulator in Android Studio.</li>
      <li>Run <code>python capture_screens.py</code> — it automatically tracks whatever screen you navigate to and snaps a screenshot directly matching the screen name.</li>
      <li>Refresh this page, and all screenshots will appear directly above each screen title! You can also click any image to view it full screen.</li>
    </ol>
  </div>

  <div class="controls-panel">
    <div class="search-box">
      <input type="text" id="searchInput" placeholder="Search by screen title, component name, or rationale (e.g. Digio, Aadhaar, Otp, Modal)..." />
    </div>
    <div class="filter-group">
      <button class="filter-btn active" data-filter="all">All (__TOTAL_SCREENS__)</button>
      <button class="filter-btn" data-filter="Complex">Complex (__COMPLEX_COUNT__)</button>
      <button class="filter-btn" data-filter="Medium">Medium (__MEDIUM_COUNT__)</button>
      <button class="filter-btn" data-filter="Simple">Simple (__SIMPLE_COUNT__)</button>
      <button class="filter-btn" data-filter="has_screenshot">With Screenshot (__CAPTURED_COUNT__)</button>
    </div>
  </div>

  <div class="screens-grid" id="screensGrid">
    <!-- Rendered via JavaScript -->
  </div>
</div>

<div class="lightbox" id="lightbox" onclick="closeLightbox()">
  <span class="lightbox-close">&times;</span>
  <img class="lightbox-content" id="lightboxImg" src="" alt="Enlarged view">
</div>

<script>
  const screens = __ROWS_JSON__;

  let activeFilter = 'all';
  let searchTerm = '';

  const grid = document.getElementById('screensGrid');
  const searchInput = document.getElementById('searchInput');
  const filterButtons = document.querySelectorAll('.filter-btn[data-filter]');

  function renderScreens() {
    const term = searchTerm.toLowerCase();
    const filtered = screens.filter(s => {
      // Tier filter
      if (activeFilter === 'Complex' && s.tier !== 'Complex') return false;
      if (activeFilter === 'Medium' && s.tier !== 'Medium') return false;
      if (activeFilter === 'Simple' && s.tier !== 'Simple') return false;
      if (activeFilter === 'has_screenshot' && !s.screenshot) return false;

      // Search term
      if (term) {
        const haystack = (s.title + ' ' + s.screen_name + ' ' + s.screen_type + ' ' + s.why).toLowerCase();
        if (!haystack.includes(term)) return false;
      }
      return true;
    });

    if (filtered.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 60px 20px; color: #64748b;">
          <h3>No screens match your search criteria</h3>
          <p style="margin-top: 8px;">Try clearing filters or searching for different keywords.</p>
        </div>
      `;
      return;
    }

    grid.innerHTML = filtered.map(s => {
      const tierBadgeClass = s.tier === 'Complex' ? 'badge-complex' : (s.tier === 'Medium' ? 'badge-medium' : 'badge-simple');
      
      const previewHtml = s.screenshot 
        ? `<img class="screen-preview-img" src="${s.screenshot}" alt="${s.title}" onclick="openLightbox('${s.screenshot}')" />`
        : `<div class="placeholder-preview">
             <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
             <span>No screenshot linked</span>
             <span style="font-size: 10px; color: #475569; margin-top: 4px;">Run capture_screens.py to snapshot</span>
           </div>`;

      return `
        <div class="screen-card" id="card-${s.safe_id}">
          <div class="screen-preview-container">
            ${previewHtml}
          </div>
          <div class="card-body">
            <div class="card-header">
              <div class="screen-title">${s.title}</div>
              <span class="badge ${tierBadgeClass}">${s.tier} (${s.est_hours}h)</span>
            </div>
            
            <div class="screen-raw-name">${s.screen_name}</div>
            <div><span class="screen-type-tag">${s.screen_type}</span></div>
            
            <div class="rationale-box">
              <strong>Rationale:</strong> ${s.why}
            </div>

            <div class="metrics-chips">
              <span class="metric-chip ${parseInt(s.visible_elements) > 20 ? 'highlight' : ''}">Elems: ${s.visible_elements}</span>
              <span class="metric-chip ${parseInt(s.buttons) > 0 ? 'highlight' : ''}">Btns: ${s.buttons}</span>
              <span class="metric-chip ${parseInt(s.form_controls) > 0 ? 'highlight' : ''}">Forms: ${s.form_controls}</span>
              <span class="metric-chip ${parseInt(s.modals) > 0 ? 'highlight' : ''}">Modals: ${s.modals}</span>
              <span class="metric-chip ${parseInt(s.auth_steps) > 0 ? 'highlight' : ''}">Auth: ${s.auth_steps}</span>
              <span class="metric-chip ${parseInt(s.custom_widgets) > 0 ? 'highlight' : ''}">Widgets: ${s.custom_widgets}</span>
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  // Event Listeners
  searchInput.addEventListener('input', (e) => {
    searchTerm = e.target.value;
    renderScreens();
  });

  filterButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      filterButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeFilter = btn.dataset.filter;
      renderScreens();
    });
  });

  function openLightbox(src) {
    document.getElementById('lightboxImg').src = src;
    document.getElementById('lightbox').classList.add('active');
  }

  function closeLightbox() {
    document.getElementById('lightbox').classList.remove('active');
  }

  // Initial render
  renderScreens();
</script>

</body>
</html>
"""

def generate_report(csv_path: str = "audit_results.csv", output_html: str = "audit_report.html", screenshots_dir: str = "screenshots"):
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    screenshots_path = Path(screenshots_dir)
    screenshots_path.mkdir(exist_ok=True)

    rows = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            screen_name = r.get("screen_name", "")
            safe_name = screen_name.replace("/", "_").replace(".", "_")
            
            # Possible screenshot filenames
            possible_files = [
                screenshots_path / f"{safe_name}.png",
                screenshots_path / f"{safe_name}.jpg",
                screenshots_path / f"{screen_name.split('/')[-1]}.png",
                screenshots_path / f"{screen_name.split('.')[-1]}.png",
            ]
            
            matched_screenshot = None
            for p in possible_files:
                if p.exists():
                    matched_screenshot = str(p.as_posix())
                    break

            r["screenshot"] = matched_screenshot or ""
            r["safe_id"] = safe_name
            rows.append(r)

    total_screens = len(rows)
    complex_count = sum(1 for r in rows if r.get("tier") == "Complex")
    medium_count = sum(1 for r in rows if r.get("tier") == "Medium")
    simple_count = sum(1 for r in rows if r.get("tier") == "Simple")
    total_hours = sum(float(r.get("est_hours", 0) or 0) for r in rows)
    captured_count = sum(1 for r in rows if r["screenshot"])

    html = HTML_TEMPLATE
    html = html.replace("__TOTAL_SCREENS__", str(total_screens))
    html = html.replace("__TOTAL_HOURS__", f"{total_hours:.1f}")
    html = html.replace("__COMPLEX_COUNT__", str(complex_count))
    html = html.replace("__MEDIUM_COUNT__", str(medium_count))
    html = html.replace("__SIMPLE_COUNT__", str(simple_count))
    html = html.replace("__CAPTURED_COUNT__", str(captured_count))
    html = html.replace("__ROWS_JSON__", json.dumps(rows))

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[+] Visual report generated successfully: {os.path.abspath(output_html)}")
    print(f"    - Total screens: {total_screens}")
    print(f"    - Screenshots linked: {captured_count}")

if __name__ == "__main__":
    generate_report()
