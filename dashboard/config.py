"""
Dashboard Configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Database
DB_PATH = os.getenv("DB_PATH", str(Path.home() / "ActivityTracker" / "data" / "activity.db"))

# Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Dashboard Settings
PAGE_TITLE = "Activity Tracker Pro"
PAGE_ICON = "📊"
LAYOUT = "wide"

# Data Settings
DEFAULT_DATE_RANGE = 7  # days
MAX_TIMELINE_SESSIONS = 50

# Productivity Thresholds
FOCUS_SESSION_MIN_DURATION = 600  # 10 minutes
FOCUS_SESSION_MIN_FOREGROUND = 0.8  # 80%

EXCELLENT_SCORE = 85
GOOD_SCORE = 70
MEDIUM_SCORE = 50

# Colors
COLOR_PRIMARY_WORK = "#10B981"  # Green
COLOR_SECONDARY_WORK = "#3B82F6"  # Blue
COLOR_BROWSER_WORK = "#8B5CF6"  # Purple
COLOR_BROWSER_NONWORK = "#F59E0B"  # Orange
COLOR_IDLE = "#EF4444"  # Red

CATEGORY_COLORS = {
    "PRIMARY_WORK": COLOR_PRIMARY_WORK,
    "SECONDARY_WORK": COLOR_SECONDARY_WORK,
    "BROWSER_WORK": COLOR_BROWSER_WORK,
    "BROWSER_NONWORK": COLOR_BROWSER_NONWORK,
    "IDLE": COLOR_IDLE,
}

# Chart Settings
CHART_HEIGHT = 400
TIMELINE_HEIGHT = 600