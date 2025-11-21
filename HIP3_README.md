# 📊 Hyperliquid HIP-3 Tools

Community tools and analytics for Hyperliquid HIP-3 markets (equity perpetuals).

**Created by:** Melon Melon Head (melon@tradexyz.community)

## About HIP-3

HIP-3 is Hyperliquid's framework for permissionless perpetual contract deployment. Anyone can deploy new perpetual markets for stocks, commodities, indices, and more.

**Popular HIP-3 Deployers:**
- **trade.xyz** - Equity perpetuals (TSLA, NVDA, XYZ100, etc.)
- **flex** - Alternative assets
- **vntl** - Venture markets

## Tools in This Repository

### 📈 XYZ Volume Tracker

Track your personal trading volume on trade.xyz markets and see how you rank against other traders.

**Features:**
- ✅ Compare your volume vs total XYZ market volume
- ✅ Calculate your market share percentage
- ✅ Get ranked (Top 1%, Top 5%, Top 10%)
- ✅ Asset-by-asset breakdown
- ✅ 100% standalone - no server needed
- ✅ Privacy-focused - runs locally on your machine

**Quick Start:**

```bash
# Install requirements
pip3 install requests

# Run the tracker
python3 xyz_volume_tracker.py YOUR_WALLET_ADDRESS

# Example
python3 xyz_volume_tracker.py 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
```

**Full Documentation:** [VOLUME_TRACKER_README.md](./VOLUME_TRACKER_README.md)

## Requirements

- Python 3.6 or higher
- `requests` library

```bash
pip3 install requests
```

## Example Output

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

✅ Analysis complete!
```

## Privacy & Security

- ✅ 100% open source - review the code yourself
- ✅ Runs entirely on your local machine
- ✅ No data sent to third parties
- ✅ Only queries public Hyperliquid API endpoints
- ✅ No tracking or analytics

## Supported Markets

The volume tracker currently supports all trade.xyz (XYZ) equity perpetuals:

- **Indices:** xyz:XYZ100 (Nasdaq 100)
- **Tech:** xyz:TSLA, xyz:NVDA, xyz:MSFT, xyz:GOOGL, xyz:AMZN, xyz:AAPL, xyz:META
- **Semiconductors:** xyz:AMD, xyz:MU, xyz:INTC
- **Finance:** xyz:COIN, xyz:HOOD
- **Other:** xyz:PLTR, xyz:ORCL, xyz:GOLD

## Use Cases

### For Traders
- Track your trading performance
- Compare your activity against market averages
- Identify which XYZ markets you're most active in
- Discover new XYZ markets you haven't tried

### For Researchers
- Analyze market participation
- Study volume distribution
- Track market concentration
- Monitor market share trends over time

### For Developers
- Use as a template for HIP-3 analytics tools
- Example of working with Hyperliquid API
- Clean, readable Python code

## Advanced Usage

### Custom Timeframes

```bash
# Last 12 hours
python3 xyz_volume_tracker.py 0xYourAddress 12

# Last 7 days (168 hours)
python3 xyz_volume_tracker.py 0xYourAddress 168
```

### Schedule Regular Checks

```bash
# Check every hour (cron)
0 * * * * cd /path/to/repo && python3 xyz_volume_tracker.py 0xYourAddress >> tracker.log 2>&1
```

### Save Output

```bash
python3 xyz_volume_tracker.py 0xYourAddress > my_stats.txt
```

## Technical Details

### Data Sources

All data comes from Hyperliquid's public API:
- **User fills:** `/info` endpoint with `userFillsByTime` query
- **Market volumes:** `/info` endpoint with `metaAndAssetCtxs` query
- **API URL:** https://api.hyperliquid.xyz/info

### Limitations

- Maximum 10,000 fills per query (Hyperliquid API limit)
- Only tracks XYZ markets (not other HIP-3 deployers yet)
- Requires internet connection
- Subject to Hyperliquid API rate limits

### How Market Share is Calculated

```python
user_volume = sum(price * abs(size) for fill in user_fills if coin.startswith("xyz:"))
market_volume = sum(dayNtlVlm for market in xyz_markets)
market_share = (user_volume / market_volume) * 100
```

## Troubleshooting

### Module Not Found

```bash
# Install dependencies
pip3 install requests
```

### Invalid Wallet Address

Ensure your address:
- Starts with `0x`
- Is exactly 42 characters long
- Contains only hexadecimal characters (0-9, a-f, A-F)

### API Timeout

- Check your internet connection
- Try again in a few minutes
- Hyperliquid API may be experiencing high load

### No Data Returned

- Verify wallet address is correct
- Check if you've traded XYZ markets recently
- Try a longer timeframe (e.g., 48 hours, 7 days)

## Future Tools

Planned additions to this repository:
- Cross-deployer volume tracker (XYZ, FLX, VNTL)
- PnL calculator for HIP-3 trades
- Funding rate analytics
- Open interest tracker
- Market maker metrics

## Contributing

Contributions welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests
- Share your analytics scripts

## License

MIT License - Free to use, modify, and distribute.

## Support

- **Issues:** Open an issue on GitHub
- **Contact:** melon@tradexyz.community
- **Discord:** Join the Hyperliquid community

## Acknowledgments

- Hyperliquid team for the excellent API
- trade.xyz team for pioneering HIP-3 equity perpetuals
- The Hyperliquid community for feedback and testing

---

**Disclaimer:** This tool is for informational purposes only. Not financial advice. Trade responsibly.
