"""
Activity Tracker Pro - Production Dashboard
Modern, responsive, and feature-rich analytics interface
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import logging

import config
from utils.data_loader import DataLoader
from utils.metrics import MetricsCalculator
from utils.visualizations import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout=config.LAYOUT,
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Main styling */
    .main-header {
        font-size: 3.5rem;
        font-weight: 900;
        background: linear-gradient(120deg, #4F46E5 0%, #7C3AED 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    
    .subtitle {
        font-size: 1.1rem;
        color: #6B7280;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: white;
        margin-bottom: 1rem;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
    
    /* Score badges */
    .score-excellent {
        color: #10B981;
        font-weight: 800;
        font-size: 2rem;
    }
    
    .score-good {
        color: #3B82F6;
        font-weight: 800;
        font-size: 2rem;
    }
    
    .score-medium {
        color: #F59E0B;
        font-weight: 800;
        font-size: 2rem;
    }
    
    .score-poor {
        color: #EF4444;
        font-weight: 800;
        font-size: 2rem;
    }
    
    /* Info boxes */
    .info-box {
        background: #F9FAFB;
        border-left: 4px solid #4F46E5;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* Stats grid */
    .stat-item {
        text-align: center;
        padding: 1rem;
        background: white;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #4F46E5 0%, #7C3AED 100%);
        color: white;
    }
    
    section[data-testid="stSidebar"] .stMarkdown {
        color: white;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Chart containers */
    .chart-container {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


class ActivityTrackerDashboard:
    def __init__(self):
        self.db_path = config.DB_PATH
        
        # Check database
        if not os.path.exists(self.db_path):
            st.error("❌ Database not found!")
            st.info(f"Expected location: `{self.db_path}`\n\nPlease run the **Activity Watcher** first.")
            st.stop()
        
        # Initialize
        self.loader = DataLoader(self.db_path)
        self.setup_gemini()
        
        # Session state
        if 'date_range' not in st.session_state:
            st.session_state.date_range = config.DEFAULT_DATE_RANGE
            
    def setup_gemini(self):
        """Setup Gemini AI"""
        try:
            if config.GEMINI_API_KEY:
                import google.generativeai as genai
                genai.configure(api_key=config.GEMINI_API_KEY)
                self.model = genai.GenerativeModel("gemini-2.5-flash")
                self.gemini_ready = True
            else:
                self.gemini_ready = False
        except Exception as e:
            logger.warning(f"Gemini AI not available: {e}")
            self.gemini_ready = False
    
    def load_data(self, days):
        """Load and prepare all data"""
        with st.spinner("Loading your activity data..."):
            df_sessions = self.loader.load_sessions(days)
            df_idle = self.loader.load_idle_periods(days)
            
            if df_sessions is None or df_sessions.empty:
                return None, None, None
            
            metrics_calc = MetricsCalculator(df_sessions, df_idle)
            metrics = metrics_calc.calculate_all_metrics()
            
            return df_sessions, df_idle, metrics_calc, metrics
    
    def render_header(self):
        """Render dashboard header"""
        st.markdown("<h1 class='main-header'>Activity Tracker Pro</h1>", unsafe_allow_html=True)
        st.markdown(
            "<p class='subtitle'>🚀 Production-grade tracking • 🧠 Smart categorization • 📊 Deep insights</p>",
            unsafe_allow_html=True
        )
    
    def render_sidebar(self):
        """Render sidebar controls"""
        with st.sidebar:
            st.markdown("## ⚙️ Controls")
            
            # Date range selector
            date_range = st.selectbox(
                "Time Period",
                options=[1, 3, 7, 14, 30, 60, 90],
                index=2,
                format_func=lambda x: f"Last {x} day{'s' if x > 1 else ''}"
            )
            
            st.session_state.date_range = date_range
            
            # Refresh button
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.rerun()
            
            st.markdown("---")
            
            # Database stats
            st.markdown("### 📊 Database Info")
            stats = self.loader.get_database_stats()
            
            if stats:
                st.metric("Total Sessions", f"{stats.get('total_sessions', 0):,}")
                st.metric("Hours Tracked", f"{stats.get('total_hours_tracked', 0):.1f}")
                st.metric("Focus Sessions", stats.get('focus_sessions', 0))
                
                if 'first_session' in stats:
                    st.caption(f"Tracking since: {stats['first_session'][:10]}")
            
            st.markdown("---")
            
            # Hotkeys reference
            st.markdown("### ⌨️ Keyboard Shortcuts")
            st.code("Ctrl+Alt+Shift+I → Start Idle")
            st.code("Ctrl+Alt+Shift+O → End Idle")
            st.code("Ctrl+Alt+Shift+P → Pause/Resume")
            
            st.markdown("---")
            
            # AI Status
            st.markdown("### 🤖 AI Assistant")
            if self.gemini_ready:
                st.success("✅ Ready")
            else:
                st.warning("⚠️ Not Configured")
                st.caption("Add `GEMINI_API_KEY` to enable AI insights")
            
            st.markdown("---")
            st.caption(f"DB: `{os.path.basename(self.db_path)}`")
            st.caption(f"Version: 2.0.0 Production")
    
    def render_key_metrics(self, metrics):
        """Render key metrics cards"""
        st.markdown("### 📈 Key Performance Indicators")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "💼 Total Active Time",
                f"{metrics['total_hours']:.1f}h",
                delta=f"{metrics['total_min']} min"
            )
        
        with col2:
            st.metric(
                "🎯 Primary Work",
                f"{metrics['primary_work_hours']:.1f}h",
                delta=f"{(metrics['primary_work_min']/max(metrics['work_min'],1)*100):.0f}% of work"
            )
        
        with col3:
            st.metric(
                "🔥 Deep Work Sessions",
                metrics['deep_work_sessions'],
                delta=f"{metrics['deep_work_hours']:.1f}h total"
            )
        
        with col4:
            st.metric(
                "☕ Break Time",
                f"{metrics['idle_min']} min",
                delta=f"{(metrics['idle_min']/max(metrics['total_min'],1)*100):.0f}% of total"
            )
    
    def render_productivity_scores(self, metrics):
        """Render productivity scores"""
        st.markdown("### 🎯 Productivity Scores")
        
        col1, col2, col3, col4 = st.columns(4)
        
        scores = [
            ("Focus Score", metrics['focus_score']),
            ("Efficiency", metrics['efficiency_score']),
            ("Time ROI", metrics['time_roi']),
            ("Productivity", metrics['productivity_score'])
        ]
        
        for col, (label, score) in zip([col1, col2, col3, col4], scores):
            with col:
                if score >= config.EXCELLENT_SCORE:
                    css_class = "score-excellent"
                    emoji = "🌟"
                elif score >= config.GOOD_SCORE:
                    css_class = "score-good"
                    emoji = "✅"
                elif score >= config.MEDIUM_SCORE:
                    css_class = "score-medium"
                    emoji = "⚠️"
                else:
                    css_class = "score-poor"
                    emoji = "❌"
                
                st.markdown(f"<div class='{css_class}'>{emoji} {score:.0f}/100</div>", unsafe_allow_html=True)
                st.caption(label)
    
    def render_session_stats(self, metrics):
        """Render session statistics"""
        st.markdown("### 📊 Session Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Sessions", metrics['total_sessions'])
        
        with col2:
            st.metric("Avg Session", f"{metrics['avg_session_min']:.1f} min")
        
        with col3:
            st.metric("Context Switches", metrics['context_switches'])
        
        with col4:
            st.metric("Fragmentation", f"{metrics['fragmentation']:.1f}/hr")
    
    def render_charts(self, df, metrics_calc, metrics):
        """Render all charts"""
        st.markdown("---")
        st.markdown("## 📊 Visual Analytics")
        
        # Row 1: Pie + Daily Trend
        col1, col2 = st.columns(2)
        
        with col1:
            fig = create_time_allocation_pie(metrics)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = create_daily_trend(df, metrics_calc)
            st.plotly_chart(fig, use_container_width=True)
        
        # Row 2: Heatmap + Focus Sessions
        col1, col2 = st.columns(2)
        
        with col1:
            fig = create_hourly_heatmap(df)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = create_focus_sessions_chart(df)
            if fig.data:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No focus sessions recorded yet. Keep working in VSCode/Cursor for 10+ minutes!")
        
        # Row 3: App Breakdown + Weekly Comparison
        col1, col2 = st.columns(2)
        
        app_stats = metrics_calc.get_app_breakdown()
        
        with col1:
            fig = create_app_breakdown_chart(app_stats, top_n=10)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = create_weekly_comparison(df)
            if fig.data:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough weekly data yet")
        
        # Full width: Timeline
        st.markdown("### 🕐 Session Timeline")
        fig = create_timeline_view(df, max_sessions=config.MAX_TIMELINE_SESSIONS)
        if fig.data:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sessions to display in timeline")
    
    def render_detailed_breakdown(self, metrics_calc):
        """Render detailed data tables"""
        st.markdown("---")
        st.markdown("## 📋 Detailed Breakdown")
        
        tab1, tab2, tab3 = st.tabs(["📅 Daily", "🕐 Hourly", "💻 Applications"])
        
        with tab1:
            daily = metrics_calc.get_daily_breakdown()
            if not daily.empty:
                st.dataframe(
                    daily.style.format("{:.1f}", subset=['duration_min']),
                    use_container_width=True
                )
            else:
                st.info("No daily data available")
        
        with tab2:
            hourly = metrics_calc.get_hourly_breakdown()
            if not hourly.empty:
                st.dataframe(
                    hourly.style.format({
                        'duration_min': '{:.1f}',
                        'productivity_score': '{:.1f}'
                    }),
                    use_container_width=True
                )
            else:
                st.info("No hourly data available")
        
        with tab3:
            app_stats = metrics_calc.get_app_breakdown()
            if not app_stats.empty:
                st.dataframe(
                    app_stats.style.format({
                        'duration_min': '{:.1f}',
                        'foreground_ratio': '{:.2f}',
                        'productivity_score': '{:.1f}'
                    }),
                    use_container_width=True
                )
            else:
                st.info("No application data available")
    
    def render_ai_insights(self, metrics, metrics_calc):
        """Render AI-powered insights"""
        st.markdown("---")
        st.markdown("## 🤖 AI-Powered Insights")
        
        if not self.gemini_ready:
            st.warning("⚠️ AI insights unavailable. Add `GEMINI_API_KEY` to your environment.")
            return
        
        if st.button("🧠 Generate AI Analysis", type="primary", use_container_width=False):
            with st.spinner("🔮 Analyzing your productivity patterns..."):
                report = self.generate_ai_report(metrics, metrics_calc)
                
                if report:
                    st.success("✅ Analysis Complete")
                    st.markdown("### 📝 Executive Summary")
                    st.markdown(report)
    
    def generate_ai_report(self, metrics, metrics_calc):
        """Generate AI report using Gemini"""
        try:
            streaks = metrics_calc.get_streaks()
            
            prompt = f"""
You are an elite productivity coach analyzing real tracked data from a knowledge worker. Provide a professional, actionable analysis.

**TRACKED METRICS:**
• Total Active Time: {metrics['total_hours']:.1f} hours ({metrics['total_min']} minutes)
• Primary Work (VSCode, Cursor): {metrics['primary_work_hours']:.1f}h ({(metrics['primary_work_min']/max(metrics['work_min'],1)*100):.0f}% of work)
• Secondary Work (Telegram, Spotify): {metrics['secondary_work_min']} minutes
• Browser Work: {metrics['browser_work_min']} minutes
• Browser Leisure: {metrics['browser_nonwork_min']} minutes
• Idle/Break Time: {metrics['idle_min']} minutes

**DEEP WORK:**
• Deep Focus Sessions: {metrics['deep_work_sessions']} sessions
• Total Deep Work: {metrics['deep_work_hours']:.1f} hours
• Average Deep Session: {metrics['avg_deep_session_min']:.0f} minutes
• Longest Focus Today: {metrics['longest_focus_today_min']:.0f} minutes

**PRODUCTIVITY SCORES:**
• Focus Score: {metrics['focus_score']:.0f}/100
• Efficiency: {metrics['efficiency_score']:.0f}/100
• Time ROI: {metrics['time_roi']:.0f}/100
• Overall Productivity: {metrics['productivity_score']:.0f}/100

**PATTERNS:**
• Total Sessions: {metrics['total_sessions']}
• Average Session: {metrics['avg_session_min']:.1f} minutes
• Context Switches: {metrics['context_switches']}
• Fragmentation: {metrics['fragmentation']:.1f} sessions/hour
• Current Streak: {streaks['current_streak']} days
• Longest Streak: {streaks['longest_streak']} days

**INSTRUCTIONS:**
1. Provide a 6-8 sentence professional analysis
2. Highlight 2-3 key strengths with specific data points
3. Identify 1-2 critical improvement areas
4. Give 3 specific, actionable recommendations
5. Use a constructive, motivating tone
6. Format with clear paragraphs and bullet points for recommendations

Generate your analysis now:
"""
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            st.error(f"❌ AI Analysis failed: {e}")
            logger.error(f"AI generation error: {e}")
            return None
    
    def render(self):
        """Main render method"""
        self.render_header()
        self.render_sidebar()
        
        # Load data
        result = self.load_data(st.session_state.date_range)
        
        if result[0] is None:
            st.warning("📭 No activity data found for the selected period.")
            st.info("""
**Getting Started:**
1. Ensure the Activity Watcher is running (check system tray)
2. Work for a few minutes in VSCode, Cursor, or your browser
3. Come back here and hit Refresh

The system tracks your activity every 30 seconds automatically.
            """)
            return
        
        df, df_idle, metrics_calc, metrics = result
        
        # Render all sections
        self.render_key_metrics(metrics)
        self.render_productivity_scores(metrics)
        self.render_session_stats(metrics)
        self.render_charts(df, metrics_calc, metrics)
        self.render_detailed_breakdown(metrics_calc)
        self.render_ai_insights(metrics, metrics_calc)
        
        # Footer
        st.markdown("---")
        st.caption("Activity Tracker Pro © 2025 | Production v2.0.0 | Dockerized & Intelligent")


if __name__ == "__main__":
    try:
        dashboard = ActivityTrackerDashboard()
        dashboard.render()
    except Exception as e:
        st.error(f"❌ Dashboard Error: {e}")
        logger.exception("Dashboard crashed")
        st.info("Please check the logs and ensure the database is accessible.")