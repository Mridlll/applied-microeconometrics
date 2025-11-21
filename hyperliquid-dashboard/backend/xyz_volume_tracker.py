#!/usr/bin/env python3
"""
Trade.XYZ Volume Tracker
Track your personal trading volume relative to total trade.xyz volume

Author: Melon Melon Head
Contact: melon@tradexyz.community

Usage:
    python3 xyz_volume_tracker.py <YOUR_WALLET_ADDRESS>
    python3 xyz_volume_tracker.py 0xYourAddressHere

Requirements:
    pip install requests
"""

import sys
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Hyperliquid API endpoints
API_URL = "https://api.hyperliquid.xyz/info"

# XYZ markets (all known equity perpetuals)
XYZ_MARKETS = [
    "xyz:XYZ100", "xyz:TSLA", "xyz:NVDA", "xyz:PLTR", "xyz:META",
    "xyz:MSFT", "xyz:GOOGL", "xyz:AMZN", "xyz:AAPL", "xyz:COIN",
    "xyz:GOLD", "xyz:HOOD", "xyz:INTC", "xyz:ORCL", "xyz:AMD", "xyz:MU"
]

def format_currency(amount: float) -> str:
    """Format number as currency"""
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.2f}B"
    elif amount >= 1_000_000:
        return f"${amount / 1_000_000:.2f}M"
    elif amount >= 1_000:
        return f"${amount / 1_000:.2f}K"
    else:
        return f"${amount:.2f}"

def validate_address(address: str) -> bool:
    """Validate Ethereum address format"""
    if not address:
        return False
    if not address.startswith("0x"):
        return False
    if len(address) != 42:
        return False
    try:
        int(address, 16)
        return True
    except ValueError:
        return False

def get_user_fills(wallet_address: str, hours_back: int = 24) -> Optional[List[Dict]]:
    """Get user's trade fills from Hyperliquid"""
    try:
        # Calculate time window
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(hours=hours_back)).timestamp() * 1000)

        # Query user fills by time
        payload = {
            "type": "userFillsByTime",
            "user": wallet_address,
            "startTime": start_time,
            "endTime": end_time
        }

        response = requests.post(API_URL, json=payload, timeout=30)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️  API Error: {response.status_code}")
            return None

    except requests.exceptions.Timeout:
        print("⚠️  Request timeout - Hyperliquid API is slow or unreachable")
        return None
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Network error: {e}")
        return None
    except Exception as e:
        print(f"⚠️  Unexpected error: {e}")
        return None

def get_xyz_market_volumes() -> Optional[Dict[str, float]]:
    """Get current 24h volume for all XYZ markets"""
    try:
        payload = {
            "type": "metaAndAssetCtxs",
            "dex": "xyz"
        }

        response = requests.post(API_URL, json=payload, timeout=30)

        if response.status_code != 200:
            print(f"⚠️  Failed to fetch XYZ market data: {response.status_code}")
            return None

        data = response.json()
        metadata = data[0] if len(data) > 0 else {}
        asset_ctxs = data[1] if len(data) > 1 else []

        universe = metadata.get("universe", [])

        volumes = {}
        for i, market in enumerate(universe):
            if i >= len(asset_ctxs):
                break

            coin_name = market.get("name", "")
            is_delisted = market.get("isDelisted", False)

            if not is_delisted:
                ctx = asset_ctxs[i]
                day_volume = float(ctx.get('dayNtlVlm') or 0)
                volumes[coin_name] = day_volume

        return volumes

    except Exception as e:
        print(f"⚠️  Error fetching XYZ volumes: {e}")
        return None

def calculate_user_volume(fills: List[Dict]) -> Dict[str, any]:
    """Calculate user's volume by asset"""
    volume_by_asset = {}
    total_volume = 0
    total_trades = 0

    for fill in fills:
        coin = fill.get("coin", "")

        # Only count XYZ markets
        if not coin.startswith("xyz:"):
            continue

        px = float(fill.get("px", 0))
        sz = abs(float(fill.get("sz", 0)))
        volume = px * sz

        if coin not in volume_by_asset:
            volume_by_asset[coin] = {"volume": 0, "trades": 0}

        volume_by_asset[coin]["volume"] += volume
        volume_by_asset[coin]["trades"] += 1
        total_volume += volume
        total_trades += 1

    return {
        "by_asset": volume_by_asset,
        "total_volume": total_volume,
        "total_trades": total_trades
    }

def print_results(wallet: str, user_stats: Dict, market_volumes: Dict[str, float], hours: int):
    """Print formatted results"""
    print("\n" + "="*80)
    print(f"📊 TRADE.XYZ VOLUME TRACKER")
    print("="*80)
    print(f"Wallet:     {wallet}")
    print(f"Timeframe:  Last {hours} hours")
    print(f"Timestamp:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("="*80)

    user_volume = user_stats["total_volume"]
    user_trades = user_stats["total_trades"]

    # Calculate total market volume
    total_market_volume = sum(market_volumes.values())

    if user_trades == 0:
        print("\n❌ NO XYZ TRADES FOUND")
        print(f"\nYou have not traded any XYZ equity perpetuals in the last {hours} hours.")
        print("\nTotal XYZ Market Volume (24h):", format_currency(total_market_volume))
        return

    # Calculate market share
    market_share_pct = (user_volume / total_market_volume * 100) if total_market_volume > 0 else 0

    print("\n📈 YOUR STATS")
    print("-"*80)
    print(f"Total Volume:      {format_currency(user_volume)}")
    print(f"Total Trades:      {user_trades:,}")
    print(f"Avg Trade Size:    {format_currency(user_volume / user_trades)}")

    print("\n🌍 MARKET COMPARISON")
    print("-"*80)
    print(f"Total XYZ Volume:  {format_currency(total_market_volume)}")
    print(f"Your Market Share: {market_share_pct:.4f}%")
    print(f"Your Rank:         {'🥇 Top 1%' if market_share_pct >= 1 else '🥈 Top 5%' if market_share_pct >= 0.2 else '🥉 Top 10%' if market_share_pct >= 0.1 else '📊 Active Trader'}")

    # Volume bar
    bar_width = 50
    filled = int(bar_width * min(market_share_pct / 100, 1))
    bar = "█" * filled + "░" * (bar_width - filled)
    print(f"\nVolume Share:      [{bar}] {market_share_pct:.4f}%")

    # Breakdown by asset
    print("\n📋 BREAKDOWN BY ASSET")
    print("-"*80)
    print(f"{'Asset':<15} {'Your Volume':<20} {'Market Volume':<20} {'Your %':<10}")
    print("-"*80)

    # Sort by user volume
    sorted_assets = sorted(
        user_stats["by_asset"].items(),
        key=lambda x: x[1]["volume"],
        reverse=True
    )

    for asset, stats in sorted_assets:
        user_vol = stats["volume"]
        market_vol = market_volumes.get(asset, 0)
        pct = (user_vol / market_vol * 100) if market_vol > 0 else 0

        print(f"{asset:<15} {format_currency(user_vol):<20} {format_currency(market_vol):<20} {pct:.3f}%")

    print("="*80)

    # Show assets you didn't trade
    untraded = [asset for asset in market_volumes.keys() if asset not in user_stats["by_asset"]]
    if untraded:
        print(f"\n💡 Active XYZ markets you didn't trade: {', '.join(untraded)}")

    print("\n✅ Analysis complete!\n")

def main():
    """Main function"""
    print("\n🔍 Trade.XYZ Volume Tracker\n")

    # Check arguments
    if len(sys.argv) < 2:
        print("❌ Error: Wallet address required\n")
        print("Usage:")
        print(f"  python3 {sys.argv[0]} <YOUR_WALLET_ADDRESS>\n")
        print("Example:")
        print(f"  python3 {sys.argv[0]} 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb\n")
        sys.exit(1)

    wallet_address = sys.argv[1].strip()

    # Validate address
    if not validate_address(wallet_address):
        print(f"❌ Error: Invalid wallet address format\n")
        print("Address must:")
        print("  - Start with '0x'")
        print("  - Be 42 characters long")
        print("  - Contain only hexadecimal characters\n")
        print(f"You provided: {wallet_address}\n")
        sys.exit(1)

    # Get timeframe (default 24 hours)
    hours_back = 24
    if len(sys.argv) > 2:
        try:
            hours_back = int(sys.argv[2])
        except ValueError:
            print(f"⚠️  Invalid hours value, using default: 24 hours")

    print(f"Analyzing wallet: {wallet_address}")
    print(f"Timeframe: Last {hours_back} hours")
    print("\nFetching data from Hyperliquid...\n")

    # Fetch user fills
    print("⏳ Getting your trade history...")
    fills = get_user_fills(wallet_address, hours_back)

    if fills is None:
        print("\n❌ Failed to fetch trade data. Please check:")
        print("  1. Your internet connection")
        print("  2. Wallet address is correct")
        print("  3. Hyperliquid API is accessible\n")
        sys.exit(1)

    # Fetch market volumes
    print("⏳ Getting XYZ market volumes...")
    market_volumes = get_xyz_market_volumes()

    if market_volumes is None:
        print("\n❌ Failed to fetch market data\n")
        sys.exit(1)

    # Calculate user stats
    print("⏳ Calculating your statistics...")
    user_stats = calculate_user_volume(fills)

    # Print results
    print_results(wallet_address, user_stats, market_volumes, hours_back)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
