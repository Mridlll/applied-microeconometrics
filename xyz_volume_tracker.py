#!/usr/bin/env python3
"""
Trade.XYZ Volume Tracker - Enhanced with Historical & Airdrop Features
Track your personal trading volume relative to total trade.xyz volume

Author: Melon Melon Head
Contact: melon@tradexyz.community

Usage:
    # Short-term (last 24 hours)
    python3 xyz_volume_tracker.py <YOUR_WALLET_ADDRESS>

    # Historical all-time analysis (for airdrops)
    python3 xyz_volume_tracker.py <YOUR_WALLET_ADDRESS> --historical

    # Custom timeframe
    python3 xyz_volume_tracker.py <YOUR_WALLET_ADDRESS> 168  # 7 days

Requirements:
    pip install requests
"""

import sys
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import os

# Hyperliquid API endpoints
API_URL = "https://api.hyperliquid.xyz/info"

# XYZ markets (all known equity perpetuals)
XYZ_MARKETS = [
    "xyz:XYZ100", "xyz:TSLA", "xyz:NVDA", "xyz:PLTR", "xyz:META",
    "xyz:MSFT", "xyz:GOOGL", "xyz:AMZN", "xyz:AAPL", "xyz:COIN",
    "xyz:GOLD", "xyz:HOOD", "xyz:INTC", "xyz:ORCL", "xyz:AMD", "xyz:MU"
]

# XYZ markets launch date (approximate - trade.xyz launched around this time)
XYZ_LAUNCH_DATE = datetime(2024, 10, 1)

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

def get_user_fills_window(wallet_address: str, start_time: int, end_time: int) -> Optional[List[Dict]]:
    """Get user's trade fills for a specific time window"""
    try:
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

def get_user_fills(wallet_address: str, hours_back: int = 24) -> Optional[List[Dict]]:
    """Get user's trade fills from Hyperliquid (simple mode)"""
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(hours=hours_back)).timestamp() * 1000)
    return get_user_fills_window(wallet_address, start_time, end_time)

def get_historical_fills(wallet_address: str, start_date: Optional[datetime] = None) -> List[Dict]:
    """
    Get all historical fills by querying in chunks
    Handles the 10k fill limit by breaking into weekly windows
    """
    if start_date is None:
        start_date = XYZ_LAUNCH_DATE

    all_fills = []
    current_time = datetime.now()

    # Calculate total weeks to query
    total_days = (current_time - start_date).days
    total_weeks = (total_days // 7) + 1

    print(f"\n🔍 Fetching historical data from {start_date.strftime('%Y-%m-%d')} to now...")
    print(f"📅 Querying {total_weeks} weekly windows (to handle 10k fill limit)...\n")

    # Query in 7-day chunks (working backwards from now)
    window_start = current_time
    week_num = 0

    while window_start > start_date:
        week_num += 1
        window_end = window_start
        window_start = max(window_start - timedelta(days=7), start_date)

        start_ms = int(window_start.timestamp() * 1000)
        end_ms = int(window_end.timestamp() * 1000)

        print(f"⏳ Week {week_num}/{total_weeks}: {window_start.strftime('%Y-%m-%d')} to {window_end.strftime('%Y-%m-%d')}...", end=" ")

        fills = get_user_fills_window(wallet_address, start_ms, end_ms)

        if fills is None:
            print("❌ Failed")
            continue

        # Filter for XYZ markets only
        xyz_fills = [f for f in fills if f.get("coin", "").startswith("xyz:")]
        all_fills.extend(xyz_fills)

        print(f"✓ {len(xyz_fills)} XYZ fills")

        # Rate limit protection
        time.sleep(0.5)

    print(f"\n✅ Fetched {len(all_fills)} total XYZ fills across {week_num} weeks")
    return all_fills

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

def calculate_airdrop_metrics(fills: List[Dict]) -> Dict:
    """Calculate airdrop-specific metrics"""
    if not fills:
        return {
            "total_volume": 0,
            "total_trades": 0,
            "days_active": 0,
            "months_active": 0,
            "total_days": 0,
            "consistency_pct": 0,
            "avg_daily_volume": 0,
            "monthly_breakdown": {},
            "daily_volumes": {},
            "first_trade": None,
            "last_trade": None
        }

    # Filter XYZ fills
    xyz_fills = [f for f in fills if f.get("coin", "").startswith("xyz:")]

    if not xyz_fills:
        return {
            "total_volume": 0,
            "total_trades": 0,
            "days_active": 0,
            "months_active": 0,
            "total_days": 0,
            "consistency_pct": 0,
            "avg_daily_volume": 0,
            "monthly_breakdown": {},
            "daily_volumes": {},
            "first_trade": None,
            "last_trade": None
        }

    # Calculate volumes
    total_volume = sum(float(f.get("px", 0)) * abs(float(f.get("sz", 0))) for f in xyz_fills)
    total_trades = len(xyz_fills)

    # Group by day and month
    daily_volumes = defaultdict(float)
    monthly_volumes = defaultdict(float)

    timestamps = []

    for fill in xyz_fills:
        ts_ms = fill.get("time", 0)
        if ts_ms == 0:
            continue

        timestamps.append(ts_ms)
        dt = datetime.fromtimestamp(ts_ms / 1000)
        date_key = dt.strftime("%Y-%m-%d")
        month_key = dt.strftime("%Y-%m")

        volume = float(fill.get("px", 0)) * abs(float(fill.get("sz", 0)))
        daily_volumes[date_key] += volume
        monthly_volumes[month_key] += volume

    # Calculate time range
    if timestamps:
        first_trade = datetime.fromtimestamp(min(timestamps) / 1000)
        last_trade = datetime.fromtimestamp(max(timestamps) / 1000)
        total_days = max((last_trade - first_trade).days, 1)
    else:
        first_trade = None
        last_trade = None
        total_days = 1

    days_active = len(daily_volumes)
    months_active = len(monthly_volumes)
    consistency_pct = (days_active / total_days * 100) if total_days > 0 else 0
    avg_daily_volume = total_volume / days_active if days_active > 0 else 0

    return {
        "total_volume": total_volume,
        "total_trades": total_trades,
        "days_active": days_active,
        "months_active": months_active,
        "total_days": total_days,
        "consistency_pct": consistency_pct,
        "avg_daily_volume": avg_daily_volume,
        "monthly_breakdown": dict(monthly_volumes),
        "daily_volumes": dict(daily_volumes),
        "first_trade": first_trade,
        "last_trade": last_trade
    }

def print_results(wallet: str, user_stats: Dict, market_volumes: Dict[str, float], hours: int):
    """Print formatted results (short-term mode)"""
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

        print(f"{asset:<15} {format_currency(user_vol):<20} {format_currency(market_vol):<20} {pct:.4f}%")

    print("="*80)

    # Show assets you didn't trade
    untraded = [asset for asset in market_volumes.keys() if asset not in user_stats["by_asset"]]
    if untraded:
        print(f"\n💡 Active XYZ markets you didn't trade: {', '.join(untraded)}")

    print("\n✅ Analysis complete!\n")

def print_airdrop_results(wallet: str, airdrop_metrics: Dict, user_stats: Dict):
    """Print formatted results for airdrop analysis"""
    print("\n" + "="*80)
    print(f"🎁 TRADE.XYZ AIRDROP ELIGIBILITY TRACKER")
    print("="*80)
    print(f"Wallet:     {wallet}")
    print(f"Analysis:   All-time historical data")
    print(f"Timestamp:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("="*80)

    if airdrop_metrics["total_trades"] == 0:
        print("\n❌ NO XYZ TRADES FOUND")
        print("\nYou have not traded any XYZ equity perpetuals.")
        return

    # Overall stats
    print("\n📊 ALL-TIME STATISTICS")
    print("-"*80)
    print(f"Total Volume:      {format_currency(airdrop_metrics['total_volume'])}")
    print(f"Total Trades:      {airdrop_metrics['total_trades']:,}")
    print(f"Avg Trade Size:    {format_currency(airdrop_metrics['total_volume'] / airdrop_metrics['total_trades'])}")
    print(f"First Trade:       {airdrop_metrics['first_trade'].strftime('%Y-%m-%d') if airdrop_metrics['first_trade'] else 'N/A'}")
    print(f"Last Trade:        {airdrop_metrics['last_trade'].strftime('%Y-%m-%d') if airdrop_metrics['last_trade'] else 'N/A'}")

    # Consistency metrics (important for airdrops!)
    print("\n🎯 TRADING CONSISTENCY (Critical for Airdrops)")
    print("-"*80)
    print(f"Days Active:       {airdrop_metrics['days_active']:,} days")
    print(f"Total Period:      {airdrop_metrics['total_days']:,} days")
    print(f"Consistency:       {airdrop_metrics['consistency_pct']:.2f}% (active days / total days)")
    print(f"Avg Daily Volume:  {format_currency(airdrop_metrics['avg_daily_volume'])}")

    # Consistency rating
    consistency = airdrop_metrics['consistency_pct']
    if consistency >= 50:
        rating = "🌟 EXCELLENT - Very active trader"
    elif consistency >= 25:
        rating = "⭐ GOOD - Regular trader"
    elif consistency >= 10:
        rating = "✓ MODERATE - Occasional trader"
    else:
        rating = "○ LOW - Sporadic trading"
    print(f"Rating:            {rating}")

    # Monthly breakdown
    print("\n📅 MONTHLY VOLUME BREAKDOWN")
    print("-"*80)
    print(f"{'Month':<12} {'Volume':<20} {'% of Total':<15}")
    print("-"*80)

    sorted_months = sorted(airdrop_metrics['monthly_breakdown'].items(), reverse=True)
    for month, volume in sorted_months[:12]:  # Show last 12 months
        pct = (volume / airdrop_metrics['total_volume'] * 100) if airdrop_metrics['total_volume'] > 0 else 0
        print(f"{month:<12} {format_currency(volume):<20} {pct:.2f}%")

    if len(sorted_months) > 12:
        print(f"... and {len(sorted_months) - 12} more months")

    # Asset breakdown
    print("\n📋 ASSET BREAKDOWN")
    print("-"*80)
    print(f"{'Asset':<15} {'Volume':<20} {'Trades':<10} {'% of Total':<12}")
    print("-"*80)

    sorted_assets = sorted(
        user_stats["by_asset"].items(),
        key=lambda x: x[1]["volume"],
        reverse=True
    )

    for asset, stats in sorted_assets:
        pct = (stats["volume"] / airdrop_metrics["total_volume"] * 100) if airdrop_metrics["total_volume"] > 0 else 0
        print(f"{asset:<15} {format_currency(stats['volume']):<20} {stats['trades']:<10} {pct:.2f}%")

    # Airdrop eligibility estimate
    print("\n🎁 AIRDROP ELIGIBILITY ESTIMATE")
    print("-"*80)

    # Volume tiers (these are estimates - actual criteria unknown)
    volume = airdrop_metrics['total_volume']
    days_active = airdrop_metrics['days_active']

    if volume >= 10_000_000 and days_active >= 60:
        tier = "🏆 TIER 1 - Whale (Very High Likelihood)"
    elif volume >= 1_000_000 and days_active >= 30:
        tier = "💎 TIER 2 - Power User (High Likelihood)"
    elif volume >= 100_000 and days_active >= 14:
        tier = "⭐ TIER 3 - Active Trader (Good Likelihood)"
    elif volume >= 10_000 and days_active >= 7:
        tier = "✓ TIER 4 - Regular Trader (Moderate Likelihood)"
    elif volume > 0:
        tier = "○ TIER 5 - Small Trader (Low Likelihood)"
    else:
        tier = "✗ NO ACTIVITY"

    print(f"Estimated Tier:    {tier}")
    print(f"\n⚠️  NOTE: This is a rough estimate. Actual airdrop criteria are unknown.")
    print(f"    Consider: volume, consistency, early adoption, diversity of assets traded")

    print("\n" + "="*80)
    print("✅ Historical analysis complete!\n")

def main():
    """Main function"""
    print("\n🔍 Trade.XYZ Volume Tracker (Enhanced)\n")

    # Check arguments
    if len(sys.argv) < 2:
        print("❌ Error: Wallet address required\n")
        print("Usage:")
        print(f"  # Short-term (last 24h)")
        print(f"  python3 {sys.argv[0]} <YOUR_WALLET_ADDRESS>\n")
        print(f"  # Historical all-time (for airdrops)")
        print(f"  python3 {sys.argv[0]} <YOUR_WALLET_ADDRESS> --historical\n")
        print(f"  # Custom timeframe")
        print(f"  python3 {sys.argv[0]} <YOUR_WALLET_ADDRESS> 168  # 7 days\n")
        print("Example:")
        print(f"  python3 {sys.argv[0]} 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb --historical\n")
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

    # Check for historical mode
    historical_mode = False
    hours_back = 24

    if len(sys.argv) > 2:
        if sys.argv[2] in ["--historical", "--airdrop", "--all-time", "-h"]:
            historical_mode = True
        else:
            try:
                hours_back = int(sys.argv[2])
            except ValueError:
                print(f"⚠️  Invalid hours value, using default: 24 hours")

    if historical_mode:
        # Historical mode for airdrop tracking
        print(f"Analyzing wallet: {wallet_address}")
        print(f"Mode: Historical all-time analysis")

        # Get all historical fills
        all_fills = get_historical_fills(wallet_address)

        # Calculate metrics
        airdrop_metrics = calculate_airdrop_metrics(all_fills)
        user_stats = calculate_user_volume(all_fills)

        # Print airdrop-focused results
        print_airdrop_results(wallet_address, airdrop_metrics, user_stats)

    else:
        # Standard short-term mode
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
