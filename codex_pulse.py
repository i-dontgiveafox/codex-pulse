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

ITEMS: tuple[tuple[str, str], ...] = (
    ("model-with-reasoning", "Model and reasoning"),
    ("model", "Model"),
    ("reasoning", "Reasoning level"),
    ("project-name", "Project name"),
    ("current-dir", "Working directory"),
    ("thread-name", "Thread name"),
    ("git-branch", "Git branch"),
    ("branch-changes", "Committed branch changes"),
    ("pull-request-number", "Pull request number"),
    ("task-progress", "Latest task progress"),
    ("run-state", "Run state"),
    ("context-used", "Context used"),
    ("context-remaining", "Context remaining"),
    ("context-window-size", "Context window size"),
    ("five-hour-limit", "Five-hour usage limit"),
    ("weekly-limit", "Weekly usage limit"),
    ("fast-mode", "Fast mode"),
    ("permissions", "Permission profile"),
    ("approval-mode", "Approval mode"),
    ("used-tokens", "Session tokens used"),
    ("total-input-tokens", "Session input tokens"),
    ("total-output-tokens", "Session output tokens"),
    ("codex-version", "Codex version"),
)
ITEM_IDS = {item_id for item_id, _ in ITEMS}


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


def preview(values: tuple[str, ...], colors: bool) -> None:
    short = {
        "model-with-reasoning": "MODEL",
        "model": "MODEL",
        "reasoning": "EFFORT",
        "project-name": "PROJECT",
        "current-dir": "FOLDER",
        "thread-name": "THREAD",
        "git-branch": "BRANCH",
        "branch-changes": "DIFF",
        "pull-request-number": "PR",
        "task-progress": "TASK",
        "run-state": "STATE",
        "context-used": "CONTEXT",
        "context-remaining": "CONTEXT LEFT",
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
    name = next((preset.upper() for preset, items in PRESETS.items() if items == values), "CUSTOM")
    accent, reset = ("\033[96m", "\033[0m") if sys.stdout.isatty() and "NO_COLOR" not in os.environ else ("", "")
    segments = "  |  ".join(short.get(value, value.upper()) for value in values) or "(empty footer)"
    print(f"\n  {accent}+-- CODEX PULSE  /  {name}{reset}")
    print(f"  {accent}|{reset}  {segments}")
    print(f"  {accent}+--{reset}  Theme colors: {'on' if colors else 'off'}")
    print("     Layout preview only; Codex supplies the live values and footer styling.\n")


def show(path: Path) -> None:
    if not path.exists():
        print(f"No Codex config found at {path}")
        return
    parsed = parse_config(path.read_text(encoding="utf-8"), path)
    tui = parsed.get("tui", {})
    configured = tui.get("status_line", [])
    preview(tuple(str(item) for item in configured), bool(tui.get("status_line_use_colors", True)))
    print(f"Config: {path}")


def customize(path: Path) -> int:
    print("\n  CODEX PULSE   /   BUILD YOUR FOOTER\n")
    for index, (item_id, label) in enumerate(ITEMS, 1):
        print(f"  {index:2}. {label:<30} {item_id}")
    print("\nEnter item numbers in the order you want them, separated by commas.")
    print("Example: 1,12,15,16,17  (model, context, 5h, week, Fast)\n")
    raw = input("Selection: ").strip()
    if not raw:
        print("No changes made.")
        return 0
    try:
        indexes = [int(part.strip()) for part in raw.split(",")]
        if len(set(indexes)) != len(indexes) or any(i < 1 or i > len(ITEMS) for i in indexes):
            raise ValueError
    except ValueError:
        print("Use unique item numbers from the list.", file=sys.stderr)
        return 2
    values = tuple(ITEMS[i - 1][0] for i in indexes)
    colors_answer = input("Use the active Codex theme colors? [Y/n]: ").strip().lower()
    colors = colors_answer not in {"n", "no"}
    preview(values, colors)
    confirm = input("Apply this footer to Codex? [y/N]: ").strip().lower()
    if confirm not in {"y", "yes"}:
        print("No changes made.")
        return 0
    saved = save_config(path, values, colors)
    print(f"Updated {path}")
    if saved != path:
        print(f"Backup:  {saved}")
    print("Restart Codex to see the new footer.")
    return 0


def main() -> int:
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
            for name, values in PRESETS.items():
                print(f"{name:<10} " + " · ".join(values))
            return 0
        if args.command == "preview":
            preview(PRESETS[args.preset], True)
            return 0
        if args.command == "show":
            show(path)
            return 0
        if args.command == "customize":
            return customize(path)
        if args.command == "apply":
            values = PRESETS[args.preset]
            saved = save_config(path, values, True)
            preview(values, True)
            print(f"Updated {path}")
            if saved != path:
                print(f"Backup:  {saved}")
            print("Restart Codex to see the new footer.")
            return 0
    except (OSError, ValueError) as exc:
        print(f"codex-pulse: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
