# Google Ads Implementation Guide

## Overview

This document describes the Google AdSense integration implemented in the AI Recipe Generator application. The implementation follows best practices for non-intrusive advertising that is relevant to cooking and food content.

## Features

### ✅ Non-Intrusive Design
- **Two ad placements only**: Sidebar and main content area
- **Cooking/food relevant ads**: Targeted to kitchen equipment, ingredients, and cooking tools
- **No pop-ups**: All ads are static and integrated into the page layout
- **Responsive design**: Ads adapt to different screen sizes

### ✅ User Experience First
- **Clearly labeled**: All ads are marked as "Mainos" (Advertisement in Finnish)
- **Tasteful styling**: Ads blend well with the application design
- **Performance optimized**: Minimal impact on page load speed
- **Easy to disable**: Can be turned off via environment variables

## Configuration

### Environment Variables

Add these variables to `recipe_ai/.env`:

```bash
# Google AdSense Configuration
GOOGLE_ADSENSE_ENABLED=true
GOOGLE_ADSENSE_CLIENT_ID=ca-pub-YOUR_PUBLISHER_ID
GOOGLE_ADSENSE_SIDEBAR_SLOT=1234567890
GOOGLE_ADSENSE_MAIN_SLOT=0987654321
```

### Ad Slot Setup

1. **Sidebar Ad**:
   - Format: Rectangle (250px height)
   - Location: Bottom of sidebar, after settings
   - Recommended for: Kitchen equipment, cooking books

2. **Main Content Ad**:
   - Format: Horizontal banner (90px height)
   - Location: Between header and main tabs
   - Recommended for: Food delivery, ingredient suppliers

## Implementation Details

### Ad Placement Strategy

The ads are placed in two strategic locations:

1. **Sidebar**: After user settings but before the "About" section
2. **Main Content**: Between the app description and the main tab navigation

### CSS Styling

```css
.ad-container {
    background-color: #f5f5f5;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 15px;
    margin: 20px 0;
    text-align: center;
    font-size: 0.9em;
    color: #666;
}
```

### Content Guidelines

All ads should be relevant to:
- 🍳 **Cooking equipment**: Pots, pans, kitchen tools
- 🥘 **Food ingredients**: Spices, fresh produce, pantry items
- 📚 **Cooking education**: Recipe books, cooking courses
- 🏪 **Food services**: Grocery delivery, meal kits
- 🍽️ **Dining**: Restaurants, food experiences

## Google AdSense Setup

### Step 1: Create AdSense Account
1. Visit [Google AdSense](https://www.google.com/adsense/)
2. Create an account and get approved
3. Note your Publisher ID (`ca-pub-XXXXXXXXXX`)

### Step 2: Create Ad Units
1. Create a **Display Ad** for sidebar (Medium Rectangle: 300x250)
2. Create a **Display Ad** for main content (Leaderboard: 728x90)
3. Note the ad slot IDs

### Step 3: Update Configuration
1. Replace `YOUR_PUBLISHER_ID` with your actual Publisher ID
2. Replace slot IDs with your actual ad unit slot IDs
3. Set `GOOGLE_ADSENSE_ENABLED=true`

### Step 4: Deploy and Test
1. Deploy the updated application
2. Verify ads are showing correctly
3. Monitor performance in AdSense dashboard

## Content Policy Compliance

The implementation ensures compliance with Google AdSense policies:

- ✅ **Content relevant ads**: Only cooking/food related content
- ✅ **Clear labeling**: All ads clearly marked as advertisements
- ✅ **No excessive ads**: Maximum 2 ad units per page
- ✅ **No invalid clicks**: Ads are not placed near action buttons
- ✅ **Mobile friendly**: Responsive design for all devices

## Performance Considerations

### Load Time Impact
- **Async loading**: AdSense script loads asynchronously
- **Conditional loading**: Ads only load when enabled
- **Minimal CSS**: Lightweight styling for ad containers

### Revenue Optimization
- **Strategic placement**: Ads placed where users naturally pause
- **Relevant targeting**: Food/cooking keywords in page content
- **Responsive sizing**: Ads adapt to screen size for better visibility

## Monitoring and Analytics

### Metrics to Track
1. **Ad performance**: CTR, RPM, impressions
2. **User experience**: Bounce rate, session duration
3. **Revenue**: Daily/monthly earnings
4. **Page speed**: Impact on load times

### Optimization Tips
1. **A/B test**: Different ad placements and sizes
2. **Content targeting**: Ensure content keywords match ad intent
3. **Seasonal adjustments**: Holiday cooking content for better rates
4. **User feedback**: Monitor complaints about ad placement

## Troubleshooting

### Common Issues

**Ads not showing:**
- Check `GOOGLE_ADSENSE_ENABLED=true`
- Verify Publisher ID is correct
- Ensure ad slot IDs are valid

**Poor performance:**
- Review ad placement for user experience
- Check content relevance to cooking/food
- Monitor page load speeds

**Policy violations:**
- Ensure ads are clearly labeled
- Avoid placing ads near buttons
- Keep content family-friendly

## Future Enhancements

### Potential Improvements
1. **Dynamic targeting**: Based on recipe type being generated
2. **Seasonal campaigns**: Holiday cooking and special occasions
3. **Local targeting**: Finnish grocery stores and restaurants
4. **Recipe-specific ads**: Ingredients for the current recipe

### Analytics Integration
1. **Google Analytics**: Track ad interaction with recipe generation
2. **Custom events**: Measure conversion from ad clicks
3. **Revenue reporting**: Automated earnings reports

## Maintenance

### Regular Tasks
1. **Monthly review**: Check ad performance and revenue
2. **Content audit**: Ensure ad relevance is maintained
3. **Policy compliance**: Stay updated with AdSense policies
4. **User feedback**: Monitor and respond to ad-related issues

### Updates Required
- Keep AdSense script up to date
- Review and update ad slot configurations
- Test ad display after major UI changes
- Monitor for policy changes from Google

---

**Note**: This implementation prioritizes user experience while maximizing revenue potential through strategic, relevant advertising placement.
