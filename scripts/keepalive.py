#!/usr/bin/env python3
"""TITAN AIO — HF Spaces Keep-Alive

Runs as systemd service. Pings HF Space every 5 minutes.
Auto-restarts if VPS reboots.

Setup:
    sudo cp /home/Aa/ugc/scripts/titan-keepalive.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable titan-keepalive
    sudo systemctl start titan-keepalive

Logs:
    journalctl -u titan-keepalive -f
"""

import time
import urllib.request
import json
import sys
from datetime import datetime

HF_SPACE_URL = "https://badjals-hehehe.hf.space"
INTERVAL = 300  # 5 minutes
LOG_FILE = "/home/Aa/ugc/data/keepalive.log"


def ping():
    """Ping HF Space /keepalive endpoint."""
    try:
        url = f"{HF_SPACE_URL}/keepalive"
        req = urllib.request.Request(url, headers={"User-Agent": "TITAN-KeepAlive/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            msg = f"{datetime.now().isoformat()} OK status={data.get('status', '?')}"
            print(msg, flush=True)
            _log(msg)
            return True
    except Exception as e:
        msg = f"{datetime.now().isoformat()} ERROR {e}"
        print(msg, flush=True)
        _log(msg)
        return False


def _log(msg):
    """Append to log file."""
    try:
        LOG_FILE and open(LOG_FILE, "a").write(msg + "\n")
    except Exception:
        pass


def main():
    print(f"Titan KeepAlive started — pinging {HF_SPACE_URL} every {INTERVAL}s", flush=True)
    _log(f"Service started at {datetime.now().isoformat()}")

    while True:
        try:
            ping()
        except Exception as e:
            _log(f"Unexpected error: {e}")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
