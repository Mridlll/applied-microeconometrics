"""
User Behavior Analytics for HIP-3 Platform
Cohort analysis, retention, and usage patterns
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import statistics
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import HIP3Database


class UserMetrics:
    """Analyze user behavior and engagement patterns"""

    def __init__(self, db: HIP3Database):
        self.db = db

    # ===== COHORT ANALYSIS =====

    def get_cohort_dashboard(self) -> Dict:
        """
        Get comprehensive cohort analysis dashboard

        Returns:
        - Cohort sizes by week
        - Retention rates
        - Average metrics per cohort
        - Cohort lifecycle analysis
        """

        cohort_data = self.db.get_cohort_analysis()
        cohorts = cohort_data.get('cohorts', [])

        # Calculate aggregate metrics
        total_users = sum(c['cohort_size'] for c in cohorts)
        avg_volume_per_user = statistics.mean([c['avg_volume'] for c in cohorts if c['avg_volume'] > 0]) if cohorts else 0
        avg_retention = statistics.mean([c['retention_rate'] for c in cohorts]) if cohorts else 0

        return {
            'summary': {
                'total_users': total_users,
                'num_cohorts': len(cohorts),
                'avg_volume_per_user': avg_volume_per_user,
                'avg_retention_rate': avg_retention,
            },
            'cohorts': cohorts,
            'timestamp': datetime.now().isoformat()
        }

    def get_retention_analysis(self, cohort_week: Optional[str] = None) -> Dict:
        """
        Detailed retention analysis

        Calculate D1, D7, D30 retention for cohorts
        """

        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Get users and their activity
        if cohort_week:
            cursor.execute("""
                SELECT user_address, first_trade_date, last_active_date
                FROM user_cohorts
                WHERE cohort_week = ?
            """, (cohort_week,))
        else:
            cursor.execute("""
                SELECT user_address, first_trade_date, last_active_date
                FROM user_cohorts
            """)

        users = [dict(row) for row in cursor.fetchall()]

        # Calculate retention rates
        retention_metrics = {
            'd1': 0,  # 1-day retention
            'd7': 0,  # 7-day retention
            'd30': 0,  # 30-day retention
        }

        if users:
            today = datetime.now()

            for user in users:
                first_date = datetime.strptime(user['first_trade_date'], "%Y-%m-%d")
                last_date = datetime.strptime(user['last_active_date'], "%Y-%m-%d") if user['last_active_date'] else first_date

                days_since_first = (today - first_date).days
                days_since_last = (today - last_date).days

                # D1: Active next day
                if days_since_first >= 1 and (last_date - first_date).days >= 1:
                    retention_metrics['d1'] += 1

                # D7: Active in first week
                if days_since_first >= 7 and (last_date - first_date).days >= 7:
                    retention_metrics['d7'] += 1

                # D30: Active in first month
                if days_since_first >= 30 and (last_date - first_date).days >= 30:
                    retention_metrics['d30'] += 1

            # Calculate percentages
            total = len(users)
            retention_metrics['d1'] = (retention_metrics['d1'] / total * 100) if total > 0 else 0
            retention_metrics['d7'] = (retention_metrics['d7'] / total * 100) if total > 0 else 0
            retention_metrics['d30'] = (retention_metrics['d30'] / total * 100) if total > 0 else 0

        return {
            'cohort_week': cohort_week or 'all',
            'total_users': len(users),
            'retention_rates': retention_metrics,
            'timestamp': datetime.now().isoformat()
        }

    # ===== USER SEGMENTATION =====

    def segment_users_by_activity(self) -> Dict:
        """
        Segment users into activity tiers

        Tiers:
        - Whales: Top 1% by volume
        - Power Users: Top 10% by volume
        - Regular Users: Top 50% by volume
        - Light Users: Bottom 50% by volume
        """

        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_address, total_volume, total_trades
            FROM user_cohorts
            WHERE total_volume > 0
            ORDER BY total_volume DESC
        """)

        users = [dict(row) for row in cursor.fetchall()]

        if not users:
            return {
                'error': 'No user data available'
            }

        total_users = len(users)

        # Define tier thresholds
        whales = users[:max(1, total_users // 100)]  # Top 1%
        power_users = users[:max(1, total_users // 10)]  # Top 10%
        regular_users = users[:max(1, total_users // 2)]  # Top 50%
        light_users = users[max(1, total_users // 2):]  # Bottom 50%

        def tier_stats(tier_users):
            if not tier_users:
                return {}
            return {
                'count': len(tier_users),
                'total_volume': sum(u['total_volume'] for u in tier_users),
                'avg_volume': statistics.mean([u['total_volume'] for u in tier_users]),
                'total_trades': sum(u['total_trades'] for u in tier_users),
                'avg_trades': statistics.mean([u['total_trades'] for u in tier_users]),
            }

        total_volume = sum(u['total_volume'] for u in users)

        return {
            'summary': {
                'total_users': total_users,
                'total_volume': total_volume,
            },
            'tiers': {
                'whales': {
                    **tier_stats(whales),
                    'volume_share': (sum(u['total_volume'] for u in whales) / total_volume * 100) if total_volume > 0 else 0
                },
                'power_users': {
                    **tier_stats(power_users),
                    'volume_share': (sum(u['total_volume'] for u in power_users) / total_volume * 100) if total_volume > 0 else 0
                },
                'regular_users': {
                    **tier_stats(regular_users),
                    'volume_share': (sum(u['total_volume'] for u in regular_users) / total_volume * 100) if total_volume > 0 else 0
                },
                'light_users': {
                    **tier_stats(light_users),
                    'volume_share': (sum(u['total_volume'] for u in light_users) / total_volume * 100) if total_volume > 0 else 0
                },
            },
            'timestamp': datetime.now().isoformat()
        }

    # ===== USAGE PATTERNS =====

    def get_trading_frequency_distribution(self) -> Dict:
        """
        Analyze how frequently users trade

        Categories:
        - Daily traders (trade most days)
        - Weekly traders (trade weekly)
        - Monthly traders (trade monthly)
        - Inactive (haven't traded recently)
        """

        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_address, days_active, last_active_date
            FROM user_cohorts
        """)

        users = [dict(row) for row in cursor.fetchall()]

        today = datetime.now()

        frequency_buckets = {
            'daily': 0,  # Active 20+ days/month
            'weekly': 0,  # Active 4-19 days/month
            'monthly': 0,  # Active 1-3 days/month
            'inactive': 0,  # No activity in 30 days
        }

        for user in users:
            if not user['last_active_date']:
                frequency_buckets['inactive'] += 1
                continue

            last_active = datetime.strptime(user['last_active_date'], "%Y-%m-%d")
            days_since_active = (today - last_active).days

            if days_since_active > 30:
                frequency_buckets['inactive'] += 1
            elif user['days_active'] >= 20:
                frequency_buckets['daily'] += 1
            elif user['days_active'] >= 4:
                frequency_buckets['weekly'] += 1
            else:
                frequency_buckets['monthly'] += 1

        total = len(users)

        return {
            'distribution': {
                'daily': {
                    'count': frequency_buckets['daily'],
                    'percentage': (frequency_buckets['daily'] / total * 100) if total > 0 else 0
                },
                'weekly': {
                    'count': frequency_buckets['weekly'],
                    'percentage': (frequency_buckets['weekly'] / total * 100) if total > 0 else 0
                },
                'monthly': {
                    'count': frequency_buckets['monthly'],
                    'percentage': (frequency_buckets['monthly'] / total * 100) if total > 0 else 0
                },
                'inactive': {
                    'count': frequency_buckets['inactive'],
                    'percentage': (frequency_buckets['inactive'] / total * 100) if total > 0 else 0
                },
            },
            'total_users': total,
            'timestamp': datetime.now().isoformat()
        }

    def get_asset_preference_patterns(self) -> Dict:
        """
        Analyze which assets users prefer to trade

        Returns:
        - Most popular assets
        - Asset co-trading patterns (users who trade X also trade Y)
        - Diversification metrics
        """

        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Get asset preferences
        cursor.execute("""
            SELECT favorite_asset, COUNT(*) as user_count
            FROM user_cohorts
            WHERE favorite_asset IS NOT NULL
            GROUP BY favorite_asset
            ORDER BY user_count DESC
        """)

        preferences = [dict(row) for row in cursor.fetchall()]

        # Get diversification (number of assets per user)
        cursor.execute("""
            SELECT user, COUNT(DISTINCT coin) as num_assets
            FROM trades
            WHERE coin LIKE 'xyz:%'
            GROUP BY user
        """)

        diversification = [dict(row) for row in cursor.fetchall()]
        avg_assets_per_user = statistics.mean([d['num_assets'] for d in diversification]) if diversification else 0

        return {
            'favorite_assets': preferences,
            'diversification': {
                'avg_assets_per_user': avg_assets_per_user,
                'users_trading_1_asset': sum(1 for d in diversification if d['num_assets'] == 1),
                'users_trading_multiple': sum(1 for d in diversification if d['num_assets'] > 1),
            },
            'timestamp': datetime.now().isoformat()
        }

    # ===== USER LIFECYCLE =====

    def get_user_lifecycle_analysis(self) -> Dict:
        """
        Analyze user lifecycle from first trade to current state

        Stages:
        - New (first week)
        - Active (trading regularly)
        - At Risk (decreasing activity)
        - Churned (inactive 30+ days)
        """

        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_address, first_trade_date, last_active_date, days_active, total_trades
            FROM user_cohorts
        """)

        users = [dict(row) for row in cursor.fetchall()]

        today = datetime.now()

        lifecycle_stages = {
            'new': [],
            'active': [],
            'at_risk': [],
            'churned': [],
        }

        for user in users:
            first_date = datetime.strptime(user['first_trade_date'], "%Y-%m-%d")
            last_date = datetime.strptime(user['last_active_date'], "%Y-%m-%d") if user['last_active_date'] else first_date

            days_since_first = (today - first_date).days
            days_since_last = (today - last_date).days

            if days_since_first <= 7:
                lifecycle_stages['new'].append(user)
            elif days_since_last > 30:
                lifecycle_stages['churned'].append(user)
            elif days_since_last > 7:
                lifecycle_stages['at_risk'].append(user)
            else:
                lifecycle_stages['active'].append(user)

        return {
            'stages': {
                'new': {
                    'count': len(lifecycle_stages['new']),
                    'percentage': len(lifecycle_stages['new']) / len(users) * 100 if users else 0
                },
                'active': {
                    'count': len(lifecycle_stages['active']),
                    'percentage': len(lifecycle_stages['active']) / len(users) * 100 if users else 0
                },
                'at_risk': {
                    'count': len(lifecycle_stages['at_risk']),
                    'percentage': len(lifecycle_stages['at_risk']) / len(users) * 100 if users else 0
                },
                'churned': {
                    'count': len(lifecycle_stages['churned']),
                    'percentage': len(lifecycle_stages['churned']) / len(users) * 100 if users else 0
                },
            },
            'total_users': len(users),
            'timestamp': datetime.now().isoformat()
        }

    # ===== TOP USERS LEADERBOARD =====

    def get_leaderboard(self, metric: str = 'volume', limit: int = 100) -> Dict:
        """
        Get top users leaderboard

        Metrics:
        - volume: Total trading volume
        - trades: Number of trades
        - fees: Total fees paid
        """

        conn = self.db.get_connection()
        cursor = conn.cursor()

        order_by = {
            'volume': 'total_volume',
            'trades': 'total_trades',
            'fees': 'total_fees_paid'
        }.get(metric, 'total_volume')

        cursor.execute(f"""
            SELECT user_address, total_volume, total_trades, total_fees_paid, days_active, cohort_week
            FROM user_cohorts
            WHERE total_volume > 0
            ORDER BY {order_by} DESC
            LIMIT ?
        """, (limit,))

        leaders = [dict(row) for row in cursor.fetchall()]

        # Add rank
        for i, leader in enumerate(leaders):
            leader['rank'] = i + 1

        return {
            'metric': metric,
            'leaderboard': leaders,
            'count': len(leaders),
            'timestamp': datetime.now().isoformat()
        }


# Example usage
if __name__ == "__main__":
    db = HIP3Database()
    metrics = UserMetrics(db)

    # Cohort analysis
    cohorts = metrics.get_cohort_dashboard()
    print(f"Total Users: {cohorts['summary']['total_users']}")
    print(f"Average Retention: {cohorts['summary']['avg_retention_rate']:.2f}%")

    # User segmentation
    segments = metrics.segment_users_by_activity()
    if 'tiers' in segments:
        print(f"\nWhales: {segments['tiers']['whales']['count']} users")
        print(f"Whale Volume Share: {segments['tiers']['whales']['volume_share']:.2f}%")

    # Trading frequency
    frequency = metrics.get_trading_frequency_distribution()
    print(f"\nDaily Traders: {frequency['distribution']['daily']['percentage']:.2f}%")
    print(f"Weekly Traders: {frequency['distribution']['weekly']['percentage']:.2f}%")
