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
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Now import analytics modules
import analytics.platform_metrics
import analytics.market_metrics
import analytics.user_metrics

# Get classes from modules
PlatformMetrics = analytics.platform_metrics.PlatformMetrics
MarketMetrics = analytics.market_metrics.MarketMetrics
UserMetrics = analytics.user_metrics.UserMetrics

from core.database import HIP3Database

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize database and analytics modules
db = HIP3Database("hip3_analytics.db")
platform_metrics = PlatformMetrics(db)
market_metrics = MarketMetrics(db)
user_metrics = UserMetrics(db)
