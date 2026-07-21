#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import yaml

SCHOLAR_FILE = Path("_data/scholar.yml")
PROGRESS_FILE = Path("_data/progress.yml")
STAT_LABELS = {
    "papers": "Papers",
    "citations": "Citations",
    "h_index": "h-index",
    "i10_index": "i10-index",
}


def read_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def read_yaml_from_git(ref: str, path: Path) -> dict:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path.as_posix()}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {}
    return yaml.safe_load(result.stdout) or {}


def publication_key(record: dict) -> str:
    return str(
        record.get("google_scholar_id")
        or record.get("key")
        or record.get("title")
        or ""
    ).strip()


def progress_key(record: dict) -> str:
    return str(record.get("id") or record.get("url") or record.get("title") or "").strip()


def signed_delta(before: object, after: object) -> str:
    if not isinstance(before, int) or not isinstance(after, int):
        return ""
    delta = after - before
    return f" ({delta:+d})" if delta else ""


def profile_lines(before: dict, after: dict) -> list[str]:
    before_profile = before.get("profile") or {}
    after_profile = after.get("profile") or {}
    lines: list[str] = []
    for key, label in STAT_LABELS.items():
        old_value = before_profile.get(key, "N/A")
        new_value = after_profile.get(key, "N/A")
        lines.append(f"- {label}: {old_value} → {new_value}{signed_delta(old_value, new_value)}")
    return lines


def new_publication_lines(before: dict, after: dict) -> list[str]:
    old_keys = {publication_key(record) for record in before.get("publications") or []}
    additions = [
        record
        for record in after.get("publications") or []
        if publication_key(record) not in old_keys
    ]
    if not additions:
        return ["- No new publications"]

    lines: list[str] = []
    for record in additions[:10]:
        title = str(record.get("title") or "Untitled")
        year = str(record.get("year") or "")
        url = str(record.get("external_url") or record.get("scholar_url") or "")
        label = f"{title} ({year})" if year else title
        lines.append(f"- [{label}]({url})" if url else f"- {label}")
    return lines


def citation_lines(before: dict, after: dict) -> list[str]:
    old_records = {
        publication_key(record): record for record in before.get("publications") or []
    }
    changes: list[tuple[int, str]] = []
    for record in after.get("publications") or []:
        old_record = old_records.get(publication_key(record))
        old_value = old_record.get("citation_count") if old_record else None
        new_value = record.get("citation_count")
        if not isinstance(old_value, int) or not isinstance(new_value, int) or old_value == new_value:
            continue
        title = str(record.get("title") or "Untitled")
        changes.append((new_value - old_value, f"- {title}: {old_value} → {new_value} ({new_value - old_value:+d})"))

    if not changes:
        return ["- No per-paper citation changes"]
    changes.sort(key=lambda item: item[0], reverse=True)
    return [line for _, line in changes[:10]]


def progress_lines(before: dict, after: dict) -> list[str]:
    old_keys = {progress_key(record) for record in before.get("items") or []}
    additions = [
        record
        for record in after.get("items") or []
        if progress_key(record) not in old_keys
    ]
    if not additions:
        return ["- No new personal or company updates"]

    lines: list[str] = []
    for record in additions[:10]:
        title = str(record.get("title") or "Untitled")
        category = str(record.get("category") or "update").title()
        url = str(record.get("url") or "")
        label = f"{category} · {title}"
        lines.append(f"- [{label}]({url})" if url else f"- {label}")
    return lines


def changed_files(ref: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--stat", ref, "--", "_bibliography", "_data", "assets/img/publication_preview"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.rstrip() for line in result.stdout.splitlines() if line.strip()]


def build_report(base_ref: str) -> str:
    before_scholar = read_yaml_from_git(base_ref, SCHOLAR_FILE)
    after_scholar = read_yaml(SCHOLAR_FILE)
    before_progress = read_yaml_from_git(base_ref, PROGRESS_FILE)
    after_progress = read_yaml(PROGRESS_FILE)
    file_lines = changed_files(base_ref) or ["No generated files changed."]

    sections = [
        "## Profile update proposal",
        "",
        "Nothing in this proposal is published until the repository owner approves it.",
        "",
        "### Scholar metrics",
        *profile_lines(before_scholar, after_scholar),
        "",
        "### New publications",
        *new_publication_lines(before_scholar, after_scholar),
        "",
        "### Citation changes",
        *citation_lines(before_scholar, after_scholar),
        "",
        "### Personal and company progress",
        *progress_lines(before_progress, after_progress),
        "",
        "### Generated file summary",
        "```text",
        *file_lines,
        "```",
    ]
    return "\n".join(sections).strip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize a generated profile update")
    parser.add_argument("--base", default="HEAD", help="Git ref to compare against")
    parser.add_argument("--output", type=Path, help="Write Markdown to this file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report(args.base)
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
