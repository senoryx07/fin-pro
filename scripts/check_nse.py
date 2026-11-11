"""
Fail fast if NSE can't be reached from this machine.

NSE blocks some cloud IP ranges; checking up front gives a clear error
instead of an hour of silently skipped downloads.
"""

import sys

import requests


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0 Safari/537.36"
    ),
    "Accept": "application/json,text/html,*/*",
}

CHECKS = {
    "archives": "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv",
    "api": (
        "https://www.nseindia.com/api/top-corp-info"
        "?symbol=RELIANCE&market=equities"
    ),
}


def main() -> int:
    session = requests.Session()
    session.headers.update(HEADERS)

    failures = []

    try:
        session.get("https://www.nseindia.com", timeout=20)
    except requests.RequestException as exc:
        failures.append(f"home page: {exc}")

    for name, url in CHECKS.items():
        try:
            response = session.get(url, timeout=30)
            print(f"{name}: HTTP {response.status_code}, {len(response.content)} bytes")

            if response.status_code != 200 or not response.content:
                failures.append(f"{name}: HTTP {response.status_code}")
        except requests.RequestException as exc:
            failures.append(f"{name}: {exc}")

    if failures:
        print("NSE is not reachable from this runner:", *failures, sep="\n  ")
        return 1

    print("NSE reachable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
