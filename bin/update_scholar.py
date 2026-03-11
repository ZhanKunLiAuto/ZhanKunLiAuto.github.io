#!/usr/bin/env python3
from __future__ import annotations

import html
import os
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote

import requests
import yaml

DATA_FILE = Path("_data/socials.yml")
BIB_FILE = Path("_bibliography/papers.bib")

SCHOLAR_URL = (
    "https://r.jina.ai/http://scholar.google.com/citations"
    "?user={scholar_id}&hl=en&cstart=0&pagesize=100&sortby=pubdate"
)
PUBLICATIONS_FALLBACK_URL = os.getenv(
    "SCHOLAR_PUBLICATIONS_FALLBACK_URL",
    "https://zhankunliauto.github.io/publications/",
)
REQUEST_TIMEOUT = 30
FIELD_ORDER = ["title", "author", "year", "html", "doi", "google_scholar_id"]


class ScholarFetchError(RuntimeError):
    pass


@dataclass
class BibEntry:
    entry_type: str
    key: str
    fields: dict[str, str]
    field_order: list[str] = field(default_factory=list)

    def merged_with(self, incoming: "BibEntry") -> "BibEntry":
        merged_fields = dict(self.fields)
        merged_fields.update({k: v for k, v in incoming.fields.items() if v})
        for field_name, field_value in self.fields.items():
            if not merged_fields.get(field_name) and field_value:
                merged_fields[field_name] = field_value

        merged_order: list[str] = []
        for field_name in FIELD_ORDER + self.field_order + incoming.field_order:
            if field_name in merged_fields and field_name not in merged_order:
                merged_order.append(field_name)

        return BibEntry(
            entry_type=incoming.entry_type or self.entry_type,
            key=self.key,
            fields=merged_fields,
            field_order=merged_order,
        )


def read_socials() -> dict:
    return yaml.safe_load(DATA_FILE.read_text()) or {}


def read_scholar_id() -> str:
    return str(read_socials().get("scholar_userid") or "").strip()


def http_get(url: str) -> str:
    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        },
    )
    response.raise_for_status()
    return response.text


def fetch_scholar_markdown(scholar_id: str) -> str:
    text = http_get(SCHOLAR_URL.format(scholar_id=scholar_id))
    lowered = text.lower()
    blocked_markers = [
        "target url returned error 403",
        "we're sorry",
        "automated queries",
        "sorry...",
    ]
    if any(marker in lowered for marker in blocked_markers):
        raise ScholarFetchError("Google Scholar blocked the profile fetch")
    return text


def fetch_publications_fallback() -> str:
    if not PUBLICATIONS_FALLBACK_URL:
        raise ScholarFetchError("No publications fallback URL configured")
    return http_get(PUBLICATIONS_FALLBACK_URL)


def normalize_text(value: str) -> str:
    value = html.unescape(value)
    value = value.replace("\xa0", " ")
    return re.sub(r"\s+", " ", value).strip()


def normalize_title(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = normalized.encode("ascii", "ignore").decode("ascii").lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def slugify_key(title: str, year: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9]+", title.lower())
    stem = "".join(tokens[:2]) or "paper"
    return f"{stem}{year}" if year else stem


def unique_key(preferred_key: str, used_keys: set[str]) -> str:
    key = preferred_key
    index = 2
    while key in used_keys:
        key = f"{preferred_key}{index}"
        index += 1
    used_keys.add(key)
    return key


def extract_year(value: str) -> str:
    match = re.search(r"\b(19|20)\d{2}\b", value)
    return match.group(0) if match else ""


def extract_scholar_id(url: str) -> str:
    match = re.search(r"citation_for_view=[^:]+:([^&\s]+)", url)
    return match.group(1) if match else ""


def parse_publications_from_markdown(text: str) -> list[BibEntry]:
    lines = [line.strip() for line in text.splitlines()]
    try:
        start = lines.index("Markdown Content:") + 1
    except ValueError as exc:
        raise ScholarFetchError("Unexpected Scholar response format") from exc

    publications: list[BibEntry] = []
    index = start
    while index < len(lines):
        line = lines[index]
        if not line.startswith("["):
            index += 1
            continue

        title_match = re.search(r"\[(.+?)\]", line)
        link_match = re.search(r"\((https://scholar\.google\.com/citations[^)]+)\)", line)
        if not title_match or not link_match:
            index += 1
            continue

        title = normalize_text(title_match.group(1))
        link = normalize_text(link_match.group(1))

        authors = ""
        info_lines: list[str] = []
        cursor = index + 1
        while cursor < len(lines):
            candidate = lines[cursor]
            if candidate.startswith("["):
                break
            if candidate:
                if not authors:
                    authors = normalize_text(candidate)
                else:
                    info_lines.append(normalize_text(candidate))
            cursor += 1

        year = extract_year(" ".join(info_lines))
        publications.append(
            BibEntry(
                entry_type="misc",
                key="",
                fields={
                    "title": title,
                    "author": authors,
                    "year": year,
                    "html": link,
                    "google_scholar_id": extract_scholar_id(link),
                },
                field_order=FIELD_ORDER.copy(),
            )
        )
        index = cursor

    return publications


def parse_publications_from_site(text: str) -> list[BibEntry]:
    pattern = re.compile(
        r'<div id="(?P<key>[^"]+)" class="col-sm-8">\s*'
        r'<div class="title">\s*(?P<title>.*?)\s*</div>\s*'
        r'<div class="author">\s*(?P<author>.*?)\s*</div>\s*'
        r'<div class="periodical">\s*(?P<year>.*?)\s*</div>.*?'
        r'<div class="links">\s*(?P<links>.*?)</div>',
        re.S,
    )

    publications: list[BibEntry] = []
    for match in pattern.finditer(text):
        links_html = match.group("links")
        links = re.findall(r'href="([^"]+)"', links_html)
        link = normalize_text(unquote(links[0])) if links else ""
        title = normalize_text(match.group("title"))
        author = normalize_text(re.sub(r"<[^>]+>", " ", match.group("author")))
        year = extract_year(normalize_text(match.group("year")))
        publications.append(
            BibEntry(
                entry_type="misc",
                key=normalize_text(match.group("key")),
                fields={
                    "title": title,
                    "author": author,
                    "year": year,
                    "html": link,
                    "google_scholar_id": extract_scholar_id(link),
                },
                field_order=FIELD_ORDER.copy(),
            )
        )

    if not publications:
        raise ScholarFetchError("Publications fallback page did not contain bibliography entries")
    return publications


def split_bib_entries(text: str) -> list[str]:
    entries: list[str] = []
    position = 0
    while True:
        start = text.find("@", position)
        if start == -1:
            return entries
        depth = 0
        cursor = start
        while cursor < len(text):
            char = text[cursor]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    entries.append(text[start : cursor + 1])
                    position = cursor + 1
                    break
            cursor += 1
        else:
            return entries


def parse_bib_entry(block: str) -> BibEntry | None:
    header_match = re.match(r"@(\w+)\{([^,]+),", block)
    if not header_match:
        return None

    entry_type, key = header_match.groups()
    body = block[header_match.end() :].rsplit("}", 1)[0]

    fields: dict[str, str] = {}
    field_order: list[str] = []
    for line in body.splitlines():
        line = line.strip().rstrip(",")
        if not line or "=" not in line:
            continue
        field_name, field_value = line.split("=", 1)
        field_name = field_name.strip()
        field_value = field_value.strip()
        if field_value.startswith("{") and field_value.endswith("}"):
            field_value = field_value[1:-1].strip()
        fields[field_name] = field_value
        field_order.append(field_name)

    return BibEntry(entry_type=entry_type, key=key.strip(), fields=fields, field_order=field_order)


def parse_existing_bib() -> list[BibEntry]:
    if not BIB_FILE.exists():
        return []
    text = BIB_FILE.read_text()
    entries: list[BibEntry] = []
    for block in split_bib_entries(text):
        entry = parse_bib_entry(block)
        if entry:
            entries.append(entry)
    return entries


def entry_match_key(entry: BibEntry) -> tuple[str, str]:
    return (
        entry.fields.get("google_scholar_id", "").strip(),
        normalize_title(entry.fields.get("title", "")),
    )


def merge_entries(
    fetched_entries: Iterable[BibEntry],
    existing_entries: list[BibEntry],
    *,
    prefer_existing: bool,
) -> list[BibEntry]:
    existing_by_scholar: dict[str, BibEntry] = {}
    existing_by_title: dict[str, BibEntry] = {}
    for entry in existing_entries:
        scholar_key, title_key = entry_match_key(entry)
        if scholar_key:
            existing_by_scholar[scholar_key] = entry
        if title_key:
            existing_by_title[title_key] = entry

    used_existing_keys: set[str] = set()
    used_output_keys: set[str] = set()
    merged: list[BibEntry] = []

    for fetched in fetched_entries:
        scholar_key, title_key = entry_match_key(fetched)
        existing = None
        if scholar_key:
            existing = existing_by_scholar.get(scholar_key)
        if existing is None and title_key:
            existing = existing_by_title.get(title_key)

        if existing:
            used_existing_keys.add(existing.key)
            candidate = fetched.merged_with(existing) if prefer_existing else existing.merged_with(fetched)
            candidate.key = unique_key(existing.key, used_output_keys)
        else:
            preferred_key = fetched.key or slugify_key(
                fetched.fields.get("title", ""),
                fetched.fields.get("year", ""),
            )
            fetched.key = unique_key(preferred_key, used_output_keys)
            candidate = fetched

        merged.append(candidate)

    for entry in existing_entries:
        if entry.key in used_existing_keys:
            continue
        entry.key = unique_key(entry.key, used_output_keys)
        merged.append(entry)

    merged.sort(
        key=lambda entry: (
            int(entry.fields.get("year", "0") or 0),
            normalize_title(entry.fields.get("title", "")),
        ),
        reverse=True,
    )
    return merged


def format_bib_entry(entry: BibEntry) -> str:
    lines = [f"@{entry.entry_type}{{{entry.key},"]
    ordered_fields: list[str] = []
    for field_name in FIELD_ORDER + entry.field_order:
        if field_name in entry.fields and field_name not in ordered_fields and entry.fields[field_name]:
            ordered_fields.append(field_name)

    for field_name in ordered_fields:
        lines.append(f"  {field_name}={{ {entry.fields[field_name]} }},")
    lines.append("}")
    return "\n".join(lines)


def write_bib(entries: list[BibEntry]) -> None:
    body = "\n\n".join(format_bib_entry(entry) for entry in entries)
    BIB_FILE.write_text(f"---\n---\n\n{body}\n")


def load_publications(scholar_id: str) -> tuple[str, list[BibEntry]]:
    try:
        markdown = fetch_scholar_markdown(scholar_id)
        return "scholar", parse_publications_from_markdown(markdown)
    except (requests.RequestException, ScholarFetchError) as scholar_error:
        fallback_page = fetch_publications_fallback()
        publications = parse_publications_from_site(fallback_page)
        sys.stderr.write(f"Scholar fetch failed, used fallback: {scholar_error}\n")
        return "fallback", publications


def main() -> None:
    scholar_id = read_scholar_id()
    if not scholar_id:
        print(f"No scholar_userid found in {DATA_FILE}")
        raise SystemExit(1)

    source, fetched_entries = load_publications(scholar_id)
    existing_entries = parse_existing_bib()
    merged_entries = merge_entries(
        fetched_entries,
        existing_entries,
        prefer_existing=(source == "fallback"),
    )
    write_bib(merged_entries)
    print(f"Updated {len(merged_entries)} publications from {source}")


if __name__ == "__main__":
    main()
