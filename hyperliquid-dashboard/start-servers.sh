#!/bin/bash

# HIP-3 Analytics Dashboard - Start Both Servers
# Main Server: http://localhost:5000 (serves HTML)
# API Server: http://localhost:5001 (provides data)

cd "$(dirname "$0")/backend"

echo "=============================================="
echo "Starting HIP-3 Analytics Dashboard"
echo "=============================================="
echo ""

# Start API Server (port 5001) in background
echo "Starting API Server on port 5001..."
cd api
python3 server_v2.py > /tmp/api_server.log 2>&1 &
API_PID=$!
echo "API Server PID: $API_PID"
cd ..

# Wait for API server to start
sleep 2

# Check if API server is running
if curl -s http://localhost:5001/health > /dev/null; then
    echo "✅ API Server started successfully"
else
    echo "❌ API Server failed to start"
    echo "Check /tmp/api_server.log for details"
    exit 1
fi

echo ""
echo "Starting Main Server on port 5000..."
python3 server.py > /tmp/main_server.log 2>&1 &
MAIN_PID=$!
echo "Main Server PID: $MAIN_PID"

# Wait for main server to start
sleep 2

# Check if main server is running
if curl -s http://localhost:5000/api/health > /dev/null; then
    echo "✅ Main Server started successfully"
else
    echo "❌ Main Server failed to start"
    echo "Check /tmp/main_server.log for details"
    kill $API_PID 2>/dev/null
    exit 1
fi

echo ""
echo "=============================================="
echo "✅ Both servers are running!"
echo "=============================================="
echo ""
echo "URLs:"
echo "  Main Dashboard:    http://localhost:5000/"
echo "  V2 Dashboard:      http://localhost:5000/dashboard_v2"
echo "  HIP-3 Analytics:   http://localhost:5000/hip3"
echo "  API Documentation: http://localhost:5001/api/docs"
echo ""
echo "Process IDs:"
echo "  Main Server: $MAIN_PID"
echo "  API Server:  $API_PID"
echo ""
echo "Logs:"
echo "  Main Server: /tmp/main_server.log"
echo "  API Server:  /tmp/api_server.log"
echo ""
echo "To stop servers: kill $MAIN_PID $API_PID"
echo "=============================================="
echo ""

# Keep script running and show logs
echo "Press Ctrl+C to stop both servers"
echo ""
trap "echo ''; echo 'Stopping servers...'; kill $MAIN_PID $API_PID 2>/dev/null; echo 'Servers stopped.'; exit 0" INT TERM

# Show combined logs
tail -f /tmp/main_server.log /tmp/api_server.log
