"""
Market-level Metrics: Oracle Tightness & Market Depth
Tracks mark vs oracle spread and orderbook liquidity
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import statistics
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import HIP3Database


class MarketMetrics:
    """Calculate oracle tightness and market depth metrics"""

    def __init__(self, db: HIP3Database):
        self.db = db

    # ===== ORACLE TIGHTNESS =====

    def calculate_oracle_tightness(self, coin: str, mark_price: float, oracle_price: float) -> Dict:
        """
        Calculate oracle tightness metrics

        Metrics:
        - Spread: absolute difference
        - Spread %: percentage difference
        - Premium: mark - oracle
        - Tightness Score: 0-100 (100 = perfect tracking)
        """

        if oracle_price == 0:
            return {
                'error': 'Invalid oracle price'
            }

        spread = abs(mark_price - oracle_price)
        spread_pct = (spread / oracle_price) * 100
        premium = mark_price - oracle_price
        premium_pct = (premium / oracle_price) * 100

        # Tightness score: inversely proportional to spread%
        # 0.01% spread = 99 score, 0.1% spread = 90 score, 1% spread = 50 score
        if spread_pct < 0.01:
            tightness_score = 100
        elif spread_pct < 0.1:
            tightness_score = 100 - (spread_pct * 100)
        elif spread_pct < 1:
            tightness_score = 90 - (spread_pct * 10)
        else:
            tightness_score = max(0, 50 - spread_pct)

        metrics = {
            'coin': coin,
            'mark_price': mark_price,
            'oracle_price': oracle_price,
            'spread': spread,
            'spread_pct': spread_pct,
            'premium': premium,
            'premium_pct': premium_pct,
            'tightness_score': tightness_score,
            'rating': self._get_tightness_rating(tightness_score),
            'timestamp': datetime.now().isoformat()
        }

        # Store in database
        self.db.store_oracle_metrics(coin, metrics)

        return metrics

    def get_oracle_spread_history(self, coin: str, hours_back: float = 24) -> Dict:
        """
        Get historical oracle spread data

        Returns:
        - Time series of spread
        - Statistics (min, max, avg, volatility)
        - Trend analysis
        """

        history = self.db.get_oracle_history(coin, hours_back)

        if not history:
            return {
                'coin': coin,
                'error': 'No historical data available'
            }

        spreads = [h['spread_pct'] for h in history]
        premiums = [h['premium'] for h in history]

        return {
            'coin': coin,
            'history': history,
            'statistics': {
                'current_spread_pct': spreads[-1] if spreads else 0,
                'avg_spread_pct': statistics.mean(spreads) if spreads else 0,
                'min_spread_pct': min(spreads) if spreads else 0,
                'max_spread_pct': max(spreads) if spreads else 0,
                'spread_volatility': statistics.stdev(spreads) if len(spreads) > 1 else 0,
                'avg_premium': statistics.mean(premiums) if premiums else 0,
                'premium_volatility': statistics.stdev(premiums) if len(premiums) > 1 else 0,
            },
            'trend': self._analyze_spread_trend(spreads),
            'hours_analyzed': hours_back,
            'data_points': len(history),
            'timestamp': datetime.now().isoformat()
        }

    def get_all_assets_oracle_health(self) -> Dict:
        """
        Get oracle health for all XYZ assets

        Returns dashboard view of oracle tightness across all markets
        """

        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Get latest oracle metrics for each asset
        cursor.execute("""
            SELECT coin,
                   mark_price,
                   oracle_price,
                   spread_pct,
                   tightness_score,
                   timestamp
            FROM oracle_metrics
            WHERE (coin, timestamp) IN (
                SELECT coin, MAX(timestamp)
                FROM oracle_metrics
                GROUP BY coin
            )
            ORDER BY tightness_score DESC
        """)

        assets = [dict(row) for row in cursor.fetchall()]

        # Calculate overall platform oracle health
        if assets:
            avg_tightness = statistics.mean([a['tightness_score'] for a in assets if a['tightness_score'] is not None])
            avg_spread = statistics.mean([a['spread_pct'] for a in assets])
        else:
            avg_tightness = 0
            avg_spread = 0

        return {
            'summary': {
                'avg_tightness_score': avg_tightness,
                'avg_spread_pct': avg_spread,
                'platform_oracle_health': self._get_tightness_rating(avg_tightness),
                'num_assets': len(assets),
            },
            'assets': assets,
            'timestamp': datetime.now().isoformat()
        }

    # ===== MARKET DEPTH =====

    def calculate_market_depth(self, coin: str, orderbook: Dict) -> Dict:
        """
        Calculate market depth metrics from orderbook data

        Metrics:
        - Bid/ask depth at 1%, 5% from mid
        - Spread in basis points
        - Depth imbalance ratio
        - Liquidity score
        """

        levels = orderbook.get('levels', [[[], []]])
        bids = levels[0][0] if levels and len(levels[0]) > 0 else []
        asks = levels[0][1] if levels and len(levels[0]) > 1 else []

        if not bids or not asks:
            return {
                'coin': coin,
                'error': 'No orderbook data available'
            }

        # Get best bid/ask
        best_bid = float(bids[0]['px']) if bids else 0
        best_ask = float(asks[0]['px']) if asks else 0

        if best_bid == 0 or best_ask == 0:
            return {
                'coin': coin,
                'error': 'Invalid orderbook prices'
            }

        mid_price = (best_bid + best_ask) / 2
        spread = best_ask - best_bid
        spread_bps = (spread / mid_price) * 10000  # Basis points

        # Calculate depth at various levels
        bid_depth_1pct = self._calculate_depth(bids, mid_price * 0.99, side='bid')
        bid_depth_5pct = self._calculate_depth(bids, mid_price * 0.95, side='bid')
        ask_depth_1pct = self._calculate_depth(asks, mid_price * 1.01, side='ask')
        ask_depth_5pct = self._calculate_depth(asks, mid_price * 1.05, side='ask')

        # Depth imbalance: ratio of bid to ask liquidity
        total_bid_depth = bid_depth_5pct
        total_ask_depth = ask_depth_5pct
        depth_imbalance = (total_bid_depth / total_ask_depth) if total_ask_depth > 0 else 0

        # Liquidity score (higher is better)
        liquidity_score = self._calculate_liquidity_score(
            bid_depth_1pct, ask_depth_1pct, spread_bps
        )

        metrics = {
            'coin': coin,
            'best_bid': best_bid,
            'best_ask': best_ask,
            'mid_price': mid_price,
            'spread': spread,
            'spread_bps': spread_bps,
            'bid_depth_1pct': bid_depth_1pct,
            'bid_depth_5pct': bid_depth_5pct,
            'ask_depth_1pct': ask_depth_1pct,
            'ask_depth_5pct': ask_depth_5pct,
            'depth_imbalance': depth_imbalance,
            'imbalance_direction': 'bid' if depth_imbalance > 1 else 'ask' if depth_imbalance < 1 else 'balanced',
            'liquidity_score': liquidity_score,
            'liquidity_rating': self._get_liquidity_rating(liquidity_score),
            'timestamp': datetime.now().isoformat()
        }

        # Store in database
        self.db.store_market_depth(coin, metrics)

        return metrics

    def get_depth_chart_data(self, coin: str, orderbook: Dict) -> Dict:
        """
        Format orderbook data for depth chart visualization

        Returns bid/ask levels formatted for charting
        """

        levels = orderbook.get('levels', [[[], []]])
        bids = levels[0][0] if levels and len(levels[0]) > 0 else []
        asks = levels[0][1] if levels and len(levels[0]) > 1 else []

        # Aggregate depth at each price level
        bid_depths = []
        ask_depths = []

        cumulative_bid = 0
        for bid in sorted(bids, key=lambda x: float(x['px']), reverse=True):
            price = float(bid['px'])
            size = float(bid['sz'])
            cumulative_bid += size
            bid_depths.append({
                'price': price,
                'depth': cumulative_bid,
                'size': size
            })

        cumulative_ask = 0
        for ask in sorted(asks, key=lambda x: float(x['px'])):
            price = float(ask['px'])
            size = float(ask['sz'])
            cumulative_ask += size
            ask_depths.append({
                'price': price,
                'depth': cumulative_ask,
                'size': size
            })

        return {
            'coin': coin,
            'bids': bid_depths[:50],  # Top 50 levels
            'asks': ask_depths[:50],
            'total_bid_liquidity': cumulative_bid,
            'total_ask_liquidity': cumulative_ask,
            'timestamp': datetime.now().isoformat()
        }

    def get_market_health_score(self, coin: str) -> Dict:
        """
        Calculate overall market health score

        Combines:
        - Oracle tightness
        - Market depth
        - Spread quality
        - Liquidity

        Returns 0-100 health score
        """

        # Get latest oracle metrics
        oracle_history = self.db.get_oracle_history(coin, hours_back=1)
        oracle_score = oracle_history[0]['tightness_score'] if oracle_history else 50

        # Get latest depth metrics
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM market_depth
            WHERE coin = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (coin,))

        depth_row = cursor.fetchone()

        if depth_row:
            depth_data = dict(depth_row)
            spread_bps = depth_data['spread_bps']
            liquidity_score = self._calculate_liquidity_score(
                depth_data['bid_depth_1pct'],
                depth_data['ask_depth_1pct'],
                spread_bps
            )
        else:
            spread_bps = 0
            liquidity_score = 50

        # Combined health score (weighted average)
        health_score = (oracle_score * 0.4) + (liquidity_score * 0.6)

        return {
            'coin': coin,
            'health_score': health_score,
            'health_rating': self._get_health_rating(health_score),
            'components': {
                'oracle_tightness': oracle_score,
                'liquidity': liquidity_score,
                'spread_bps': spread_bps,
            },
            'timestamp': datetime.now().isoformat()
        }

    # ===== PRIVATE HELPER METHODS =====

    def _get_tightness_rating(self, score: float) -> str:
        """Get rating label for tightness score"""
        if score >= 95:
            return 'Excellent'
        elif score >= 85:
            return 'Good'
        elif score >= 70:
            return 'Fair'
        else:
            return 'Poor'

    def _analyze_spread_trend(self, spreads: List[float]) -> str:
        """Analyze trend in spread over time"""
        if len(spreads) < 2:
            return 'insufficient_data'

        # Compare recent vs earlier spreads
        mid = len(spreads) // 2
        early_avg = statistics.mean(spreads[:mid])
        recent_avg = statistics.mean(spreads[mid:])

        if recent_avg < early_avg * 0.9:
            return 'improving'  # Spread narrowing
        elif recent_avg > early_avg * 1.1:
            return 'degrading'  # Spread widening
        else:
            return 'stable'

    def _calculate_depth(self, orders: List[Dict], price_threshold: float, side: str) -> float:
        """Calculate total liquidity up to price threshold"""
        total_depth = 0

        for order in orders:
            price = float(order['px'])
            size = float(order['sz'])

            if side == 'bid' and price >= price_threshold:
                total_depth += size
            elif side == 'ask' and price <= price_threshold:
                total_depth += size

        return total_depth

    def _calculate_liquidity_score(self, bid_depth: float, ask_depth: float, spread_bps: float) -> float:
        """
        Calculate liquidity score (0-100)

        Higher depth and lower spread = higher score
        """

        # Average depth at 1%
        avg_depth = (bid_depth + ask_depth) / 2

        # Depth score (0-50): more depth = higher score
        if avg_depth > 100:
            depth_score = 50
        elif avg_depth > 50:
            depth_score = 40
        elif avg_depth > 10:
            depth_score = 30
        elif avg_depth > 1:
            depth_score = 20
        else:
            depth_score = 10

        # Spread score (0-50): tighter spread = higher score
        if spread_bps < 5:
            spread_score = 50
        elif spread_bps < 10:
            spread_score = 40
        elif spread_bps < 20:
            spread_score = 30
        elif spread_bps < 50:
            spread_score = 20
        else:
            spread_score = 10

        return depth_score + spread_score

    def _get_liquidity_rating(self, score: float) -> str:
        """Get rating label for liquidity score"""
        if score >= 80:
            return 'Excellent'
        elif score >= 60:
            return 'Good'
        elif score >= 40:
            return 'Fair'
        else:
            return 'Poor'

    def _get_health_rating(self, score: float) -> str:
        """Get rating label for overall health score"""
        if score >= 90:
            return '💚 Excellent'
        elif score >= 75:
            return '💚 Good'
        elif score >= 60:
            return '💛 Fair'
        elif score >= 40:
            return '🟠 Poor'
        else:
            return '🔴 Critical'


# Example usage
if __name__ == "__main__":
    db = HIP3Database()
    metrics = MarketMetrics(db)

    # Example: Calculate oracle tightness
    coin = "xyz:XYZ100"
    mark_price = 1000.50
    oracle_price = 1000.45

    oracle_metrics = metrics.calculate_oracle_tightness(coin, mark_price, oracle_price)
    print(f"Oracle Tightness for {coin}:")
    print(f"Spread: {oracle_metrics['spread_pct']:.4f}%")
    print(f"Tightness Score: {oracle_metrics['tightness_score']:.2f}/100")
    print(f"Rating: {oracle_metrics['rating']}")

    # Get oracle health for all assets
    oracle_health = metrics.get_all_assets_oracle_health()
    print(f"\nPlatform Oracle Health: {oracle_health['summary']['platform_oracle_health']}")
    print(f"Average Spread: {oracle_health['summary']['avg_spread_pct']:.4f}%")
