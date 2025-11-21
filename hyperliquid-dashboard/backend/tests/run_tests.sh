#!/bin/bash
# HIP-3 Analytics Platform - Complete Test Suite

echo "================================================================================"
echo "🧪 HIP-3 Analytics Platform - Complete Test Suite"
echo "================================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Generate Test Data
echo -e "${BLUE}Step 1: Generating Test Data${NC}"
echo "--------------------------------------------------------------------------------"
python3 generate_test_data.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Test data generation failed${NC}"
    exit 1
fi
echo ""

# Step 2: Start API Server (in background)
echo -e "${BLUE}Step 2: Starting API Server${NC}"
echo "--------------------------------------------------------------------------------"
cd ../api
export PYTHONPATH="${PYTHONPATH}:$(pwd)/.."

# Update server to use test database
sed -i.bak 's/hip3_analytics.db/hip3_analytics_test.db/g' server_v2.py

python3 server_v2.py > /tmp/hip3_server.log 2>&1 &
SERVER_PID=$!
echo -e "${GREEN}✓ Server started (PID: $SERVER_PID)${NC}"
echo "  Waiting for server to be ready..."
sleep 3
cd ../tests

# Check if server is running
if ! curl -s http://localhost:5000/health > /dev/null; then
    echo -e "${RED}❌ Server failed to start${NC}"
    cat /tmp/hip3_server.log
    exit 1
fi
echo -e "${GREEN}✓ Server is ready${NC}"
echo ""

# Step 3: Run API Tests
echo -e "${BLUE}Step 3: Running API Endpoint Tests${NC}"
echo "--------------------------------------------------------------------------------"
python3 test_api_endpoints.py
TEST_RESULT=$?
echo ""

# Step 4: Cleanup
echo -e "${BLUE}Step 4: Cleanup${NC}"
echo "--------------------------------------------------------------------------------"
echo "Stopping server (PID: $SERVER_PID)..."
kill $SERVER_PID 2>/dev/null

# Restore original server
cd ../api
mv server_v2.py.bak server_v2.py 2>/dev/null
cd ../tests

echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""

# Final Summary
echo "================================================================================"
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo "================================================================================"
    echo ""
    echo "📊 Test Database: hip3_analytics_test.db"
    echo "📝 Server Logs:   /tmp/hip3_server.log"
    echo ""
    echo "Next Steps:"
    echo "  1. Review test results above"
    echo "  2. Check server logs if needed: cat /tmp/hip3_server.log"
    echo "  3. Ready to build the UI!"
    echo ""
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo "================================================================================"
    echo ""
    echo "Check the test output above for details"
    echo "Server logs: cat /tmp/hip3_server.log"
    echo ""
fi

exit $TEST_RESULT
