"""
HIP-3 XYZ Markets Advanced Analytics
Comprehensive tracking of trade.xyz equity perpetuals with detailed metrics
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from collections import defaultdict
import statistics


class HIP3Analytics:
    """Advanced analytics specifically for HIP-3 XYZ markets"""

    def __init__(self, use_testnet: bool = False):
        self.base_url = (
            "https://api.hyperliquid-testnet.xyz" if use_testnet
            else "https://api.hyperliquid.xyz"
        )
        self.info_url = f"{self.base_url}/info"

        # XYZ equity perps (HIP-3 markets)
        self.xyz_assets = [
            "xyz:XYZ100", "xyz:NVDA", "xyz:AAPL", "xyz:AMZN", "xyz:COIN",
            "xyz:GOLD", "xyz:GOOGL", "xyz:HOOD", "xyz:INTC", "xyz:META",
            "xyz:MSFT", "xyz:ORCL", "xyz:PLTR", "xyz:TSLA"
        ]

        # Real fee structure from Hyperliquid
        self.TAKER_FEE = 0.00045  # 0.045%
        self.MAKER_REBATE = 0.00015  # 0.015%

    def _post_request(self, data: Dict) -> Dict:
        """Make POST request to API"""
        try:
            response = requests.post(
                self.info_url,
                headers={"Content-Type": "application/json"},
                json=data,
                timeout=15
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return {}

    def get_recent_trades(self, coin: str, limit: int = 5000) -> List[Dict]:
        """Get recent trades for a specific XYZ asset"""
        result = self._post_request({
            "type": "trades",
            "coin": coin
        })
        if isinstance(result, list):
            return result[:limit]
        return []

    def analyze_xyz_platform_metrics(self, hours_back: int = 24) -> Dict:
        """
        Comprehensive HIP-3 platform analytics
        Returns total volume, fees, unique wallets, and advanced metrics
        """
        cutoff_time = (datetime.now() - timedelta(hours=hours_back)).timestamp() * 1000

        total_volume = 0
        total_taker_fees = 0
        total_maker_rebates = 0
        unique_wallets: Set[str] = set()
        all_trades = []
        asset_volumes = {}

        print(f"Analyzing HIP-3 markets for last {hours_back} hours...")

        # Collect trades from all XYZ assets
        for asset in self.xyz_assets:
            try:
                trades = self.get_recent_trades(asset, limit=5000)
                recent_trades = [t for t in trades if t.get("time", 0) >= cutoff_time]

                asset_volume = 0
                for trade in recent_trades:
                    price = float(trade.get("px", 0))
                    size = abs(float(trade.get("sz", 0)))
                    volume = price * size

                    total_volume += volume
                    asset_volume += volume
                    all_trades.append({**trade, "coin": asset})

                    # Track unique wallets
                    users = trade.get("users", [])
                    for user in users:
                        if user and user != "0x0000000000000000000000000000000000000000":
                            unique_wallets.add(user.lower())

                    # Calculate fees (assume 70% taker, 30% maker)
                    taker_vol = volume * 0.7
                    maker_vol = volume * 0.3
                    total_taker_fees += taker_vol * self.TAKER_FEE
                    total_maker_rebates += maker_vol * self.MAKER_REBATE

                asset_volumes[asset] = asset_volume
                print(f"  {asset}: {len(recent_trades)} trades, ${asset_volume:,.2f} volume")

            except Exception as e:
                print(f"Error analyzing {asset}: {e}")
                continue

        # Calculate net platform revenue
        platform_revenue = total_taker_fees - total_maker_rebates

        return {
            "timeframe_hours": hours_back,
            "total_volume": total_volume,
            "total_taker_fees": total_taker_fees,
            "total_maker_rebates": total_maker_rebates,
            "platform_revenue": platform_revenue,
            "unique_wallets": len(unique_wallets),
            "total_trades": len(all_trades),
            "asset_volumes": asset_volumes,
            "timestamp": datetime.now().isoformat()
        }

    def analyze_wallet_activity(self, hours_back: int = 24) -> Dict:
        """
        Advanced wallet analytics: frequency, size, duration
        """
        cutoff_time = (datetime.now() - timedelta(hours=hours_back)).timestamp() * 1000

        wallet_stats = defaultdict(lambda: {
            "trade_count": 0,
            "total_volume": 0,
            "assets_traded": set(),
            "timestamps": [],
            "trade_sizes": []
        })

        print(f"Analyzing wallet activity for {hours_back} hours...")

        # Collect all trades
        for asset in self.xyz_assets:
            try:
                trades = self.get_recent_trades(asset, limit=5000)
                recent_trades = [t for t in trades if t.get("time", 0) >= cutoff_time]

                for trade in recent_trades:
                    price = float(trade.get("px", 0))
                    size = abs(float(trade.get("sz", 0)))
                    volume = price * size
                    timestamp = trade.get("time", 0) / 1000  # Convert to seconds

                    users = trade.get("users", [])
                    for user in users:
                        if user and user != "0x0000000000000000000000000000000000000000":
                            wallet = user.lower()
                            wallet_stats[wallet]["trade_count"] += 1
                            wallet_stats[wallet]["total_volume"] += volume
                            wallet_stats[wallet]["assets_traded"].add(asset)
                            wallet_stats[wallet]["timestamps"].append(timestamp)
                            wallet_stats[wallet]["trade_sizes"].append(volume)

            except Exception as e:
                print(f"Error analyzing wallet activity for {asset}: {e}")
                continue

        # Calculate advanced metrics for each wallet
        wallet_analytics = []
        for wallet, stats in wallet_stats.items():
            if stats["trade_count"] == 0:
                continue

            # Average trade size
            avg_trade_size = stats["total_volume"] / stats["trade_count"]

            # Trade frequency (trades per hour)
            timestamps = sorted(stats["timestamps"])
            if len(timestamps) > 1:
                time_span_hours = (timestamps[-1] - timestamps[0]) / 3600
                frequency = stats["trade_count"] / max(time_span_hours, 1)
            else:
                frequency = 0

            # Average duration between trades (in minutes)
            if len(timestamps) > 1:
                intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
                avg_duration = statistics.mean(intervals) / 60  # Convert to minutes
            else:
                avg_duration = 0

            # Median trade size
            median_trade_size = statistics.median(stats["trade_sizes"]) if stats["trade_sizes"] else 0

            wallet_analytics.append({
                "wallet": wallet,
                "trade_count": stats["trade_count"],
                "total_volume": stats["total_volume"],
                "avg_trade_size": avg_trade_size,
                "median_trade_size": median_trade_size,
                "assets_traded": len(stats["assets_traded"]),
                "frequency_per_hour": frequency,
                "avg_duration_minutes": avg_duration
            })

        # Sort by volume descending
        wallet_analytics.sort(key=lambda x: x["total_volume"], reverse=True)

        # Calculate platform-wide averages
        if wallet_analytics:
            platform_avg_trade_size = statistics.mean([w["avg_trade_size"] for w in wallet_analytics])
            platform_avg_frequency = statistics.mean([w["frequency_per_hour"] for w in wallet_analytics])
            platform_avg_duration = statistics.mean([w["avg_duration_minutes"] for w in wallet_analytics if w["avg_duration_minutes"] > 0])
        else:
            platform_avg_trade_size = 0
            platform_avg_frequency = 0
            platform_avg_duration = 0

        return {
            "timeframe_hours": hours_back,
            "total_unique_wallets": len(wallet_analytics),
            "top_wallets": wallet_analytics[:50],  # Top 50
            "platform_averages": {
                "avg_trade_size": platform_avg_trade_size,
                "avg_frequency_per_hour": platform_avg_frequency,
                "avg_duration_minutes": platform_avg_duration
            },
            "timestamp": datetime.now().isoformat()
        }

    def analyze_xyz_asset_breakdown(self, hours_back: int = 24) -> List[Dict]:
        """
        Detailed breakdown for each XYZ asset
        """
        cutoff_time = (datetime.now() - timedelta(hours=hours_back)).timestamp() * 1000

        asset_analytics = []

        for asset in self.xyz_assets:
            try:
                trades = self.get_recent_trades(asset, limit=5000)
                recent_trades = [t for t in trades if t.get("time", 0) >= cutoff_time]

                if not recent_trades:
                    continue

                total_volume = 0
                unique_wallets = set()
                trade_sizes = []
                buy_volume = 0
                sell_volume = 0

                for trade in recent_trades:
                    price = float(trade.get("px", 0))
                    size = abs(float(trade.get("sz", 0)))
                    volume = price * size

                    total_volume += volume
                    trade_sizes.append(volume)

                    # Track buy/sell volume
                    side = trade.get("side", "")
                    if side == "B":
                        buy_volume += volume
                    else:
                        sell_volume += volume

                    # Track unique wallets
                    users = trade.get("users", [])
                    for user in users:
                        if user and user != "0x0000000000000000000000000000000000000000":
                            unique_wallets.add(user.lower())

                # Calculate metrics
                avg_trade_size = total_volume / len(recent_trades) if recent_trades else 0
                median_trade_size = statistics.median(trade_sizes) if trade_sizes else 0

                # Calculate fees
                taker_vol = total_volume * 0.7
                maker_vol = total_volume * 0.3
                fees_paid = (taker_vol * self.TAKER_FEE) - (maker_vol * self.MAKER_REBATE)

                asset_analytics.append({
                    "asset": asset,
                    "total_volume": total_volume,
                    "total_trades": len(recent_trades),
                    "unique_wallets": len(unique_wallets),
                    "avg_trade_size": avg_trade_size,
                    "median_trade_size": median_trade_size,
                    "buy_volume": buy_volume,
                    "sell_volume": sell_volume,
                    "buy_sell_ratio": buy_volume / sell_volume if sell_volume > 0 else 0,
                    "fees_paid": fees_paid
                })

            except Exception as e:
                print(f"Error analyzing {asset}: {e}")
                continue

        # Sort by volume descending
        asset_analytics.sort(key=lambda x: x["total_volume"], reverse=True)

        return asset_analytics

    def get_comprehensive_hip3_analytics(self, hours_back: int = 24) -> Dict:
        """
        Get all HIP-3 analytics in one comprehensive report
        """
        print(f"\n=== Generating Comprehensive HIP-3 Analytics ({hours_back}h) ===\n")

        platform_metrics = self.analyze_xyz_platform_metrics(hours_back)
        wallet_activity = self.analyze_wallet_activity(hours_back)
        asset_breakdown = self.analyze_xyz_asset_breakdown(hours_back)

        return {
            "timeframe_hours": hours_back,
            "platform_metrics": platform_metrics,
            "wallet_activity": wallet_activity,
            "asset_breakdown": asset_breakdown,
            "timestamp": datetime.now().isoformat()
        }


def main():
    """Test HIP-3 analytics"""
    print("Testing HIP-3 XYZ Markets Analytics...\n")

    analytics = HIP3Analytics(use_testnet=False)

    # Get 24h comprehensive analytics
    results = analytics.get_comprehensive_hip3_analytics(hours_back=24)

    print("\n=== Platform Metrics ===")
    pm = results["platform_metrics"]
    print(f"Total Volume (24h): ${pm['total_volume']:,.2f}")
    print(f"Platform Revenue: ${pm['platform_revenue']:,.2f}")
    print(f"Taker Fees Collected: ${pm['total_taker_fees']:,.2f}")
    print(f"Maker Rebates Paid: ${pm['total_maker_rebates']:,.2f}")
    print(f"Unique Wallets: {pm['unique_wallets']}")
    print(f"Total Trades: {pm['total_trades']}")

    print("\n=== Platform Averages ===")
    pa = results["wallet_activity"]["platform_averages"]
    print(f"Avg Trade Size: ${pa['avg_trade_size']:,.2f}")
    print(f"Avg Frequency: {pa['avg_frequency_per_hour']:.2f} trades/hour")
    print(f"Avg Duration Between Trades: {pa['avg_duration_minutes']:.1f} minutes")

    print("\n=== Top XYZ Assets by Volume ===")
    for asset in results["asset_breakdown"][:5]:
        print(f"{asset['asset']:15} ${asset['total_volume']:>12,.2f}  "
              f"{asset['total_trades']:>6} trades  "
              f"{asset['unique_wallets']:>4} wallets")


if __name__ == "__main__":
    main()
