# Rate-Limit Investigation — 2026-05-27

Empirical probe of `https://api.anthropic.com/api/oauth/usage` to
establish when the widget's polling triggers HTTP 429 and how the
lockout behaves. The findings drove commit `6ed3288` which lowered
the default `refresh_seconds` from 600 → 180 and introduced the
`EPHEMERAL_KEYS` mechanism so a session override does not persist.

This document is a baseline. If a future 429 episode looks different,
diff the new behavior against the logs in `logs/` to quantify the
policy drift.

## Background

Commit [`af7cbe1`](../../../../commit/af7cbe1) — *"Respect Retry-After
header, raise default interval to 10min"* — recorded the previous
empirical guess:

> "Empirical guess: endpoint allows ~10-12 polls/hour per token,
> sliding window. 10 minute interval = 6/hour, safely under."
>
> "observed 2276 sec = 38 min" Retry-After

That observation pinned the safe default at 600s. This investigation
re-measured the threshold under controlled conditions to see whether
a faster interval (300s / 180s) was actually safe.

## Methodology

A single-caller logger (`rate_test.py`) polls the endpoint at a fixed
`INTERVAL` and writes one log line per response. It captures:

- HTTP status code
- `Retry-After` header value
- Response body (on error)
- Server-side latency (ms)
- Reported utilization (`five_hour`, `seven_day`, `seven_day_omelette`)

The widget itself was stopped during testing so the logger was the
sole consumer of the rate-limit budget for the test token. Phases
were run sequentially, halving the interval each time:

| Phase | Interval | Effective rate | Log file | Outcome |
|-------|----------|----------------|----------|---------|
| 1 | 300s | 12/hr | [`logs/300s.log`](logs/300s.log) | 1 call, cut short |
| 2 | 180s | 20/hr | [`logs/180s.log`](logs/180s.log) | 13/13 × 200 in 36 min |
| 3 | 90s | 40/hr | [`logs/90s.log`](logs/90s.log) | 13/13 × 200 in 18 min |
| 4 | 60s | 60/hr | [`logs/60s.log`](logs/60s.log) | first 429 at call #9 (8 min) |

## Findings

### 1. Threshold is ~30 calls/hour, not 12/hr

The first 429 of phase 4 (60s) landed at call #9 — 21:09:17 KST.
The trailing-60-min count at that moment was ~32 calls (including
all of phases 2 and 3). The widget author's previous estimate of
10-12/hr was conservative by roughly 3×.

### 2. `Retry-After: 0` — advisory, not enforced cooldown

Every 429 in this investigation returned `Retry-After: 0s`. Body:

```json
{
  "error": {
    "type": "rate_limit_error",
    "message": "Rate limited. Please try again later."
  }
}
```

The previous observation of `Retry-After: 2276s` (38 minutes) was not
reproduced. The policy may have changed since that recording, or the
trigger conditions for a long lockout are stricter than the burst we
generated here.

### 3. Lockout recovery is short

The 60s phase saw 3 consecutive 429s (#009-#011), then a 200 (#012)
exactly 3 minutes after the first 429. Continued polling at 60s
yielded an alternating 200/429 pattern: refill rate ≈ 0.5 tokens/min
= 30/hr, matching the inferred threshold. After ~7 minutes of
alternating, a 2:1 fail/success pattern emerged briefly — possible
mild deepening, or noise around the boundary.

### 4. Network discontinuity reset the counter

At calls #20 and #21 a 2-minute DNS outage occurred
(`<urlopen error [Errno 11001] getaddrinfo failed>`). After the
network recovered, **23+ consecutive 200s** followed at the same 60s
cadence, well over the 30/hr ceiling — see lines starting `#022` in
[`logs/60s.log`](logs/60s.log).

The most likely explanation is that DNS re-resolution routed the
connection to a different Cloudflare edge, where the per-edge rate
counter was untouched. This is a caveat — widgets behind unstable
networks may see less consistent throttling than the threshold
suggests.

### 5. Error is Anthropic application-layer, not Cloudflare WAF

The body shape (`{"error": {"type": "rate_limit_error", ...}}`) is
Anthropic's standard error format. No `x-ratelimit-*` response
headers are exposed (unlike the Messages API). `Server: cloudflare`
+ `_cfuvid` cookie suggest Cloudflare handles the edge transport,
but the 429 decision itself comes from the application layer.

## Resulting Default

| `refresh_seconds` | Rate | Margin vs ~30/hr | Verdict |
|-----------|------|------------------|---------|
| 600 (previous default) | 6/hr | 20% | safe, slow |
| **180 (new default)** | **20/hr** | **67%** | **safe, responsive** |
| 90 | 40/hr | 133% | sustained burst |
| 60 | 60/hr | 200% | triggers within 8 min |

180s polls every 3 minutes — 3× more responsive than the old default,
still comfortably under threshold for an indefinite runtime.

The companion change in `widget.pyw` (commit `6ed3288`) also makes
`refresh_seconds` ephemeral: the right-click prompt updates the
interval for the current session only, so an accidental burst setting
cannot stick across restarts and silently drain the bucket.

## Reproducing

```bash
# From this directory:
python rate_test.py
```

Edit the `INTERVAL` constant at the top of `rate_test.py` to change
the cadence. Logs append to `rate_test.log` in the same directory.

Stop the widget before running so this script is the only caller for
your token.

## Comparing Against a Future Incident

If you hit a future 429 episode and want to know whether Anthropic
changed the policy, compare the new behavior against the baselines
here:

| Signal | 2026-05-27 baseline | If different now... |
|--------|---------------------|---------------------|
| `Retry-After` value on 429 | `0` (advisory) | Strict cooldown re-introduced |
| Lockout duration | 3 min (one refill) | Longer = burst tolerance reduced |
| First 429 at 60s pace | ~8 min in | Earlier = threshold lowered |
| Error `type` field | `rate_limit_error` | New error class |
| Sustained safe rate | ~20/hr (180s) | Adjust default accordingly |

Re-run `rate_test.py` with the same phases (300 → 180 → 90 → 60) to
generate fresh logs and diff against `logs/`.
