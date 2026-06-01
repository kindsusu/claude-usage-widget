# Claude Usage Widget

Always-on-top Windows desktop widget showing real-time Claude Max plan usage. Matches `claude.ai/settings/usage` exactly — pulls the same numbers via the official OAuth endpoint.

![widget preview](https://via.placeholder.com/280x180?text=Widget+Preview)

## Features

- **Real-time usage** — 5-hour session, 7-day total, Sonnet-only weekly
- **Light / Dark theme** toggle (☾/☀ button)
- **Transparency** slider popup (30–100%)
- **Smart top-most** — floats above only when Claude (or the widget itself) is the active window; recedes when you switch to other apps
- **Multi-monitor** aware — drag to any screen
- **31 pixel pets** with whole-body animations (bounce/sway/float/squish/breathe), random assignment on first run
- **System tray** — X button minimizes to tray; left-click tray to toggle, right-click for menu
- **Gradient bars** — smooth green → yellow → red as usage climbs
- **Single file** — `widget.pyw` is fully self-contained (~280 KB with embedded pet sprites)

## Requirements

- Windows 10/11
- Python 3.8+
- [Claude Code](https://claude.com/code) installed and logged in (`claude login`)
- `pip install pillow pystray`

The widget reads the OAuth token Claude Code stores in `~/.claude/.credentials.json` — no manual API key or cookie handling needed. It also **auto-refreshes the token** when it expires, so it keeps working without running Claude Code (see [Token handling](#token-handling-automatic)).

## Install

```bash
pip install pillow pystray
```

Download `widget.pyw` and double-click `실행.bat`, or run directly:

```bash
pythonw widget.pyw
```

### Auto-start on boot

Create a shortcut to `widget.pyw` (target: `pythonw.exe "...\widget.pyw"`) and drop it into your Startup folder:

```
Win+R → shell:startup → paste shortcut
```

## How it works

The widget calls Anthropic's official OAuth usage endpoint directly:

```
GET https://api.anthropic.com/api/oauth/usage
Authorization: Bearer <token from ~/.claude/.credentials.json>
anthropic-beta: oauth-2025-04-20
```

Response shape:

```json
{
  "five_hour":        { "utilization": 18.0, "resets_at": "..." },
  "seven_day":        { "utilization": 7.0,  "resets_at": "..." },
  "seven_day_sonnet": { "utilization": 0.0,  "resets_at": "..." },
  "extra_usage":      { "is_enabled": false }
}
```

This is the same data `claude.ai/settings/usage` displays. The endpoint is undocumented but stable; it's what the [official Claude Code statusline payload](https://docs.claude.com/en/docs/claude-code/statusline) exposes via `rate_limits`.

## Configuration

Settings live in `widget_config.json` (auto-generated next to `widget.pyw`):

| Key | Default | Notes |
|---|---|---|
| `refresh_seconds` | 180 | How often to poll the API |
| `theme` | `light` | `light` or `dark` |
| `alpha` | 0.95 | Window transparency (0.3–1.0) |
| `smart_topmost` | true | Float only when Claude is active |
| `plan_label` | `Max` | Shown in title bar |
| `pet` | (random) | Key into the embedded pet sprites |
| `x`, `y` | 100, 100 | Window position |

Right-click the widget for the full menu (refresh, theme, pet reroll, settings, quit).

## Pet system

31 pixel-art pets are embedded as base64 inside `widget.pyw`. On first run, one is randomly assigned and persisted in `widget_config.json`. To reroll, use the right-click menu → "펫 다시 뽑기".

Each pet gets a deterministic animation style (bounce, sway, float, squish, or breathe) based on its name — same pet always animates the same way.

## System tray

Click the **X** on the widget to minimize it to the system tray (it does **not** quit — the process keeps running so the widget can be brought back instantly).

- **Tray icon left-click** → toggle widget visibility
- **Tray icon right-click** → menu (Show/Hide, Refresh now, Quit)
- The only way to fully quit is the **Quit** item in the tray menu

## Token handling (automatic)

The widget refreshes its own access token, so you normally **never** have to touch it:

- The OAuth **access token** lives ~8 hours. When it expires, the widget POSTs the stored **refresh token** to `platform.claude.com/v1/oauth/token` (public Claude Code `client_id`) and writes the rotated tokens back to `~/.claude/.credentials.json`.
- This works even if **Claude Code isn't running** and even after the **computer was powered off for days/weeks** — on next launch the widget just mints a fresh token from the refresh token.
- The token refresh endpoint is **separate** from the usage endpoint's rate limit, so auto-refresh never contributes to the `API limit` 429s.
- Refresh-token **rotation** is handled correctly (the new refresh token from each response is persisted).

### When you *do* need to act

The only time manual action is needed is if the **refresh token itself** becomes invalid — which is rare (lasts months to a year):

- Very long inactivity (months)
- Password change / sign-out elsewhere / Anthropic security revocation

Then the footer shows **"토큰 갱신 실패 · Claude Code에서 /login"** — just run `claude login` (or `/login` inside Claude Code) once and the widget recovers on the next poll.

## For AI agents (Claude Code, etc.)

If you're an AI assistant installing this on behalf of a user, follow these steps in order. Each step has a verification command — stop and tell the user if a step fails.

### Prerequisites (verify, do not auto-install)

```bash
# 1. Windows? (this widget is Windows-only — Win32 APIs)
ver   # should show "Microsoft Windows"

# 2. Python 3.8+
python --version

# 2b. Required Python packages
pip install pillow pystray

# 3. Claude Code installed and logged in
test -f "$USERPROFILE/.claude/.credentials.json" && python -c "
import json
d = json.load(open(r'$USERPROFILE/.claude/.credentials.json'))
print('logged in:', 'claudeAiOauth' in d and bool(d['claudeAiOauth'].get('accessToken')))
"
```

If any prerequisite is missing, instruct the user:
- No Python → install from https://www.python.org/downloads/ with "Add Python to PATH" checked
- No Claude Code → `npm install -g @anthropic-ai/claude-code`
- Not logged in → user must run `claude login` themselves (browser OAuth, can't be automated)

### Install

```bash
# Pick a stable install location — user's home or Desktop
INSTALL_DIR="$HOME/claude-usage-widget"

# Clone
git clone https://github.com/kindsusu/claude-usage-widget.git "$INSTALL_DIR"

# Install Python deps
pip install pillow pystray

# Verify imports work
python -c "from PIL import Image, ImageTk; import pystray; print('deps OK')"
```

### Launch

```bash
# Use cmd //c on Git Bash to avoid bash interpreting Windows paths
cmd //c start "" pythonw "$INSTALL_DIR/widget.pyw"

# Verify it stayed alive after 2 seconds
sleep 2 && tasklist | grep -i pythonw
```

If `pythonw` is not in PATH, use the full path: `C:/Users/<user>/AppData/Local/Programs/Python/Python3xx/pythonw.exe`.

### Autostart on boot (optional)

```powershell
$lnk = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\Claude Usage Widget.lnk"
$pythonw = (Get-Command pythonw).Source
$widget = "$env:USERPROFILE\claude-usage-widget\widget.pyw"
$sh = New-Object -ComObject WScript.Shell
$shortcut = $sh.CreateShortcut($lnk)
$shortcut.TargetPath = $pythonw
$shortcut.Arguments = "`"$widget`""
$shortcut.WorkingDirectory = Split-Path $widget -Parent
$shortcut.Save()
```

### Common issues

| Symptom | Likely cause | Fix |
|---|---|---|
| Widget process starts but no window visible | `widget_config.json` has off-screen `x`/`y` | Delete `widget_config.json` and relaunch |
| Pet (image) doesn't show | Old PIL or wrong widget version | `pip install --upgrade pillow`, ensure widget.pyw is fresh from this repo |
| Footer shows "토큰 갱신 실패" | refresh token invalid (rare) | User runs `claude login` once |
| Footer shows "API rate limited" | Too many polls in short time | Wait 5–10 min; widget auto-backs-off |
| Title bar shows `●` instead of pet | `ImageTk.PhotoImage` called before `tk.Tk()` | Bug in older version — pull latest |

### Do NOT

- Do NOT modify `~/.claude/.credentials.json` (Claude Code owns it)
- Do NOT bundle your own PETS_B64 unless rebuilding from `pets/` source images
- Do NOT change the API endpoint or headers — `anthropic-beta: oauth-2025-04-20` is required

## Credits

Inspired by [INNO-HI/ClaudeUsageWidget](https://github.com/INNO-HI/ClaudeUsageWidget) (Node.js) — that repo was the key reference for finding the OAuth `usage` endpoint. This is a Python/tkinter port with a different UI and a few extra features (smart topmost, pets, theme toggle).

## License

MIT — see [LICENSE](LICENSE).
