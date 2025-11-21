#!/usr/bin/env python3
"""
Quick diagnostic to check what's wrong with the current setup
"""

import requests
import json

API_BASE = "http://localhost:5000/api"

print("="*80)
print("🔍 HIP-3 Analytics Platform - Diagnostics")
print("="*80)
print()

# Test API server
print("1. Testing API Server...")
try:
    response = requests.get("http://localhost:5000/health", timeout=2)
    if response.status_code == 200:
        print("   ✅ API server is running")
    else:
        print("   ❌ API server returned error:", response.status_code)
except Exception as e:
    print("   ❌ API server is NOT running")
    print("   Start it with: cd backend/api && python3 server_v2.py")
    print()
    exit(1)

print()

# Test platform metrics
print("2. Testing Platform Metrics...")
try:
    response = requests.get(f"{API_BASE}/platform/dashboard", timeout=5)
    data = response.json()

    if data.get('success'):
        overview = data['data']['platform_overview']
        print(f"   ✅ Platform Overview:")
        print(f"      24h Volume: ${overview.get('total_volume_24h', 0):,.2f}")
        print(f"      24h Fees: ${overview.get('total_fees_24h', 0):,.2f}")
        print(f"      Total OI: ${overview.get('total_oi', 0):,.2f}")
        print(f"      DAU: {overview.get('unique_traders_24h', 0)}")
    else:
        print(f"   ❌ Error: {data.get('error')}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

print()

# Test assets
print("3. Testing Asset Metrics...")
try:
    response = requests.get(f"{API_BASE}/assets/summary", timeout=5)
    data = response.json()

    if data.get('success'):
        assets = data['data']
        print(f"   ✅ Found {len(assets)} assets")
        if assets:
            top_asset = max(assets, key=lambda x: x.get('volume', 0) or 0)
            print(f"      Top by volume: {top_asset['coin']} - ${top_asset.get('volume', 0):,.2f}")
    else:
        print(f"   ❌ Error: {data.get('error')}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

print()

# Test oracle
print("4. Testing Oracle Metrics...")
try:
    response = requests.get(f"{API_BASE}/oracle/health", timeout=5)
    data = response.json()

    if data.get('success'):
        summary = data['data'].get('summary', {})
        print(f"   ✅ Oracle Health:")
        print(f"      Avg Tightness: {summary.get('avg_tightness_score', 0):.2f}/100")
        print(f"      Avg Spread: {summary.get('avg_spread_pct', 0):.4f}%")
        print(f"      Assets Tracked: {summary.get('num_assets', 0)}")
    else:
        print(f"   ❌ Error: {data.get('error')}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

print()

# Test users
print("5. Testing User Metrics...")
try:
    response = requests.get(f"{API_BASE}/users/cohorts", timeout=5)
    data = response.json()

    if data.get('success'):
        summary = data['data'].get('summary', {})
        print(f"   ✅ User Analytics:")
        print(f"      Total Users: {summary.get('total_users', 0)}")
        print(f"      Avg Volume/User: ${summary.get('avg_volume_per_user', 0):,.2f}")
        print(f"      Avg Retention: {summary.get('avg_retention_rate', 0):.2f}%")
    else:
        print(f"   ❌ Error: {data.get('error')}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

print()
print("="*80)
print("📊 Summary")
print("="*80)
print()
print("If all tests passed:")
print("  1. API server is working correctly")
print("  2. Open the NEW UI: http://localhost:8000/dashboard_v2.html")
print()
print("If tests failed:")
print("  1. Make sure API server is running: cd backend/api && python3 server_v2.py")
print("  2. Make sure test data exists: cd backend/tests && ls hip3_analytics_test.db")
print()
