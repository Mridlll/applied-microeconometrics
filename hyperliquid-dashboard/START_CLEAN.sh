#!/bin/bash
# Quick start script for HIP-3 Analytics Platform

echo "================================================================================"
echo "🚀 Starting HIP-3 Analytics Platform (Clean Setup)"
echo "================================================================================"
echo ""

# Kill any existing servers
echo "1. Cleaning up existing servers..."
pkill -f "server_v2.py" 2>/dev/null
pkill -f "http.server.*8000" 2>/dev/null
sleep 2

# Check if test data exists
if [ ! -f "backend/tests/hip3_analytics_test.db" ]; then
    echo "2. Generating test data..."
    cd backend/tests
    python3 generate_test_data.py
    cd ../..
else
    echo "2. ✅ Test data already exists"
fi

echo ""

# Start API server with test data
echo "3. Starting API server..."
cd backend/api

# Create temp server that uses test database
cat > server_test_temp.py << 'EOF'
import sys
sys.path.insert(0, '..')
exec(open('server_v2.py').read().replace('hip3_analytics.db', '../tests/hip3_analytics_test.db'))
EOF

# Start in background
python3 server_test_temp.py > /tmp/api_server.log 2>&1 &
API_PID=$!
echo "   ✅ API server started (PID: $API_PID)"
echo "   📝 Logs: tail -f /tmp/api_server.log"

cd ../..
sleep 2

# Test API
if curl -s http://localhost:5000/health > /dev/null; then
    echo "   ✅ API health check passed"
else
    echo "   ❌ API health check failed"
    exit 1
fi

echo ""

# Start frontend server
echo "4. Starting frontend server..."
cd frontend
python3 -m http.server 8000 > /tmp/frontend_server.log 2>&1 &
FRONTEND_PID=$!
echo "   ✅ Frontend server started (PID: $FRONTEND_PID)"

cd ..
sleep 1

echo ""
echo "================================================================================"
echo "✅ SETUP COMPLETE!"
echo "================================================================================"
echo ""
echo "🌐 Open your browser to:"
echo "   👉 http://localhost:8000/dashboard_v2.html"
echo ""
echo "📊 API Endpoints:"
echo "   http://localhost:5000/api/platform/dashboard"
echo "   http://localhost:5000/api/assets/summary"
echo "   http://localhost:5000/api/docs"
echo ""
echo "📝 Logs:"
echo "   API:      tail -f /tmp/api_server.log"
echo "   Frontend: tail -f /tmp/frontend_server.log"
echo ""
echo "🛑 To stop:"
echo "   kill $API_PID $FRONTEND_PID"
echo "   or run: pkill -f server_v2.py && pkill -f http.server"
echo ""
echo "================================================================================"
