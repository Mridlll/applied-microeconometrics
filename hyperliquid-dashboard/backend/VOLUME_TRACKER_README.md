# 📊 Trade.XYZ Volume Tracker

Track your personal trading volume relative to total trade.xyz (HIP-3 XYZ equity perpetuals) volume.

**Created by:** Melon Melon Head (melon@tradexyz.community)

## What It Does

✅ Shows your XYZ trading volume vs total market volume
✅ Calculates your market share percentage
✅ Breaks down by individual assets (NVDA, TSLA, XYZ100, etc.)
✅ Shows your rank (Top 1%, Top 5%, etc.)
✅ Works completely standalone (no server needed)

## Requirements

- Python 3.6 or higher
- `requests` library

### Install Requirements

```bash
pip install requests
```

Or if you have pip3:

```bash
pip3 install requests
```

## Usage

### Basic Usage (Last 24 Hours)

```bash
python3 xyz_volume_tracker.py YOUR_WALLET_ADDRESS
```

### Example

```bash
python3 xyz_volume_tracker.py 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
```

### Custom Timeframe

```bash
# Last 12 hours
python3 xyz_volume_tracker.py 0xYourAddress 12

# Last 7 days (168 hours)
python3 xyz_volume_tracker.py 0xYourAddress 168
```

## Output Example

```
================================================================================
📊 TRADE.XYZ VOLUME TRACKER
================================================================================
Wallet:     0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
Timeframe:  Last 24 hours
Timestamp:  2025-11-21 01:15:30 UTC
================================================================================

📈 YOUR STATS
--------------------------------------------------------------------------------
Total Volume:      $1.23M
Total Trades:      456
Avg Trade Size:    $2.70K

🌍 MARKET COMPARISON
--------------------------------------------------------------------------------
Total XYZ Volume:  $149.28M
Your Market Share: 0.8245%
Your Rank:         🥈 Top 5%

Volume Share:      [████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0.8245%

📋 BREAKDOWN BY ASSET
--------------------------------------------------------------------------------
Asset           Your Volume          Market Volume        Your %
--------------------------------------------------------------------------------
xyz:XYZ100      $850.50K             $148.35M             0.5732%
xyz:NVDA        $245.30K             $56.53M              0.4339%
xyz:TSLA        $89.20K              $23.40M              0.3812%
xyz:PLTR        $45.00K              $14.32M              0.3143%

💡 Active XYZ markets you didn't trade: xyz:META, xyz:GOOGL, xyz:AMZN

✅ Analysis complete!
```

## Error Handling

### Invalid Wallet Address

```
❌ Error: Invalid wallet address format

Address must:
  - Start with '0x'
  - Be 42 characters long
  - Contain only hexadecimal characters
```

### No Trades Found

```
❌ NO XYZ TRADES FOUND

You have not traded any XYZ equity perpetuals in the last 24 hours.

Total XYZ Market Volume (24h): $149.28M
```

### API Errors

The script handles:
- ✅ Network timeouts
- ✅ API unavailability
- ✅ Invalid responses
- ✅ Rate limiting
- ✅ Connection errors

## Features

### 1. Market Share Calculation
Shows your exact percentage of total XYZ volume

### 2. Rank Badges
- 🥇 Top 1% - Market share ≥ 1%
- 🥈 Top 5% - Market share ≥ 0.2%
- 🥉 Top 10% - Market share ≥ 0.1%
- 📊 Active Trader - Any volume

### 3. Asset Breakdown
See which XYZ assets you trade most

### 4. Suggestions
Shows active XYZ markets you haven't traded yet

## Tracked Markets

All XYZ equity perpetuals:
- xyz:XYZ100 (Nasdaq 100 index)
- xyz:TSLA (Tesla)
- xyz:NVDA (Nvidia)
- xyz:PLTR (Palantir)
- xyz:META (Meta/Facebook)
- xyz:MSFT (Microsoft)
- xyz:GOOGL (Google)
- xyz:AMZN (Amazon)
- xyz:AAPL (Apple)
- xyz:COIN (Coinbase)
- xyz:GOLD (Gold futures)
- xyz:HOOD (Robinhood)
- xyz:INTC (Intel)
- xyz:ORCL (Oracle)
- xyz:AMD (AMD)
- xyz:MU (Micron)

## Privacy

- ✅ Runs 100% locally on your machine
- ✅ Only queries Hyperliquid public API
- ✅ No data sent to third parties
- ✅ No tracking or analytics
- ✅ Open source (you can read the code)

## Troubleshooting

### "requests" module not found

```bash
pip3 install requests
```

### Permission denied

```bash
chmod +x xyz_volume_tracker.py
```

### API timeout

- Check your internet connection
- Try again in a few minutes
- Hyperliquid API may be experiencing high load

### No data returned

- Verify wallet address is correct
- Check if you've traded XYZ markets recently
- Try a longer timeframe (48 hours, 7 days)

## Advanced Usage

### Run as executable

```bash
chmod +x xyz_volume_tracker.py
./xyz_volume_tracker.py 0xYourAddress
```

### Save output to file

```bash
python3 xyz_volume_tracker.py 0xYourAddress > my_stats.txt
```

### Schedule regular checks (cron)

```bash
# Check every hour
0 * * * * python3 /path/to/xyz_volume_tracker.py 0xYourAddress >> tracker.log 2>&1
```

## Technical Details

### Data Sources

- User fills: Hyperliquid `/info` endpoint (`userFillsByTime`)
- Market volumes: Hyperliquid `/info` endpoint (`metaAndAssetCtxs`)
- Timeframe: Configurable (default 24 hours, max 10,000 fills)

### Limitations

- Maximum 10,000 fills per query (Hyperliquid API limit)
- Only tracks XYZ markets (not other HIP-3 deployers)
- Requires internet connection
- Subject to Hyperliquid API rate limits

### Calculation Method

```python
user_volume = sum(price * abs(size) for fill in user_fills if coin.startswith("xyz:"))
market_volume = sum(dayNtlVlm for market in xyz_markets)
market_share = (user_volume / market_volume) * 100
```

## Support

Issues or questions?
- Check the code (it's simple and readable)
- Verify your wallet address format
- Test with a known active trading wallet first

## License

Free to use, modify, and distribute. No warranty provided.
