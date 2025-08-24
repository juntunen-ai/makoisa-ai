"""
Google Ads Integration - Commercial Module

This module provides Google AdSense integration for monetizing the recipe AI interface.
This component is licensed separately for commercial use.

License: Commercial use authorized for original author (Harri Juntunen/juntunen-ai)
Contact: harri@juntunen.ai for third-party commercial licensing
"""

import os
import streamlit as st
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class GoogleAdsManager:
    """Manages Google AdSense integration for commercial deployments."""
    
    def __init__(self):
        """Initialize Google Ads Manager with environment configuration."""
        self.enabled = os.getenv('GOOGLE_ADSENSE_ENABLED', 'false').lower() == 'true'
        self.client_id = os.getenv('GOOGLE_ADSENSE_CLIENT_ID', '')
        self.sidebar_slot = os.getenv('GOOGLE_ADSENSE_SIDEBAR_SLOT', '')
        self.main_slot = os.getenv('GOOGLE_ADSENSE_MAIN_SLOT', '')
        
        if self.enabled and not self.client_id:
            logger.warning("Google AdSense enabled but no client ID configured")
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if Google Ads are enabled and properly configured."""
        return self.enabled and bool(self.client_id)
    
    def render_google_ad(self, slot_id: str, width: int = 320, height: int = 100) -> None:
        """
        Render a Google AdSense ad unit.
        
        Args:
            slot_id: Google AdSense slot ID
            width: Ad width in pixels
            height: Ad height in pixels
        """
        if not self.is_enabled() or not slot_id:
            return
        
        ad_html = f"""
        <ins class="adsbygoogle"
             style="display:inline-block;width:{width}px;height:{height}px"
             data-ad-client="{self.client_id}"
             data-ad-slot="{slot_id}">
        </ins>
        <script>
             (adsbygoogle = window.adsbygoogle || []).push({{}});
        </script>
        """
        
        st.components.v1.html(ad_html, height=height + 20)
    
    def render_sidebar_ad(self) -> None:
        """Render sidebar advertisement (300x250 medium rectangle)."""
        if not self.is_enabled():
            return
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Sponsored**")
        
        # AdSense code for sidebar
        sidebar_ad_html = f"""
        <div style="text-align: center; padding: 10px;">
            <ins class="adsbygoogle"
                 style="display:inline-block;width:300px;height:250px"
                 data-ad-client="{self.client_id}"
                 data-ad-slot="{self.sidebar_slot}"
                 data-ad-format="rectangle"
                 data-ad-theme="cooking">
            </ins>
            <script>
                 (adsbygoogle = window.adsbygoogle || []).push({{}});
            </script>
        </div>
        """
        
        st.sidebar.components.v1.html(sidebar_ad_html, height=280)
    
    def render_main_ad(self, position: str = "top") -> None:
        """
        Render main content area advertisement (728x90 leaderboard).
        
        Args:
            position: Ad position ("top", "middle", "bottom")
        """
        if not self.is_enabled():
            return
        
        st.markdown(f"*Advertisement - {position.title()}*")
        
        # AdSense code for main content area
        main_ad_html = f"""
        <div style="text-align: center; padding: 15px 0; border: 1px solid #e0e0e0; border-radius: 5px; margin: 10px 0;">
            <ins class="adsbygoogle"
                 style="display:inline-block;width:728px;height:90px"
                 data-ad-client="{self.client_id}"
                 data-ad-slot="{self.main_slot}"
                 data-ad-format="leaderboard"
                 data-ad-theme="cooking">
            </ins>
            <script>
                 (adsbygoogle = window.adsbygoogle || []).push({{}});
            </script>
        </div>
        """
        
        st.components.v1.html(main_ad_html, height=120)
    
    def inject_adsense_script(self) -> None:
        """Inject Google AdSense JavaScript into the page head."""
        if not self.is_enabled():
            return
        
        adsense_script = f"""
        <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={self.client_id}"
                crossorigin="anonymous"></script>
        """
        
        st.components.v1.html(adsense_script, height=0)
    
    def get_ad_config(self) -> Dict[str, Any]:
        """Get current ad configuration for debugging."""
        return {
            "enabled": self.enabled,
            "client_id": self.client_id[:10] + "..." if self.client_id else None,
            "sidebar_slot": bool(self.sidebar_slot),
            "main_slot": bool(self.main_slot),
        }


# Global instance for easy importing
ads_manager = GoogleAdsManager()


def render_sidebar_ad() -> None:
    """Convenience function for sidebar ad rendering."""
    ads_manager.render_sidebar_ad()


def render_main_ad(position: str = "top") -> None:
    """Convenience function for main content ad rendering."""
    ads_manager.render_main_ad(position)


def inject_adsense_script() -> None:
    """Convenience function for AdSense script injection."""
    ads_manager.inject_adsense_script()


def is_ads_enabled() -> bool:
    """Convenience function to check if ads are enabled."""
    return ads_manager.is_enabled()
