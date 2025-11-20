# Platform Analytics & User Activity Guide

This guide explains the new analytics features added to the Hyperliquid Dashboard, similar to Dune Analytics.

## Overview

The dashboard now tracks and displays comprehensive platform analytics including:
- User activity metrics (estimated)
- Platform growth trends
- Historical data visualization
- Cumulative statistics

## Features

### 1. Platform Activity Metrics 📊

**Estimated Total Users**
- Platform-wide user count estimate
- Based on open interest and trading activity
- Updated every 10 seconds

**Active Users (24h)**
- Estimated users trading in the last 24 hours
- Calculated from daily volume
- Assumes average trade size of $5,000

**Estimated Trades (24h)**
- Daily transaction count
- Derived from 24h trading volume
- Provides activity level indicator

**Days Tracked**
- Number of days with historical data
- Shows data collection duration
- Maximum 90 days retained

### 2. Growth Metrics 📈

**Volume Growth**
- 7-day growth percentage
- 30-day growth percentage
- Color-coded (green = positive, red = negative)

**Open Interest Growth**
- 7-day OI change
- 30-day OI change
- Indicates platform expansion

### 3. Time-Series Charts

**Volume Trend (30 Days)**
- Line chart showing daily volume over time
- Visualizes trading activity patterns
- Helps identify trends and seasonality

**Open Interest Trend (30 Days)**
- Historical OI progression
- Shows capital inflow/outflow
- Indicates platform growth trajectory

## Data Collection

### Automatic Tracking

The analytics module automatically:
1. Records market snapshots every 10 seconds
2. Stores data in `data/platform_history.json`
3. Retains 90 days of historical data
4. Calculates cumulative and growth metrics

### Data Points Collected

Each snapshot includes:
```json
{
  "timestamp": "2025-11-20T22:45:00",
  "total_volume_24h": 1234567890,
  "total_open_interest": 987654321,
  "total_assets": 221,
  "avg_funding_rate": 0.00015,
  "active_assets": 180
}
```

## API Endpoints

### `/api/analytics`
Comprehensive analytics data including:
- Cumulative statistics
- Growth metrics (7d and 30d)
- Platform estimates
- Time-series data

**Example Response:**
```json
{
  "cumulative_stats": {
    "cumulative_volume": 123456789,
    "days_tracked": 15,
    "first_recorded": "2025-11-05T10:00:00",
    "latest_snapshot": {...}
  },
  "growth_metrics": {
    "volume_growth_7d": 15.5,
    "volume_growth_30d": 45.2,
    "oi_growth_7d": 8.3,
    "oi_growth_30d": 22.1
  },
  "platform_metrics": {
    "estimated_total_users": 98765,
    "estimated_active_users_24h": 12345,
    "estimated_daily_trades": 123456
  },
  "time_series": {
    "volume_30d": [...],
    "open_interest_30d": [...]
  }
}
```

### `/api/platform-metrics`
Get estimated platform metrics only.

### `/api/analytics/time-series/<metric>/<days>`
Get specific metric time-series.

**Valid metrics:**
- `total_volume_24h`
- `total_open_interest`
- `total_assets`
- `avg_funding_rate`

**Example:**
```
GET /api/analytics/time-series/total_volume_24h/30
```

## Estimation Methodology

### User Estimates

Since the Hyperliquid API doesn't provide direct user counts, we estimate based on:

**Total Users:**
```
estimated_total_users = total_open_interest / 10,000
```
Assumes average user has $10,000 in open positions.

**Active Users (24h):**
```
estimated_active_users = estimated_daily_trades / 10
```
Assumes active users make ~10 trades per day.

**Daily Trades:**
```
estimated_daily_trades = total_volume_24h / 5,000
```
Assumes average trade size of $5,000.

### Important Notes

⚠️ **These are rough estimates** and may not reflect actual user counts. They serve as proxy metrics for platform activity levels.

✅ **Use for trend analysis**, not absolute numbers. Growth patterns are more meaningful than specific values.

## Dashboard Sections

### Platform Activity & User Metrics
Located below the main metrics cards, this section displays:
- Four metric cards with estimated user data
- Color-coded values for easy reading
- Real-time updates every 10 seconds

### Growth Metrics
Dedicated section showing:
- Volume growth (7d and 30d)
- Open Interest growth (7d and 30d)
- Percentage changes with color coding
- Quick overview of platform trajectory

### Time-Series Charts
Two line charts displaying:
- 30-day volume trend (blue)
- 30-day OI trend (purple)
- Formatted Y-axis ($1M, $10M, $100M, etc.)
- Date labels on X-axis

## Data Persistence

### Storage Location
```
hyperliquid-dashboard/data/platform_history.json
```

### Data Retention
- Maximum 90 days of hourly snapshots
- Automatic cleanup of old data
- ~2,160 data points maximum
- Approximately 500KB file size

### Backup & Export

To backup historical data:
```bash
cp data/platform_history.json data/backup_$(date +%Y%m%d).json
```

To export for analysis:
```python
import json
with open('data/platform_history.json') as f:
    data = json.load(f)
# Use pandas, matplotlib, etc. for analysis
```

## Customization

### Adjust Estimation Parameters

Edit `backend/analytics.py`:

```python
# Change average trade size assumption
estimated_daily_trades = int(total_volume_24h / 3000)  # from 5000

# Change trades per user assumption
estimated_active_users = int(estimated_daily_trades / 15)  # from 10

# Change user capital assumption
estimated_total_users = int(total_open_interest / 5000)  # from 10000
```

### Change Data Retention

```python
# In analytics.py, _save_history method
cutoff = (datetime.now() - timedelta(days=180)).isoformat()  # from 90
```

### Adjust Refresh Rate

Edit `frontend/js/dashboard.js`:
```javascript
const REFRESH_INTERVAL = 30000; // 30 seconds instead of 10
```

## Troubleshooting

### No Historical Data

If time-series charts are empty:
1. Wait 10 seconds for first snapshot
2. Check `data/platform_history.json` exists
3. Verify API endpoint: `http://localhost:5000/api/analytics`
4. Check browser console for errors

### Estimates Seem Off

User estimates are intentionally rough:
- Designed for trend analysis
- Not meant to be precise counts
- Focus on growth rates, not absolute values
- Adjust parameters if needed (see Customization)

### Charts Not Updating

1. Check network tab for API calls
2. Verify analytics endpoint returns data
3. Check console for JavaScript errors
4. Ensure Chart.js is loaded

## Best Practices

1. **Let Data Accumulate**: Wait 24-48 hours for meaningful trends
2. **Focus on Growth**: Use percentage changes, not raw numbers
3. **Compare Periods**: 7d vs 30d shows acceleration/deceleration
4. **Monitor Trends**: Sustained growth is more important than spikes
5. **Cross-Reference**: Compare user metrics with volume/OI trends

## Future Enhancements

Potential additions:
- [ ] Cohort analysis (user retention)
- [ ] Geographic distribution (if available)
- [ ] Asset-specific user metrics
- [ ] Whale tracking (large positions)
- [ ] Liquidation analytics
- [ ] PnL distribution estimates
- [ ] Market maker vs taker ratios
- [ ] Cross-market correlation analysis

## Support

For issues or questions:
- Check the main [README.md](README.md)
- Review API responses in browser network tab
- Inspect `data/platform_history.json` for data issues
- Check server logs for backend errors

---

**Note**: This analytics system is designed to provide insights similar to Dune Analytics dashboards, but using real-time API data with client-side aggregation and storage.
