"""
Commercial Module Initialization

This module contains commercial features and extensions that require
separate licensing for commercial use.
"""

# Commercial module version
__version__ = "1.3.0-dev"

# License notice
__license__ = """
Commercial License Notice:
- Original author (Harri Juntunen/juntunen-ai) has full commercial rights
- Third parties require separate commercial license
- Contact: harri@juntunen.ai for licensing inquiries
"""

# Available commercial components
__all__ = [
    "google_ads",
    "GoogleAdsManager",
]

# Conditional imports based on licensing
try:
    from .google_ads import GoogleAdsManager, ads_manager
    GOOGLE_ADS_AVAILABLE = True
except ImportError:
    GOOGLE_ADS_AVAILABLE = False
    GoogleAdsManager = None
    ads_manager = None
