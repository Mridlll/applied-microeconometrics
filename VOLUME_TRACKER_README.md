# 📊 Trade.XYZ Volume Tracker - Enhanced Edition

Track your personal trading volume relative to total trade.xyz (HIP-3 XYZ equity perpetuals) volume.

**Created by:** Melon Melon Head (melon@tradexyz.community)

## What It Does

### Short-Term Mode (Market Comparison)
✅ Shows your XYZ trading volume vs total market volume
✅ Calculates your market share percentage
✅ Breaks down by individual assets (NVDA, TSLA, XYZ100, etc.)
✅ Shows your rank (Top 1%, Top 5%, etc.)
✅ Works completely standalone (no server needed)

### Historical Mode (Airdrop Tracking) 🎁 NEW!
✅ All-time volume tracking (handles 10k fill limit)
✅ Monthly volume breakdown
✅ Trading consistency metrics (days active / total days)
✅ Airdrop eligibility tier estimate
✅ First trade & early adopter status
✅ Average daily volume calculation

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

### Short-Term Mode (Last 24 Hours)

Compare your recent volume to total market volume:

```bash
python3 xyz_volume_tracker.py YOUR_WALLET_ADDRESS
```

### Historical Mode (Airdrop Tracking) 🎁

Get all-time stats for airdrop eligibility:

```bash
python3 xyz_volume_tracker.py YOUR_WALLET_ADDRESS --historical
```

**Other aliases:** `--airdrop`, `--all-time`, `-h`

### Custom Timeframe

```bash
# Last 12 hours
python3 xyz_volume_tracker.py 0xYourAddress 12

# Last 7 days (168 hours)
python3 xyz_volume_tracker.py 0xYourAddress 168

# Last 30 days
python3 xyz_volume_tracker.py 0xYourAddress 720
```

## Output Examples

### Short-Term Output (Market Comparison)

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

### Historical Output (Airdrop Tracking) 🎁

```
================================================================================
🎁 TRADE.XYZ AIRDROP ELIGIBILITY TRACKER
================================================================================
Wallet:     0xYourAddress
Analysis:   All-time historical data
Timestamp:  2025-11-21 02:00:00 UTC
================================================================================

📊 ALL-TIME STATISTICS
--------------------------------------------------------------------------------
Total Volume:      $12.50M
Total Trades:      5,432
Avg Trade Size:    $2.30K
First Trade:       2024-10-15
Last Trade:        2025-11-21

🎯 TRADING CONSISTENCY (Critical for Airdrops)
--------------------------------------------------------------------------------
Days Active:       85 days
Total Period:      128 days
Consistency:       66.41% (active days / total days)
Avg Daily Volume:  $147.06K
Rating:            🌟 EXCELLENT - Very active trader

📅 MONTHLY VOLUME BREAKDOWN
--------------------------------------------------------------------------------
Month        Volume               % of Total
--------------------------------------------------------------------------------
2025-11      $4.20M               33.60%
2025-10      $3.80M               30.40%
2024-12      $2.50M               20.00%
2024-11      $1.50M               12.00%
2024-10      $500.00K             4.00%

📋 ASSET BREAKDOWN
--------------------------------------------------------------------------------
Asset           Volume               Trades     % of Total
--------------------------------------------------------------------------------
xyz:XYZ100      $6.50M               2,890      52.00%
xyz:NVDA        $2.80M               1,234      22.40%
xyz:TSLA        $1.90M               876        15.20%
xyz:PLTR        $720.00K             298        5.76%
xyz:META        $590.00K             134        4.72%

🎁 AIRDROP ELIGIBILITY ESTIMATE
--------------------------------------------------------------------------------
Estimated Tier:    💎 TIER 2 - Power User (High Likelihood)

⚠️  NOTE: This is a rough estimate. Actual airdrop criteria are unknown.
    Consider: volume, consistency, early adoption, diversity of assets traded

================================================================================
✅ Historical analysis complete!
```

## How Historical Mode Works

**Problem:** Hyperliquid API returns max 10,000 fills per query

**Solution:** The tracker automatically:
1. Breaks queries into 7-day windows
2. Fetches data week-by-week from XYZ launch date (Oct 2024)
3. Aggregates all fills across all weeks
4. Calculates comprehensive historical metrics

**Example:** If you have 30,000 fills over 3 months, it will query in ~12 weekly chunks to get all your data.

```
🔍 Fetching historical data from 2024-10-01 to now...
📅 Querying 18 weekly windows (to handle 10k fill limit)...

⏳ Week 1/18: 2025-11-14 to 2025-11-21... ✓ 432 XYZ fills
⏳ Week 2/18: 2025-11-07 to 2025-11-14... ✓ 567 XYZ fills
⏳ Week 3/18: 2025-10-31 to 2025-11-07... ✓ 389 XYZ fills
...

✅ Fetched 5,432 total XYZ fills across 18 weeks
```

## Airdrop Tier Estimates

The tracker estimates your airdrop eligibility based on volume and consistency:

| Tier | Volume | Days Active | Likelihood |
|------|--------|-------------|------------|
| 🏆 Tier 1 | $10M+ | 60+ days | Very High |
| 💎 Tier 2 | $1M+ | 30+ days | High |
| ⭐ Tier 3 | $100K+ | 14+ days | Good |
| ✓ Tier 4 | $10K+ | 7+ days | Moderate |
| ○ Tier 5 | Any volume | Any | Low |

**Note:** These are estimates. Actual airdrop criteria are unknown and may consider additional factors.

## Airdrop Optimization Tips

Based on typical airdrop criteria:

1. **Volume:** Higher is better, but consistency matters more than one-time spikes
2. **Consistency:** Trade regularly (aim for 50%+ active days)
3. **Early Adoption:** First trade date matters (Oct-Nov 2024 = early)
4. **Asset Diversity:** Trade multiple XYZ markets, not just one
5. **Organic Activity:** Avoid wash trading patterns

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

### 1. Market Share Calculation (Short-Term)
Shows your exact percentage of total XYZ volume

### 2. Rank Badges (Short-Term)
- 🥇 Top 1% - Market share ≥ 1%
- 🥈 Top 5% - Market share ≥ 0.2%
- 🥉 Top 10% - Market share ≥ 0.1%
- 📊 Active Trader - Any volume

### 3. Asset Breakdown (Both Modes)
See which XYZ assets you trade most

### 4. Historical Aggregation (Historical Mode)
Fetches all your trades by querying in weekly chunks

### 5. Consistency Tracking (Historical Mode)
- Days active / Total days percentage
- Average daily volume
- Rating: Excellent, Good, Moderate, Low

### 6. Monthly Breakdown (Historical Mode)
See your volume trends month-by-month

### 7. Airdrop Tier Estimate (Historical Mode)
5-tier system based on volume + consistency

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
- For historical mode, ensure you traded after Oct 2024

### Historical mode takes too long

- Normal for active traders (1-2 minutes for 50+ weeks)
- Script queries week-by-week with 0.5s delays
- Progress is shown for each week
- Cannot be sped up due to API rate limits

## Advanced Usage

### Run as executable

```bash
chmod +x xyz_volume_tracker.py
./xyz_volume_tracker.py 0xYourAddress --historical
```

### Save output to file

```bash
python3 xyz_volume_tracker.py 0xYourAddress --historical > airdrop_stats.txt
```

### Schedule regular checks (cron)

```bash
# Check 24h stats every hour
0 * * * * python3 /path/to/xyz_volume_tracker.py 0xYourAddress >> tracker.log 2>&1

# Run historical analysis weekly (Sundays at 2am)
0 2 * * 0 python3 /path/to/xyz_volume_tracker.py 0xYourAddress --historical >> airdrop.log 2>&1
```

### Batch check multiple wallets

```bash
#!/bin/bash
for wallet in wallet1.txt wallet2.txt wallet3.txt; do
  addr=$(cat $wallet)
  echo "Checking $addr..."
  python3 xyz_volume_tracker.py $addr --historical > "airdrop_${addr}.txt"
done
```

## Technical Details

### Data Sources

- User fills: Hyperliquid `/info` endpoint (`userFillsByTime`)
- Market volumes: Hyperliquid `/info` endpoint (`metaAndAssetCtxs`)
- API URL: https://api.hyperliquid.xyz/info

### Limitations

- Maximum 10,000 fills per API query (handled by chunking in historical mode)
- Only tracks XYZ markets (not other HIP-3 deployers)
- Requires internet connection
- Subject to Hyperliquid API rate limits
- Historical mode: 0.5s delay between weekly queries (~30s for 60 weeks)

### Calculation Methods

**Market Share:**
```python
user_volume = sum(price * abs(size) for fill in user_fills if coin.startswith("xyz:"))
market_volume = sum(dayNtlVlm for market in xyz_markets)
market_share = (user_volume / market_volume) * 100
```

**Trading Consistency:**
```python
days_active = count(unique_dates_with_trades)
total_days = (last_trade_date - first_trade_date).days
consistency = (days_active / total_days) * 100
```

**Airdrop Tier:**
```python
if volume >= $10M and days_active >= 60: tier = 1  # Whale
elif volume >= $1M and days_active >= 30: tier = 2  # Power User
elif volume >= $100K and days_active >= 14: tier = 3  # Active
elif volume >= $10K and days_active >= 7: tier = 4  # Regular
else: tier = 5  # Small
```

## Use Cases

### For Traders
- Track short-term performance vs market
- Compare activity against other traders
- Identify most active markets

### For Airdrop Farmers 🎁
- **Estimate airdrop eligibility**
- **Track consistency over time**
- **Optimize trading strategy**
- **Monitor monthly volume trends**
- **Verify early adopter status**

### For Researchers
- Analyze market participation
- Study volume distribution
- Track individual trading patterns

## Support

Issues or questions?
- Check the code (it's simple and readable)
- Verify your wallet address format
- Test with a known active trading wallet first
- Contact: melon@tradexyz.community

## License

MIT License - Free to use, modify, and distribute. No warranty provided.

---

**Disclaimer:** This tool is for informational purposes only. Airdrop estimates are speculative. Not financial advice.
