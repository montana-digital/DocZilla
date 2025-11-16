"""
Progress Indicator Utilities

Progress bars with time remaining estimates for bulk operations.
"""

import streamlit as st
import time
from typing import Optional
from collections import deque


class ProgressEstimator:
    """
    Estimate ETA using exponential moving average.
    
    Used for calculating time remaining in bulk operations.
    """
    
    def __init__(self, alpha: float = 0.3):
        """
        Initialize progress estimator.
        
        Args:
            alpha: Smoothing factor (0-1, higher = more responsive)
        """
        self.alpha = alpha
        self.rates = deque(maxlen=10)  # Keep last 10 rate samples
        self.current_rate = 0.0
        self.start_time = None
        self.items_processed = 0
    
    def start(self):
        """Start timing."""
        self.start_time = time.time()
        self.items_processed = 0
        self.current_rate = 0.0
        self.rates.clear()
    
    def update(self, items_processed: int):
        """
        Update progress estimate.
        
        Args:
            items_processed: Number of items processed so far
        """
        if self.start_time is None:
            self.start_time = time.time()
            return
        
        elapsed_time = time.time() - self.start_time
        
        if elapsed_time > 0:
            rate = items_processed / elapsed_time
            self.rates.append(rate)
            
            # Exponential moving average
            if self.current_rate == 0:
                self.current_rate = rate
            else:
                self.current_rate = (self.alpha * rate + 
                                   (1 - self.alpha) * self.current_rate)
        
        self.items_processed = items_processed
    
    def estimate_eta(self, total_items: int) -> float:
        """
        Estimate time remaining in seconds.
        
        Args:
            total_items: Total number of items to process
        
        Returns:
            Estimated seconds remaining
        """
        if self.current_rate == 0:
            return 0.0
        
        remaining_items = total_items - self.items_processed
        if remaining_items <= 0:
            return 0.0
        
        return remaining_items / self.current_rate
    
    def format_eta(self, seconds: float) -> str:
        """
        Format ETA as human-readable string.
        
        Args:
            seconds: Seconds remaining
        
        Returns:
            Formatted string (e.g., "~2 min remaining")
        """
        if seconds < 60:
            return f"~{int(seconds)}s remaining"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"~{minutes} min remaining"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            if minutes > 0:
                return f"~{hours}h {minutes}min remaining"
            return f"~{hours}h remaining"


def show_progress_bar(
    current: int,
    total: int,
    estimator: Optional[ProgressEstimator] = None,
    key: Optional[str] = None
):
    """
    Show progress bar with time remaining estimate.
    
    Args:
        current: Current progress (items processed)
        total: Total items to process
        estimator: ProgressEstimator instance (optional)
        key: Optional key for progress bar widget
    """
    if total == 0:
        return
    
    progress = current / total
    progress_pct = int(progress * 100)
    
    # Estimate time remaining
    eta_str = ""
    if estimator:
        estimator.update(current)
        eta_seconds = estimator.estimate_eta(total)
        eta_str = estimator.format_eta(eta_seconds)
    
    # Display progress bar
    if key:
        st.progress(
            progress,
            text=f"{progress_pct}% | {current}/{total} files {eta_str}".strip()
        )
    else:
        st.progress(
            progress,
            text=f"{progress_pct}% | {current}/{total} files {eta_str}".strip()
        )

