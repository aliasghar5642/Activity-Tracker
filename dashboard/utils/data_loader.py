"""
Data Loading and Preparation Utilities
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DataLoader:
    def __init__(self, db_path):
        self.db_path = db_path
        
    def get_connection(self):
        """Get database connection with timeout"""
        return sqlite3.connect(self.db_path, timeout=30)
    
    def load_sessions(self, days=30):
        """Load sessions from database"""
        try:
            query = """
                SELECT 
                    id,
                    start_time,
                    end_time,
                    process_name,
                    process_display_name,
                    window_title,
                    category,
                    subcategory,
                    duration_seconds,
                    foreground_seconds,
                    keystroke_count,
                    mouse_click_count,
                    is_focus_session,
                    productivity_score
                FROM sessions
                WHERE start_time >= datetime('now', ?)
                ORDER BY start_time DESC
            """
            
            conn = self.get_connection()
            df = pd.read_sql_query(query, conn, params=(f'-{days} days',))
            conn.close()
            
            if df.empty:
                return None
                
            # Data preprocessing
            df['start_dt'] = pd.to_datetime(df['start_time'])
            df['end_dt'] = pd.to_datetime(df['end_time'])
            
            # Handle open sessions
            open_sessions = df['end_dt'].isna()
            if open_sessions.any():
                df.loc[open_sessions, 'end_dt'] = datetime.now()
                
            df['duration_min'] = df['duration_seconds'] / 60.0
            df['foreground_min'] = df['foreground_seconds'] / 60.0
            df['foreground_ratio'] = df['foreground_seconds'] / df['duration_seconds'].replace(0, 1)
            
            df['date'] = df['start_dt'].dt.date
            df['hour'] = df['start_dt'].dt.hour
            df['day_of_week'] = df['start_dt'].dt.day_name()
            df['week'] = df['start_dt'].dt.isocalendar().week
            
            # Display name fallback
            df['display_name'] = df['process_display_name'].fillna(df['process_name'])
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
            return None
    
    def load_idle_periods(self, days=30):
        """Load idle periods"""
        try:
            query = """
                SELECT 
                    start_time,
                    end_time,
                    duration_seconds,
                    reason
                FROM idle_periods
                WHERE start_time >= datetime('now', ?)
                ORDER BY start_time DESC
            """
            
            conn = self.get_connection()
            df = pd.read_sql_query(query, conn, params=(f'-{days} days',))
            conn.close()
            
            if df.empty:
                return None
                
            df['start_dt'] = pd.to_datetime(df['start_time'])
            df['end_dt'] = pd.to_datetime(df['end_time'])
            df['duration_min'] = df['duration_seconds'] / 60.0
            df['date'] = df['start_dt'].dt.date
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to load idle periods: {e}")
            return None
    
    def load_system_events(self, days=30):
        """Load system events"""
        try:
            query = """
                SELECT 
                    event_type,
                    timestamp,
                    details
                FROM system_events
                WHERE timestamp >= datetime('now', ?)
                ORDER BY timestamp DESC
            """
            
            conn = self.get_connection()
            df = pd.read_sql_query(query, conn, params=(f'-{days} days',))
            conn.close()
            
            if df.empty:
                return None
                
            df['timestamp_dt'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp_dt'].dt.date
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to load system events: {e}")
            return None
    
    def get_database_stats(self):
        """Get database statistics"""
        try:
            conn = self.get_connection()
            c = conn.cursor()
            
            stats = {}
            
            # Total sessions
            c.execute("SELECT COUNT(*) FROM sessions")
            stats['total_sessions'] = c.fetchone()[0]
            
            # Date range
            c.execute("SELECT MIN(start_time), MAX(start_time) FROM sessions")
            result = c.fetchone()
            if result[0]:
                stats['first_session'] = result[0]
                stats['last_session'] = result[1]
            
            # Total time tracked
            c.execute("SELECT SUM(duration_seconds) FROM sessions")
            total_seconds = c.fetchone()[0] or 0
            stats['total_hours_tracked'] = total_seconds / 3600.0
            
            # Focus sessions
            c.execute("SELECT COUNT(*) FROM sessions WHERE is_focus_session = 1")
            stats['focus_sessions'] = c.fetchone()[0]
            
            # Idle periods
            c.execute("SELECT COUNT(*), SUM(duration_seconds) FROM idle_periods")
            result = c.fetchone()
            stats['idle_periods'] = result[0] or 0
            stats['total_idle_hours'] = (result[1] or 0) / 3600.0
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}