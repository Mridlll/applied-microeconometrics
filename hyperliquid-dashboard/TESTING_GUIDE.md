# 🧪 HIP-3 Analytics Platform - Testing Guide

## Quick Start

### 1. Generate Test Data

```bash
cd backend/tests
python3 generate_test_data.py
```

This creates:
- 10,000 trades
- 2,688 market snapshots (7 days)
- 768 oracle metrics (2 days)
- 200 depth snapshots
- 100 user cohorts
- **$87M total volume**, $26K fees

### 2. Start API Server

```bash
cd backend/api
# Update server to use test database
sed 's/hip3_analytics.db/hip3_analytics_test.db/g' server_v2.py > server_test.py
python3 server_test.py
```

Server will start on `http://localhost:5000`

### 3. Test API Endpoints

```bash
cd backend/tests
python3 test_api_endpoints.py
```

Tests all 25+ endpoints including:
- Platform metrics
- Asset metrics
- Oracle tightness
- Market depth
- User analytics

### 4. Open Modern UI

Open in browser:
```
hyperliquid-dashboard/frontend/dashboard_v2.html
```

Or serve it:
```bash
cd hyperliquid-dashboard/frontend
python3 -m http.server 8000
# Then open: http://localhost:8000/dashboard_v2.html
```

## What You'll See

### Dashboard Features

**🎯 KPI Cards**
- 24h Volume: $87.2M
- 24h Fees: $26.2K
- Total OI: Real-time aggregate
- DAU: 100 unique traders

**🏥 Market Health Matrix**
- All 16 XYZ assets
- Volume, OI, Trades, Traders
- Health status badges

**📊 Charts**
- Volume distribution (bar chart)
- Fee breakdown (donut chart)

**🎨 Design**
- Dune Analytics-inspired
- Dark theme + glassmorphism
- Purple/indigo gradients
- Smooth animations

## API Endpoints to Test

### Platform Metrics
```bash
curl http://localhost:5000/api/platform/dashboard
curl http://localhost:5000/api/platform/fees
curl http://localhost:5000/api/platform/oi
```

### Assets
```bash
curl http://localhost:5000/api/assets/summary
curl http://localhost:5000/api/assets/comparison
curl http://localhost:5000/api/assets/xyz:XYZ100
```

### Oracle
```bash
curl "http://localhost:5000/api/oracle/health"
curl "http://localhost:5000/api/oracle/xyz:TSLA/tightness?mark_price=250&oracle_price=249.95"
```

### Users
```bash
curl http://localhost:5000/api/users/cohorts
curl http://localhost:5000/api/users/segments
curl http://localhost:5000/api/users/leaderboard
```

## Expected Results

### Platform Metrics
- ✅ Total volume: ~$87M
- ✅ Total fees: ~$26K
- ✅ 100 unique traders
- ✅ 10,000 trades

### Per-Asset Metrics (XYZ100, TSLA, NVDA, etc.)
- ✅ Volume breakdown by asset
- ✅ Fee collection
- ✅ Trade counts
- ✅ Trader counts

### Oracle Tightness
- ✅ Spread < 0.05% (very tight)
- ✅ Tightness scores 95-100
- ✅ Historical spread tracking

### User Analytics
- ✅ 100 users across cohorts
- ✅ Whales: top 1%
- ✅ Power users: top 10%
- ✅ Retention rates

## Troubleshooting

### API Server Won't Start
```bash
# Check if port 5000 is in use
lsof -i :5000

# Kill existing process
kill $(lsof -t -i:5000)
```

### No Data in UI
1. Verify API server is running
2. Check browser console (F12)
3. Test API directly: `curl http://localhost:5000/health`

### CORS Errors
- API has CORS enabled
- If issues persist, serve UI from same origin:
  ```bash
  # Copy UI to backend
  cp frontend/dashboard_v2.html backend/api/static/
  # Access via: http://localhost:5000/static/dashboard_v2.html
  ```

## Next Steps

After testing:

1. **Connect Real Data**
   - Replace test database with production
   - Set up WebSocket for real-time updates

2. **Add More Pages**
   - Oracle tightness page
   - Market depth charts
   - User leaderboards

3. **Deploy**
   - Dockerize backend
   - Deploy to cloud
   - Add authentication

## Performance Checks

- API response times: <100ms
- Dashboard load time: <2s
- Chart render time: <500ms
- 25+ endpoints all working

## Success Criteria

✅ Test data generated successfully
✅ API server runs without errors
✅ All endpoints return valid JSON
✅ UI loads and displays data
✅ Charts render correctly
✅ No console errors
✅ Mobile responsive

---

**Status:** Ready for Testing! 🚀
**Database:** `hip3_analytics_test.db`
**UI:** `dashboard_v2.html`
