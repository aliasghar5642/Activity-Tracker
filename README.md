# Activity Tracker Pro 📊

Production-grade activity tracking system with intelligent categorization, Docker deployment, and AI-powered insights.

## 🌟 Features

### Intelligent Tracking
- **Smart Categorization**: Automatically distinguishes between:
  - **Primary Work**: VSCode, Cursor, IDEs (highest priority)
  - **Secondary Work**: Telegram, Slack, Spotify (supportive tools)
  - **Browser Intelligence**: Detects work vs. leisure domains
  - **Auto-Idle Detection**: No activity for 5 minutes = automatic idle
  
### Advanced Analytics
- **Deep Work Sessions**: Tracks focused work periods (10+ min, 80%+ active)
- **Productivity Scores**: Focus, Efficiency, Time ROI metrics
- **Activity Heatmaps**: Hour-by-hour, day-by-day patterns
- **Timeline Views**: Visual session history
- **Streak Tracking**: Consecutive productive days

### Production Ready
- **Dockerized Architecture**: Container-based deployment
- **Persistent Storage**: Database survives restarts
- **Health Checks**: Automatic service monitoring
- **Optimized Performance**: Handles months of data efficiently

### AI Insights
- **Gemini Integration**: AI-powered productivity analysis
- **Actionable Recommendations**: Data-driven improvement suggestions
- **Trend Analysis**: Pattern recognition and forecasting

## 🏗️ Architecture

```
activity-tracker-pro/
├── watcher/          # Background monitoring service
├── dashboard/        # Streamlit analytics interface
├── shared/           # Database initialization
└── data/             # Persistent SQLite storage
```

## 🚀 Quick Start

### Prerequisites
- **Windows 10/11** (for watcher - requires GUI access)
- **Docker Desktop** (for dashboard)
- **Python 3.11+** (for local watcher)

### Installation

1. **Clone the repository**
```bash
git clone <repo-url>
cd activity-tracker-pro
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY (optional)
```

3. **Start the system**

#### Option A: Windows Native Watcher + Docker Dashboard (Recommended)

**Terminal 1: Run Watcher on Windows**
```bash
cd watcher
pip install -r requirements.txt
python watcher.py
```

**Terminal 2: Run Dashboard in Docker**
```bash
docker-compose up dashboard
```

#### Option B: Everything on Windows (No Docker)

**Terminal 1: Watcher**
```bash
cd watcher
pip install -r requirements.txt
python watcher.py
```

**Terminal 2: Dashboard**
```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

4. **Access Dashboard**
Open browser: http://localhost:8501

## 📝 Usage

### Keyboard Shortcuts
- `Ctrl+Alt+Shift+I` - Start manual idle mode
- `Ctrl+Alt+Shift+O` - End idle mode
- `Ctrl+Alt+Shift+P` - Pause/Resume tracking

### System Tray Icon
- **Green** 🟢 - Actively tracking
- **Red** 🔴 - Idle mode
- **Gray** ⚪ - Paused

### Dashboard Features
1. **Time Period Selector**: View last 1-90 days
2. **Real-time Metrics**: KPIs update every 30 seconds
3. **Interactive Charts**: Hover for detailed info
4. **AI Analysis**: Click "Generate AI Analysis" for insights
5. **Data Export**: Download detailed breakdowns

## 🔧 Configuration

### Watcher Configuration (`watcher/config.py`)

```python
# Sample interval
SAMPLE_INTERVAL = 1  # seconds

# Session creation interval
FLUSH_INTERVAL = 30  # seconds

# Auto-idle threshold
IDLE_THRESHOLD = 300  # 5 minutes

# Customize application categories
PRIMARY_WORK_APPS = {
    "code.exe": "VSCode",
    "cursor.exe": "Cursor",
    # Add your apps here
}

# Customize work domains
WORK_DOMAINS = [
    "github.com",
    "stackoverflow.com",
    # Add your domains here
]
```

### Dashboard Configuration (`dashboard/config.py`)

```python
# Default date range
DEFAULT_DATE_RANGE = 7  # days

# Focus session thresholds
FOCUS_SESSION_MIN_DURATION = 600  # 10 minutes
FOCUS_SESSION_MIN_FOREGROUND = 0.8  # 80% active

# Productivity score thresholds
EXCELLENT_SCORE = 85
GOOD_SCORE = 70
MEDIUM_SCORE = 50
```

## 📊 Database Schema

### Sessions Table
- Tracks every 30-second window
- Categories: PRIMARY_WORK, SECONDARY_WORK, BROWSER_WORK, BROWSER_NONWORK, IDLE
- Metrics: duration, foreground time, productivity score, focus session flag

### Idle Periods Table
- Tracks manual and automatic idle periods
- Reason: manual, auto, shutdown

### System Events Table
- Logs: startup, shutdown, pause, resume events

## 🐳 Docker Notes

### Why Watcher Runs on Host
Docker containers **cannot access Windows GUI APIs** (pygetwindow, keyboard). The watcher must run natively on Windows to:
- Detect active window titles
- Capture keyboard shortcuts
- Show system tray icon

The dashboard runs perfectly in Docker as it only needs database access.

### Docker Commands

```bash
# Start dashboard only
docker-compose up dashboard

# View logs
docker-compose logs -f dashboard

# Rebuild after changes
docker-compose up --build dashboard

# Stop services
docker-compose down
```

## 🎯 Productivity Metrics Explained

### Focus Score (0-100)
Measures concentration quality:
- **85-100**: Excellent - Deep work dominates
- **70-84**: Good - Solid focus with minor distractions
- **50-69**: Medium - Fragmented attention
- **0-49**: Poor - High distraction level

Formula: `(Primary Work Ratio × 60) + (Focus Quality × 40)`

### Efficiency Score (0-100)
Percentage of tracked time spent on work:
- Work = PRIMARY_WORK + SECONDARY_WORK + BROWSER_WORK
- Formula: `(Work Time / Total Time) × 100`

### Time ROI (0-300+)
Value generated per minute tracked:
- Primary Work: 3x multiplier
- Browser Work: 1x multiplier
- Secondary Work: 0.8x multiplier
- Formula: `(Weighted Value / Total Time) × 100`

### Deep Work Sessions
Continuous PRIMARY_WORK periods with:
- Duration ≥ 10 minutes
- Foreground ratio ≥ 80%
- Minimal context switches

## 🔐 Privacy & Security

- **All data stays local**: SQLite database on your machine
- **No telemetry**: Zero data leaves your system (except AI API calls)
- **Gemini API**: Only sends aggregated metrics, not raw data
- **Open source**: Audit the code yourself

## 🛠️ Troubleshooting

### Watcher Issues

**Problem**: Hotkeys not working
- **Solution**: Run as administrator

**Problem**: No data recorded
- **Solution**: Check logs in `~/ActivityTracker/logs/watcher.log`

**Problem**: High CPU usage
- **Solution**: Increase `SAMPLE_INTERVAL` in config

### Dashboard Issues

**Problem**: Database not found
- **Solution**: Ensure watcher has run for at least 30 seconds

**Problem**: Charts not loading
- **Solution**: Wait for more data (minimum 1 hour recommended)

**Problem**: AI insights unavailable
- **Solution**: Add `GEMINI_API_KEY` to `.env` file

## 📈 Roadmap

- [ ] Web-based configuration UI
- [ ] Export reports to PDF
- [ ] Integration with Google Calendar
- [ ] Mobile companion app
- [ ] Team analytics (multi-user)
- [ ] Browser extension
- [ ] Pomodoro timer integration

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

- Streamlit for the amazing dashboard framework
- Plotly for interactive visualizations
- Google Gemini for AI capabilities

## 📞 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: support@example.com

---

**Built with ❤️ for productivity enthusiasts**

*Track smart. Work smarter. Live better.*