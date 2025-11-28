"""
Visualization Utilities
"""
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import config


def create_time_allocation_pie(metrics):
    """Create pie chart for time allocation"""
    data = pd.DataFrame({
        'Category': [
            'Primary Work',
            'Secondary Work',
            'Browser (Work)',
            'Browser (Leisure)',
            'Idle/Breaks'
        ],
        'Minutes': [
            metrics['primary_work_min'],
            metrics['secondary_work_min'],
            metrics['browser_work_min'],
            metrics['browser_nonwork_min'],
            metrics['idle_min']
        ]
    })
    
    # Filter out zero values
    data = data[data['Minutes'] > 0]
    
    colors = [
        config.COLOR_PRIMARY_WORK,
        config.COLOR_SECONDARY_WORK,
        config.COLOR_BROWSER_WORK,
        config.COLOR_BROWSER_NONWORK,
        config.COLOR_IDLE
    ]
    
    fig = px.pie(
        data,
        values='Minutes',
        names='Category',
        title='Time Allocation',
        color_discrete_sequence=colors[:len(data)],
        hole=0.4
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>%{value:.0f} min<br>%{percent}<extra></extra>'
    )
    
    fig.update_layout(height=config.CHART_HEIGHT)
    
    return fig


def create_daily_trend(df, metrics_calc):
    """Create daily trend bar chart"""
    daily = metrics_calc.get_daily_breakdown()
    
    if daily.empty:
        return go.Figure()
    
    # Prepare data for stacked bar
    daily_reset = daily.reset_index()
    
    # Get available categories
    categories = []
    colors = []
    for cat in ['PRIMARY_WORK', 'SECONDARY_WORK', 'BROWSER_WORK', 'BROWSER_NONWORK', 'IDLE']:
        if cat in daily.columns:
            categories.append(cat)
            colors.append(config.CATEGORY_COLORS[cat])
    
    fig = go.Figure()
    
    for cat, color in zip(categories, colors):
        if cat in daily.columns:
            fig.add_trace(go.Bar(
                x=daily_reset['date'],
                y=daily_reset[cat],
                name=cat.replace('_', ' ').title(),
                marker_color=color,
                hovertemplate='%{y:.0f} min<extra></extra>'
            ))
    
    fig.update_layout(
        title='Daily Activity Trend',
        xaxis_title='Date',
        yaxis_title='Minutes',
        barmode='stack',
        height=config.CHART_HEIGHT,
        hovermode='x unified',
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig


def create_hourly_heatmap(df):
    """Create heatmap of hourly activity"""
    # Create hour x day of week matrix
    heatmap_data = df.groupby(['day_of_week', 'hour'])['duration_min'].sum().unstack(fill_value=0)
    
    # Reorder days
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data.reindex([d for d in day_order if d in heatmap_data.index])
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='Viridis',
        hovertemplate='Hour: %{x}<br>Day: %{y}<br>Activity: %{z:.0f} min<extra></extra>'
    ))
    
    fig.update_layout(
        title='Activity Heatmap (by Hour and Day)',
        xaxis_title='Hour of Day',
        yaxis_title='Day of Week',
        height=400
    )
    
    return fig


def create_timeline_view(df, max_sessions=50):
    """Create timeline of recent sessions"""
    # Filter and limit
    timeline_df = df.head(max_sessions).copy()
    timeline_df = timeline_df[timeline_df['duration_seconds'] > 30]  # Filter very short sessions
    
    if timeline_df.empty:
        return go.Figure()
    
    # Sort by start time
    timeline_df = timeline_df.sort_values('start_dt')
    
    # Create color mapping
    timeline_df['color'] = timeline_df['category'].map(config.CATEGORY_COLORS)
    
    # Create hover text
    timeline_df['hover_text'] = timeline_df.apply(
        lambda row: f"<b>{row['display_name']}</b><br>" +
                    f"{row['window_title'][:50]}...<br>" +
                    f"Duration: {row['duration_min']:.1f} min<br>" +
                    f"Focus: {row['foreground_ratio']*100:.0f}%",
        axis=1
    )
    
    fig = px.timeline(
        timeline_df,
        x_start='start_dt',
        x_end='end_dt',
        y='display_name',
        color='category',
        title=f'Session Timeline (Last {len(timeline_df)} sessions)',
        color_discrete_map=config.CATEGORY_COLORS,
        hover_data=['window_title', 'duration_min']
    )
    
    fig.update_yaxes(autorange='reversed')
    fig.update_layout(
        height=config.TIMELINE_HEIGHT,
        xaxis_title='Time',
        yaxis_title='Application',
        showlegend=True
    )
    
    return fig


def create_app_breakdown_chart(app_stats, top_n=10):
    """Create horizontal bar chart of top applications"""
    top_apps = app_stats.head(top_n).sort_values('duration_min')
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=top_apps.index,
        x=top_apps['duration_min'],
        orientation='h',
        marker_color=config.COLOR_PRIMARY_WORK,
        text=top_apps['duration_min'].apply(lambda x: f'{x:.0f} min'),
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Time: %{x:.0f} min<br>Sessions: %{customdata[0]}<extra></extra>',
        customdata=top_apps[['sessions']].values
    ))
    
    fig.update_layout(
        title=f'Top {top_n} Applications by Time',
        xaxis_title='Minutes',
        yaxis_title='Application',
        height=400,
        showlegend=False
    )
    
    return fig


def create_focus_sessions_chart(df):
    """Create chart showing focus sessions over time"""
    focus_sessions = df[df['is_focus_session'] == 1].copy()
    
    if focus_sessions.empty:
        return go.Figure()
    
    focus_sessions['date'] = focus_sessions['start_dt'].dt.date
    daily_focus = focus_sessions.groupby('date').agg({
        'duration_min': 'sum',
        'id': 'count'
    }).rename(columns={'id': 'count'})
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(
            x=daily_focus.index,
            y=daily_focus['duration_min'],
            name='Focus Minutes',
            marker_color=config.COLOR_PRIMARY_WORK,
            hovertemplate='%{y:.0f} min<extra></extra>'
        ),
        secondary_y=False,
    )
    
    fig.add_trace(
        go.Scatter(
            x=daily_focus.index,
            y=daily_focus['count'],
            name='Focus Sessions',
            mode='lines+markers',
            line=dict(color=config.COLOR_BROWSER_WORK, width=2),
            marker=dict(size=8),
            hovertemplate='%{y} sessions<extra></extra>'
        ),
        secondary_y=True,
    )
    
    fig.update_xaxes(title_text='Date')
    fig.update_yaxes(title_text='Minutes', secondary_y=False)
    fig.update_yaxes(title_text='Session Count', secondary_y=True)
    
    fig.update_layout(
        title='Deep Focus Sessions Over Time',
        height=config.CHART_HEIGHT,
        hovermode='x unified'
    )
    
    return fig


def create_productivity_gauge(score, title):
    """Create gauge chart for productivity score"""
    if score >= config.EXCELLENT_SCORE:
        color = config.COLOR_PRIMARY_WORK
    elif score >= config.GOOD_SCORE:
        color = config.COLOR_BROWSER_WORK
    elif score >= config.MEDIUM_SCORE:
        color = config.COLOR_BROWSER_NONWORK
    else:
        color = config.COLOR_IDLE
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        title={'text': title},
        delta={'reference': 70, 'increasing': {'color': config.COLOR_PRIMARY_WORK}},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 50], 'color': 'lightgray'},
                {'range': [50, 70], 'color': 'gray'},
                {'range': [70, 85], 'color': 'darkgray'}
            ],
            'threshold': {
                'line': {'color': 'red', 'width': 4},
                'thickness': 0.75,
                'value': 85
            }
        }
    ))
    
    fig.update_layout(height=250)
    
    return fig


def create_weekly_comparison(df):
    """Create weekly comparison chart"""
    df['week'] = df['start_dt'].dt.isocalendar().week
    df['year'] = df['start_dt'].dt.year
    
    weekly = df.groupby(['year', 'week', 'category'])['duration_min'].sum().unstack(fill_value=0)
    
    if weekly.empty:
        return go.Figure()
    
    # Get last 4 weeks
    weekly = weekly.tail(4)
    weekly.index = weekly.index.map(lambda x: f'Week {x[1]}')
    
    fig = go.Figure()
    
    for cat in ['PRIMARY_WORK', 'SECONDARY_WORK', 'BROWSER_WORK']:
        if cat in weekly.columns:
            fig.add_trace(go.Bar(
                x=weekly.index,
                y=weekly[cat],
                name=cat.replace('_', ' ').title(),
                marker_color=config.CATEGORY_COLORS[cat]
            ))
    
    fig.update_layout(
        title='Weekly Activity Comparison',
        xaxis_title='Week',
        yaxis_title='Minutes',
        barmode='group',
        height=config.CHART_HEIGHT
    )
    
    return fig