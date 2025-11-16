"""
Animation Components

Title animation utilities for Streamlit.
"""

import streamlit as st
from typing import Literal
import time


def animate_title(
    text: str,
    animation_type: Literal["typewriter", "fade"] = "fade",
    speed: float = 0.05,
    container=None
):
    """
    Animate text appearance (typewriter or fade effect).
    
    Note: Streamlit doesn't support true animations easily.
    This provides a simple implementation that can be enhanced.
    
    Args:
        text: Text to animate
        animation_type: Type of animation ("typewriter" or "fade")
        speed: Animation speed (delay between characters/updates)
        container: Streamlit container to render in (default: main area)
    """
    if container is None:
        container = st
    
    if animation_type == "typewriter":
        # Typewriter effect - show characters one by one
        placeholder = container.empty()
        for i in range(len(text) + 1):
            placeholder.title(text[:i])
            time.sleep(speed)
    else:
        # Fade effect - simple appearance
        # Streamlit doesn't support CSS animations easily,
        # so we use markdown with styling
        st.markdown(
            f'<h1 style="animation: fadeIn 1s;">{text}</h1>',
            unsafe_allow_html=True
        )


def render_title_with_animation(
    app_name: str,
    static_text: str = "Part of the SPEAR Toolkit",
    animation_type: Literal["typewriter", "fade"] = "fade"
):
    """
    Render title with app name animation and static text.
    
    Args:
        app_name: Name of the app (will be animated)
        static_text: Static text to display (e.g., "Part of the SPEAR Toolkit")
        animation_type: Type of animation for app name
    """
    # Render static text first
    st.caption(static_text)
    
    # Render app name (simple implementation - can be enhanced)
    # For now, just display normally as Streamlit doesn't easily support animations
    # In a real implementation, you might use CSS or JavaScript
    st.title(app_name)
    
    # Note: For true animations in Streamlit, you would need:
    # 1. Custom CSS in .streamlit/config.toml
    # 2. JavaScript components
    # 3. Or use external libraries that support animations
    
    # Simple CSS-based fade animation
    st.markdown(
        """
        <style>
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        h1 {
            animation: fadeIn 1s ease-in;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

