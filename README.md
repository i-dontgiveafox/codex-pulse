# Codex Pulse

**A calm, customizable usage strip for the bottom of Codex CLI.**

Codex Pulse shapes Codex's native footer around the things you care about: model, context window, five-hour and weekly remaining usage, Git state, task progress, and run permissions. It uses Codex's native status-line renderer and active theme colors, so your usage remains inside the real Codex TUI without extra overlays or API keys.

```text
gpt-6.1-sol · project · Context 42% used · 5h 28% left · weekly 71% left · ⚡ Fast
```

---

## Install & Quick Start

Requires Python 3.11+ and Codex CLI. Zero third-party dependencies.

```powershell
# Browse presets and preview footer layouts
python .\codex_pulse.py presets
python .\codex_pulse.py preview pulse

# Apply a preset to your Codex CLI configuration
python .\codex_pulse.py apply pulse
```

Restart Codex CLI to see your updated footer.

*Settings are saved to `%USERPROFILE%\.codex\config.toml` (or `$CODEX_HOME/config.toml`). Codex Pulse automatically creates a timestamped `.bak` backup of your configuration before every update.*

---

## Presets Showcase

| Preset | Contents | Best For |
|---|---|---|
| `pulse` *(Default)* | Model, Context Used, 5-Hour Limit, Weekly Limit, Fast Mode | Calm, daily coding & usage tracking |
| `studio` | Model, Project Name, Git Branch, Context Used, Both Limits | Multi-repository engineering |
| `sprint` | Model, Task Progress, Run State, Context Used, Both Limits | Autonomous agent runs & multi-step tasks |
| `sentinel` | Model, Permission Profile, Approval Mode, Both Limits | Sensitive setups & secure sandboxes |
| `wide` | Model, Project, Branch, Task Progress, Context, Both Limits, Fast Mode | Panoramic monitors & full telemetry |

```powershell
python .\codex_pulse.py preview studio
python .\codex_pulse.py apply studio
python .\codex_pulse.py show
```

### Visual Layout Previews

#### `pulse`
```text
  ┌── [ CODEX PULSE • PULSE ] ─────────────────────────────
  │  [MODEL+REASON] ┆ [CONTEXT] ┆ [5H LIMIT] ┆ [WEEK LIMIT] ┆ [FAST]
  ├── [ LIVE STRIP ] ──────────────────────────────────────────────────
  │  gpt-6.1-sol (medium) · Context 42% used · 5h 28% left · weekly 71% left · ⚡ Fast
  └── Note: Layout preview only. Live values & colors rendered natively by Codex.
```

#### `studio`
```text
  ┌── [ CODEX PULSE • STUDIO ] ────────────────────────────
  │  [MODEL+REASON] ┆ [PROJECT] ┆ [BRANCH] ┆ [CONTEXT] ┆ [5H LIMIT] ┆ [WEEK LIMIT]
  ├── [ LIVE STRIP ] ──────────────────────────────────────────────────
  │  gpt-6.1-sol (medium) · codex-pulse · main* · Context 42% used · 5h 28% left · weekly 71% left
  └── Note: Layout preview only. Live values & colors rendered natively by Codex.
```

#### `wide`
```text
  ┌── [ CODEX PULSE • WIDE ] ──────────────────────────────
  │  [MODEL+REASON] ┆ [PROJECT] ┆ [BRANCH] ┆ [PROGRESS] ┆ [CONTEXT] ┆ [5H LIMIT] ┆ [WEEK LIMIT] ┆ [FAST]
  ├── [ LIVE STRIP ] ──────────────────────────────────────────────────
  │  gpt-6.1-sol (medium) · codex-pulse · main* · Step 3/5 · Context 42% used · 5h 28% left · weekly 71% left · ⚡ Fast
  └── Note: Layout preview only. Live values & colors rendered natively by Codex.
```

---

## Customizable Themes

Codex Pulse leverages Codex's native `status_line_use_colors = true` setting so that your status line footer dynamically inherits your active Codex TUI theme palette.

Change your theme at any time in the Codex TUI by entering `/theme`, or set `[tui].theme` in `config.toml`.

### Theme Palette Previews

Here is how your footer renders across Codex's popular built-in themes:

#### 🌌 Tokyo Night
Electric cyan model badge, deep indigo dividers, lavender context, and vibrant yellow Fast mode:
```text
  [gpt-6.1-sol] · [codex-pulse] · [Context 34% used] · [5h 82% left] · [⚡ Fast]
```

#### ☕ Catppuccin Mocha
Soft sapphire model label, mauve task step, peach context usage, and pastel green quota:
```text
  [gpt-6.1-sol] · [Step 3/5] · [Context 42% used] · [5h 68% left] · [weekly 85% left]
```

#### ❄️ Nord
Arctic frost cyan model, polar night segment dividers, and aurora green remaining quotas:
```text
  [gpt-6.1-sol] · [git:main*] · [Context 28% used] · [5h 91% left] · [⚡ Fast]
```

#### 🧛 Dracula
Vampire purple accent, cyan model tag, neon pink context percentage, and green limit indicators:
```text
  [gpt-6.1-sol (medium)] · [Context 45% used] · [5h 74% left] · [weekly 62% left]
```

#### 🍂 Gruvbox
Warm retro amber model, aqua context window metrics, bright orange 5h limits, and yellow Fast badge:
```text
  [gpt-6.1-sol] · [codex-pulse] · [Context 38% used] · [5h 80% left] · [⚡ Fast]
```

#### 🌑 Minimal Monochrome
Clean, high-contrast black-and-white for distraction-free terminal work (`status_line_use_colors = false`):
```text
  gpt-6.1-sol | codex-pulse | main* | Context 42% used | 5h 28% left | weekly 71% left
```

---

## Interactive Customizer

Build a personalized footer layout selecting status items in your preferred order:

```powershell
python .\codex_pulse.py customize
```

### Available Status Items

Items are organized into 6 intuitive categories:

- **🧠 Model & Intelligence**: Model & reasoning effort (`model-with-reasoning`), model name only (`model`), reasoning effort level (`reasoning`).
- **📁 Workspace & Git**: Project name (`project-name`), working directory (`current-dir`), thread title (`thread-name`), Git branch (`git-branch`), branch diff changes (`branch-changes`), pull request number (`pull-request-number`).
- **⚡ Progress & Execution**: Latest task step (`task-progress`), run state (`run-state`).
- **📊 Context & Quotas**: Context used % (`context-used`), context remaining % (`context-remaining`), window size (`context-window-size`), 5-hour quota (`five-hour-limit`), weekly quota (`weekly-limit`), Fast mode (`fast-mode`).
- **🛡️ Security & Permissions**: Permission profile (`permissions`), approval mode (`approval-mode`).
- **📈 Metrics & System**: Session tokens used (`used-tokens`), input tokens (`total-input-tokens`), output tokens (`total-output-tokens`), Codex version (`codex-version`).

---

## Configuration Details

Codex Pulse updates only two keys inside your user-level Codex configuration (`config.toml`):
- `[tui].status_line`: Array of selected item IDs in your chosen display order.
- `[tui].status_line_use_colors`: Boolean (`true` or `false`) to enable or disable theme palette colors.

To open Codex's built-in interactive item picker at any time, run `/statusline` in the TUI.

---

## License

MIT. See [LICENSE](LICENSE).
