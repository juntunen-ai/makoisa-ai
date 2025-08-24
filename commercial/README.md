# Commercial Module

This directory contains commercial features and extensions for the Makoisa AI project.

## 🔒 License Notice

The components in this `commercial/` directory are subject to **separate commercial licensing terms** and are **not covered by the PolyForm Noncommercial License** that applies to the rest of the project.

## 📦 Components

### Google Ads Integration
- **File**: `google_ads.py`
- **Purpose**: AdSense integration for revenue generation
- **License**: Commercial use authorized for original author
- **Integration**: Optional module for recipe AI interface

### Usage

```python
# Optional import for commercial deployments
try:
    from commercial.google_ads import GoogleAdsManager
    ads_enabled = True
except ImportError:
    ads_enabled = False

# Use ads functionality if available
if ads_enabled:
    ads_manager = GoogleAdsManager()
    ads_manager.render_sidebar_ad()
```

## 🤝 Commercial Licensing

To use these commercial components:
1. **Original Author**: Full commercial rights granted
2. **Third Parties**: Contact harri@juntunen.ai for commercial licensing
3. **Contributors**: Subject to Contributor License Agreement

## 🚀 Deployment

For production deployments requiring monetization:
1. Ensure commercial license is in place
2. Configure Google AdSense account
3. Set environment variables for ad configuration
4. Enable commercial module in deployment

---

*These commercial components enable monetization while maintaining clear separation from the open source core functionality.*
