# Codex Pulse

A small project for keeping Codex usage visible while you work.

## First step: use Codex's built-in usage meters

Recent Codex builds can show the five-hour and weekly usage windows in the terminal status line. Add this to your Codex `config.toml` (usually `%USERPROFILE%\.codex\config.toml` on Windows):

```toml
[tui]
status_line = ["model-with-reasoning", "current-dir", "five-hour-limit", "weekly-limit"]
```

Then restart Codex. You can also use `/statusline` in the Codex TUI to configure the built-in status line interactively.

This project does not modify your Codex configuration automatically. The native status line is the dependable starting point; custom status-line commands are not currently a supported config option in Codex's documented configuration.

## Project direction

The initial goal is a clear, low-maintenance usage display inspired by [claude-pulse](https://github.com/NoobyGains/claude-pulse), tailored to Codex. Next steps:

- Confirm which Codex versions expose the native usage meters.
- Explore whether Codex stores additional usage details locally in a stable format.
- Add an optional custom monitor only if it can use a supported, privacy-conscious data source.

## License

MIT. See [LICENSE](LICENSE).
