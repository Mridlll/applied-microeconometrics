#!/usr/bin/env python3
"""
Periodic Market Snapshot Collector
Collects OI, volume, funding data for all HIP-3 markets every 10 minutes
Run this with cron or as a background service
"""

import requests
import time
import sys
from datetime import datetime

API_URL = "http://localhost:5000/api/hip3/collect-snapshots"
INTERVAL_MINUTES = 10

def collect_snapshot():
    """Collect a single snapshot"""
    try:
        response = requests.post(API_URL, timeout=30)

        if response.ok:
            data = response.json()
            print(f"[{datetime.now().isoformat()}] ✓ Collected {data.get('snapshots_stored', 0)} market snapshots")
            return True
        else:
            print(f"[{datetime.now().isoformat()}] ✗ Error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"[{datetime.now().isoformat()}] ✗ Exception: {e}")
        return False

def run_continuous():
    """Run continuously, collecting snapshots every N minutes"""
    print(f"Starting continuous snapshot collector (every {INTERVAL_MINUTES} minutes)")
    print(f"Target API: {API_URL}")
    print("Press Ctrl+C to stop\n")

    while True:
        collect_snapshot()

        # Wait for next interval
        print(f"Sleeping for {INTERVAL_MINUTES} minutes...\n")
        time.sleep(INTERVAL_MINUTES * 60)

def run_once():
    """Collect one snapshot and exit"""
    success = collect_snapshot()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Single run mode (for cron)
        run_once()
    else:
        # Continuous mode
        try:
            run_continuous()
        except KeyboardInterrupt:
            print("\nStopped by user")
            sys.exit(0)
