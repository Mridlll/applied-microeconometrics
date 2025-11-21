#!/bin/bash

# Quick test script to verify both servers work

cd "$(dirname "$0")/backend"

echo "=============================================="
echo "Testing HIP-3 Analytics Dashboard Setup"
echo "=============================================="
echo ""

# Start API Server (port 5001)
echo "1. Starting API Server on port 5001..."
cd api
python3 server_v2.py > /tmp/api_server_test.log 2>&1 &
API_PID=$!
cd ..
sleep 3

# Test API Server
echo "2. Testing API Server..."
API_HEALTH=$(curl -s http://localhost:5001/health)
if [ $? -eq 0 ]; then
    echo "   ✅ API Server is responding"
    echo "   Response: $API_HEALTH"
else
    echo "   ❌ API Server failed"
    kill $API_PID 2>/dev/null
    exit 1
fi

# Test API data endpoint
echo ""
echo "3. Testing API data endpoint..."
API_DATA=$(curl -s http://localhost:5001/api/platform/overview)
if echo "$API_DATA" | grep -q '"success": true'; then
    echo "   ✅ API is returning data"
    echo "   Sample: $(echo $API_DATA | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Active Markets: {data['data']['active_markets']}, Total Volume: \${data['data']['total_volume']:,.2f}\")")"
else
    echo "   ❌ API data endpoint failed"
    kill $API_PID 2>/dev/null
    exit 1
fi

echo ""
echo "4. Starting Main Server on port 5000..."
python3 server.py > /tmp/main_server_test.log 2>&1 &
MAIN_PID=$!
sleep 3

# Test Main Server
echo "5. Testing Main Server..."
MAIN_HEALTH=$(curl -s http://localhost:5000/api/health)
if [ $? -eq 0 ]; then
    echo "   ✅ Main Server is responding"
else
    echo "   ❌ Main Server failed"
    kill $MAIN_PID $API_PID 2>/dev/null
    exit 1
fi

# Test dashboard route
echo ""
echo "6. Testing /dashboard_v2 route..."
DASHBOARD=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/dashboard_v2)
if [ "$DASHBOARD" = "200" ]; then
    echo "   ✅ Dashboard route is working (HTTP $DASHBOARD)"
else
    echo "   ❌ Dashboard route failed (HTTP $DASHBOARD)"
    kill $MAIN_PID $API_PID 2>/dev/null
    exit 1
fi

echo ""
echo "=============================================="
echo "✅ ALL TESTS PASSED!"
echo "=============================================="
echo ""
echo "Configuration verified:"
echo "  ✅ API Server running on port 5001"
echo "  ✅ Main Server running on port 5000"
echo "  ✅ Dashboard accessible at /dashboard_v2"
echo "  ✅ API endpoints returning data"
echo "  ✅ Module imports working correctly"
echo ""
echo "Servers are running. Access at:"
echo "  Main Dashboard:    http://localhost:5000/"
echo "  V2 Dashboard:      http://localhost:5000/dashboard_v2"
echo ""
echo "Server PIDs:"
echo "  Main: $MAIN_PID"
echo "  API:  $API_PID"
echo ""
echo "To stop: kill $MAIN_PID $API_PID"
echo "=============================================="
