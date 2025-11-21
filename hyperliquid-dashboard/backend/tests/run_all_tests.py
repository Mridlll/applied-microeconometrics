#!/usr/bin/env python3
"""
Complete test runner for HIP-3 Analytics Platform
Generates test data and runs all API tests
"""

import subprocess
import sys
import time
import os
import signal

def run_command(cmd, description):
    """Run a command and print results"""
    print(f"\n{'='*80}")
    print(f"🔧 {description}")
    print(f"{'='*80}\n")

    result = subprocess.run(cmd, shell=True, capture_output=False)

    if result.returncode != 0:
        print(f"\n❌ {description} failed")
        return False

    print(f"\n✅ {description} completed")
    return True

def main():
    """Run complete test suite"""
    print("="*80)
    print("🧪 HIP-3 Analytics Platform - Complete Test Suite")
    print("="*80)

    # Step 1: Generate test data
    if not run_command("python3 generate_test_data.py", "Generating Test Data"):
        return 1

    # Step 2: Run API tests with server
    print(f"\n{'='*80}")
    print("🚀 Starting API Server and Running Tests")
    print(f"{'='*80}\n")

    # Start server in background
    server_env = os.environ.copy()
    server_env['PYTHONPATH'] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Update server to use test database temporarily
    server_file = "../api/server_v2.py"
    with open(server_file, 'r') as f:
        server_code = f.read()

    server_code_test = server_code.replace('hip3_analytics.db', 'hip3_analytics_test.db')

    with open(server_file, 'w') as f:
        f.write(server_code_test)

    print("Starting API server...")
    server_process = subprocess.Popen(
        ["python3", "../api/server_v2.py"],
        env=server_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    print("Waiting for server to be ready...")
    time.sleep(4)

    # Check if server is running
    try:
        import requests
        response = requests.get("http://localhost:5000/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server is ready")
        else:
            print("❌ Server health check failed")
            server_process.kill()
            # Restore original server file
            with open(server_file, 'w') as f:
                f.write(server_code)
            return 1
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        server_process.kill()
        # Restore original server file
        with open(server_file, 'w') as f:
            f.write(server_code)
        return 1

    # Run tests
    print("\nRunning API endpoint tests...\n")
    test_result = subprocess.run(["python3", "test_api_endpoints.py"])

    # Cleanup: stop server
    print("\nStopping server...")
    server_process.terminate()
    server_process.wait()

    # Restore original server file
    with open(server_file, 'w') as f:
        f.write(server_code)

    print("✅ Cleanup complete")

    # Final summary
    print("\n" + "="*80)
    if test_result.returncode == 0:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*80)
    print("\n📊 Test Database: hip3_analytics_test.db")
    print("🚀 Ready to build the UI!\n")

    return test_result.returncode

if __name__ == "__main__":
    sys.exit(main())
