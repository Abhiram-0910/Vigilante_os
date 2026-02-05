#!/usr/bin/env python3
"""
Warm-up script: ping the API every 2 minutes to avoid cold starts.
Run in background on the same host as the server (e.g. cron or systemd).
Usage: python scripts/warmup.py [BASE_URL]
"""
import os
import sys
import time
import urllib.request

BASE_URL = os.getenv("WARMUP_URL", os.getenv("BASE_URL", "http://127.0.0.1:8000"))
API_KEY = os.getenv("VIBHISHAN_API_KEY", "gov_secure_access_2026")
INTERVAL_SEC = 120  # 2 minutes


def ping():
    try:
        req = urllib.request.Request(
            f"{BASE_URL.rstrip('/')}/health",
            headers={"User-Agent": "VIBHISHAN-Warmup/1.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            if r.status == 200:
                return True
    except Exception as e:
        print(f"Warmup ping failed: {e}", file=sys.stderr)
    return False


def main():
    if len(sys.argv) > 1:
        global BASE_URL
        BASE_URL = sys.argv[1].rstrip("/")
    print(f"Warmup: pinging {BASE_URL} every {INTERVAL_SEC}s")
    while True:
        ping()
        time.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    main()
