#!/usr/bin/env python3
"""Configure Codex CLI's native status line with compact usage-focused presets."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
import sys
import tempfile
import tomllib
from pathlib import Path


def init_terminal() -> None:
    """Initialize terminal for UTF-8 encoding and ANSI virtual terminal processing on Windows."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure") and stream.encoding and stream.encoding.lower() != "utf-8":
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)
        except Exception:
            pass


class UI:
    """Helper for ANSI colors, text styling, and terminal dividers."""

    def __init__(self) -> None:
        init_terminal()
        self.enabled = (
            "NO_COLOR" not in os.environ
            and (
                "FORCE_COLOR" in os.environ
                or "CLICOLOR_FORCE" in os.environ
                or sys.stdout.isatty()
            )
        )
        self.unicode_ok = self._test_encoding("┌─│└┆•⚡🧠")

    @staticmethod
    def _test_encoding(sample: str) -> bool:
        encoding = sys.stdout.encoding or "ascii"
        try:
            sample.encode(encoding)
            return True
        except (UnicodeEncodeError, LookupError):
            return False

    def _wrap(self, code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.enabled else text

    def bold(self, text: str) -> str:
        return self._wrap("1", text)

    def dim(self, text: str) -> str:
        return self._wrap("2", text)

    def cyan(self, text: str) -> str:
        return self._wrap("96", text)

    def bright_blue(self, text: str) -> str:
        return self._wrap("94", text)

    def green(self, text: str) -> str:
        return self._wrap("92", text)

    def yellow(self, text: str) -> str:
        return self._wrap("93", text)

    def magenta(self, text: str) -> str:
        return self._wrap("95", text)

    def red(self, text: str) -> str:
        return self._wrap("91", text)

    def white(self, text: str) -> str:
        return self._wrap("97", text)

    @property
    def box_top(self) -> str:
        return "┌──" if self.unicode_ok else "+--"

    @property
    def box_mid(self) -> str:
        return "├──" if self.unicode_ok else "+--"

    @property
    def box_bot(self) -> str:
        return "└──" if self.unicode_ok else "+--"

    @property
    def box_vert(self) -> str:
        return "│" if self.unicode_ok else "|"

    @property
    def box_line(self) -> str:
        return "─" if self.unicode_ok else "-"

    @property
    def divider(self) -> str:
        return "┆" if self.unicode_ok else "|"

    @property
    def dot(self) -> str:
        return "·" if self.unicode_ok else "-"

    @property
    def bullet(self) -> str:
        return "•" if self.unicode_ok else "*"

    def icon(self, emoji: str) -> str:
        return f"{emoji} " if self.unicode_ok else ""


ui = UI()


PRESETS: dict[str, tuple[str, ...]] = {
    "pulse": (
        "model-with-reasoning",
        "context-used",
        "five-hour-limit",
        "weekly-limit",
        "fast-mode",
    ),
    "studio": (
        "model-with-reasoning",
        "project-name",
        "git-branch",
        "context-used",
        "five-hour-limit",
        "weekly-limit",
    ),
    "sprint": (
        "model-with-reasoning",
        "task-progress",
        "run-state",
        "context-used",
        "five-hour-limit",
        "weekly-limit",
    ),
    "sentinel": (
        "model-with-reasoning",
        "permissions",
        "approval-mode",
        "five-hour-limit",
        "weekly-limit",
    ),
    "wide": (
        "model-with-reasoning",
        "project-name",
        "git-branch",
        "task-progress",
        "context-used",
        "five-hour-limit",
        "weekly-limit",
        "fast-mode",
    ),
}

PRESET_METADATA: dict[str, dict[str, str]] = {
    "pulse": {
        "title": "Pulse (Balanced / Default)",
        "summary": "Clean, usage-focused layout for daily coding sessions.",
    },
    "studio": {
        "title": "Studio (Workspace & Git)",
        "summary": "Developer-first view featuring active project, branch, and usage limits.",
    },
    "sprint": {
        "title": "Sprint (Agentic Progress)",
        "summary": "Monitors task progress, execution state, and context during long agent runs.",
    },
    "sentinel": {
        "title": "Sentinel (Security & Governance)",
        "summary": "Prioritizes permissions, approval modes, and quotas for sensitive setups.",
    },
    "wide": {
        "title": "Wide (Panoramic & Comprehensive)",
        "summary": "Full panoramic footer displaying workspace, task status, quotas, and fast mode.",
    },
}

SECTIONS: tuple[tuple[str, str, tuple[tuple[str, str, str], ...]], ...] = (
    (
        "MODEL & INTELLIGENCE",
        "🧠",
        (
            ("model-with-reasoning", "Model & Reasoning", "Combined active model & reasoning effort"),
            ("model", "Model Name", "Model name only (e.g. gpt-6.1-sol)"),
            ("reasoning", "Reasoning Level", "Reasoning effort level (e.g. low, med, high)"),
        ),
    ),
    (
        "WORKSPACE & GIT",
        "📁",
        (
            ("project-name", "Project Name", "Active workspace or repository name"),
            ("current-dir", "Working Directory", "Path of current working directory"),
            ("thread-name", "Thread Name", "Current chat/task thread title"),
            ("git-branch", "Git Branch", "Active Git branch name"),
            ("branch-changes", "Branch Changes", "Committed/uncommitted branch diff stats"),
            ("pull-request-number", "Pull Request", "Associated GitHub/remote PR number"),
        ),
    ),
    (
        "PROGRESS & EXECUTION",
        "⚡",
        (
            ("task-progress", "Task Progress", "Active step & task progress indicator"),
            ("run-state", "Run State", "Execution state (idle, running, tool running)"),
        ),
    ),
    (
        "CONTEXT & QUOTAS",
        "📊",
        (
            ("context-used", "Context Used", "Percentage of context window consumed"),
            ("context-remaining", "Context Remaining", "Available headroom left in context window"),
            ("context-window-size", "Window Size", "Total capacity of the active model window"),
            ("five-hour-limit", "5-Hour Limit", "Remaining quota in 5-hour rolling limit"),
            ("weekly-limit", "Weekly Limit", "Remaining quota in weekly usage limit"),
            ("fast-mode", "Fast Mode", "Fast / Priority execution indicator"),
        ),
    ),
    (
        "SECURITY & PERMISSIONS",
        "🛡️",
        (
            ("permissions", "Permissions", "Sandbox execution security profile"),
            ("approval-mode", "Approval Mode", "Auto-run vs prompt-for-approval mode"),
        ),
    ),
    (
        "METRICS & DIAGNOSTICS",
        "📈",
        (
            ("used-tokens", "Session Tokens", "Total tokens consumed in current session"),
            ("total-input-tokens", "Input Tokens", "Prompt tokens sent to model"),
            ("total-output-tokens", "Output Tokens", "Completion tokens returned by model"),
            ("codex-version", "Codex Version", "Installed Codex CLI version tag"),
        ),
    ),
)

ITEMS: tuple[tuple[str, str], ...] = tuple(
    (item_id, label)
    for _, _, section_items in SECTIONS
    for item_id, label, _ in section_items
)
ITEM_IDS = {item_id for item_id, _ in ITEMS}

SHORT_TAGS: dict[str, str] = {
    "model-with-reasoning": "MODEL+REASON",
    "model": "MODEL",
    "reasoning": "EFFORT",
    "project-name": "PROJECT",
    "current-dir": "CWD",
    "thread-name": "THREAD",
    "git-branch": "BRANCH",
    "branch-changes": "DIFF",
    "pull-request-number": "PR",
    "task-progress": "PROGRESS",
    "run-state": "STATE",
    "context-used": "CONTEXT",
    "context-remaining": "HEADROOM",
    "context-window-size": "WINDOW",
    "five-hour-limit": "5H LIMIT",
    "weekly-limit": "WEEK LIMIT",
    "fast-mode": "FAST",
    "permissions": "SANDBOX",
    "approval-mode": "APPROVAL",
    "used-tokens": "TOKENS",
    "total-input-tokens": "INPUT",
    "total-output-tokens": "OUTPUT",
    "codex-version": "VERSION",
}

SAMPLE_VALUES: dict[str, str] = {
    "model-with-reasoning": "gpt-6.1-sol (medium)",
    "model": "gpt-6.1-sol",
    "reasoning": "effort: med",
    "project-name": "codex-pulse",
    "current-dir": "~/projects/codex-pulse",
    "thread-name": "#42-refactor",
    "git-branch": "main*",
    "branch-changes": "+14 -3",
    "pull-request-number": "PR #18",
    "task-progress": "Step 3/5",
    "run-state": "Ready",
    "context-used": "Context 42% used",
    "context-remaining": "58% headroom",
    "context-window-size": "128k window",
    "five-hour-limit": "5h 28% left",
    "weekly-limit": "weekly 71% left",
    "fast-mode": "⚡ Fast",
    "permissions": "sandbox: relaxed",
    "approval-mode": "manual approval",
    "used-tokens": "14.2k tokens",
    "total-input-tokens": "10.8k in",
    "total-output-tokens": "3.4k out",
    "codex-version": "codex v0.2.1",
}


def config_path(override: str | None) -> Path:
    if override:
        return Path(override).expanduser()
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "config.toml"
    return Path.home() / ".codex" / "config.toml"


def parse_config(text: str, path: Path) -> dict:
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"Cannot safely edit invalid TOML in {path}: {exc}") from exc


def table_bounds(lines: list[str], table_name: str) -> tuple[int, int] | None:
    header = re.compile(r"^\s*\[([^\]]+)\]\s*(?:#.*)?$")
    start = None
    for index, line in enumerate(lines):
        match = header.match(line)
        if not match:
            continue
        if start is not None:
            return start, index
        if match.group(1).strip() == table_name:
            start = index
    return (start, len(lines)) if start is not None else None


def assignment_end(lines: list[str], start: int, key: str) -> int:
    line = lines[start]
    value = line.split("=", 1)[1]
    if key != "status_line":
        return start + 1

    depth = 0
    in_string = False
    escaped = False
    for offset, chunk in enumerate(lines[start:], start):
        text = chunk.split("#", 1)[0]
        if offset == start:
            text = text.split("=", 1)[1]
        for char in text:
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
        if depth <= 0 and not in_string:
            return offset + 1
    raise ValueError(f"Could not find the end of the {key} array")


def toml_array(values: tuple[str, ...]) -> list[str]:
    if not values:
        return ["status_line = []"]
    rows = ["status_line = ["]
    rows.extend(f'    "{item}",' for item in values)
    rows.append("]")
    return rows


def set_tui_values(text: str, path: Path, values: tuple[str, ...], colors: bool) -> str:
    lines = text.splitlines()
    bounds = table_bounds(lines, "tui")
    if bounds is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend(["[tui]"])
        bounds = (len(lines) - 1, len(lines))

    start, end = bounds
    replacements = {
        "status_line": toml_array(values),
        "status_line_use_colors": [f"status_line_use_colors = {str(colors).lower()}"],
    }
    for key, replacement in replacements.items():
        bounds = table_bounds(lines, "tui")
        assert bounds is not None
        start, end = bounds
        pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
        found = next((i for i in range(start + 1, end) if pattern.match(lines[i])), None)
        if found is None:
            lines[end:end] = replacement
        else:
            stop = assignment_end(lines, found, key)
            lines[found:stop] = replacement

    updated = "\n".join(lines).rstrip() + "\n"
    parsed = parse_config(updated, path)
    tui = parsed.get("tui", {})
    if tui.get("status_line") != list(values):
        raise ValueError("Config validation failed: status_line did not round-trip")
    if tui.get("status_line_use_colors") is not colors:
        raise ValueError("Config validation failed: theme color setting did not round-trip")
    return updated


def save_config(path: Path, values: tuple[str, ...], colors: bool) -> Path:
    old_text = path.read_text(encoding="utf-8") if path.exists() else ""
    parse_config(old_text, path)
    new_text = set_tui_values(old_text, path, values, colors)
    path.parent.mkdir(parents=True, exist_ok=True)

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.name}.codex-pulse-{stamp}.bak")
    suffix = 1
    while backup.exists():
        backup = path.with_name(f"{path.name}.codex-pulse-{stamp}-{suffix}.bak")
        suffix += 1
    backed_up = False
    if path.exists() and old_text != new_text:
        shutil.copy2(path, backup)
        backed_up = True

    if old_text != new_text:
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", newline="\n", dir=path.parent,
                prefix=f".{path.name}.", suffix=".tmp", delete=False,
            ) as temporary:
                temp_path = Path(temporary.name)
                temporary.write(new_text)
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temp_path, path)
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()
    return backup if backed_up else path


def preview(
    values: tuple[str, ...],
    colors: bool,
    preset_name: str | None = None,
    config_file: str | Path | None = None,
) -> None:
    if preset_name is None:
        preset_name = next((name.upper() for name, items in PRESETS.items() if items == values), "CUSTOM")
    else:
        preset_name = preset_name.upper()

    color_state = ui.green("Enabled (active Codex theme)") if colors else ui.dim("Disabled (monochrome)")
    total_slots = f"{len(values)} items" if values else "None (empty)"

    if values:
        slots_display = f" {ui.divider} ".join(f"[{SHORT_TAGS.get(v, v.upper())}]" for v in values)
        simulated_display = f" {ui.dot} ".join(SAMPLE_VALUES.get(v, v) for v in values)
    else:
        slots_display = ui.dim("(no items configured)")
        simulated_display = ui.dim("(empty footer)")

    header_text = f"CODEX PULSE • {preset_name}" if config_file is None else "CODEX PULSE • ACTIVE CONFIG"
    rule = ui.box_line * 68
    print()
    print(f"  {ui.cyan(ui.box_top)} {ui.bold(f'[ {header_text} ]')} {ui.cyan(rule[:max(0, 48 - len(header_text))])}")
    if config_file is not None:
        print(f"  {ui.cyan(ui.box_vert)}  {ui.dim('Config File  :') } {ui.white(str(config_file))}")
        print(f"  {ui.cyan(ui.box_vert)}  {ui.dim('Preset Match :') } {ui.yellow(preset_name)}")
    print(f"  {ui.cyan(ui.box_vert)}  {ui.dim('Theme Colors :')} {color_state}")
    print(f"  {ui.cyan(ui.box_vert)}  {ui.dim('Total Slots  :') } {ui.white(ui.bold(total_slots))}")
    print(f"  {ui.cyan(ui.box_vert)}")
    print(f"  {ui.cyan(ui.box_mid)} {ui.bold('[ STATUS LINE SLOTS ]')} {ui.cyan(ui.box_line * 45)}")
    print(f"  {ui.cyan(ui.box_vert)}  {slots_display}")
    print(f"  {ui.cyan(ui.box_vert)}")
    print(f"  {ui.cyan(ui.box_mid)} {ui.bold('[ SIMULATED LIVE FOOTER ]')} {ui.cyan(ui.box_line * 41)}")
    print(f"  {ui.cyan(ui.box_vert)}  {ui.green(simulated_display)}")
    print(f"  {ui.cyan(ui.box_vert)}")
    print(f"  {ui.cyan(ui.box_bot)} {ui.dim('Note: Layout preview only. Live values & colors are rendered by Codex.')}")
    print()


def presets_catalog() -> None:
    print()
    print(f"  {ui.cyan(ui.box_top)} {ui.bold('[ CODEX PULSE • PRESET CATALOG ]')} {ui.cyan(ui.box_line * 36)}")
    print(f"  {ui.cyan(ui.box_vert)}  Pre-configured footer layouts tuned for different coding workflows.")
    print(f"  {ui.cyan(ui.box_vert)}")

    for name, values in PRESETS.items():
        meta = PRESET_METADATA.get(name, {})
        title = meta.get("title", name.title())
        summary = meta.get("summary", "")
        slots = f" {ui.divider} ".join(f"[{SHORT_TAGS.get(v, v.upper())}]" for v in values)

        sec_header = f"[ {name.upper()} ] ({title})"
        print(f"  {ui.cyan(ui.box_mid)} {ui.bold(ui.yellow(f'[ {name.upper()} ]'))} {ui.white(f'({title})')} {ui.cyan(ui.box_line * max(3, 62 - len(sec_header)))}")
        if summary:
            print(f"  {ui.cyan(ui.box_vert)}  {ui.dim(summary)}")
        print(f"  {ui.cyan(ui.box_vert)}  {ui.dim('Slots:')} {slots}")
        print(f"  {ui.cyan(ui.box_vert)}  {ui.dim('Apply:')} {ui.green(f'python codex_pulse.py apply {name}')}")
        print(f"  {ui.cyan(ui.box_vert)}")

    print(f"  {ui.cyan(ui.box_bot)} {ui.dim('Run')} {ui.green('python codex_pulse.py customize')} {ui.dim('to interactively build your own footer.')}")
    print()


def show(path: Path) -> None:
    if not path.exists():
        print(f"\n  {ui.yellow('[!]')} No Codex config found at {path}")
        print(f"      Run {ui.green('python codex_pulse.py apply pulse')} to initialize it.\n")
        return
    parsed = parse_config(path.read_text(encoding="utf-8"), path)
    tui = parsed.get("tui", {})
    configured = tuple(str(item) for item in tui.get("status_line", []))
    colors = bool(tui.get("status_line_use_colors", True))

    preset_match = next((name.upper() for name, items in PRESETS.items() if items == configured), "CUSTOM")
    preview(configured, colors, preset_name=preset_match, config_file=path)


def customize(path: Path) -> int:
    print()
    print(f"  {ui.cyan(ui.box_top)} {ui.bold('[ CODEX PULSE • FOOTER DESIGNER ]')} {ui.cyan(ui.box_line * 34)}")
    print(f"  {ui.cyan(ui.box_vert)}  Select status items to build your custom Codex CLI footer.")
    print(f"  {ui.cyan(ui.box_vert)}  Items will appear from left to right in the exact order chosen.")
    print(f"  {ui.cyan(ui.box_vert)}")

    current_idx = 1
    for section_title, icon, section_items in SECTIONS:
        sec_header = f"[ {ui.icon(icon)}{section_title} ]"
        print(f"  {ui.cyan(ui.box_mid)} {ui.bold(ui.white(sec_header))} {ui.cyan(ui.box_line * max(3, 62 - len(sec_header)))}")
        for item_id, label, description in section_items:
            badge = ui.cyan(f"[{current_idx:02d}]")
            item_lbl = ui.white(ui.bold(f"{label:<22}"))
            item_tag = ui.dim(f"{item_id:<21}")
            desc_tag = ui.dim(f"{ui.bullet} {description}")
            print(f"  {ui.cyan(ui.box_vert)}  {badge}  {item_lbl}  {item_tag}  {desc_tag}")
            current_idx += 1
        print(f"  {ui.cyan(ui.box_vert)}")

    print(f"  {ui.cyan(ui.box_mid)} {ui.bold('[ SELECTION GUIDE ]')} {ui.cyan(ui.box_line * 49)}")
    print(f"  {ui.cyan(ui.box_vert)}  Enter item numbers separated by commas in your desired display order.")
    print(f"  {ui.cyan(ui.box_vert)}  {ui.dim('Examples:')}")
    print(f"  {ui.cyan(ui.box_vert)}    {ui.yellow(f'{ui.bullet} Balanced usage :')} 1, 12, 15, 16, 17  {ui.dim('(Model, Context, 5h, Week, Fast)')}")
    print(f"  {ui.cyan(ui.box_vert)}    {ui.yellow(f'{ui.bullet} Full workspace :')} 1, 4, 7, 10, 12, 15, 16  {ui.dim('(Model, Project, Git, Task, Limits)')}")
    print(f"  {ui.cyan(ui.box_vert)}")

    raw = input(f"  {ui.cyan(ui.box_bot)} {ui.bold('Enter selection')} (or press Enter to cancel): ").strip()
    if not raw:
        print(f"\n  {ui.dim('No changes made.')}\n")
        return 0

    try:
        indexes = [int(part.strip()) for part in raw.split(",")]
        if len(set(indexes)) != len(indexes) or any(i < 1 or i > len(ITEMS) for i in indexes):
            raise ValueError
    except ValueError:
        print(f"\n  {ui.red('[!]')} Error: Please provide unique valid item numbers between 1 and {len(ITEMS)}.\n", file=sys.stderr)
        return 2

    values = tuple(ITEMS[i - 1][0] for i in indexes)
    print()
    colors_answer = input(f"  {ui.cyan('?')}  Use active Codex theme palette for footer colors? [Y/n]: ").strip().lower()
    colors = colors_answer not in {"n", "no"}

    preview(values, colors)

    confirm = input(f"  {ui.cyan('?')}  Apply this custom footer to your Codex configuration? [y/N]: ").strip().lower()
    if confirm not in {"y", "yes"}:
        print(f"\n  {ui.dim('Configuration discarded. No changes made.')}\n")
        return 0

    saved = save_config(path, values, colors)
    print()
    print(f"  {ui.green('✓')} {ui.bold('Successfully updated Codex configuration!')}")
    print(f"    {ui.dim('Config file :')} {path}")
    if saved != path:
        print(f"    {ui.dim('Backup file :')} {saved}")
    print(f"    {ui.yellow('Note        :')} Restart Codex CLI to load your new footer.\n")
    return 0


def main() -> int:
    init_terminal()
    parser = argparse.ArgumentParser(description="Customize Codex's native bottom status line")
    parser.add_argument("--config", help="Codex config.toml path (defaults to CODEX_HOME or ~/.codex)")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("presets", help="list available layouts")
    apply_parser = subparsers.add_parser("apply", help="apply a preset to Codex config")
    apply_parser.add_argument("preset", choices=tuple(PRESETS))
    preview_parser = subparsers.add_parser("preview", help="preview a preset without changing files")
    preview_parser.add_argument("preset", nargs="?", choices=tuple(PRESETS), default="pulse")
    subparsers.add_parser("customize", help="choose status-line items and their order")
    subparsers.add_parser("show", help="show the configured footer")
    args = parser.parse_args()
    path = config_path(args.config)

    try:
        if args.command == "presets":
            presets_catalog()
            return 0
        if args.command == "preview":
            preview(PRESETS[args.preset], True, preset_name=args.preset)
            return 0
        if args.command == "show":
            show(path)
            return 0
        if args.command == "customize":
            return customize(path)
        if args.command == "apply":
            values = PRESETS[args.preset]
            saved = save_config(path, values, True)
            preview(values, True, preset_name=args.preset)
            print(f"  {ui.green('✓')} {ui.bold(f'Applied preset {args.preset.upper()}!')}")
            print(f"    {ui.dim('Config file :')} {path}")
            if saved != path:
                print(f"    {ui.dim('Backup file :')} {saved}")
            print(f"    {ui.yellow('Note        :')} Restart Codex to see the new footer.\n")
            return 0
    except (OSError, ValueError) as exc:
        print(f"codex-pulse: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
