"""Health check utility script for Cognitia Runtime."""

from __future__ import annotations

import json
import sys
import urllib.request
from typing import Any


def check_health(url: str = "http://127.0.0.1:8000/v1/health") -> int:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Cognitia-HealthCheck/1.0"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                print(f"[HEALTH CHECK PASS] Status: {data.get('status')}, ABI: {data.get('cognitive_abi_version')}")
                return 0
            else:
                print(f"[HEALTH CHECK FAIL] Unexpected status code: {resp.status}")
                return 1
    except Exception as e:
        print(f"[HEALTH CHECK ERROR] Could not connect to {url}: {e}")
        return 2


if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/v1/health"
    sys.exit(check_health(target_url))