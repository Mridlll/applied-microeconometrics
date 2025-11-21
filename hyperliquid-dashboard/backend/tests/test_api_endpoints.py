#!/usr/bin/env python3
"""
Comprehensive API Endpoint Tests
Tests all 25+ endpoints with generated test data
"""

import requests
import json
import time
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:5000"

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(name, passed, response_time=None):
    """Print test result"""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    time_str = f" ({response_time:.2f}ms)" if response_time else ""
    print(f"  {status} {name}{time_str}")

def test_endpoint(method, endpoint, expected_keys=None, data=None):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    start_time = time.time()

    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        else:
            return False, 0

        response_time = (time.time() - start_time) * 1000

        if response.status_code != 200:
            print(f"    {RED}Status: {response.status_code}{RESET}")
            return False, response_time

        result = response.json()

        if not result.get('success'):
            print(f"    {RED}Error: {result.get('error')}{RESET}")
            return False, response_time

        # Check expected keys
        if expected_keys:
            data_obj = result.get('data', {})
            for key in expected_keys:
                if key not in data_obj:
                    print(f"    {RED}Missing key: {key}{RESET}")
                    return False, response_time

        return True, response_time

    except Exception as e:
        print(f"    {RED}Exception: {str(e)}{RESET}")
        return False, 0

def main():
    """Run all tests"""
    print("="*80)
    print(f"{BLUE}🧪 HIP-3 Analytics Platform - API Endpoint Tests{RESET}")
    print("="*80)
    print()

    total_tests = 0
    passed_tests = 0

    # Health check
    print(f"{YELLOW}Health Check:{RESET}")
    passed, rt = test_endpoint("GET", "/health")
    print_test("Health check", passed, rt)
    total_tests += 1
    if passed: passed_tests += 1
    print()

    # Platform Metrics
    print(f"{YELLOW}Platform Metrics:{RESET}")

    tests = [
        ("GET", "/api/platform/dashboard", ["platform_overview", "asset_breakdown"]),
        ("GET", "/api/platform/overview", ["total_volume", "total_fees"]),
        ("GET", "/api/platform/fees", ["summary", "by_asset"]),
        ("GET", "/api/platform/oi", ["summary", "by_asset"]),
        ("GET", "/api/platform/activity", ["summary", "by_asset"]),
    ]

    for method, endpoint, keys in tests:
        passed, rt = test_endpoint(method, endpoint, keys)
        print_test(endpoint, passed, rt)
        total_tests += 1
        if passed: passed_tests += 1

    print()

    # Asset Metrics
    print(f"{YELLOW}Asset Metrics:{RESET}")

    tests = [
        ("GET", "/api/assets/summary", None),
        ("GET", "/api/assets/comparison", ["rankings", "totals"]),
        ("GET", "/api/assets/xyz:XYZ100", ["current_metrics", "weekly_metrics"]),
        ("GET", "/api/assets/xyz:TSLA", ["current_metrics"]),
    ]

    for method, endpoint, keys in tests:
        passed, rt = test_endpoint(method, endpoint, keys)
        print_test(endpoint, passed, rt)
        total_tests += 1
        if passed: passed_tests += 1

    print()

    # Oracle Metrics
    print(f"{YELLOW}Oracle Metrics:{RESET}")

    tests = [
        ("GET", "/api/oracle/health", ["summary", "assets"]),
        ("GET", "/api/oracle/xyz:XYZ100/tightness?mark_price=200&oracle_price=199.98", ["tightness_score", "spread_pct"]),
        ("GET", "/api/oracle/xyz:NVDA/history?hours=24", ["statistics"]),
    ]

    for method, endpoint, keys in tests:
        passed, rt = test_endpoint(method, endpoint, keys)
        print_test(endpoint, passed, rt)
        total_tests += 1
        if passed: passed_tests += 1

    print()

    # Market Depth
    print(f"{YELLOW}Market Depth:{RESET}")

    # Sample orderbook data
    orderbook = {
        "levels": [[
            [  # Bids
                {"px": "199.95", "sz": "10.5"},
                {"px": "199.90", "sz": "25.0"},
            ],
            [  # Asks
                {"px": "200.05", "sz": "12.0"},
                {"px": "200.10", "sz": "30.0"},
            ]
        ]]
    }

    tests = [
        ("POST", "/api/depth/xyz:XYZ100/metrics", ["spread_bps", "liquidity_score"], orderbook),
        ("POST", "/api/depth/xyz:TSLA/chart", ["bids", "asks"], orderbook),
    ]

    for method, endpoint, keys, data in tests:
        passed, rt = test_endpoint(method, endpoint, keys, data)
        print_test(endpoint, passed, rt)
        total_tests += 1
        if passed: passed_tests += 1

    print()

    # User Metrics
    print(f"{YELLOW}User Metrics:{RESET}")

    tests = [
        ("GET", "/api/users/cohorts", ["summary", "cohorts"]),
        ("GET", "/api/users/retention", ["retention_rates"]),
        ("GET", "/api/users/segments", ["tiers"]),
        ("GET", "/api/users/frequency", ["distribution"]),
        ("GET", "/api/users/preferences", ["favorite_assets"]),
        ("GET", "/api/users/lifecycle", ["stages"]),
        ("GET", "/api/users/leaderboard?metric=volume&limit=10", ["leaderboard"]),
    ]

    for method, endpoint, keys in tests:
        passed, rt = test_endpoint(method, endpoint, keys)
        print_test(endpoint, passed, rt)
        total_tests += 1
        if passed: passed_tests += 1

    print()

    # API Documentation
    print(f"{YELLOW}Documentation:{RESET}")
    passed, rt = test_endpoint("GET", "/api/docs", ["endpoints"])
    print_test("/api/docs", passed, rt)
    total_tests += 1
    if passed: passed_tests += 1

    print()

    # Summary
    print("="*80)
    print(f"{BLUE}TEST SUMMARY{RESET}")
    print("="*80)
    print(f"Total Tests:   {total_tests}")
    print(f"Passed:        {GREEN}{passed_tests}{RESET}")
    print(f"Failed:        {RED}{total_tests - passed_tests}{RESET}")
    print(f"Success Rate:  {passed_tests/total_tests*100:.1f}%")
    print()

    if passed_tests == total_tests:
        print(f"{GREEN}✅ ALL TESTS PASSED!{RESET}")
    else:
        print(f"{RED}❌ SOME TESTS FAILED{RESET}")

    print("="*80)
    print()

if __name__ == "__main__":
    main()
