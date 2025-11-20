"""
Leaderboard and Advanced Trading Analytics
Automatically tracks top traders, large trades, and platform-wide statistics
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import json


class LeaderboardAnalytics:
    """Advanced analytics for trader leaderboards and large trades"""

    def __init__(self, use_testnet: bool = False):
        self.base_url = (
            "https://api.hyperliquid-testnet.xyz" if use_testnet
            else "https://api.hyperliquid.xyz"
        )
        self.info_url = f"{self.base_url}/info"

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

    def get_recent_trades(self, coin: str, limit: int = 1000) -> List[Dict]:
        """Get recent trades for analysis"""
        result = self._post_request({
            "type": "trades",
            "coin": coin
        })
        if isinstance(result, list):
            return result[:limit]
        return []

    def analyze_large_trades(self, coin: str, threshold_usd: float = 100000) -> List[Dict]:
        """
        Find large/interesting trades above threshold
        Returns trades with size, direction, and potential market impact
        """
        trades = self.get_recent_trades(coin, limit=1000)
        large_trades = []

        for trade in trades:
            price = float(trade.get("px", 0))
            size = abs(float(trade.get("sz", 0)))
            value_usd = price * size

            if value_usd >= threshold_usd:
                large_trades.append({
                    "coin": coin,
                    "time": datetime.fromtimestamp(trade.get("time", 0) / 1000).isoformat(),
                    "price": price,
                    "size": size,
                    "value_usd": value_usd,
                    "side": "BUY" if trade.get("side") == "B" else "SELL",
                    "hash": trade.get("hash", "")
                })

        # Sort by value descending
        large_trades.sort(key=lambda x: x["value_usd"], reverse=True)
        return large_trades[:50]  # Top 50 large trades

    def calculate_average_trade_size(self, coin: str) -> Dict:
        """Calculate average trade size and distribution"""
        trades = self.get_recent_trades(coin, limit=1000)

        if not trades:
            return {
                "coin": coin,
                "avg_trade_size_usd": 0,
                "median_trade_size_usd": 0,
                "total_trades": 0,
                "small_trades_pct": 0,
                "medium_trades_pct": 0,
                "large_trades_pct": 0
            }

        trade_sizes = []
        for trade in trades:
            price = float(trade.get("px", 0))
            size = abs(float(trade.get("sz", 0)))
            value_usd = price * size
            trade_sizes.append(value_usd)

        avg_size = sum(trade_sizes) / len(trade_sizes)
        sorted_sizes = sorted(trade_sizes)
        median_size = sorted_sizes[len(sorted_sizes) // 2]

        # Categorize trades
        small = sum(1 for s in trade_sizes if s < 10000)  # < $10k
        medium = sum(1 for s in trade_sizes if 10000 <= s < 100000)  # $10k-$100k
        large = sum(1 for s in trade_sizes if s >= 100000)  # >= $100k

        return {
            "coin": coin,
            "avg_trade_size_usd": avg_size,
            "median_trade_size_usd": median_size,
            "total_trades": len(trades),
            "small_trades_pct": (small / len(trades) * 100),
            "medium_trades_pct": (medium / len(trades) * 100),
            "large_trades_pct": (large / len(trades) * 100)
        }

    def get_top_traders_by_volume(self, hours_back: int = 24, limit: int = 100) -> List[Dict]:
        """
        Get top traders by trading volume across all assets
        Note: This requires scanning recent trades and aggregating by user
        """
        # Get leaderboard data from Hyperliquid
        # This endpoint returns top traders by PnL
        leaderboard = self._post_request({
            "type": "leaderboard",
            "window": "day" if hours_back == 24 else "allTime"
        })

        if not leaderboard or not isinstance(leaderboard, list):
            return []

        top_traders = []
        for i, entry in enumerate(leaderboard[:limit]):
            trader_data = {
                "rank": i + 1,
                "user": entry.get("user", "Unknown"),
                "account_value": float(entry.get("accountValue", 0)),
                "pnl": float(entry.get("pnl", 0)),
                "pnl_pct": float(entry.get("pnlPct", 0)),
                "vlm": float(entry.get("vlm", 0)),  # Volume
                "n_trades": int(entry.get("nTrades", 0))
            }

            top_traders.append(trader_data)

        return top_traders

    def get_asset_specific_traders(self, coin: str, hours_back: int = 4) -> List[Dict]:
        """
        Get top traders for a specific asset by analyzing recent trades
        """
        trades = self.get_recent_trades(coin, limit=2000)

        cutoff_time = (datetime.now() - timedelta(hours=hours_back)).timestamp() * 1000
        recent_trades = [t for t in trades if t.get("time", 0) >= cutoff_time]

        # Aggregate by user (if user data available)
        # Note: Public trades API doesn't always include user addresses
        # This is a simplified version
        user_volumes = defaultdict(lambda: {"volume": 0, "trades": 0})

        for trade in recent_trades:
            # Try to extract user info from hash or other fields
            user_id = trade.get("user", "Anonymous")
            price = float(trade.get("px", 0))
            size = abs(float(trade.get("sz", 0)))

            user_volumes[user_id]["volume"] += price * size
            user_volumes[user_id]["trades"] += 1

        # Sort by volume
        sorted_traders = sorted(
            [{"user": k, "volume": v["volume"], "trades": v["trades"]}
             for k, v in user_volumes.items()],
            key=lambda x: x["volume"],
            reverse=True
        )

        return sorted_traders[:20]

    def get_platform_wide_analytics(self, top_assets: List[str]) -> Dict:
        """
        Get comprehensive platform analytics including:
        - Average trade sizes across markets
        - Large trade activity
        - Top traders leaderboard
        """
        # Calculate average trade sizes for top assets
        trade_size_analytics = []
        for coin in top_assets[:10]:  # Analyze top 10 assets
            try:
                stats = self.calculate_average_trade_size(coin)
                trade_size_analytics.append(stats)
            except Exception as e:
                print(f"Error analyzing {coin}: {e}")
                continue

        # Get top traders leaderboard
        top_traders_24h = self.get_top_traders_by_volume(hours_back=24, limit=100)

        # Find largest recent trades across all markets
        all_large_trades = []
        for coin in top_assets[:5]:  # Check top 5 markets
            try:
                large_trades = self.analyze_large_trades(coin, threshold_usd=50000)
                all_large_trades.extend(large_trades[:10])
            except Exception as e:
                print(f"Error finding large trades for {coin}: {e}")
                continue

        # Sort all large trades by value
        all_large_trades.sort(key=lambda x: x["value_usd"], reverse=True)

        return {
            "trade_size_analytics": trade_size_analytics,
            "top_traders": top_traders_24h[:50],  # Top 50 traders
            "largest_trades": all_large_trades[:20],  # Top 20 largest trades
            "timestamp": datetime.now().isoformat()
        }
