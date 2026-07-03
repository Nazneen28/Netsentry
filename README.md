# 🛡️ NetSentry — Network Uptime Monitor

A real-time network monitoring tool with an interactive analytics dashboard.

## 📊 Dashboard Preview

![NetSentry Dashboard](screenshot.png)

## 🔧 Tech Stack

- **Bash** — Network monitoring script
- **Python** — Data processing & report generation
- **pandas** — Log file analysis
- **Chart.js** — Interactive visualizations
- **HTML/CSS** — Dashboard UI

## ✨ Features

- ✅ Monitors multiple hosts/URLs via ping
- ✅ Logs uptime/downtime with timestamps
- ✅ macOS desktop notifications on failure
- ✅ Interactive HTML dashboard with:
  - Uptime bar chart per host
  - UP vs DOWN donut chart with % center
  - Live log table with filters
  - Per-host detail pages
  - Reports, Alerts, Settings pages
  - Fully working sidebar navigation

## 📁 Project Structure

```text
netsentry/
├── netsentry.sh          # Bash monitor
├── netsentry_report.py   # Python dashboard generator
├── hosts.txt             # Hosts to monitor
├── netsentry.log         # Auto-generated log
├── netsentry_dashboard.html  # Interactive dashboard
└── README.md
```

## 🚀 Usage

**1. Add hosts to monitor:**

```bash
echo "google.com" >> hosts.txt
echo "github.com" >> hosts.txt
```

**2. Run the monitor:**

```bash
chmod +x netsentry.sh
./netsentry.sh
```

**3. Generate dashboard:**

```bash
python3 netsentry_report.py
```

Dashboard auto-opens in your browser!

## 👩‍💻 Author

**Nazneen** — Cloud Engineering Roadmap | Phase 1 Week 3
