"""
HIP-3 XYZ Markets Advanced Analytics using WebSocket Data
Real-time comprehensive tracking of trade.xyz equity perpetuals
"""

from datetime import datetime
from typing import Dict, List, Set
from collections import defaultdict
import statistics


class HIP3WebSocketAnalytics:
    """Advanced analytics for HIP-3 XYZ markets using WebSocket data"""

    def __init__(self, xyz_client):
        """
        Initialize with XYZMarketsClient instance
        xyz_client: XYZMarketsClient instance with WebSocket connection
        """
        self.xyz_client = xyz_client

        # Real fee structure from Hyperliquid
        self.TAKER_FEE = 0.00045  # 0.045%
        self.MAKER_REBATE = 0.00015  # 0.015%

    def get_platform_metrics(self, hours_back: float = 24) -> Dict:
        """
        Comprehensive HIP-3 platform analytics from WebSocket data
        Returns total volume, fees, unique wallets, and advanced metrics
        """
        seconds_back = int(hours_back * 3600)
        trades = self.xyz_client.get_trades_since(seconds_back)

        if not trades:
            return {
                "timeframe_hours": hours_back,
                "total_volume": 0,
                "total_taker_fees": 0,
                "total_maker_rebates": 0,
                "platform_revenue": 0,
                "unique_wallets": 0,
                "total_trades": 0,
                "assets_active": 0,
                "timestamp": datetime.now().isoformat()
            }

        total_volume = 0
        unique_wallets: Set[str] = set()
        assets_active: Set[str] = set()

        for trade in trades:
            price = float(trade.get("px", 0))
            size = abs(float(trade.get("sz", 0)))
            volume = price * size
            total_volume += volume

            # Track assets
            coin = trade.get("coin", "")
            if coin:
                assets_active.add(coin)

            # Track unique wallets
            users = trade.get("users", [])
            for user in users:
                if user and user != "0x0000000000000000000000000000000000000000":
                    unique_wallets.add(user.lower())

        # Calculate fees (assume 70% taker, 30% maker)
        taker_vol = total_volume * 0.7
        maker_vol = total_volume * 0.3
        total_taker_fees = taker_vol * self.TAKER_FEE
        total_maker_rebates = maker_vol * self.MAKER_REBATE
        platform_revenue = total_taker_fees - total_maker_rebates

        return {
            "timeframe_hours": hours_back,
            "total_volume": total_volume,
            "total_taker_fees": total_taker_fees,
            "total_maker_rebates": total_maker_rebates,
            "platform_revenue": platform_revenue,
            "unique_wallets": len(unique_wallets),
            "total_trades": len(trades),
            "assets_active": len(assets_active),
            "timestamp": datetime.now().isoformat()
        }

    def get_wallet_analytics(self, hours_back: float = 24) -> Dict:
        """
        Advanced wallet analytics: frequency, size, duration
        """
        seconds_back = int(hours_back * 3600)
        trades = self.xyz_client.get_trades_since(seconds_back)

        wallet_stats = defaultdict(lambda: {
            "trade_count": 0,
            "total_volume": 0,
            "assets_traded": set(),
            "timestamps": [],
            "trade_sizes": []
        })

        # Collect wallet statistics
        for trade in trades:
            price = float(trade.get("px", 0))
            size = abs(float(trade.get("sz", 0)))
            volume = price * size
            timestamp = trade.get("received_at", 0)
            coin = trade.get("coin", "")

            users = trade.get("users", [])
            for user in users:
                if user and user != "0x0000000000000000000000000000000000000000":
                    wallet = user.lower()
                    wallet_stats[wallet]["trade_count"] += 1
                    wallet_stats[wallet]["total_volume"] += volume
                    wallet_stats[wallet]["assets_traded"].add(coin)
                    wallet_stats[wallet]["timestamps"].append(timestamp)
                    wallet_stats[wallet]["trade_sizes"].append(volume)

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
                frequency = stats["trade_count"] / max(time_span_hours, 0.1)
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
                "wallet_short": f"{wallet[:6]}...{wallet[-4:]}",
                "trade_count": stats["trade_count"],
                "total_volume": stats["total_volume"],
                "avg_trade_size": avg_trade_size,
                "median_trade_size": median_trade_size,
                "assets_traded_count": len(stats["assets_traded"]),
                "frequency_per_hour": frequency,
                "avg_duration_minutes": avg_duration
            })

        # Sort by volume descending
        wallet_analytics.sort(key=lambda x: x["total_volume"], reverse=True)

        # Calculate platform-wide averages
        if wallet_analytics:
            platform_avg_trade_size = statistics.mean([w["avg_trade_size"] for w in wallet_analytics])
            platform_avg_frequency = statistics.mean([w["frequency_per_hour"] for w in wallet_analytics])
            active_durations = [w["avg_duration_minutes"] for w in wallet_analytics if w["avg_duration_minutes"] > 0]
            platform_avg_duration = statistics.mean(active_durations) if active_durations else 0
        else:
            platform_avg_trade_size = 0
            platform_avg_frequency = 0
            platform_avg_duration = 0

        return {
            "timeframe_hours": hours_back,
            "total_unique_wallets": len(wallet_analytics),
            "top_wallets": wallet_analytics[:100],  # Top 100
            "platform_averages": {
                "avg_trade_size": platform_avg_trade_size,
                "avg_frequency_per_hour": platform_avg_frequency,
                "avg_duration_minutes": platform_avg_duration
            },
            "timestamp": datetime.now().isoformat()
        }

    def get_asset_breakdown(self, hours_back: float = 24) -> List[Dict]:
        """
        Detailed breakdown for each XYZ asset
        """
        seconds_back = int(hours_back * 3600)
        trades = self.xyz_client.get_trades_since(seconds_back)

        asset_stats = defaultdict(lambda: {
            "total_volume": 0,
            "trade_count": 0,
            "unique_wallets": set(),
            "trade_sizes": [],
            "buy_volume": 0,
            "sell_volume": 0
        })

        # Collect asset statistics
        for trade in trades:
            coin = trade.get("coin", "")
            if not coin:
                continue

            price = float(trade.get("px", 0))
            size = abs(float(trade.get("sz", 0)))
            volume = price * size
            side = trade.get("side", "")

            asset_stats[coin]["total_volume"] += volume
            asset_stats[coin]["trade_count"] += 1
            asset_stats[coin]["trade_sizes"].append(volume)

            if side == "B":
                asset_stats[coin]["buy_volume"] += volume
            else:
                asset_stats[coin]["sell_volume"] += volume

            users = trade.get("users", [])
            for user in users:
                if user and user != "0x0000000000000000000000000000000000000000":
                    asset_stats[coin]["unique_wallets"].add(user.lower())

        # Calculate metrics for each asset
        asset_analytics = []
        for asset, stats in asset_stats.items():
            if stats["trade_count"] == 0:
                continue

            avg_trade_size = stats["total_volume"] / stats["trade_count"]
            median_trade_size = statistics.median(stats["trade_sizes"]) if stats["trade_sizes"] else 0

            # Calculate fees
            taker_vol = stats["total_volume"] * 0.7
            maker_vol = stats["total_volume"] * 0.3
            fees_paid = (taker_vol * self.TAKER_FEE) - (maker_vol * self.MAKER_REBATE)

            buy_sell_ratio = stats["buy_volume"] / stats["sell_volume"] if stats["sell_volume"] > 0 else 0

            asset_analytics.append({
                "asset": asset,
                "total_volume": stats["total_volume"],
                "total_trades": stats["trade_count"],
                "unique_wallets": len(stats["unique_wallets"]),
                "avg_trade_size": avg_trade_size,
                "median_trade_size": median_trade_size,
                "buy_volume": stats["buy_volume"],
                "sell_volume": stats["sell_volume"],
                "buy_sell_ratio": buy_sell_ratio,
                "fees_paid": fees_paid
            })

        # Sort by volume descending
        asset_analytics.sort(key=lambda x: x["total_volume"], reverse=True)

        return asset_analytics

    def get_comprehensive_analytics(self, hours_back: float = 24) -> Dict:
        """
        Get all HIP-3 analytics in one comprehensive report
        """
        platform_metrics = self.get_platform_metrics(hours_back)
        wallet_activity = self.get_wallet_analytics(hours_back)
        asset_breakdown = self.get_asset_breakdown(hours_back)

        return {
            "timeframe_hours": hours_back,
            "platform_metrics": platform_metrics,
            "wallet_activity": wallet_activity,
            "asset_breakdown": asset_breakdown,
            "data_collection_status": {
                "total_historical_trades": len(self.xyz_client.all_trades_history),
                "oldest_trade_age_seconds": platform_metrics.get("timeframe_hours", 0) * 3600,
                "websocket_connected": self.xyz_client.connected
            },
            "timestamp": datetime.now().isoformat()
        }
