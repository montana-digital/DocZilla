"""
Activity Log Components

UI components for displaying activity logs.
"""

import streamlit as st
from typing import List, Dict, Optional
from src.app.utils.logging import get_logger, LogLevel


def render_activity_log(
    logs: List[Dict],
    filter_level: Optional[str] = None,
    max_display: int = 100
):
    """
    Render activity log entries in UI.
    
    Args:
        logs: List of log entry dictionaries
        filter_level: Optional level filter (INFO, WARN, ERROR, FATAL)
        max_display: Maximum entries to display
    """
    # Filter by level if specified
    if filter_level:
        logs = [log for log in logs if log.get("level", "").upper() == filter_level.upper()]
    
    # Limit display
    logs = logs[:max_display]
    
    if not logs:
        st.info("No log entries found.")
        return
    
    # Display logs
    for log in logs:
        level = log.get("level", "INFO")
        timestamp = log.get("timestamp", "")
        message = log.get("message", "")
        
        # Color code by level
        if level == "ERROR" or level == "FATAL":
            st.error(f"**{timestamp}** [{level}] {message}")
        elif level == "WARN":
            st.warning(f"**{timestamp}** [{level}] {message}")
        else:
            st.info(f"**{timestamp}** [{level}] {message}")


def render_log_filters() -> Optional[str]:
    """
    Render log filter controls.
    
    Returns:
        Selected filter level or None
    """
    filter_options = ["All", "INFO", "WARN", "ERROR", "FATAL"]
    selected = st.selectbox("Filter by level", filter_options)
    
    return None if selected == "All" else selected


def render_log_statistics(logs: List[Dict]):
    """
    Render log statistics summary.
    
    Args:
        logs: List of log entry dictionaries
    """
    if not logs:
        return
    
    # Count by level
    level_counts = {}
    for log in logs:
        level = log.get("level", "INFO")
        level_counts[level] = level_counts.get(level, 0) + 1
    
    # Display metrics
    cols = st.columns(len(level_counts))
    for i, (level, count) in enumerate(level_counts.items()):
        with cols[i]:
            st.metric(level, count)

