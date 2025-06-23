# Google Ads Local Testing Guide

## 🚀 Quick Start

The Streamlit application is now running with Google Ads integration at:
**http://localhost:8501**

## 📍 Where to Find the Ads

### Sidebar Ad
- **Location**: Left sidebar
- **Position**: After dietary restrictions and recipe settings, before the "About" section
- **Size**: 250px height rectangle
- **Label**: "Mainos" (Advertisement in Finnish)

### Main Content Ad  
- **Location**: Main content area
- **Position**: Between the app description and the main tabs
- **Size**: 90px height horizontal banner
- **Label**: "Mainos" (Advertisement in Finnish)

## 👀 What You Should See

When ads are **ENABLED** (`GOOGLE_ADSENSE_ENABLED=true`):
- ✅ Gray bordered containers with "Mainos" labels
- ✅ Placeholder content about cooking equipment
- ✅ Professional styling that matches the app design
- ✅ Non-intrusive placement

When ads are **DISABLED** (`GOOGLE_ADSENSE_ENABLED=false`):
- ❌ No ad containers appear at all
- ❌ No "Mainos" labels visible
- ❌ Clean interface without advertising

## 🧪 Testing Scenarios

### Test 1: Verify Ads Appear
1. ✅ Confirm `GOOGLE_ADSENSE_ENABLED=true` in `recipe_ai/.env`
2. ✅ Load http://localhost:8501
3. ✅ Look for 2 ad containers (sidebar + main content)
4. ✅ Verify "Mainos" labels are visible

### Test 2: Verify Ads Can Be Disabled
1. 🔧 Change `GOOGLE_ADSENSE_ENABLED=false` in `recipe_ai/.env`
2. 🔄 Restart Streamlit app
3. ❌ Confirm no ad containers appear
4. ✅ Verify app functions normally without ads

### Test 3: Test Responsive Design
1. 📱 Resize browser window to different sizes
2. 📱 Check that ads adapt to screen size
3. 📱 Verify ads don't break layout on mobile sizes

### Test 4: Test Recipe Generation with Ads
1. 🍳 Generate a recipe using the app
2. 🍳 Verify ads remain visible throughout the process
3. 🍳 Confirm ads don't interfere with recipe functionality

## 📋 Current Configuration

```bash
GOOGLE_ADSENSE_ENABLED=true
GOOGLE_ADSENSE_CLIENT_ID=ca-pub-YOUR_PUBLISHER_ID
GOOGLE_ADSENSE_SIDEBAR_SLOT=1234567890
GOOGLE_ADSENSE_MAIN_SLOT=0987654321
```

**Note**: These are placeholder values for testing. Replace with real AdSense IDs for production.

## 🔧 Making Changes

### To Disable Ads Temporarily:
```bash
# Edit recipe_ai/.env
GOOGLE_ADSENSE_ENABLED=false
```

### To Customize Ad Content:
```bash
# Edit recipe_ai/ui/app.py
# Look for render_google_ad() function
# Modify the placeholder content inside ad_html
```

### To Change Ad Placement:
```bash
# Edit recipe_ai/ui/app.py
# Move render_sidebar_ad() or render_main_ad() calls
# to different locations in the UI
```

## 🚀 Production Setup

When ready for production:

1. **Get Google AdSense Account**:
   - Apply at https://www.google.com/adsense/
   - Get approved and note your Publisher ID

2. **Create Ad Units**:
   - Create sidebar ad (300x250 rectangle)
   - Create main content ad (728x90 leaderboard)
   - Note the ad slot IDs

3. **Update Configuration**:
   ```bash
   GOOGLE_ADSENSE_CLIENT_ID=ca-pub-YOUR_REAL_PUBLISHER_ID
   GOOGLE_ADSENSE_SIDEBAR_SLOT=YOUR_REAL_SIDEBAR_SLOT
   GOOGLE_ADSENSE_MAIN_SLOT=YOUR_REAL_MAIN_SLOT
   ```

4. **Deploy and Monitor**:
   - Deploy to production
   - Monitor ad performance in AdSense dashboard
   - Optimize based on user engagement

## 📊 Expected Performance

### Development (Current State):
- Placeholder ad content visible
- Configuration system working
- Non-intrusive placement confirmed

### Production (After AdSense Setup):
- Real cooking/food-related ads
- Revenue generation from ad clicks
- Targeted content for Finnish cooking audience

## 🐛 Troubleshooting

### Ads Not Appearing:
- Check `GOOGLE_ADSENSE_ENABLED=true`
- Verify no JavaScript errors in browser console
- Confirm Streamlit app restarted after config changes

### Ads Interfering with UI:
- Check CSS styling in app.py
- Verify responsive design at different screen sizes
- Adjust ad container margins/padding if needed

### Performance Issues:
- Monitor page load times
- Check browser network tab for ad script loading
- Consider async loading optimization

---

**✅ The Google Ads implementation is complete and ready for testing!**

Navigate to http://localhost:8501 to see the ads in action.
