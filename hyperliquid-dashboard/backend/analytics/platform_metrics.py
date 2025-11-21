"""
Platform-level Metrics for XYZ (HIP-3) Analytics
Calculates platform KPIs: fees, volume, OI, trades for all 16 assets
"""

from datetime import datetime, timedelta
from typing import Dict, List
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import HIP3Database


class PlatformMetrics:
    """Calculate platform-level metrics and KPIs"""

    def __init__(self, db: HIP3Database):
        self.db = db

    def get_platform_dashboard(self) -> Dict:
        """
        Get complete platform dashboard with all key metrics

        Returns metrics for:
        - Total platform (volume, fees, OI, trades)
        - Per-asset breakdown (all 16 XYZ assets)
        - Growth trends
        - User metrics
        """

        # Get overall platform metrics
        overview = self.db.get_platform_overview()

        # Get per-asset breakdown
        asset_summary = self.db.get_all_assets_summary()

        # Calculate growth trends
        growth = self._calculate_growth_trends()

        # User metrics
        user_metrics = self._get_user_metrics()

        return {
            'platform_overview': {
                'total_volume_24h': overview.get('total_volume', 0),
                'total_fees_24h': overview.get('total_fees', 0),
                'total_oi': overview.get('total_oi', 0),
                'avg_oi': overview.get('avg_oi', 0),
                'total_trades_24h': overview.get('total_trades', 0),
                'unique_traders_24h': overview.get('unique_traders', 0),
                'avg_trade_size': overview.get('avg_trade_size', 0),
                'active_markets': overview.get('active_markets', 0),
                'platform_revenue': overview.get('platform_revenue', 0),
            },
            'asset_breakdown': asset_summary,
            'growth_trends': growth,
            'user_metrics': user_metrics,
            'timestamp': datetime.now().isoformat()
        }

    def get_asset_detailed_metrics(self, coin: str) -> Dict:
        """
        Get detailed metrics for a specific asset

        Includes:
        - 24h volume
        - Fees collected
        - Number of trades
        - Average OI
        - Unique traders
        - Historical trends
        """

        # Current metrics (24h)
        metrics_24h = self.db.get_asset_metrics(coin, hours_back=24)

        # 7-day metrics for comparison
        metrics_7d = self.db.get_asset_metrics(coin, hours_back=168)

        # Historical snapshots
        snapshots = self.db.get_market_snapshots(coin, hours_back=168)

        # Calculate trends
        volume_trend = self._calculate_trend(snapshots, 'volume_24h')
        oi_trend = self._calculate_trend(snapshots, 'open_interest_usd')

        return {
            'coin': coin,
            'current_metrics': {
                'volume_24h': metrics_24h.get('volume', 0),
                'fees_collected_24h': metrics_24h.get('fees_collected', 0),
                'num_trades_24h': metrics_24h.get('num_trades', 0),
                'avg_oi': metrics_24h.get('avg_oi', 0),
                'current_oi': metrics_24h.get('current_oi', 0),
                'unique_traders_24h': metrics_24h.get('unique_traders', 0),
                'avg_trade_size': metrics_24h.get('avg_trade_size', 0),
            },
            'weekly_metrics': {
                'volume_7d': metrics_7d.get('volume', 0),
                'fees_collected_7d': metrics_7d.get('fees_collected', 0),
                'num_trades_7d': metrics_7d.get('num_trades', 0),
                'unique_traders_7d': metrics_7d.get('unique_traders', 0),
            },
            'trends': {
                'volume_trend': volume_trend,
                'oi_trend': oi_trend,
            },
            'historical_snapshots': snapshots[-24:] if len(snapshots) > 24 else snapshots,  # Last 24 data points
            'timestamp': datetime.now().isoformat()
        }

    def get_all_assets_comparison(self) -> Dict:
        """
        Compare all 16 XYZ assets side-by-side

        Returns ranked lists by:
        - Volume
        - Fees
        - OI
        - Number of trades
        - Growth rate
        """

        assets = self.db.get_all_assets_summary()

        # Sort by different metrics
        by_volume = sorted(assets, key=lambda x: x.get('volume', 0) or 0, reverse=True)
        by_fees = sorted(assets, key=lambda x: x.get('fees_collected', 0) or 0, reverse=True)
        by_oi = sorted(assets, key=lambda x: x.get('current_oi', 0) or 0, reverse=True)
        by_trades = sorted(assets, key=lambda x: x.get('num_trades', 0) or 0, reverse=True)

        # Calculate market share
        total_volume = sum(a.get('volume', 0) or 0 for a in assets)
        total_fees = sum(a.get('fees_collected', 0) or 0 for a in assets)
        total_oi = sum(a.get('current_oi', 0) or 0 for a in assets)

        for asset in assets:
            asset['volume_share'] = (asset.get('volume', 0) or 0) / total_volume * 100 if total_volume > 0 else 0
            asset['fee_share'] = (asset.get('fees_collected', 0) or 0) / total_fees * 100 if total_fees > 0 else 0
            asset['oi_share'] = (asset.get('current_oi', 0) or 0) / total_oi * 100 if total_oi > 0 else 0

        return {
            'rankings': {
                'by_volume': [{'coin': a['coin'], 'value': a.get('volume', 0), 'share': a.get('volume_share', 0)} for a in by_volume],
                'by_fees': [{'coin': a['coin'], 'value': a.get('fees_collected', 0), 'share': a.get('fee_share', 0)} for a in by_fees],
                'by_oi': [{'coin': a['coin'], 'value': a.get('current_oi', 0), 'share': a.get('oi_share', 0)} for a in by_oi],
                'by_trades': [{'coin': a['coin'], 'value': a.get('num_trades', 0)} for a in by_trades],
            },
            'totals': {
                'total_volume': total_volume,
                'total_fees': total_fees,
                'total_oi': total_oi,
                'total_trades': sum(a.get('num_trades', 0) or 0 for a in assets),
            },
            'assets': assets,
            'timestamp': datetime.now().isoformat()
        }

    def get_fee_breakdown(self) -> Dict:
        """
        Detailed fee analysis across all assets

        Returns:
        - Total fees collected
        - Per-asset fee breakdown
        - Fee rate analysis
        - Revenue projections
        """

        assets = self.db.get_all_assets_summary()

        total_fees_24h = sum(a.get('fees_collected', 0) or 0 for a in assets)
        total_volume_24h = sum(a.get('volume', 0) or 0 for a in assets)

        # Calculate effective fee rate
        avg_fee_rate = (total_fees_24h / total_volume_24h * 100) if total_volume_24h > 0 else 0

        # Project annual revenue (extrapolate 24h to year)
        projected_annual_revenue = total_fees_24h * 365

        # Per-asset fee analysis
        fee_details = []
        for asset in assets:
            volume = asset.get('volume', 0) or 0
            fees = asset.get('fees_collected', 0) or 0
            fee_rate = (fees / volume * 100) if volume > 0 else 0

            fee_details.append({
                'coin': asset['coin'],
                'fees_24h': fees,
                'volume_24h': volume,
                'fee_rate_pct': fee_rate,
                'fee_share': (fees / total_fees_24h * 100) if total_fees_24h > 0 else 0
            })

        # Sort by fees collected
        fee_details = sorted(fee_details, key=lambda x: x['fees_24h'], reverse=True)

        return {
            'summary': {
                'total_fees_24h': total_fees_24h,
                'total_volume_24h': total_volume_24h,
                'avg_fee_rate_pct': avg_fee_rate,
                'projected_annual_revenue': projected_annual_revenue,
                'projected_monthly_revenue': projected_annual_revenue / 12,
            },
            'by_asset': fee_details,
            'timestamp': datetime.now().isoformat()
        }

    def get_oi_analysis(self) -> Dict:
        """
        Open Interest analysis across all assets

        Returns:
        - Total OI
        - Per-asset OI breakdown
        - OI trends
        - OI concentration
        """

        assets = self.db.get_all_assets_summary()

        total_oi = sum(a.get('current_oi', 0) or 0 for a in assets)

        # OI breakdown
        oi_breakdown = []
        for asset in assets:
            oi = asset.get('current_oi', 0) or 0
            oi_breakdown.append({
                'coin': asset['coin'],
                'oi': oi,
                'oi_share': (oi / total_oi * 100) if total_oi > 0 else 0
            })

        # Sort by OI
        oi_breakdown = sorted(oi_breakdown, key=lambda x: x['oi'], reverse=True)

        # Calculate Herfindahl-Hirschman Index (concentration measure)
        hhi = sum((item['oi_share'] ** 2) for item in oi_breakdown)

        # Get historical OI trends
        oi_trends = {}
        for asset in assets[:5]:  # Top 5 assets
            snapshots = self.db.get_market_snapshots(asset['coin'], hours_back=168)
            if snapshots:
                oi_trends[asset['coin']] = [
                    {'timestamp': s['timestamp'], 'oi': s['open_interest_usd']}
                    for s in snapshots[-24:]  # Last 24 data points
                ]

        return {
            'summary': {
                'total_oi': total_oi,
                'avg_oi_per_asset': total_oi / len(assets) if assets else 0,
                'concentration_index': hhi,
                'concentration_level': 'High' if hhi > 2500 else 'Moderate' if hhi > 1500 else 'Low',
            },
            'by_asset': oi_breakdown,
            'trends': oi_trends,
            'timestamp': datetime.now().isoformat()
        }

    def get_trading_activity_analysis(self) -> Dict:
        """
        Trading activity patterns analysis

        Returns:
        - Trade count trends
        - Average trade sizes
        - Trading velocity
        - Peak trading times
        """

        assets = self.db.get_all_assets_summary()

        total_trades = sum(a.get('num_trades', 0) or 0 for a in assets)
        total_volume = sum(a.get('volume', 0) or 0 for a in assets)

        # Per-asset trading activity
        activity_breakdown = []
        for asset in assets:
            trades = asset.get('num_trades', 0) or 0
            volume = asset.get('volume', 0) or 0
            avg_size = asset.get('avg_trade_size', 0) or 0

            activity_breakdown.append({
                'coin': asset['coin'],
                'num_trades': trades,
                'trade_share': (trades / total_trades * 100) if total_trades > 0 else 0,
                'volume': volume,
                'avg_trade_size': avg_size,
            })

        # Sort by trade count
        activity_breakdown = sorted(activity_breakdown, key=lambda x: x['num_trades'], reverse=True)

        # Calculate trading velocity (trades per hour)
        trades_per_hour = total_trades / 24

        return {
            'summary': {
                'total_trades_24h': total_trades,
                'trades_per_hour': trades_per_hour,
                'avg_trade_size': total_volume / total_trades if total_trades > 0 else 0,
            },
            'by_asset': activity_breakdown,
            'timestamp': datetime.now().isoformat()
        }

    # ===== PRIVATE HELPER METHODS =====

    def _calculate_growth_trends(self) -> Dict:
        """Calculate 24h vs 7d growth trends"""
        # This would compare current metrics to past periods
        # Simplified for now
        return {
            'volume_growth_pct': 0,  # Would calculate from historical data
            'user_growth_pct': 0,
            'trade_growth_pct': 0,
            'oi_growth_pct': 0,
        }

    def _get_user_metrics(self) -> Dict:
        """Get user-related metrics"""
        overview = self.db.get_platform_overview()

        return {
            'dau': overview.get('unique_traders', 0),  # Daily Active Users
            'total_users': 0,  # Would need to count from user_cohorts table
            'new_users_today': 0,  # Would need to query today's new users
        }

    def _calculate_trend(self, snapshots: List[Dict], field: str) -> str:
        """Calculate trend direction from historical snapshots"""
        if len(snapshots) < 2:
            return 'flat'

        values = [s.get(field, 0) or 0 for s in snapshots if s.get(field) is not None]

        if len(values) < 2:
            return 'flat'

        # Simple trend: compare first half to second half
        mid = len(values) // 2
        first_half_avg = sum(values[:mid]) / mid if mid > 0 else 0
        second_half_avg = sum(values[mid:]) / (len(values) - mid) if (len(values) - mid) > 0 else 0

        if second_half_avg > first_half_avg * 1.05:
            return 'up'
        elif second_half_avg < first_half_avg * 0.95:
            return 'down'
        else:
            return 'flat'


# Example usage
if __name__ == "__main__":
    db = HIP3Database()
    metrics = PlatformMetrics(db)

    # Get platform dashboard
    dashboard = metrics.get_platform_dashboard()
    print("Platform Dashboard:")
    print(f"Total Volume 24h: ${dashboard['platform_overview']['total_volume_24h']:,.2f}")
    print(f"Total Fees 24h: ${dashboard['platform_overview']['total_fees_24h']:,.2f}")
    print(f"Total OI: ${dashboard['platform_overview']['total_oi']:,.2f}")
    print(f"DAU: {dashboard['platform_overview']['unique_traders_24h']}")

    # Get fee breakdown
    fees = metrics.get_fee_breakdown()
    print(f"\nFee Analysis:")
    print(f"Total Fees: ${fees['summary']['total_fees_24h']:,.2f}")
    print(f"Projected Annual Revenue: ${fees['summary']['projected_annual_revenue']:,.2f}")

    # Get OI analysis
    oi_analysis = metrics.get_oi_analysis()
    print(f"\nOI Analysis:")
    print(f"Total OI: ${oi_analysis['summary']['total_oi']:,.2f}")
    print(f"Concentration: {oi_analysis['summary']['concentration_level']}")
