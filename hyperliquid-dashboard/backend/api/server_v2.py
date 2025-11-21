"""
HIP-3 Analytics Platform API Server (v2)
Consolidated API with all platform, market, and user metrics
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import HIP3Database
from analytics.platform_metrics import PlatformMetrics
from analytics.market_metrics import MarketMetrics
from analytics.user_metrics import UserMetrics

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize database and analytics modules
db = HIP3Database("hip3_analytics.db")
platform_metrics = PlatformMetrics(db)
market_metrics = MarketMetrics(db)
user_metrics = UserMetrics(db)

# ===== HEALTH CHECK =====

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0'
    })

# ===== PLATFORM METRICS =====

@app.route('/api/platform/dashboard', methods=['GET'])
def get_platform_dashboard():
    """Get complete platform dashboard with all KPIs"""
    try:
        dashboard = platform_metrics.get_platform_dashboard()
        return jsonify({
            'success': True,
            'data': dashboard
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/platform/overview', methods=['GET'])
def get_platform_overview():
    """Get platform overview metrics"""
    try:
        overview = db.get_platform_overview()
        return jsonify({
            'success': True,
            'data': overview
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/platform/fees', methods=['GET'])
def get_fee_breakdown():
    """Get detailed fee analysis"""
    try:
        fees = platform_metrics.get_fee_breakdown()
        return jsonify({
            'success': True,
            'data': fees
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/platform/oi', methods=['GET'])
def get_oi_analysis():
    """Get Open Interest analysis"""
    try:
        oi = platform_metrics.get_oi_analysis()
        return jsonify({
            'success': True,
            'data': oi
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/platform/activity', methods=['GET'])
def get_trading_activity():
    """Get trading activity analysis"""
    try:
        activity = platform_metrics.get_trading_activity_analysis()
        return jsonify({
            'success': True,
            'data': activity
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ===== ASSET METRICS =====

@app.route('/api/assets/summary', methods=['GET'])
def get_assets_summary():
    """Get summary for all 16 XYZ assets"""
    try:
        summary = db.get_all_assets_summary()
        return jsonify({
            'success': True,
            'data': summary
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/assets/comparison', methods=['GET'])
def get_assets_comparison():
    """Compare all assets side-by-side"""
    try:
        comparison = platform_metrics.get_all_assets_comparison()
        return jsonify({
            'success': True,
            'data': comparison
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/assets/<coin>', methods=['GET'])
def get_asset_details(coin):
    """Get detailed metrics for specific asset"""
    try:
        details = platform_metrics.get_asset_detailed_metrics(coin)
        return jsonify({
            'success': True,
            'data': details
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ===== ORACLE METRICS =====

@app.route('/api/oracle/health', methods=['GET'])
def get_oracle_health():
    """Get oracle health for all assets"""
    try:
        health = market_metrics.get_all_assets_oracle_health()
        return jsonify({
            'success': True,
            'data': health
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/oracle/<coin>/tightness', methods=['GET'])
def get_oracle_tightness(coin):
    """Calculate oracle tightness for specific asset"""
    try:
        mark_price = float(request.args.get('mark_price', 0))
        oracle_price = float(request.args.get('oracle_price', 0))

        if mark_price == 0 or oracle_price == 0:
            return jsonify({
                'success': False,
                'error': 'mark_price and oracle_price parameters required'
            }), 400

        tightness = market_metrics.calculate_oracle_tightness(coin, mark_price, oracle_price)
        return jsonify({
            'success': True,
            'data': tightness
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/oracle/<coin>/history', methods=['GET'])
def get_oracle_history(coin):
    """Get oracle spread history"""
    try:
        hours = float(request.args.get('hours', 24))
        history = market_metrics.get_oracle_spread_history(coin, hours)
        return jsonify({
            'success': True,
            'data': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ===== MARKET DEPTH =====

@app.route('/api/depth/<coin>/metrics', methods=['POST'])
def calculate_market_depth(coin):
    """Calculate market depth metrics from orderbook"""
    try:
        orderbook = request.get_json()

        if not orderbook:
            return jsonify({
                'success': False,
                'error': 'Orderbook data required in request body'
            }), 400

        depth = market_metrics.calculate_market_depth(coin, orderbook)
        return jsonify({
            'success': True,
            'data': depth
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/depth/<coin>/chart', methods=['POST'])
def get_depth_chart(coin):
    """Get depth chart data for visualization"""
    try:
        orderbook = request.get_json()

        if not orderbook:
            return jsonify({
                'success': False,
                'error': 'Orderbook data required in request body'
            }), 400

        chart_data = market_metrics.get_depth_chart_data(coin, orderbook)
        return jsonify({
            'success': True,
            'data': chart_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/market/<coin>/health', methods=['GET'])
def get_market_health(coin):
    """Get overall market health score"""
    try:
        health = market_metrics.get_market_health_score(coin)
        return jsonify({
            'success': True,
            'data': health
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ===== USER METRICS =====

@app.route('/api/users/cohorts', methods=['GET'])
def get_cohort_analysis():
    """Get cohort analysis dashboard"""
    try:
        cohorts = user_metrics.get_cohort_dashboard()
        return jsonify({
            'success': True,
            'data': cohorts
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users/retention', methods=['GET'])
def get_retention_analysis():
    """Get retention analysis"""
    try:
        cohort_week = request.args.get('cohort_week')
        retention = user_metrics.get_retention_analysis(cohort_week)
        return jsonify({
            'success': True,
            'data': retention
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users/segments', methods=['GET'])
def get_user_segments():
    """Get user segmentation by activity"""
    try:
        segments = user_metrics.segment_users_by_activity()
        return jsonify({
            'success': True,
            'data': segments
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users/frequency', methods=['GET'])
def get_trading_frequency():
    """Get trading frequency distribution"""
    try:
        frequency = user_metrics.get_trading_frequency_distribution()
        return jsonify({
            'success': True,
            'data': frequency
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users/preferences', methods=['GET'])
def get_asset_preferences():
    """Get asset preference patterns"""
    try:
        preferences = user_metrics.get_asset_preference_patterns()
        return jsonify({
            'success': True,
            'data': preferences
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users/lifecycle', methods=['GET'])
def get_user_lifecycle():
    """Get user lifecycle analysis"""
    try:
        lifecycle = user_metrics.get_user_lifecycle_analysis()
        return jsonify({
            'success': True,
            'data': lifecycle
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get top users leaderboard"""
    try:
        metric = request.args.get('metric', 'volume')
        limit = int(request.args.get('limit', 100))
        leaderboard = user_metrics.get_leaderboard(metric, limit)
        return jsonify({
            'success': True,
            'data': leaderboard
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ===== DATA INGESTION =====

@app.route('/api/ingest/trade', methods=['POST'])
def ingest_trade():
    """Ingest a single trade"""
    try:
        trade_data = request.get_json()

        if not trade_data:
            return jsonify({
                'success': False,
                'error': 'Trade data required'
            }), 400

        db.record_trade(trade_data)

        return jsonify({
            'success': True,
            'message': 'Trade recorded successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ingest/snapshot', methods=['POST'])
def ingest_market_snapshot():
    """Ingest market snapshot"""
    try:
        data = request.get_json()

        if not data or 'coin' not in data or 'snapshot' not in data:
            return jsonify({
                'success': False,
                'error': 'Coin and snapshot data required'
            }), 400

        db.store_market_snapshot(data['coin'], data['snapshot'])

        return jsonify({
            'success': True,
            'message': 'Snapshot stored successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ===== API DOCUMENTATION =====

@app.route('/api/docs', methods=['GET'])
def get_api_docs():
    """Get API documentation"""
    return jsonify({
        'version': '2.0',
        'name': 'HIP-3 Analytics Platform API',
        'endpoints': {
            'Platform Metrics': {
                'GET /api/platform/dashboard': 'Complete platform dashboard',
                'GET /api/platform/overview': 'Platform overview metrics',
                'GET /api/platform/fees': 'Fee breakdown analysis',
                'GET /api/platform/oi': 'Open Interest analysis',
                'GET /api/platform/activity': 'Trading activity patterns',
            },
            'Asset Metrics': {
                'GET /api/assets/summary': 'Summary for all 16 assets',
                'GET /api/assets/comparison': 'Compare all assets',
                'GET /api/assets/<coin>': 'Detailed metrics for specific asset',
            },
            'Oracle Metrics': {
                'GET /api/oracle/health': 'Oracle health for all assets',
                'GET /api/oracle/<coin>/tightness': 'Oracle tightness metrics',
                'GET /api/oracle/<coin>/history': 'Oracle spread history',
            },
            'Market Depth': {
                'POST /api/depth/<coin>/metrics': 'Calculate depth metrics',
                'POST /api/depth/<coin>/chart': 'Get depth chart data',
                'GET /api/market/<coin>/health': 'Market health score',
            },
            'User Metrics': {
                'GET /api/users/cohorts': 'Cohort analysis',
                'GET /api/users/retention': 'Retention analysis',
                'GET /api/users/segments': 'User segmentation',
                'GET /api/users/frequency': 'Trading frequency',
                'GET /api/users/preferences': 'Asset preferences',
                'GET /api/users/lifecycle': 'User lifecycle',
                'GET /api/users/leaderboard': 'Top users leaderboard',
            },
            'Data Ingestion': {
                'POST /api/ingest/trade': 'Ingest trade data',
                'POST /api/ingest/snapshot': 'Ingest market snapshot',
            },
        }
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    print("="*80)
    print("HIP-3 Analytics Platform API v2.0")
    print("="*80)
    print("\nStarting server on http://localhost:5001")
    print("\nAPI Endpoints:")
    print("  Platform: /api/platform/*")
    print("  Assets:   /api/assets/*")
    print("  Oracle:   /api/oracle/*")
    print("  Depth:    /api/depth/*")
    print("  Users:    /api/users/*")
    print("\nDocumentation: http://localhost:5001/api/docs")
    print("="*80)
    print()

    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
        threaded=True
    )
