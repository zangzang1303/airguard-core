#!/usr/bin/env python3
"""
AirGuard AI - Public Healthcheck & Smoke Test Runner (B4-OPS-02)
Usage:
    python scripts/smoke_test_public.py --url http://localhost:8000
    python scripts/smoke_test_public.py --url https://airguard-backend.onrender.com
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error

def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def run_test(name: str, method: str, url: str, headers: dict = None, body: dict = None, expected_status: int = 200) -> bool:
    headers = headers or {}
    data = None
    if body:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    start_time = time.time()
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            elapsed = (time.time() - start_time) * 1000
            status = res.getcode()
            res_body = res.read().decode("utf-8")
            
            if status == expected_status:
                print(f"  [PASS] {name} ({status}) - {elapsed:.0f}ms")
                return True
            else:
                print(f"  [FAIL] {name} - Expected {expected_status}, got {status}")
                return False
    except urllib.error.HTTPError as e:
        elapsed = (time.time() - start_time) * 1000
        if e.code == expected_status:
            print(f"  [PASS] {name} ({e.code}) - {elapsed:.0f}ms")
            return True
        print(f"  [FAIL] {name} - HTTP Error {e.code}: {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"  [FAIL] {name} - Network/Connection Error: {e.reason}")
        return False
    except Exception as e:
        print(f"  [FAIL] {name} - Error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="AirGuard AI Public Smoke Test")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of backend (default: http://localhost:8000)")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    print_header(f"AIRGUARD AI SMOKE TEST SUITE - TARGET: {base_url}")

    results = []

    # 1. Healthcheck
    results.append(run_test("1. Health Endpoint (/health)", "GET", f"{base_url}/health"))

    # 2. Stations List
    results.append(run_test("2. Station Catalog (/api/v1/stations)", "GET", f"{base_url}/api/v1/stations"))

    # 3. Station S01 Current Measurement
    results.append(run_test("3. Station Current Data (/api/v1/stations/S01/current)", "GET", f"{base_url}/api/v1/stations/S01/current"))

    # 4. Station S01 History
    results.append(run_test("4. Station History (/api/v1/stations/S01/history?hours=24)", "GET", f"{base_url}/api/v1/stations/S01/history?hours=24"))

    # 5. Station Forecast
    results.append(run_test("5. Station Forecast (/api/v1/stations/S01/forecast?metric=pm25)", "GET", f"{base_url}/api/v1/stations/S01/forecast?metric=pm25"))

    # 6. Active Alerts
    results.append(run_test("6. Active Alerts (/api/v1/alerts)", "GET", f"{base_url}/api/v1/alerts"))

    # 7. Approvals (Manager HITL)
    results.append(run_test(
        "7. Approvals List (/api/v1/approvals)",
        "GET",
        f"{base_url}/api/v1/approvals",
        headers={"X-User-ID": "USR-002", "X-User-Role": "manager"}
    ))

    # 8. Agent Grounded Chat
    results.append(run_test(
        "8. AI Agent Chat (/api/v1/agent/chat)",
        "POST",
        f"{base_url}/api/v1/agent/chat",
        body={
            "message": "Chất lượng không khí trạm S01 hiện tại thế nào?",
            "user_id": "USR-001",
            "station_id": "S01"
        }
    ))

    # 9. Audit Logs
    results.append(run_test(
        "9. Audit Logs (/api/v1/audit-logs)",
        "GET",
        f"{base_url}/api/v1/audit-logs",
        headers={"X-User-ID": "USR-002", "X-User-Role": "manager"}
    ))

    # Summary
    passed = sum(1 for r in results if r)
    total = len(results)
    print_header(f"RESULT: {passed}/{total} TESTS PASSED")

    if passed == total:
        print("\nAll endpoints are healthy and ready for public demo!")
        sys.exit(0)
    else:
        print(f"\nWarning: {total - passed} endpoint(s) failed or returned error.")
        sys.exit(1)

if __name__ == "__main__":
    main()
