# HIP-3 Analytics Dashboard - Quick Start Guide

## 🎯 Overview

This dashboard consists of two servers running simultaneously:

- **Main Server** (port 5000): Serves HTML pages
- **API Server** (port 5001): Provides data endpoints

## ✅ What Was Fixed

### 1. Port Configuration
- **API Server**: Changed from port 5000 → 5001
- **Main Server**: Remains on port 5000
- **Dashboard**: Updated to call API on port 5001

### 2. Module Import Conflicts
- Created `backend/analytics/__init__.py` to bridge legacy and new code
- Supports both:
  - Legacy: `from analytics import PlatformAnalytics`
  - New: `from analytics.platform_metrics import PlatformMetrics`

### 3. Dashboard Route
- Added `/dashboard_v2` route to main server
- Access at: http://localhost:5000/dashboard_v2

### 4. Database Setup
- Generated test database with 10,000 trades
- Located at: `backend/api/hip3_analytics.db`
- Contains realistic data for 16 XYZ markets

## 🚀 Quick Start

### Option 1: Automated Testing Script
\`\`\`bash
cd hyperliquid-dashboard
./test-servers.sh
\`\`\`

This will:
1. Start both servers
2. Run health checks
3. Verify all endpoints
4. Display server PIDs and URLs

### Option 2: Manual Server Startup
\`\`\`bash
cd hyperliquid-dashboard

# Start API Server (port 5001)
cd backend/api
python3 server_v2.py &

# Start Main Server (port 5000)
cd ..
python3 server.py &
\`\`\`

### Option 3: Full Startup Script
\`\`\`bash
cd hyperliquid-dashboard
./start-servers.sh
\`\`\`

This provides real-time logs from both servers.

## 📊 Access Points

Once servers are running:

| Service | URL | Description |
|---------|-----|-------------|
| Main Dashboard | http://localhost:5000/ | Original dashboard |
| V2 Dashboard | http://localhost:5000/dashboard_v2 | New analytics dashboard |
| HIP-3 Analytics | http://localhost:5000/hip3 | Advanced analytics |
| API Health | http://localhost:5001/health | API health check |
| API Docs | http://localhost:5001/api/docs | API documentation |

## 🔧 Regenerate Test Data

If you need fresh test data:

\`\`\`bash
cd hyperliquid-dashboard/backend
python3 tests/generate_test_data.py
cp tests/hip3_analytics_test.db api/hip3_analytics.db
\`\`\`

## 🐛 Troubleshooting

### API Returns Empty Data
\`\`\`bash
# Ensure database exists in the right location
ls -lh backend/api/hip3_analytics.db
\`\`\`

### Port Already in Use
\`\`\`bash
# Check what's using the ports
lsof -i :5000
lsof -i :5001

# Kill existing processes
pkill -f "python3 server"
\`\`\`

### Import Errors
\`\`\`bash
# Verify analytics package structure
cd hyperliquid-dashboard/backend
python3 -c "from analytics import PlatformAnalytics; print('✓ Legacy import works')"
python3 -c "from analytics.platform_metrics import PlatformMetrics; print('✓ New import works')"
\`\`\`

## 📁 Project Structure

\`\`\`
hyperliquid-dashboard/
├── backend/
│   ├── server.py                    # Main server (port 5000)
│   ├── analytics.py                 # Legacy analytics module
│   ├── analytics/                   # New analytics package
│   │   ├── __init__.py             # Package bridge
│   │   ├── platform_metrics.py
│   │   ├── market_metrics.py
│   │   └── user_metrics.py
│   ├── api/
│   │   ├── server_v2.py            # API server (port 5001)
│   │   └── hip3_analytics.db       # Test database
│   └── tests/
│       └── generate_test_data.py   # Database generator
├── frontend/
│   ├── index.html                  # Main dashboard
│   ├── dashboard_v2.html           # V2 dashboard (Dune-style)
│   └── hip3-analytics.html
├── start-servers.sh                # Full startup script
├── test-servers.sh                 # Quick test script
└── QUICKSTART.md                   # This file
\`\`\`

## 🎨 Dashboard Features

### V2 Dashboard (\`/dashboard_v2\`)
- Real-time KPI cards (Volume, Fees, OI, DAU)
- Market health matrix for all 16 assets
- Volume distribution charts
- Fee revenue breakdown
- Modern glassmorphism UI (Dune/DefiLlama inspired)

### API Endpoints Used
- \`GET /api/platform/dashboard\` - Complete dashboard data
- \`GET /api/assets/summary\` - All assets summary
- \`GET /api/assets/comparison\` - Asset comparisons
- \`GET /api/platform/fees\` - Fee analysis

## 📝 Development Notes

### Adding New Features
1. API endpoints go in \`backend/api/server_v2.py\`
2. Analytics logic goes in \`backend/analytics/\` modules
3. Frontend updates go in \`frontend/dashboard_v2.html\`

### Running Tests
\`\`\`bash
cd hyperliquid-dashboard/backend/tests
python3 test_api_endpoints.py
\`\`\`

## ✅ Verification Checklist

- [x] Both servers start without port conflicts
- [x] API server on port 5001 responds to health checks
- [x] Main server on port 5000 serves dashboard
- [x] \`/dashboard_v2\` route returns 200
- [x] API endpoints return real data (not empty)
- [x] Dashboard pulls data from API successfully
- [x] Module imports work for both legacy and new code

## 🚦 Status

All systems operational! Dashboard is ready for use.
