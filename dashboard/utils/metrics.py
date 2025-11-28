"""
Metrics Calculation Utilities
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class MetricsCalculator:
    def __init__(self, df_sessions, df_idle=None):
        self.df = df_sessions
        self.df_idle = df_idle
        
    def calculate_all_metrics(self):
        """Calculate comprehensive metrics"""
        return {
            **self.calculate_time_metrics(),
            **self.calculate_focus_metrics(),
            **self.calculate_productivity_metrics(),
            **self.calculate_distribution_metrics(),
        }
    
    def calculate_time_metrics(self):
        """Calculate time-based metrics"""
        df = self.df
        
        # Total time by category
        primary_min = df[df['category'] == 'PRIMARY_WORK']['duration_min'].sum()
        secondary_min = df[df['category'] == 'SECONDARY_WORK']['duration_min'].sum()
        browser_work_min = df[df['category'] == 'BROWSER_WORK']['duration_min'].sum()
        browser_nonwork_min = df[df['category'] == 'BROWSER_NONWORK']['duration_min'].sum()
        idle_min = df[df['category'] == 'IDLE']['duration_min'].sum()
        
        # Add idle periods
        if self.df_idle is not None and not self.df_idle.empty:
            idle_min += self.df_idle['duration_min'].sum()
        
        # Total work time
        work_min = primary_min + secondary_min + browser_work_min
        
        # Total tracked time
        total_min = work_min + browser_nonwork_min + idle_min
        
        return {
            'primary_work_min': round(primary_min),
            'secondary_work_min': round(secondary_min),
            'browser_work_min': round(browser_work_min),
            'browser_nonwork_min': round(browser_nonwork_min),
            'idle_min': round(idle_min),
            'work_min': round(work_min),
            'total_min': round(total_min),
            'primary_work_hours': round(primary_min / 60, 1),
            'work_hours': round(work_min / 60, 1),
            'total_hours': round(total_min / 60, 1),
        }
    
    def calculate_focus_metrics(self):
        """Calculate focus and deep work metrics"""
        df = self.df
        
        # Deep work sessions: PRIMARY_WORK with high focus
        deep_work = df[
            (df['category'] == 'PRIMARY_WORK') &
            (df['is_focus_session'] == 1)
        ]
        
        deep_work_min = deep_work['duration_min'].sum()
        deep_work_count = len(deep_work)
        
        # Average deep work session length
        avg_deep_session = deep_work['duration_min'].mean() if not deep_work.empty else 0
        
        # Longest deep work session today
        today = datetime.now().date()
        today_deep = deep_work[deep_work['date'] == today]
        longest_today = today_deep['duration_min'].max() if not today_deep.empty else 0
        
        # Focus ratio (PRIMARY_WORK with high foreground ratio)
        primary_work = df[df['category'] == 'PRIMARY_WORK']
        if not primary_work.empty:
            focused_work = primary_work[primary_work['foreground_ratio'] >= 0.7]
            focus_ratio = (focused_work['duration_min'].sum() / primary_work['duration_min'].sum()) * 100
        else:
            focus_ratio = 0
        
        return {
            'deep_work_min': round(deep_work_min),
            'deep_work_hours': round(deep_work_min / 60, 1),
            'deep_work_sessions': deep_work_count,
            'avg_deep_session_min': round(avg_deep_session),
            'longest_focus_today_min': round(longest_today),
            'focus_ratio': round(focus_ratio, 1),
        }
    
    def calculate_productivity_metrics(self):
        """Calculate productivity scores"""
        df = self.df
        
        time_metrics = self.calculate_time_metrics()
        total_min = time_metrics['total_min']
        work_min = time_metrics['work_min']
        primary_min = time_metrics['primary_work_min']
        
        if total_min == 0:
            return {
                'productivity_score': 0,
                'efficiency_score': 0,
                'focus_score': 0,
                'time_roi': 0,
            }
        
        # Productivity Score (weighted average of all productivity_score values)
        avg_productivity = df['productivity_score'].mean()
        
        # Efficiency Score (work time / total time)
        efficiency = (work_min / total_min) * 100
        
        # Focus Score (primary work quality)
        if work_min > 0:
            # Weight: primary work contributes most to focus
            focus_score = (
                (primary_min / work_min) * 60 +  # 60% for primary work ratio
                (self.calculate_focus_metrics()['focus_ratio']) * 0.4  # 40% for focus quality
            )
        else:
            focus_score = 0
        
        # Time ROI (value generated per minute)
        # Primary work = 3x value, browser work = 1x, secondary = 0.8x
        value = (
            primary_min * 3.0 +
            time_metrics['browser_work_min'] * 1.0 +
            time_metrics['secondary_work_min'] * 0.8
        )
        time_roi = (value / total_min) * 100 if total_min > 0 else 0
        
        return {
            'productivity_score': round(avg_productivity, 1),
            'efficiency_score': round(efficiency, 1),
            'focus_score': round(focus_score, 1),
            'time_roi': round(time_roi, 1),
        }
    
    def calculate_distribution_metrics(self):
        """Calculate distribution metrics"""
        df = self.df
        
        # Session statistics
        total_sessions = len(df)
        avg_session_min = df['duration_min'].mean() if total_sessions > 0 else 0
        median_session_min = df['duration_min'].median() if total_sessions > 0 else 0
        
        # Fragmentation (sessions per hour)
        time_metrics = self.calculate_time_metrics()
        total_hours = time_metrics['total_hours']
        fragmentation = total_sessions / max(total_hours, 1)
        
        # Context switches (category changes)
        context_switches = (df['category'] != df['category'].shift()).sum() - 1
        context_switches = max(0, context_switches)
        
        return {
            'total_sessions': total_sessions,
            'avg_session_min': round(avg_session_min, 1),
            'median_session_min': round(median_session_min, 1),
            'fragmentation': round(fragmentation, 1),
            'context_switches': context_switches,
        }
    
    def get_daily_breakdown(self):
        """Get daily breakdown of activities"""
        daily = self.df.groupby('date').agg({
            'duration_min': 'sum',
            'id': 'count'
        }).rename(columns={'id': 'sessions'})
        
        # Add category breakdown
        category_daily = self.df.groupby(['date', 'category'])['duration_min'].sum().unstack(fill_value=0)
        
        result = pd.concat([daily, category_daily], axis=1)
        result = result.sort_index(ascending=False)
        
        return result
    
    def get_hourly_breakdown(self):
        """Get hourly activity pattern"""
        hourly = self.df.groupby('hour').agg({
            'duration_min': 'sum',
            'id': 'count',
            'productivity_score': 'mean'
        }).rename(columns={'id': 'sessions'})
        
        return hourly
    
    def get_app_breakdown(self):
        """Get breakdown by application"""
        app_stats = self.df.groupby('display_name').agg({
            'duration_min': 'sum',
            'id': 'count',
            'foreground_ratio': 'mean',
            'productivity_score': 'mean',
            'is_focus_session': 'sum'
        }).rename(columns={'id': 'sessions', 'is_focus_session': 'focus_sessions'})
        
        app_stats = app_stats.sort_values('duration_min', ascending=False)
        
        return app_stats
    
    def get_streaks(self):
        """Calculate productivity streaks"""
        df = self.df.copy()
        df = df.sort_values('start_dt')
        
        # Daily work time
        daily_work = df[df['category'].isin(['PRIMARY_WORK', 'SECONDARY_WORK', 'BROWSER_WORK'])]
        daily_work = daily_work.groupby('date')['duration_min'].sum()
        
        # Find streak (days with 60+ min of work)
        threshold = 60
        work_days = daily_work >= threshold
        
        # Current streak
        current_streak = 0
        today = datetime.now().date()
        
        for i in range(len(work_days)):
            check_date = today - timedelta(days=i)
            if check_date in work_days.index and work_days[check_date]:
                current_streak += 1
            else:
                break
        
        # Longest streak
        longest_streak = 0
        current_count = 0
        
        for value in work_days:
            if value:
                current_count += 1
                longest_streak = max(longest_streak, current_count)
            else:
                current_count = 0
        
        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak,
        }