"""
Analytics Module for Hyperliquid Dashboard
Tracks and analyzes platform activity over time
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict


class PlatformAnalytics:
    """Handles platform-wide analytics and historical tracking"""

    def __init__(self, data_dir: str = "../data"):
        self.data_dir = data_dir
        self.history_file = os.path.join(data_dir, "platform_history.json")
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist"""
        os.makedirs(self.data_dir, exist_ok=True)

    def _load_history(self) -> List[Dict]:
        """Load historical data"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading history: {e}")
                return []
        return []

    def _save_history(self, history: List[Dict]):
        """Save historical data"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")

    def record_snapshot(self, market_data: Dict):
        """Record a snapshot of current market state"""
        history = self._load_history()

        # Calculate aggregates from current market data
        assets = market_data.get("assets", [])

        total_volume_24h = sum(asset.get("day_ntl_vlm", 0) for asset in assets)
        total_open_interest = sum(asset.get("open_interest", 0) for asset in assets)
        avg_funding = (
            sum(asset.get("funding_rate", 0) for asset in assets) / len(assets)
            if assets else 0
        )

        # Create snapshot
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "total_volume_24h": total_volume_24h,
            "total_open_interest": total_open_interest,
            "total_assets": len(assets),
            "avg_funding_rate": avg_funding,
            "active_assets": len([a for a in assets if a.get("day_ntl_vlm", 0) > 0])
        }

        history.append(snapshot)

        # Keep only last 90 days of hourly data
        cutoff = (datetime.now() - timedelta(days=90)).isoformat()
        history = [h for h in history if h["timestamp"] > cutoff]

        self._save_history(history)

        return snapshot

    def get_cumulative_stats(self) -> Dict:
        """Calculate cumulative statistics"""
        history = self._load_history()

        if not history:
            return {
                "cumulative_volume": 0,
                "cumulative_data_points": len(history),
                "first_recorded": None,
                "days_tracked": 0
            }

        # Calculate cumulative volume (approximation)
        # Note: This is a rough estimate based on 24h rolling volumes
        total_volume = sum(h.get("total_volume_24h", 0) for h in history)

        first_date = datetime.fromisoformat(history[0]["timestamp"])
        last_date = datetime.fromisoformat(history[-1]["timestamp"])
        days_tracked = (last_date - first_date).days

        return {
            "cumulative_volume": total_volume,
            "cumulative_data_points": len(history),
            "first_recorded": history[0]["timestamp"],
            "last_recorded": history[-1]["timestamp"],
            "days_tracked": days_tracked,
            "latest_snapshot": history[-1] if history else None
        }

    def get_time_series(self, metric: str = "total_volume_24h",
                        days: int = 30) -> List[Dict]:
        """Get time series data for a specific metric"""
        history = self._load_history()

        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        filtered = [h for h in history if h["timestamp"] > cutoff]

        return [
            {
                "timestamp": h["timestamp"],
                "value": h.get(metric, 0)
            }
            for h in filtered
        ]

    def get_growth_metrics(self) -> Dict:
        """Calculate growth metrics"""
        history = self._load_history()

        if len(history) < 2:
            return {
                "volume_growth_7d": 0,
                "volume_growth_30d": 0,
                "oi_growth_7d": 0,
                "oi_growth_30d": 0
            }

        now = datetime.now()

        # Get snapshots from 7 and 30 days ago
        seven_days_ago = (now - timedelta(days=7)).isoformat()
        thirty_days_ago = (now - timedelta(days=30)).isoformat()

        recent_7d = [h for h in history if h["timestamp"] >= seven_days_ago]
        recent_30d = [h for h in history if h["timestamp"] >= thirty_days_ago]

        latest = history[-1]

        def calculate_growth(old_val, new_val):
            if old_val == 0:
                return 0
            return ((new_val - old_val) / old_val) * 100

        # Calculate growth rates
        volume_growth_7d = 0
        oi_growth_7d = 0
        if len(recent_7d) > 1:
            volume_growth_7d = calculate_growth(
                recent_7d[0].get("total_volume_24h", 0),
                latest.get("total_volume_24h", 0)
            )
            oi_growth_7d = calculate_growth(
                recent_7d[0].get("total_open_interest", 0),
                latest.get("total_open_interest", 0)
            )

        volume_growth_30d = 0
        oi_growth_30d = 0
        if len(recent_30d) > 1:
            volume_growth_30d = calculate_growth(
                recent_30d[0].get("total_volume_24h", 0),
                latest.get("total_volume_24h", 0)
            )
            oi_growth_30d = calculate_growth(
                recent_30d[0].get("total_open_interest", 0),
                latest.get("total_open_interest", 0)
            )

        return {
            "volume_growth_7d": volume_growth_7d,
            "volume_growth_30d": volume_growth_30d,
            "oi_growth_7d": oi_growth_7d,
            "oi_growth_30d": oi_growth_30d,
            "data_points_7d": len(recent_7d),
            "data_points_30d": len(recent_30d)
        }

    def estimate_platform_metrics(self, market_data: Dict) -> Dict:
        """
        Estimate platform-wide metrics based on market data
        Note: These are estimates as we don't have access to actual user counts
        """
        assets = market_data.get("assets", [])

        total_volume_24h = sum(asset.get("day_ntl_vlm", 0) for asset in assets)
        total_open_interest = sum(asset.get("open_interest", 0) for asset in assets)

        # Rough estimates based on volume and OI
        # Assume average trade size of $5000 and avg user trades 10x per day
        estimated_daily_trades = int(total_volume_24h / 5000) if total_volume_24h > 0 else 0
        estimated_active_users = int(estimated_daily_trades / 10) if estimated_daily_trades > 0 else 0

        # Assume 20% of OI represents unique users (very rough)
        estimated_total_users = int(total_open_interest / 10000) if total_open_interest > 0 else 0

        return {
            "estimated_daily_trades": estimated_daily_trades,
            "estimated_active_users_24h": estimated_active_users,
            "estimated_total_users": max(estimated_total_users, estimated_active_users),
            "total_volume_24h": total_volume_24h,
            "total_open_interest": total_open_interest,
            "note": "User metrics are rough estimates based on volume and OI"
        }

    def get_dashboard_analytics(self, market_data: Dict) -> Dict:
        """Get comprehensive analytics for dashboard"""
        # Record current snapshot
        self.record_snapshot(market_data)

        # Get various metrics
        cumulative = self.get_cumulative_stats()
        growth = self.get_growth_metrics()
        platform_metrics = self.estimate_platform_metrics(market_data)

        # Get time series for charts
        volume_series = self.get_time_series("total_volume_24h", days=30)
        oi_series = self.get_time_series("total_open_interest", days=30)

        return {
            "cumulative_stats": cumulative,
            "growth_metrics": growth,
            "platform_metrics": platform_metrics,
            "time_series": {
                "volume_30d": volume_series,
                "open_interest_30d": oi_series
            },
            "timestamp": datetime.now().isoformat()
        }
