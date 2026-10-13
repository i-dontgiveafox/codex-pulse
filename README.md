# Codex Pulse

**A calm, customizable usage strip for the bottom of Codex CLI.**

Codex Pulse helps you shape Codex's native footer around the things you care about: model, context, five-hour and weekly remaining usage, git state, task progress, and run permissions. It uses Codex's own status-line items and active theme colors, so the information stays inside the real Codex TUI.

```text
gpt-6.1-sol · project · Context 42% used · 5h 28% left · weekly 71% left · ⚡ Fast
```

The exact labels and values are rendered by Codex and depend on your version and current session.

## Install

Requires Python 3.11+ and Codex CLI. No third-party packages or API keys.

```powershell
python .\codex_pulse.py preview
python .\codex_pulse.py apply pulse
```

Restart Codex to see the updated footer. The setting is stored in your user-level Codex config (`%USERPROFILE%\.codex\config.toml` on Windows, or `$CODEX_HOME/config.toml` when `CODEX_HOME` is set), so it persists across interactive CLI launches. Your current `config.toml` is backed up beside itself before an update. Codex Pulse changes only `[tui].status_line` and `[tui].status_line_use_colors`.

To open Codex's own interactive picker at any time, enter `/statusline` in the TUI. Use `/theme` to change the palette that colors the footer.

## Presets

| Preset | Footer contents |
| --- | --- |
| `pulse` | Model, context, five-hour limit, weekly limit, Fast mode |
| `studio` | Model, project, git branch, context, both limits |
| `sprint` | Model, task progress, run state, context, both limits |
| `sentinel` | Model, permissions, approval mode, both limits |
| `wide` | Model, project, branch, task progress, context, both limits, Fast mode |

```powershell
python .\codex_pulse.py presets
python .\codex_pulse.py preview studio
python .\codex_pulse.py apply studio
python .\codex_pulse.py customize
python .\codex_pulse.py show
```

`customize` lets you choose footer items and their order, then opt into the active Codex theme colors. The preview is a guide: Codex supplies the final wording, live values, and theme styling.

## What it can show

The current Codex TUI offers built-in items for model and reasoning, project or working directory, git branch and committed branch changes, task progress, run state, permissions and approval mode, context usage, five-hour and weekly remaining usage, Fast mode, token counts, and more. Some fields appear only when Codex has data for them.

Codex Pulse keeps the layout compact and gives you presets for different workflows. It does not try to estimate usage from session logs or make extra network requests.

## A note about customization

Codex currently owns the footer renderer. It supports choosing and ordering built-in items and using the active theme's colors. Codex does not expose a supported external command hook for arbitrary labels, custom bar glyphs, or per-item colors. Pulse uses the supported footer API instead of patching or replacing the Codex executable. See the [Codex status-line picker source](https://github.com/openai/codex/blob/main/codex-rs/tui/src/bottom_pane/status_line_setup.rs) for the current item list and the [custom status-line request](https://github.com/openai/codex/issues/17827) for the external-renderer limitation.

## License

MIT. See [LICENSE](LICENSE).
