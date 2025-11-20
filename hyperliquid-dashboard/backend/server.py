"""
Flask server for Hyperliquid Dashboard
Serves real-time trading data via REST API
"""

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from hyperliquid_api import HyperliquidAPI
from analytics import PlatformAnalytics
from advanced_analytics import HyperliquidAdvancedAnalytics
import os
import json
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize API client and analytics
api = HyperliquidAPI(use_testnet=False)
analytics = PlatformAnalytics(data_dir=os.path.join(os.path.dirname(__file__), '..', 'data'))
advanced = HyperliquidAdvancedAnalytics(use_testnet=False)

# Cache for reducing API calls
cache = {
    "market_summary": {"data": None, "timestamp": None},
    "universe": {"data": None, "timestamp": None}
}

CACHE_DURATION = 10  # seconds


def is_cache_valid(cache_key: str) -> bool:
    """Check if cached data is still valid"""
    if cache[cache_key]["timestamp"] is None:
        return False
    elapsed = (datetime.now() - cache[cache_key]["timestamp"]).total_seconds()
    return elapsed < CACHE_DURATION


@app.route('/')
def index():
    """Serve the main dashboard page"""
    frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    return send_from_directory(frontend_path, 'index.html')


@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


@app.route('/api/market-summary')
def market_summary():
    """Get comprehensive market summary"""
    if not is_cache_valid("market_summary"):
        data = api.get_market_summary()
        cache["market_summary"]["data"] = data
        cache["market_summary"]["timestamp"] = datetime.now()

    return jsonify(cache["market_summary"]["data"])


@app.route('/api/universe')
def universe():
    """Get list of all tradable assets"""
    if not is_cache_valid("universe"):
        data = api.get_universe()
        cache["universe"]["data"] = data
        cache["universe"]["timestamp"] = datetime.now()

    return jsonify(cache["universe"]["data"])


@app.route('/api/asset/<coin>')
def asset_details(coin):
    """Get detailed information for a specific asset"""
    try:
        # Get current price and market data
        summary = api.get_market_summary()
        asset_data = next(
            (a for a in summary.get("assets", []) if a["name"] == coin),
            None
        )

        if not asset_data:
            return jsonify({"error": "Asset not found"}), 404

        # Get order book
        l2_book = api.get_l2_snapshot(coin)

        # Get recent trades
        trades = api.get_recent_trades(coin, limit=50)

        return jsonify({
            "asset": asset_data,
            "orderbook": l2_book,
            "recent_trades": trades
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/candles/<coin>/<interval>')
def candles(coin, interval):
    """Get candlestick data for charting"""
    try:
        valid_intervals = ["1m", "15m", "1h", "4h", "1d"]
        if interval not in valid_intervals:
            return jsonify({"error": "Invalid interval"}), 400

        data = api.get_candles(coin, interval)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/funding/<coin>')
def funding(coin):
    """Get funding rate history"""
    try:
        data = api.get_funding_history(coin)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/stats')
def market_stats():
    """Get aggregated market statistics"""
    try:
        summary = api.get_market_summary()
        assets = summary.get("assets", [])

        if not assets:
            return jsonify({"error": "No data available"}), 500

        # Calculate aggregate stats
        total_volume_24h = sum(a["day_ntl_vlm"] for a in assets)
        total_open_interest = sum(a["open_interest"] for a in assets)

        # Get top gainers and losers
        sorted_by_change = sorted(assets, key=lambda x: x["change_24h"], reverse=True)
        top_gainers = sorted_by_change[:5]
        top_losers = sorted_by_change[-5:]

        # Get highest volume
        sorted_by_volume = sorted(assets, key=lambda x: x["day_ntl_vlm"], reverse=True)
        top_by_volume = sorted_by_volume[:10]

        stats = {
            "timestamp": summary["timestamp"],
            "total_assets": len(assets),
            "total_volume_24h": total_volume_24h,
            "total_open_interest": total_open_interest,
            "top_gainers": top_gainers,
            "top_losers": top_losers,
            "top_by_volume": top_by_volume
        }

        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/analytics')
def get_analytics():
    """Get comprehensive platform analytics"""
    try:
        summary = api.get_market_summary()
        analytics_data = analytics.get_dashboard_analytics(summary)
        return jsonify(analytics_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/analytics/time-series/<metric>/<int:days>')
def get_time_series(metric, days):
    """Get time series data for a specific metric"""
    try:
        valid_metrics = ["total_volume_24h", "total_open_interest", "total_assets", "avg_funding_rate"]
        if metric not in valid_metrics:
            return jsonify({"error": "Invalid metric"}), 400

        data = analytics.get_time_series(metric, days)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/platform-metrics')
def platform_metrics():
    """Get real platform metrics with actual fee calculations"""
    try:
        summary = api.get_market_summary()
        metrics = advanced.get_real_platform_metrics(summary)
        return jsonify(metrics)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/granular/candles/<coin>/<interval>')
def get_granular_candles(coin, interval):
    """
    Get granular candlestick data
    Intervals: 1m, 15m, 1h, 4h, 1d, 1w
    Query params: hours_back (default 24)
    """
    try:
        hours_back = request.args.get('hours_back', 24, type=int)
        candles = advanced.get_granular_market_data(coin, interval, hours_back)
        return jsonify(candles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/user/pnl/<user_address>')
def get_user_pnl(user_address):
    """
    Get user PnL data
    Query params: window (day, week, month, allTime)
    """
    try:
        window = request.args.get('window', 'day', type=str)
        pnl_data = advanced.analyze_user_pnl(user_address, window)
        return jsonify(pnl_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/user/volume/<user_address>')
def get_user_volume(user_address):
    """
    Get user volume breakdown
    Query params: hours_back (default 24)
    """
    try:
        hours_back = request.args.get('hours_back', 24, type=int)
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(hours=hours_back)).timestamp() * 1000)

        volume_data = advanced.get_user_volume_breakdown(user_address, start_time, end_time)
        return jsonify(volume_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/user/fills/<user_address>')
def get_user_fills(user_address):
    """Get user's recent fills (trades)"""
    try:
        fills = advanced.get_user_fills(user_address, aggregation=False)
        return jsonify(fills)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/portfolio/<user_address>')
def get_portfolio_value(user_address):
    """
    Get portfolio value history
    Query params: window (day, week, month, allTime, perpDay, perpWeek, perpMonth, perpAllTime)
    """
    try:
        window = request.args.get('window', 'day', type=str)
        portfolio = advanced.get_portfolio_value(user_address, window)
        return jsonify(portfolio)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("Starting Hyperliquid Dashboard Server...")
    print("Dashboard will be available at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
