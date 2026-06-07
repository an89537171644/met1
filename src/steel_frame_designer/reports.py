"""Report-writing helpers."""

from __future__ import annotations

from pathlib import Path


def write_markdown_report(path: str | Path, title: str, lines: list[str]) -> Path:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join([f"# {title}", "", *lines, ""])
    report_path.write_text(content, encoding="utf-8")
    return report_path
