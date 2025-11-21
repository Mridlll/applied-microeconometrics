# HIP-3 Market Snapshot Collection

## Overview

The snapshot collection system tracks Open Interest (OI), volume, funding rates, and prices over time for all HIP-3 markets. This enables **real 24-hour trend analysis** instead of just point-in-time snapshots.

## Why Snapshots?

**Problem**: The Hyperliquid API only provides current values (not historical trends)
**Solution**: Periodically collect and store market data to build time-series

### What Gets Tracked

For each HIP-3 market (xyz, flx, vntl):
- Open Interest (contracts and USD value)
- 24h Volume
- Funding Rate
- Mark Price
- Oracle Price
- Premium
- Previous Day Price

## Setup

### Option 1: Continuous Background Collection (Recommended)

Run the collector in the background:

```bash
cd /home/user/applied-microeconometrics/hyperliquid-dashboard/backend

# Run continuously (collects every 10 minutes)
python3 collect_snapshots.py &

# Or use nohup to persist after logout
nohup python3 collect_snapshots.py > snapshots.log 2>&1 &
```

### Option 2: Cron Job

Add to your crontab (`crontab -e`):

```cron
# Collect market snapshots every 10 minutes
*/10 * * * * cd /home/user/applied-microeconometrics/hyperliquid-dashboard/backend && python3 collect_snapshots.py --once >> snapshots.log 2>&1
```

### Option 3: Manual Collection

Collect a single snapshot:

```bash
python3 collect_snapshots.py --once
```

Or via API:

```bash
curl -X POST http://localhost:5000/api/hip3/collect-snapshots
```

## View OI Trends

Once you've collected multiple snapshots over time:

```bash
# Get OI trends for all XYZ markets
curl http://localhost:5000/api/hip3/oi-trends

# Get OI trends for FLX markets
curl "http://localhost:5000/api/hip3/oi-trends?dex=flx"

# Get OI trends for last 6 hours
curl "http://localhost:5000/api/hip3/oi-trends?hours_back=6"
```

### Response Example

```json
{
  "dex": "xyz",
  "timeframe_hours": 24,
  "total_markets": 8,
  "markets": [
    {
      "coin": "xyz:XYZ100",
      "data_points": 144,
      "current_oi": 56809236.36,
      "min_oi": 52100000.00,
      "max_oi": 59200000.00,
      "avg_oi": 55500000.00,
      "oi_change_24h": 2100000.00,
      "oi_change_pct": 3.84,
      "snapshots": [...]
    }
  ]
}
```

## Data Window Disclaimers

All analytics endpoints now include actual data collection window:

```json
{
  "actual_data_hours": 2.5,
  "is_full_24h": false,
  "disclaimer": "Data from last 2.5 hours (not full 24h)",
  ...
}
```

**Until the system runs for 24+ hours, all "24h" metrics are partial!**

## Storage & Cleanup

### Database Table

Snapshots are stored in `market_snapshots` table in `xyz_trades.db`.

### Disk Usage

- ~200 bytes per snapshot
- 11 markets × 144 snapshots/day = ~300 KB/day
- 30 days = ~9 MB

### Cleanup Old Data

Clean up snapshots older than 30 days:

```python
from trade_database import TradeDatabase

db = TradeDatabase("xyz_trades.db")
deleted = db.cleanup_old_snapshots(days_to_keep=30)
print(f"Deleted {deleted} old snapshots")
```

## Monitoring

Check collection status:

```bash
# View recent log
tail -f snapshots.log

# Count snapshots in database
sqlite3 xyz_trades.db "SELECT COUNT(*) FROM market_snapshots"

# View latest snapshot timestamp
sqlite3 xyz_trades.db "SELECT datetime(MAX(timestamp), 'unixepoch') FROM market_snapshots"
```

## Troubleshooting

### No Snapshots Collected

**Issue**: `snapshots_stored: 0`

**Causes**:
- Server not running (`python3 server.py`)
- No active markets with volume > 0
- Database connection issue

### Collection Fails

**Issue**: 500 error or exception

**Check**:
1. Server is running: `curl http://localhost:5000/api/health`
2. Database is writable: Check file permissions on `xyz_trades.db`
3. API is reachable: Test manually with `curl -X POST http://localhost:5000/api/hip3/collect-snapshots`

### Gaps in Time Series

**Issue**: Missing data points in charts

**Cause**: Collector wasn't running continuously

**Solution**:
- Use continuous mode or cron
- Snapshots are timestamped, gaps are visible in analysis
- System works with partial data, just shows actual_data_hours

## Best Practices

1. **Start Early**: Begin collecting snapshots as soon as you deploy
2. **Continuous**: Use background process, not manual collection
3. **Monitor**: Check logs periodically to ensure collection is working
4. **Backup**: Periodically backup `xyz_trades.db` (contains all snapshots)
5. **Cleanup**: Run cleanup every month to prevent database bloat

## Future Enhancements

Potential improvements:
- Adaptive collection frequency (faster during high volatility)
- Snapshot compression for long-term storage
- Export to Parquet for analytics tools
- Alerting on OI changes > X%
- Integration with external monitoring (Grafana, etc.)
