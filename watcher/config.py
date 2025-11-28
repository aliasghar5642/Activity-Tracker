"""
Configuration for Activity Watcher
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import ctypes 
import sqlite3

load_dotenv()

# Paths
BASE_DIR = Path(os.getenv("WATCHER_BASE_DIR", Path.home() / "ActivityTracker"))
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "activity.db"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Monitoring Settings
SAMPLE_INTERVAL = 1  # seconds
FLUSH_INTERVAL = 60  # seconds - create session every 60s
IDLE_THRESHOLD = 300  # seconds - auto-idle after 5min of no input

# Application Categorization
PRIMARY_WORK_APPS = {
    "code.exe": "VSCode",
    "cursor.exe": "Cursor", 
    "chrome.exe": "Chrome",
}

SECONDARY_WORK_APPS = {
    "telegram.exe": "Telegram",
    "spotify.exe": "Spotify",
}

BROWSER_APPS = {
    "firefox.exe": "Firefox",
    "msedge.exe": "Edge",
    "brave.exe": "Brave",
}

# Browser Domain Categorization
WORK_DOMAINS = [
    "github.com",
    "stackoverflow.com",
    "dev.to",
    "medium.com",
    "docs.python.org",
    "developer.mozilla.org",
    "aws.amazon.com",
    "cloud.google.com",
    "vercel.com",
    "netlify.com",
    "railway.app",
    "render.com",
    "localhost",
    "127.0.0.1",
]

NON_WORK_DOMAINS = [
    "youtube.com",
    "netflix.com",
    "reddit.com",
    "twitter.com",
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "twitch.tv",
]

# Hotkeys
HOTKEY_IDLE_START = "ctrl+alt+shift+i"
HOTKEY_IDLE_END = "ctrl+alt+shift+o"
HOTKEY_TOGGLE_MONITORING = "ctrl+alt+shift+p"

# UI Settings
ICON_COLOR_ACTIVE = "#10B981"  # Green
ICON_COLOR_IDLE = "#EF4444"    # Red
ICON_COLOR_PAUSED = "#6B7280"  # Gray