"""
Activity Tracker Pro - Production Watcher
Intelligent categorization with Primary/Secondary/Idle detection
"""

import os
import sys
import time
import threading
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
import ctypes

try:
    import winsound
    import keyboard
    import psutil
    import pygetwindow as gw
    import pystray
    from pystray import MenuItem as item
    from PIL import Image, ImageDraw
    WINDOWS_FEATURES = True
except ImportError:
    WINDOWS_FEATURES = False
    print("Warning: Windows-specific features unavailable (running in Docker?)")

import config

# Logging setup
logging.basicConfig(
    filename=config.LOG_DIR / "watcher.log",
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8"
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger().addHandler(console)


class ActivityWatcher:
    def __init__(self):
        self.db_path = config.DB_PATH
        self.monitoring = True
        self.is_idle = False
        self.is_paused = False
        
        self.idle_start = None
        self.current_session = None
        
        self.buffer = []
        self.last_flush = time.time()
        self.last_activity = time.time()
        
        self.icon = None
        
        self.init_db()
        self.setup_hotkeys()
        self.log_system_event("SYSTEM_STARTUP")
        
        logging.info("=" * 60)
        logging.info("Activity Watcher STARTED")
        logging.info(f"Database: {self.db_path}")
        logging.info(f"Flush Interval: {config.FLUSH_INTERVAL}s")
        logging.info("=" * 60)

    def init_db(self):
        """Initialize SQLite database with optimized schema"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Sessions table - the heart of tracking
        c.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                process_name TEXT NOT NULL,
                process_display_name TEXT,
                window_title TEXT,
                category TEXT NOT NULL,
                subcategory TEXT,
                duration_seconds REAL NOT NULL,
                foreground_seconds REAL NOT NULL,
                keystroke_count INTEGER DEFAULT 0,
                mouse_click_count INTEGER DEFAULT 0,
                is_focus_session BOOLEAN DEFAULT 0,
                productivity_score REAL DEFAULT 0
            )
        """)
        
        # Idle periods
        c.execute("""
            CREATE TABLE IF NOT EXISTS idle_periods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_seconds REAL,
                reason TEXT
            )
        """)
        
        # System events
        c.execute("""
            CREATE TABLE IF NOT EXISTS system_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                details TEXT
            )
        """)
        
        # Create indexes for performance
        c.execute("CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions(start_time)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_sessions_category ON sessions(category)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_idle_start ON idle_periods(start_time)")
        
        conn.commit()
        conn.close()
        logging.info("Database initialized successfully")

    def setup_hotkeys(self):
        """Setup keyboard shortcuts"""
        if not WINDOWS_FEATURES:
            logging.warning("Hotkeys unavailable - Windows features not loaded")
            return
            
        try:
            keyboard.add_hotkey(config.HOTKEY_IDLE_START, self.start_idle_mode)
            keyboard.add_hotkey(config.HOTKEY_IDLE_END, self.end_idle_mode)
            keyboard.add_hotkey(config.HOTKEY_TOGGLE_MONITORING, self.toggle_monitoring)
            logging.info("Hotkeys registered successfully")
        except Exception as e:
            logging.error(f"Failed to register hotkeys: {e}")

    def beep(self, freq=1000, dur=200):
        """Audio feedback"""
        if WINDOWS_FEATURES:
            try:
                winsound.Beep(freq, dur)
            except:
                pass

    def start_idle_mode(self):
        """Manual idle mode activation"""
        if not self.is_idle:
            self.flush_buffer(force=True)
            self.is_idle = True
            self.idle_start = datetime.now()
            self.beep(800, 300)
            self.update_icon()
            self.log_system_event("IDLE_MODE_MANUAL_START")
            logging.info("🔴 IDLE MODE: Manual activation")

    def end_idle_mode(self):
        """End idle mode"""
        if self.is_idle:
            duration = (datetime.now() - self.idle_start).total_seconds()
            self.log_idle_period(
                self.idle_start,
                datetime.now(),
                duration,
                "manual"
            )
            self.is_idle = False
            self.idle_start = None
            self.last_activity = time.time()
            self.beep(1500, 200)
            self.update_icon()
            self.log_system_event("IDLE_MODE_MANUAL_END")
            logging.info(f"🟢 ACTIVE MODE: Resumed (idle duration: {duration:.0f}s)")

    def toggle_monitoring(self):
        """Pause/Resume monitoring"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.flush_buffer(force=True)
            self.log_system_event("MONITORING_PAUSED")
            logging.info("⏸️  MONITORING PAUSED")
        else:
            self.last_activity = time.time()
            self.log_system_event("MONITORING_RESUMED")
            logging.info("▶️  MONITORING RESUMED")
        self.beep(1200, 150)
        self.update_icon()

    def log_system_event(self, event_type, details=None):
        """Log system events"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(
                "INSERT INTO system_events (event_type, timestamp, details) VALUES (?, ?, ?)",
                (event_type, datetime.now().isoformat(), details)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Failed to log system event: {e}")

    def log_idle_period(self, start, end, duration, reason):
        """Log idle period to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(
                """INSERT INTO idle_periods 
                   (start_time, end_time, duration_seconds, reason) 
                   VALUES (?, ?, ?, ?)""",
                (start.isoformat(), end.isoformat(), duration, reason)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Failed to log idle period: {e}")

    def get_foreground_app(self):
        """
        Get currently active window and process using reliable PID lookup via Windows API.
        This fixes the flawed string matching logic.
        """
        if not WINDOWS_FEATURES:
            return None, None, None
            
        try:
            win = gw.getActiveWindow()
            if not win or not win.title.strip():
                return None, None, None
                
            title = win.title.strip()
            
            # 1. Get the Window Handle (hWnd) from pygetwindow object
            # We access the internal handle attribute
            hWnd = win._hWnd
            
            # 2. Use ctypes to call GetWindowThreadProcessId (Windows API)
            user32 = ctypes.windll.user32
            pid = ctypes.c_ulong()
            # Get the PID of the process that owns the window handle
            user32.GetWindowThreadProcessId(hWnd, ctypes.pointer(pid))
            proc_id = pid.value
            
            # 3. Use psutil to get the process name from the reliable PID
            if proc_id != 0:
                try:
                    proc = psutil.Process(proc_id)
                    proc_name = proc.name()
                    
                    # Return the reliably found process name
                    return proc_name, proc_name.lower(), title
                except psutil.NoSuchProcess:
                    # Process might have closed between getting PID and looking up
                    logging.debug(f"Process with PID {proc_id} not found.")
                    
            return "Unknown.exe", "unknown.exe", title # Fallback if PID lookup fails
            
        except Exception as e:
            # Catch errors related to pygetwindow or ctypes failure
            logging.debug(f"Failed to get foreground app (PID lookup failed): {e}")
            return None, None, None

    def categorize_activity(self, process_name, process_lower, window_title):
        """
        Intelligent categorization system:
        - PRIMARY_WORK: Main coding/development tools
        - SECONDARY_WORK: Communication, music, support tools
        - BROWSER_WORK: Browsers on work-related sites
        - BROWSER_NONWORK: Browsers on entertainment sites
        - IDLE: Everything else
        """
        if not process_name:
            return "IDLE", None, 0
            
        # Check primary work apps (VSCode, Cursor, etc.)
        if process_lower in config.PRIMARY_WORK_APPS:
            display_name = config.PRIMARY_WORK_APPS[process_lower]
            return "PRIMARY_WORK", display_name, 100
            
        # Check secondary work apps (Telegram, Spotify)
        if process_lower in config.SECONDARY_WORK_APPS:
            display_name = config.SECONDARY_WORK_APPS[process_lower]
            return "SECONDARY_WORK", display_name, 60
            
        # Browser intelligence
        if process_lower in config.BROWSER_APPS:
            display_name = config.BROWSER_APPS[process_lower]
            title_lower = window_title.lower()
            
            # Check for work domains
            for domain in config.WORK_DOMAINS:
                if domain in title_lower:
                    return "BROWSER_WORK", f"{display_name} (Work)", 80
                    
            # Check for non-work domains
            for domain in config.NON_WORK_DOMAINS:
                if domain in title_lower:
                    return "BROWSER_NONWORK", f"{display_name} (Leisure)", 20
                    
            # Default to work for unknown browser activity
            return "BROWSER_WORK", display_name, 70
            
        # Everything else is idle
        return "IDLE", process_name, 0

    def flush_buffer(self, force=False):
        """Flush activity buffer to database, ignoring samples with no detectable process name for categorization."""
        if not self.buffer or self.is_idle or self.is_paused:
            self.buffer.clear()
            return
            
        if not force and time.time() - self.last_flush < config.FLUSH_INTERVAL:
            return
            
        # Analyze buffer
        total_samples = len(self.buffer)
        activity_counts = {}
        total_fg = 0
        
        # --- FIX: Filter out samples with no process name for categorization ---
        valid_samples = []
        for sample in self.buffer:
            (_, proc, _, _, _, _, _) = sample
            if proc:
                valid_samples.append(sample)
                total_fg += 1
            else:
                # Still increment total_fg only for samples with a detected process
                pass 
        
        if not valid_samples:
            logging.warning("Skipping session flush: Buffer contained only samples with no detectable process name.")
            self.buffer.clear()
            self.last_flush = time.time()
            return
        
        # Build activity counts ONLY from valid samples
        for _, proc, proc_lower, title, cat, subcat, score in valid_samples:
            key = (proc, cat, subcat)
            if key not in activity_counts:
                activity_counts[key] = {'count': 0, 'title': title, 'score': score}
            activity_counts[key]['count'] += 1
        # --- END FIX ---
        
        # Find dominant activity (We now know winner_proc is NOT None)
        dominant = max(activity_counts.items(), key=lambda x: x[1]['count'])
        (winner_proc, winner_cat, winner_subcat), data = dominant
        
        winner_title = data['title']
        winner_score = data['score']
        
        # Calculate metrics
        duration = config.FLUSH_INTERVAL
        # foreground_ratio is calculated based on ALL samples (total_samples), correctly penalizing the session
        foreground_ratio = total_fg / max(total_samples, 1)
        foreground_seconds = foreground_ratio * duration
        
        # Determine if this is a focus session
        is_focus = (
            winner_cat == "PRIMARY_WORK" and
            duration >= 600 and  # At least 10 minutes
            foreground_ratio >= 0.8  # 80% active
        )
        
        # Calculate productivity score
        productivity = winner_score * foreground_ratio
        
        # Save to database
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            start_time = (datetime.now() - timedelta(seconds=duration)).isoformat()
            
            c.execute("""
                INSERT INTO sessions 
                (start_time, end_time, process_name, process_display_name, 
                 window_title, category, subcategory, duration_seconds, 
                 foreground_seconds, is_focus_session, productivity_score)
                VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                start_time,
                winner_proc,
                winner_subcat or winner_proc,
                winner_title,
                winner_cat,
                winner_subcat,
                duration,
                foreground_seconds,
                1 if is_focus else 0,
                productivity
            ))
            
            conn.commit()
            conn.close()
            
            emoji = "🎯" if is_focus else "💻" if winner_cat.startswith("PRIMARY") else "📱" if winner_cat.startswith("SECONDARY") else "🌐"
            logging.info(
                f"{emoji} Session: {winner_subcat or winner_proc} | "
                f"{duration}s | FG: {foreground_seconds:.1f}s | "
                f"Score: {productivity:.0f}"
            )
            
        except Exception as e:
            logging.error(f"Failed to save session: {e}")
            
        self.buffer.clear()
        self.last_flush = time.time()

    def check_auto_idle(self):
        """Check for automatic idle (no activity)"""
        if self.is_idle or self.is_paused:
            return
            
        idle_duration = time.time() - self.last_activity
        
        if idle_duration > config.IDLE_THRESHOLD:
            self.flush_buffer(force=True)
            self.is_idle = True
            self.idle_start = datetime.now() - timedelta(seconds=idle_duration)
            self.log_idle_period(
                self.idle_start,
                datetime.now(),
                idle_duration,
                "auto"
            )
            logging.info(f"🔴 AUTO-IDLE: No activity for {idle_duration:.0f}s")
            self.update_icon()

    def monitor_loop(self):
        """Main monitoring loop"""
        logging.info("Monitor loop started")
        
        while self.monitoring:
            try:
                # Check for auto-idle
                self.check_auto_idle()
                
                # Skip if idle or paused
                if self.is_idle or self.is_paused:
                    time.sleep(5)
                    continue
                    
                # Get current activity
                proc_name, proc_lower, window_title = self.get_foreground_app()
                
                if proc_name:
                    self.last_activity = time.time()
                    
                # Categorize
                category, subcategory, score = self.categorize_activity(
                    proc_name, proc_lower, window_title
                )
                
                # Add to buffer
                self.buffer.append((
                    time.time(),
                    proc_name,
                    proc_lower,
                    window_title,
                    category,
                    subcategory,
                    score
                ))
                
                # Flush if needed
                if time.time() - self.last_flush >= config.FLUSH_INTERVAL:
                    self.flush_buffer()
                    
                time.sleep(config.SAMPLE_INTERVAL)
                
            except Exception as e:
                logging.error(f"Monitor loop error: {e}")
                time.sleep(5)

    def create_icon(self, color):
        """Create system tray icon"""
        img = Image.new("RGB", (64, 64), color)
        d = ImageDraw.Draw(img)
        d.rectangle((12, 12, 52, 52), outline="white", width=4)
        return img

    def update_icon(self):
        """Update system tray icon"""
        if not self.icon or not WINDOWS_FEATURES:
            return
            
        if self.is_paused:
            color = config.ICON_COLOR_PAUSED
            title = "Tracker: Paused"
        elif self.is_idle:
            color = config.ICON_COLOR_IDLE
            title = "Tracker: Idle"
        else:
            color = config.ICON_COLOR_ACTIVE
            title = "Tracker: Active"
            
        self.icon.icon = self.create_icon(color)
        self.icon.title = title

    def quit_app(self, icon=None, item=None):
        """Clean shutdown"""
        logging.info("Shutdown initiated")
        self.monitoring = False
        
        if self.buffer:
            self.flush_buffer(force=True)
            
        if self.is_idle and self.idle_start:
            duration = (datetime.now() - self.idle_start).total_seconds()
            self.log_idle_period(
                self.idle_start,
                datetime.now(),
                duration,
                "shutdown"
            )
            
        self.log_system_event("SYSTEM_SHUTDOWN")
        
        if self.icon:
            self.icon.stop()
            
        logging.info("Shutdown complete")
        os._exit(0)

    def run(self):
        """Start the watcher"""
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        monitor_thread.start()
        
        if WINDOWS_FEATURES:
            # Create system tray icon
            menu = (
                item("Idle Mode On", self.start_idle_mode),
                item("Idle Mode Off", self.end_idle_mode),
                item("Pause/Resume", self.toggle_monitoring),
                item("Exit", self.quit_app)
            )
            
            self.icon = pystray.Icon(
                "ActivityTracker",
                self.create_icon(config.ICON_COLOR_ACTIVE),
                "Activity Tracker Pro",
                menu
            )
            
            self.update_icon()
            self.icon.run()
        else:
            # Console mode (Docker)
            logging.info("Running in console mode (Docker)")
            try:
                while self.monitoring:
                    time.sleep(10)
            except KeyboardInterrupt:
                self.quit_app()


if __name__ == "__main__":
    # Windows startup registration
    if WINDOWS_FEATURES and sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            if getattr(sys, 'frozen', False):
                path = f'"{sys.executable}"'
            else:
                path = f'"{sys.executable}" "{os.path.abspath(__file__)}"'
                
            winreg.SetValueEx(key, "ActivityTrackerPro", 0, winreg.REG_SZ, path)
            winreg.CloseKey(key)
            logging.info("Startup registration successful")
        except Exception as e:
            logging.warning(f"Startup registration failed: {e}")
    
    # Run watcher
    watcher = ActivityWatcher()
    watcher.run()