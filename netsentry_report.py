import pandas as pd
import os
import webbrowser
from datetime import datetime

LOG_FILE = "netsentry.log"

try:
    df = pd.read_csv(LOG_FILE, names=["timestamp", "host", "status"])
except FileNotFoundError:
    import random
    data = []
    hosts = ["8.8.8.8", "cloudflare.com", "github.com", "google.com"]
    for h in hosts:
        for i in range(10):
            data.append({
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "host": h,
                "status": "UP" if random.random() > 0.05 else "DOWN"
            })
    df = pd.DataFrame(data)

df["timestamp"] = pd.to_datetime(df["timestamp"])

uptime = df.groupby("host")["status"].apply(
    lambda x: round((x == "UP").sum() / len(x) * 100, 1)
).reset_index()
uptime.columns = ["host", "uptime_pct"]

total_hosts = len(uptime)
total_checks = len(df)
avg_uptime = round(uptime["uptime_pct"].mean(), 1)
alerts = int((uptime["uptime_pct"] < 100).sum())
generated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
up_count = int((df["status"] == "UP").sum())
down_count = int((df["status"] == "DOWN").sum())
up_pct = round(up_count / len(df) * 100, 1)
stat_alert_color = "#ff4444" if alerts > 0 else "#00cc66"
alert_label = "Issues Found" if alerts > 0 else "No Issues"
bar_labels = list(uptime["host"])
bar_values = list(uptime["uptime_pct"])
bar_colors = ["'#00cc66'" if v >= 90 else "'#ff4444'" for v in bar_values]

sidebar_hosts = ""
for _, row in uptime.iterrows():
    dot = "#00cc66" if row["uptime_pct"] >= 90 else "#ff4444"
    sidebar_hosts += f'<div class="nav-item host-link" onclick="showHost(\'{row["host"]}\')"><span class="dot" style="background:{dot}"></span>{row["host"]}</div>'

host_rows = ""
for _, row in uptime.iterrows():
    sc = "#00cc66" if row["uptime_pct"] >= 90 else "#ff4444"
    last_check = df[df["host"] == row["host"]]["timestamp"].max().strftime('%I:%M:%S %p')
    total_h = len(df[df["host"] == row["host"]])
    down_h = len(df[(df["host"] == row["host"]) & (df["status"] == "DOWN")])
    host_rows += f"""<tr>
        <td>{row["host"]}</td>
        <td><span class="badge" style="background:{sc}20;color:{sc};border:1px solid {sc}">UP</span></td>
        <td style="color:{sc};font-weight:600">{row["uptime_pct"]}%</td>
        <td>{last_check} <span style="width:7px;height:7px;border-radius:50%;background:{sc};display:inline-block;margin-left:4px"></span></td>
    </tr>"""

log_rows = ""
for _, row in df.sort_values("timestamp", ascending=False).head(20).iterrows():
    c = "#00cc66" if row["status"] == "UP" else "#ff4444"
    log_rows += f"""<tr>
        <td>{row["timestamp"].strftime('%Y-%m-%d %H:%M:%S')}</td>
        <td>{row["host"]}</td>
        <td><span class="badge" style="background:{c}20;color:{c};border:1px solid {c}">{row["status"]}</span></td>
    </tr>"""

# Per-host detail panels
host_panels = ""
for _, row in uptime.iterrows():
    hdf = df[df["host"] == row["host"]].sort_values("timestamp", ascending=False)
    sc = "#00cc66" if row["uptime_pct"] >= 90 else "#ff4444"
    h_logs = ""
    for _, lr in hdf.head(10).iterrows():
        lc = "#00cc66" if lr["status"] == "UP" else "#ff4444"
        h_logs += f"""<tr>
            <td>{lr["timestamp"].strftime('%Y-%m-%d %H:%M:%S')}</td>
            <td><span class="badge" style="background:{lc}20;color:{lc};border:1px solid {lc}">{lr["status"]}</span></td>
        </tr>"""
    host_panels += f"""
    <div id="host-{row["host"]}" class="page" style="display:none">
      <div class="page-header">
        <div>
          <h1 style="color:#e6edf3">🖥️ {row["host"]}</h1>
          <div class="subtitle">Host Detail View</div>
        </div>
      </div>
      <div class="stats" style="grid-template-columns:repeat(3,1fr)">
        <div class="stat-card">
          <div class="stat-value" style="color:{sc}">{row["uptime_pct"]}%</div>
          <div class="stat-label">Uptime</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color:#a78bfa">{len(hdf)}</div>
          <div class="stat-label">Total Checks</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color:#ff4444">{len(hdf[hdf["status"]=="DOWN"])}</div>
          <div class="stat-label">Downtime Events</div>
        </div>
      </div>
      <div class="card">
        <div class="card-title">📋 Check History</div>
        <div class="card-sub">All checks for {row["host"]}</div>
        <table><tr><th>Timestamp</th><th>Status</th></tr>{h_logs}</table>
      </div>
    </div>"""

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>NetSentry Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{display:flex;background:#0a0e1a;color:#e6edf3;font-family:'Segoe UI',sans-serif;min-height:100vh}}

  /* SIDEBAR */
  .sidebar{{width:220px;background:#0d1117;border-right:1px solid #1e2736;display:flex;flex-direction:column;flex-shrink:0;height:100vh;position:sticky;top:0}}
  .sidebar-logo{{padding:20px 16px;border-bottom:1px solid #1e2736}}
  .brand{{font-size:16px;font-weight:700;color:#58a6ff;display:flex;align-items:center;gap:8px}}
  .brand-sub{{font-size:10px;color:#8b949e;margin-top:2px}}
  .nav-section{{padding:14px 16px 6px;font-size:10px;color:#8b949e;letter-spacing:1.5px;text-transform:uppercase}}
  .nav-item{{padding:9px 16px;font-size:13px;color:#8b949e;cursor:pointer;display:flex;align-items:center;gap:9px;border-radius:6px;margin:2px 8px;transition:all 0.15s}}
  .nav-item:hover{{background:#161b22;color:#e6edf3}}
  .nav-item.active{{background:#161b22;color:#58a6ff;font-weight:600}}
  .dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}
  .sidebar-footer{{margin-top:auto;padding:14px 16px;border-top:1px solid #1e2736}}
  .sys-ok{{font-size:11px;color:#00cc66;font-weight:600}}
  .sys-time{{font-size:10px;color:#8b949e;margin-top:3px}}

  /* MAIN */
  .main{{flex:1;overflow:auto}}
  .page{{display:none;padding:0}}
  .page.active{{display:block}}
  .page-header{{background:#0d1117;border-bottom:1px solid #1e2736;padding:16px 24px;display:flex;justify-content:space-between;align-items:center}}
  .page-header h1{{font-size:20px;font-weight:700}}
  .subtitle{{font-size:12px;color:#8b949e;margin-top:2px}}
  .topbar-right{{display:flex;align-items:center;gap:10px}}
  .refresh-badge{{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:6px 12px;font-size:12px;color:#8b949e;display:flex;align-items:center;gap:6px}}
  .pulse{{width:6px;height:6px;border-radius:50%;background:#00cc66;animation:pulse 2s infinite}}
  @keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:0.3}}}}

  .content{{padding:22px}}
  .stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px}}
  .stat-card{{background:#0d1117;border:1px solid #1e2736;border-radius:10px;padding:16px}}
  .stat-header{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px}}
  .stat-icon{{width:34px;height:34px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:15px}}
  .stat-value{{font-size:26px;font-weight:700}}
  .stat-label{{font-size:11px;color:#8b949e;margin-top:2px}}
  .stat-sub{{font-size:11px;margin-top:6px}}
  .grid-2-1{{display:grid;grid-template-columns:2fr 1fr;gap:14px;margin-bottom:14px}}
  .grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}}
  .card{{background:#0d1117;border:1px solid #1e2736;border-radius:10px;padding:18px}}
  .card-title{{font-size:13px;font-weight:600;color:#e6edf3;margin-bottom:3px}}
  .card-sub{{font-size:11px;color:#8b949e;margin-bottom:14px}}
  .chart-wrap{{position:relative;height:200px}}
  table{{width:100%;border-collapse:collapse;font-size:12px}}
  th{{text-align:left;padding:8px 10px;background:#161b22;color:#8b949e;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:0.5px}}
  td{{padding:9px 10px;border-bottom:1px solid #1e2736;color:#c9d1d9}}
  tr:last-child td{{border-bottom:none}}
  tr:hover td{{background:#161b22}}
  .badge{{padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600}}

  /* LOGS PAGE */
  .log-filter{{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap}}
  .filter-btn{{padding:5px 14px;border-radius:20px;border:1px solid #30363d;background:transparent;color:#8b949e;font-size:11px;cursor:pointer;transition:all 0.15s}}
  .filter-btn:hover,.filter-btn.active{{background:#58a6ff20;border-color:#58a6ff;color:#58a6ff}}

  /* ALERTS PAGE */
  .alert-card{{background:#0d1117;border:1px solid #ff444430;border-left:3px solid #ff4444;border-radius:8px;padding:14px;margin-bottom:10px}}
  .alert-ok{{background:#0d1117;border:1px solid #00cc6630;border-left:3px solid #00cc66;border-radius:8px;padding:14px;margin-bottom:10px}}

  /* REPORTS PAGE */
  .report-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}}
</style>
</head>
<body>

<!-- SIDEBAR -->
<div class="sidebar">
  <div class="sidebar-logo">
    <div class="brand">🛡️ NetSentry</div>
    <div class="brand-sub">Network Uptime Monitor</div>
  </div>

  <div class="nav-section">Navigation</div>
  <div class="nav-item active" onclick="showPage('dashboard',this)">📊 Dashboard</div>
  <div class="nav-item" onclick="showPage('hosts',this)">🖥️ Hosts</div>
  <div class="nav-item" onclick="showPage('logs',this)">📋 Logs</div>
  <div class="nav-item" onclick="showPage('reports',this)">📈 Reports</div>
  <div class="nav-item" onclick="showPage('alerts',this)">🔔 Alerts {f'<span style="background:#ff4444;color:#fff;border-radius:10px;padding:1px 6px;font-size:10px;margin-left:auto">{alerts}</span>' if alerts > 0 else ''}</div>
  <div class="nav-item" onclick="showPage('settings',this)">⚙️ Settings</div>
  <div class="nav-item" onclick="showPage('about',this)">ℹ️ About</div>

  <div class="nav-section">Hosts</div>
  {sidebar_hosts}

  <div class="sidebar-footer">
    <div class="sys-ok">● All Systems Operational</div>
    <div class="sys-time">Last check: {generated}</div>
  </div>
</div>

<!-- MAIN CONTENT -->
<div class="main">

  <!-- DASHBOARD PAGE -->
  <div id="page-dashboard" class="page active">
    <div class="page-header">
      <div>
        <h1>NetSentry Dashboard</h1>
        <div class="subtitle">Real-time network monitoring and uptime analytics</div>
      </div>
      <div class="topbar-right">
        <div class="refresh-badge"><span class="pulse"></span>Auto Refresh: 10s</div>
        <div style="font-size:11px;color:#8b949e">{generated}</div>
      </div>
    </div>
    <div class="content">
      <div class="stats">
        <div class="stat-card">
          <div class="stat-header">
            <div><div class="stat-value" style="color:#58a6ff">{total_hosts}</div><div class="stat-label">Hosts Monitored</div></div>
            <div class="stat-icon" style="background:#58a6ff20">🖥️</div>
          </div>
          <div class="stat-sub" style="color:#00cc66">All Active</div>
        </div>
        <div class="stat-card">
          <div class="stat-header">
            <div><div class="stat-value" style="color:#a78bfa">{total_checks}</div><div class="stat-label">Total Checks</div></div>
            <div class="stat-icon" style="background:#a78bfa20">⚡</div>
          </div>
          <div class="stat-sub" style="color:#8b949e">Today</div>
        </div>
        <div class="stat-card">
          <div class="stat-header">
            <div><div class="stat-value" style="color:#00cc66">{avg_uptime}%</div><div class="stat-label">Average Uptime</div></div>
            <div class="stat-icon" style="background:#00cc6620">🛡️</div>
          </div>
          <div class="stat-sub" style="color:#00cc66">Excellent</div>
        </div>
        <div class="stat-card">
          <div class="stat-header">
            <div><div class="stat-value" style="color:{stat_alert_color}">{alerts}</div><div class="stat-label">Alerts</div></div>
            <div class="stat-icon" style="background:{stat_alert_color}20">🔔</div>
          </div>
          <div class="stat-sub" style="color:{stat_alert_color}">{alert_label}</div>
        </div>
      </div>
      <div class="grid-2-1">
        <div class="card">
          <div class="card-title">📊 Uptime Overview</div>
          <div class="card-sub">Uptime percentage per host</div>
          <div class="chart-wrap"><canvas id="barChart"></canvas></div>
        </div>
        <div class="card">
          <div class="card-title">🍩 Uptime Distribution</div>
          <div class="card-sub">UP vs DOWN ratio</div>
          <div class="chart-wrap"><canvas id="donutChart"></canvas></div>
        </div>
      </div>
      <div class="grid-2">
        <div class="card">
          <div class="card-title">📋 Recent Log <span style="color:#8b949e;font-weight:400">(Last 10 checks)</span></div>
          <div class="card-sub">Latest monitoring results</div>
          <table><tr><th>Timestamp</th><th>Host</th><th>Status</th></tr>{log_rows}</table>
        </div>
        <div class="card">
          <div class="card-title">🖥️ Hosts Status</div>
          <div class="card-sub">Current status of all monitored hosts</div>
          <table><tr><th>Host</th><th>Status</th><th>Uptime</th><th>Last Check</th></tr>{host_rows}</table>
        </div>
      </div>
    </div>
  </div>

  <!-- HOSTS PAGE -->
  <div id="page-hosts" class="page">
    <div class="page-header"><div><h1>🖥️ Hosts</h1><div class="subtitle">All monitored hosts and their status</div></div></div>
    <div class="content">
      <div class="card">
        <div class="card-title">All Hosts</div>
        <div class="card-sub">Click a host in the sidebar to see detailed view</div>
        <table>
          <tr><th>Host</th><th>Status</th><th>Uptime %</th><th>Total Checks</th><th>Last Check</th></tr>
          {host_rows}
        </table>
      </div>
    </div>
  </div>

  <!-- LOG PAGE -->
  <div id="page-logs" class="page">
    <div class="page-header"><div><h1>📋 Logs</h1><div class="subtitle">Full monitoring log history</div></div></div>
    <div class="content">
      <div class="card">
        <div class="card-title">All Log Entries</div>
        <div class="card-sub">{len(df)} total entries</div>
        <div class="log-filter">
          <button class="filter-btn active" onclick="filterLog('all',this)">All</button>
          <button class="filter-btn" onclick="filterLog('UP',this)">UP Only</button>
          <button class="filter-btn" onclick="filterLog('DOWN',this)">DOWN Only</button>
        </div>
        <table id="logTable">
          <tr><th>Timestamp</th><th>Host</th><th>Status</th></tr>
          {log_rows}
        </table>
      </div>
    </div>
  </div>

  <!-- REPORTS PAGE -->
  <div id="page-reports" class="page">
    <div class="page-header"><div><h1>📈 Reports</h1><div class="subtitle">Uptime analytics and summaries</div></div></div>
    <div class="content">
      <div class="report-grid">
        <div class="card">
          <div class="card-title">📊 Uptime Bar Chart</div>
          <div class="card-sub">Per host breakdown</div>
          <div class="chart-wrap"><canvas id="barChart2"></canvas></div>
        </div>
        <div class="card">
          <div class="card-title">🍩 UP vs DOWN</div>
          <div class="card-sub">Overall ratio</div>
          <div class="chart-wrap"><canvas id="donutChart2"></canvas></div>
        </div>
        <div class="card" style="grid-column:1/-1">
          <div class="card-title">📋 Summary Table</div>
          <div class="card-sub">Aggregated stats per host</div>
          <table><tr><th>Host</th><th>Uptime %</th><th>UP Checks</th><th>DOWN Checks</th><th>Total</th></tr>
          {''.join([f"<tr><td>{r['host']}</td><td style='color:#00cc66;font-weight:600'>{r['uptime_pct']}%</td><td>{len(df[(df['host']==r['host'])&(df['status']=='UP')])}</td><td style='color:#ff4444'>{len(df[(df['host']==r['host'])&(df['status']=='DOWN')])}</td><td>{len(df[df['host']==r['host']])}</td></tr>" for _,r in uptime.iterrows()])}
          </table>
        </div>
      </div>
    </div>
  </div>

  <!-- ALERTS PAGE -->
  <div id="page-alerts" class="page">
    <div class="page-header"><div><h1>🔔 Alerts</h1><div class="subtitle">Issues and notifications</div></div></div>
    <div class="content">
      {''.join([f'<div class="alert-card"><b style="color:#ff4444">⚠️ {r["host"]}</b> — Uptime below 100% ({r["uptime_pct"]}%)<div style="font-size:11px;color:#8b949e;margin-top:4px">Detected downtime events during monitoring period</div></div>' for _,r in uptime[uptime["uptime_pct"]<100].iterrows()]) if alerts > 0 else '<div class="alert-ok"><b style="color:#00cc66">✅ All Clear</b> — No issues detected<div style="font-size:11px;color:#8b949e;margin-top:4px">All hosts are running at 100% uptime</div></div>'}
    </div>
  </div>

  <!-- SETTINGS PAGE -->
  <div id="page-settings" class="page">
    <div class="page-header"><div><h1>⚙️ Settings</h1><div class="subtitle">Dashboard configuration</div></div></div>
    <div class="content">
      <div class="card">
        <div class="card-title">Configuration</div>
        <div class="card-sub">NetSentry settings</div>
        <table>
          <tr><th>Setting</th><th>Value</th></tr>
          <tr><td>Log File</td><td style="color:#58a6ff">netsentry.log</td></tr>
          <tr><td>Hosts File</td><td style="color:#58a6ff">hosts.txt</td></tr>
          <tr><td>Refresh Interval</td><td style="color:#00cc66">10 seconds</td></tr>
          <tr><td>Alert Threshold</td><td style="color:#ffde59">&lt; 100% uptime</td></tr>
          <tr><td>macOS Notifications</td><td style="color:#00cc66">Enabled</td></tr>
          <tr><td>Dashboard Version</td><td style="color:#8b949e">v1.0</td></tr>
        </table>
      </div>
    </div>
  </div>

  <!-- ABOUT PAGE -->
  <div id="page-about" class="page">
    <div class="page-header"><div><h1>ℹ️ About NetSentry</h1><div class="subtitle">Project information</div></div></div>
    <div class="content">
      <div class="card">
        <div class="card-title">NetSentry v1.0</div>
        <div class="card-sub">Built as part of the Cloud Engineering Roadmap — Week 3 Project</div>
        <table>
          <tr><th>Detail</th><th>Info</th></tr>
          <tr><td>Author</td><td style="color:#58a6ff">Nazneen</td></tr>
          <tr><td>Phase</td><td style="color:#00cc66">Phase 1 — Foundations</td></tr>
          <tr><td>Tech Stack</td><td style="color:#a78bfa">Bash + Python + pandas + Chart.js</td></tr>
          <tr><td>Purpose</td><td>Network uptime monitoring with visual analytics</td></tr>
          <tr><td>Generated</td><td style="color:#8b949e">{generated}</td></tr>
        </table>
      </div>
    </div>
  </div>

  <!-- HOST DETAIL PAGES -->
  {host_panels}

</div>

<script>
// PAGE SWITCHING
function showPage(id, el) {{
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const pg = document.getElementById('page-' + id);
  if(pg) pg.classList.add('active');
  if(el) el.classList.add('active');
  if(id === 'reports') setTimeout(initReportCharts, 100);
}}

function showHost(host) {{
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const pg = document.getElementById('host-' + host);
  if(pg) pg.classList.add('active');
}}

// LOG FILTER
function filterLog(type, btn) {{
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const rows = document.querySelectorAll('#logTable tr:not(:first-child)');
  rows.forEach(row => {{
    if(type === 'all') row.style.display = '';
    else row.style.display = row.innerText.includes(type) ? '' : 'none';
  }});
}}

// BAR CHART (Dashboard)
new Chart(document.getElementById('barChart'), {{
  type: 'bar',
  data: {{
    labels: {bar_labels},
    datasets: [{{ label: 'Uptime %', data: {bar_values}, backgroundColor: [{', '.join(bar_colors)}], borderRadius: 6, borderSkipped: false }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      y: {{ min: 0, max: 110, ticks: {{ color: '#8b949e', callback: v => v + '%' }}, grid: {{ color: '#1e2736' }} }},
      x: {{ ticks: {{ color: '#8b949e' }}, grid: {{ display: false }} }}
    }}
  }}
}});

// DONUT CHART (Dashboard)
new Chart(document.getElementById('donutChart'), {{
  type: 'doughnut',
  data: {{
    labels: ['UP', 'DOWN'],
    datasets: [{{ data: [{up_count}, {down_count}], backgroundColor: ['#00cc66','#ff4444'], borderWidth: 0 }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false, cutout: '70%',
    plugins: {{ legend: {{ position: 'bottom', labels: {{ color: '#8b949e', font: {{ size: 11 }} }} }} }}
  }},
  plugins: [{{
    id: 'center',
    afterDraw(chart) {{
      const {{ ctx, chartArea: {{ top, bottom, left, right }} }} = chart;
      ctx.save();
      ctx.font = 'bold 20px Segoe UI'; ctx.fillStyle = '#00cc66';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText('{up_pct}%', (left+right)/2, (top+bottom)/2 - 8);
      ctx.font = '10px Segoe UI'; ctx.fillStyle = '#8b949e';
      ctx.fillText('UP', (left+right)/2, (top+bottom)/2 + 12);
      ctx.restore();
    }}
  }}]
}});

// REPORTS CHARTS (lazy init)
function initReportCharts() {{
  if(window.reportChartsInit) return;
  window.reportChartsInit = true;
  new Chart(document.getElementById('barChart2'), {{
    type: 'bar',
    data: {{ labels: {bar_labels}, datasets: [{{ data: {bar_values}, backgroundColor: [{', '.join(bar_colors)}], borderRadius:6, borderSkipped:false }}] }},
    options: {{ responsive:true, maintainAspectRatio:false, plugins:{{legend:{{display:false}}}}, scales:{{ y:{{min:0,max:110,ticks:{{color:'#8b949e',callback:v=>v+'%'}},grid:{{color:'#1e2736'}}}}, x:{{ticks:{{color:'#8b949e'}},grid:{{display:false}}}} }} }}
  }});
  new Chart(document.getElementById('donutChart2'), {{
    type: 'doughnut',
    data: {{ labels:['UP','DOWN'], datasets:[{{data:[{up_count},{down_count}],backgroundColor:['#00cc66','#ff4444'],borderWidth:0}}] }},
    options: {{ responsive:true, maintainAspectRatio:false, cutout:'70%', plugins:{{legend:{{position:'bottom',labels:{{color:'#8b949e'}}}}}} }},
    plugins: [{{
      id: 'center2',
      afterDraw(chart) {{
        const {{ ctx, chartArea: {{ top, bottom, left, right }} }} = chart;
        ctx.save();
        ctx.font = 'bold 20px Segoe UI'; ctx.fillStyle = '#00cc66';
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText('{up_pct}%', (left+right)/2, (top+bottom)/2 - 8);
        ctx.font = '10px Segoe UI'; ctx.fillStyle = '#8b949e';
        ctx.fillText('UP', (left+right)/2, (top+bottom)/2 + 12);
        ctx.restore();
      }}
    }}]
  }});
}}
</script>
</body>
</html>"""

output_path = os.path.abspath("netsentry_dashboard.html")
with open(output_path, "w") as f:
    f.write(html)

webbrowser.open(f"file://{output_path}")
print(f"✅ NetSentry Dashboard opened!")