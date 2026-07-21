#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import yaml

SCHOLAR_FILE = Path("_data/scholar.yml")
STAT_LABELS = {
    "papers": "论文数量",
    "citations": "总引用量",
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


def signed_delta(before: object, after: object) -> str:
    if not isinstance(before, int) or not isinstance(after, int):
        return ""
    delta = after - before
    return f"（{delta:+d}）" if delta else "（无变化）"


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
        return ["- 无新增论文"]

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
        changes.append((new_value - old_value, f"- {title}：{old_value} → {new_value}（{new_value - old_value:+d}）"))

    if not changes:
        return ["- 无单篇论文引用变化"]
    changes.sort(key=lambda item: item[0], reverse=True)
    return [line for _, line in changes[:10]]


def removed_publication_lines(before: dict, after: dict) -> list[str]:
    new_keys = {publication_key(record) for record in after.get("publications") or []}
    removals = [
        record
        for record in before.get("publications") or []
        if publication_key(record) not in new_keys
    ]
    if not removals:
        return ["- 无移除论文"]

    return [f"- {record.get('title') or 'Untitled'}" for record in removals[:10]]


def changed_files(ref: str) -> list[str]:
    result = subprocess.run(
        [
            "git",
            "diff",
            "--stat",
            ref,
            "--",
            "_bibliography/papers.bib",
            "_data/scholar.yml",
            "assets/img/publication_preview",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.rstrip() for line in result.stdout.splitlines() if line.strip()]


def build_report(base_ref: str) -> str:
    before_scholar = read_yaml_from_git(base_ref, SCHOLAR_FILE)
    after_scholar = read_yaml(SCHOLAR_FILE)
    file_lines = changed_files(base_ref) or ["没有生成文件发生变化。"]

    sections = [
        "## Google Scholar 每周更新提案",
        "",
        "本提案仅包含 Google Scholar 数据；在仓库所有者批准前不会发布到个人主页。",
        "",
        "### 核心指标",
        *profile_lines(before_scholar, after_scholar),
        "",
        "### 新增论文",
        *new_publication_lines(before_scholar, after_scholar),
        "",
        "### 单篇引用变化",
        *citation_lines(before_scholar, after_scholar),
        "",
        "### 移除或缺失的论文",
        *removed_publication_lines(before_scholar, after_scholar),
        "",
        "### 文件变更摘要",
        "```text",
        *file_lines,
        "```",
    ]
    return "\n".join(sections).strip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize a generated Google Scholar update")
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
