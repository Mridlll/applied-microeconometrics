"""
Flask server for Hyperliquid Dashboard
Serves real-time trading data via REST API
"""

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from hyperliquid_api import HyperliquidAPI
from analytics import PlatformAnalytics
from advanced_analytics import HyperliquidAdvancedAnalytics
from leaderboard_analytics import LeaderboardAnalytics
from xyz_markets import XYZMarketsClient
import os
import json
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize API client and analytics
api = HyperliquidAPI(use_testnet=False)
analytics = PlatformAnalytics(data_dir=os.path.join(os.path.dirname(__file__), '..', 'data'))
advanced = HyperliquidAdvancedAnalytics(use_testnet=False)
leaderboard = LeaderboardAnalytics(use_testnet=False)

# Initialize XYZ Markets WebSocket client
xyz_client = XYZMarketsClient(use_testnet=False)
xyz_connected = False

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


@app.route('/api/leaderboard/top-traders')
def get_top_traders():
    """Get top traders leaderboard - automatically populated"""
    try:
        hours_back = request.args.get('hours_back', 24, type=int)
        limit = request.args.get('limit', 50, type=int)
        traders = leaderboard.get_top_traders_by_volume(hours_back, limit)
        return jsonify(traders)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/leaderboard/large-trades/<coin>')
def get_large_trades(coin):
    """Get large/interesting trades for specific asset"""
    try:
        threshold = request.args.get('threshold', 50000, type=float)
        trades = leaderboard.analyze_large_trades(coin, threshold)
        return jsonify(trades)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/leaderboard/trade-sizes')
def get_trade_sizes():
    """Get average trade size analytics across top assets"""
    try:
        summary = api.get_market_summary()
        top_assets = sorted(summary.get("assets", []), key=lambda x: x["day_ntl_vlm"], reverse=True)[:10]
        top_coins = [asset["name"] for asset in top_assets]

        trade_size_analytics = []
        for coin in top_coins:
            try:
                stats = leaderboard.calculate_average_trade_size(coin)
                trade_size_analytics.append(stats)
            except Exception as e:
                print(f"Error analyzing {coin}: {e}")
                continue

        return jsonify(trade_size_analytics)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/leaderboard/platform-analytics')
def get_platform_analytics():
    """Get comprehensive platform-wide analytics including top traders and large trades"""
    try:
        summary = api.get_market_summary()
        top_assets = sorted(summary.get("assets", []), key=lambda x: x["day_ntl_vlm"], reverse=True)[:10]
        top_coins = [asset["name"] for asset in top_assets]

        analytics_data = leaderboard.get_platform_wide_analytics(top_coins)
        return jsonify(analytics_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/leaderboard/asset-traders/<coin>')
def get_asset_traders(coin):
    """Get top traders for a specific asset"""
    try:
        hours_back = request.args.get('hours_back', 4, type=int)
        traders = leaderboard.get_asset_specific_traders(coin, hours_back)
        return jsonify(traders)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/tradfi/detailed-analytics')
def get_tradfi_analytics():
    """
    Get detailed analytics for TradFi/Equity perpetuals
    Includes OI tracking, funding rates, liquidations, and microstructure changes
    """
    try:
        summary = api.get_market_summary()
        metrics = advanced.get_real_platform_metrics(summary)

        # Get TradFi assets with detailed analytics
        tradfi_data = metrics.get("tradfi_perps", {})
        tradfi_assets = tradfi_data.get("assets", [])

        # Sort by volume descending
        tradfi_assets.sort(key=lambda x: x.get("day_ntl_vlm", 0), reverse=True)

        # Add percentage of total for each asset
        total_tradfi_volume = tradfi_data.get("total_volume", 1)
        total_tradfi_oi = tradfi_data.get("total_oi", 1)

        for asset in tradfi_assets:
            asset["volume_pct"] = (asset.get("day_ntl_vlm", 0) / total_tradfi_volume * 100) if total_tradfi_volume > 0 else 0
            asset["oi_pct"] = (asset.get("open_interest", 0) / total_tradfi_oi * 100) if total_tradfi_oi > 0 else 0

        return jsonify({
            "timestamp": summary.get("timestamp"),
            "total_count": tradfi_data.get("count", 0),
            "total_volume_24h": tradfi_data.get("total_volume", 0),
            "total_open_interest": tradfi_data.get("total_oi", 0),
            "assets": tradfi_assets,
            "crypto_comparison": {
                "crypto_volume": metrics.get("crypto_perps", {}).get("total_volume", 0),
                "crypto_oi": metrics.get("crypto_perps", {}).get("total_oi", 0),
                "tradfi_volume_pct": (tradfi_data.get("total_volume", 0) / metrics.get("total_volume_24h", 1) * 100) if metrics.get("total_volume_24h") > 0 else 0,
                "tradfi_oi_pct": (tradfi_data.get("total_oi", 0) / metrics.get("total_open_interest", 1) * 100) if metrics.get("total_open_interest") > 0 else 0
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/xyz/markets')
def get_xyz_markets():
    """Get XYZ equity perpetuals market data from WebSocket"""
    try:
        global xyz_connected
        if not xyz_connected:
            return jsonify({
                "error": "XYZ WebSocket not connected",
                "connected": False,
                "assets": []
            }), 503

        market_data = xyz_client.get_market_data()

        # Format data for API response
        assets = []
        for asset_name, data in market_data.items():
            assets.append({
                "name": asset_name,
                "mark_price": data.get("mark_price"),
                "last_update": data.get("last_update"),
                "recent_trades_count": len(data.get("recent_trades", []))
            })

        return jsonify({
            "connected": True,
            "timestamp": datetime.now().isoformat(),
            "total_assets": len(assets),
            "assets": assets
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/xyz/asset/<asset_name>')
def get_xyz_asset(asset_name):
    """Get detailed XYZ asset data including recent trades"""
    try:
        # Ensure asset name has xyz: prefix
        if not asset_name.startswith("xyz:"):
            asset_name = f"xyz:{asset_name}"

        asset_data = xyz_client.get_asset_data(asset_name)

        if not asset_data:
            return jsonify({"error": "Asset not found or no data available"}), 404

        return jsonify({
            "name": asset_name,
            "mark_price": asset_data.get("mark_price"),
            "last_update": asset_data.get("last_update"),
            "recent_trades": asset_data.get("recent_trades", [])
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("Starting Hyperliquid Dashboard Server...")
    print("Dashboard will be available at: http://localhost:5000")

    # Connect to XYZ markets WebSocket
    print("\nConnecting to XYZ Markets WebSocket...")
    xyz_connected = xyz_client.connect()
    if xyz_connected:
        print("XYZ WebSocket connected successfully")
        print(f"Tracking {len(xyz_client.xyz_assets)} XYZ equity perpetuals")
    else:
        print("Warning: XYZ WebSocket connection failed")

    app.run(debug=True, host='0.0.0.0', port=5000)
