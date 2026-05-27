"""Probe /api/oauth/usage and log every response.

Single-caller logger used in the 2026-05-27 rate-limit investigation
(see README.md). Run while the widget is STOPPED so this script is
the sole consumer of the rate-limit budget for the local Claude
token in ~/.claude/.credentials.json.

Tune INTERVAL to the cadence you want to probe.
"""
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

# Default: matches the widget's post-investigation default (180s = 20/hr).
# Lower this (e.g. 60) to reproduce the rate-limit conditions documented
# in README.md; raise it for a passive sanity check.
INTERVAL = 180

CREDS = Path.home() / ".claude" / ".credentials.json"
URL = "https://api.anthropic.com/api/oauth/usage"
LOG = Path(__file__).with_name("rate_test.log")


def log(msg):
    line = f"{datetime.now().isoformat(timespec='seconds')}  {msg}"
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


def get_token():
    return json.loads(CREDS.read_text(encoding="utf-8")).get(
        "claudeAiOauth", {}).get("accessToken")


def poll(n):
    token = get_token()
    if not token:
        log(f"#{n:03d} NO_TOKEN")
        return
    req = urllib.request.Request(URL, headers={
        "Authorization": f"Bearer {token}",
        "anthropic-beta": "oauth-2025-04-20",
        "Accept": "application/json",
        "User-Agent": "claude-usage-widget/2.0",
    })
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = int((time.time() - t0) * 1000)
            fh = (data.get("five_hour") or {}).get("utilization")
            sd = (data.get("seven_day") or {}).get("utilization")
            om = (data.get("seven_day_omelette") or {}).get("utilization")
            log(f"#{n:03d} 200 ({elapsed}ms) 5h={fh}% 7d={sd}% omelette={om}%")
    except urllib.error.HTTPError as e:
        retry = e.headers.get("Retry-After", "?")
        try:
            body = e.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            body = "<unreadable>"
        log(f"#{n:03d} HTTP {e.code} Retry-After={retry}s body={body!r}")
    except Exception as e:
        log(f"#{n:03d} EXCEPTION {type(e).__name__}: {e}")


def main():
    log(f"=== START interval={INTERVAL}s pid={__import__('os').getpid()} ===")
    n = 0
    while True:
        n += 1
        poll(n)
        try:
            time.sleep(INTERVAL)
        except KeyboardInterrupt:
            log("=== STOPPED by interrupt ===")
            sys.exit(0)


if __name__ == "__main__":
    main()
