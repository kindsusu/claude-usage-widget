# Claude Usage Widget

Always-on-top Windows desktop widget showing real-time Claude Max plan usage. Matches `claude.ai/settings/usage` exactly — pulls the same numbers via the official OAuth endpoint.

![widget preview](https://via.placeholder.com/280x180?text=Widget+Preview)

## Features

- **Real-time usage** — 5-hour session, 7-day total, Sonnet-only weekly
- **Light / Dark theme** toggle (☾/☀ button)
- **Transparency** slider popup (30–100%)
- **Smart top-most** — floats above only when Claude (or the widget itself) is the active window; recedes when you switch to other apps
- **Multi-monitor** aware — drag to any screen
- **20 pixel pets** — random pet assigned on first run, persistent (stored in config)
- **Gradient bars** — smooth green → yellow → red as usage climbs
- **Single file** — `widget.pyw` is fully self-contained (~280 KB with embedded pet sprites)

## Requirements

- Windows 10/11
- Python 3.8+
- [Claude Code](https://claude.com/code) installed and logged in (`claude login`)
- `pip install pillow`

The widget reads the OAuth token Claude Code stores in `~/.claude/.credentials.json` — no manual API key or cookie handling needed.

## Install

```bash
pip install pillow
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

20 pixel-art pets are embedded as base64 inside `widget.pyw`. On first run, one is randomly assigned and persisted in `widget_config.json`. To reroll, use the right-click menu → "펫 다시 뽑기".

## Token expiry

If you see "토큰 만료 (claude login)" in the footer, just run `claude login` in any terminal — the widget will pick up the refreshed token within one polling cycle.

## Credits

Inspired by [INNO-HI/ClaudeUsageWidget](https://github.com/INNO-HI/ClaudeUsageWidget) (Node.js) — that repo was the key reference for finding the OAuth `usage` endpoint. This is a Python/tkinter port with a different UI and a few extra features (smart topmost, pets, theme toggle).

## License

MIT — see [LICENSE](LICENSE).
