#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import html
import re
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlencode

import requests
import yaml

CONFIG_FILE = Path("_data/profile_update.yml")
PROGRESS_FILE = Path("_data/progress.yml")
REQUEST_TIMEOUT = 30
DEFAULT_MAX_ITEMS = 6
DEFAULT_LOOKBACK_DAYS = 120


class ProgressFetchError(RuntimeError):
    pass


def read_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def normalize_text(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", html.unescape(value or ""))
    return re.sub(r"\s+", " ", without_tags).strip()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def child_text(node: ET.Element, names: set[str]) -> str:
    for child in node:
        if local_name(child.tag) in names and child.text:
            return normalize_text(child.text)
    return ""


def item_link(node: ET.Element) -> str:
    for child in node:
        if local_name(child.tag) != "link":
            continue
        href = str(child.attrib.get("href") or "").strip()
        if href:
            return href
        if child.text:
            return child.text.strip()
    return ""


def parse_datetime(value: str) -> datetime | None:
    normalized = str(value or "").strip()
    if not normalized:
        return None

    try:
        parsed = parsedate_to_datetime(normalized)
    except (TypeError, ValueError, OverflowError):
        parsed = None

    if parsed is None:
        try:
            parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        except ValueError:
            return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def build_source_url(source: dict) -> str:
    direct_url = str(source.get("url") or "").strip()
    if direct_url:
        return direct_url

    query = str(source.get("google_news_query") or "").strip()
    if not query:
        raise ProgressFetchError("Source needs either url or google_news_query")

    locale = source.get("locale") or {}
    language = str(locale.get("language") or "zh-CN")
    country = str(locale.get("country") or "CN")
    edition = str(locale.get("edition") or "CN:zh-Hans")
    params = urlencode({"q": query, "hl": language, "gl": country, "ceid": edition})
    return f"https://news.google.com/rss/search?{params}"


def fetch_feed(url: str) -> str:
    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": "profile-update-bot/1.0 (+https://github.com/ZhanKunLiAuto)"},
    )
    response.raise_for_status()
    return response.text


def parse_feed(text: str) -> list[dict[str, str]]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError as error:
        raise ProgressFetchError(f"Invalid RSS/Atom response: {error}") from error

    records: list[dict[str, str]] = []
    for node in root.iter():
        if local_name(node.tag) not in {"item", "entry"}:
            continue

        title = child_text(node, {"title"})
        link = item_link(node)
        published = child_text(node, {"pubdate", "published", "updated", "date"})
        summary = child_text(node, {"description", "summary", "content"})
        if title and link:
            records.append(
                {
                    "title": title,
                    "url": link,
                    "published": published,
                    "summary": summary,
                }
            )
    return records


def matches_keywords(record: dict[str, str], source: dict) -> bool:
    haystack = " ".join(
        [record.get("title", ""), record.get("summary", "")]
    ).casefold()
    include_any = [str(term).casefold() for term in source.get("include_any") or []]
    include_all = [str(term).casefold() for term in source.get("include_all") or []]
    exclude_any = [str(term).casefold() for term in source.get("exclude_any") or []]

    if include_any and not any(term in haystack for term in include_any):
        return False
    if include_all and not all(term in haystack for term in include_all):
        return False
    return not any(term in haystack for term in exclude_any)


def record_id(source_key: str, record: dict[str, str]) -> str:
    identity = f"{source_key}\n{record.get('url') or record.get('title')}"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    return f"feed-{digest}"


def source_key(source: dict) -> str:
    configured = str(source.get("key") or "").strip()
    if configured:
        return configured
    name = str(source.get("name") or "source").casefold()
    return re.sub(r"[^a-z0-9]+", "-", name).strip("-") or "source"


def records_for_source(source: dict, *, now: datetime, lookback_days: int) -> list[dict]:
    key = source_key(source)
    feed_text = fetch_feed(build_source_url(source))
    parsed_records = parse_feed(feed_text)
    cutoff = now - timedelta(days=lookback_days)
    limit = int(source.get("limit") or DEFAULT_MAX_ITEMS)

    candidates: list[dict] = []
    for record in parsed_records:
        published = parse_datetime(record.get("published", ""))
        if published is None or published < cutoff or not matches_keywords(record, source):
            continue

        candidates.append(
            {
                "id": record_id(key, record),
                "managed": True,
                "source_key": key,
                "category": str(source.get("category") or "company"),
                "date": published.date().isoformat(),
                "title": record["title"],
                "summary": record.get("summary", "")[:320],
                "url": record["url"],
                "source": str(source.get("name") or key),
            }
        )

    candidates.sort(key=lambda item: item["date"], reverse=True)
    return candidates[:limit]


def deduplicate(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique_items: list[dict] = []
    for item in items:
        identity = str(item.get("url") or item.get("title") or item.get("id") or "").casefold()
        if not identity or identity in seen:
            continue
        seen.add(identity)
        unique_items.append(item)
    return unique_items


def build_progress_data(config: dict, existing: dict, *, now: datetime) -> dict:
    progress_config = config.get("progress") or {}
    sources = [source for source in progress_config.get("sources") or [] if source.get("enabled", True)]
    max_items = int(progress_config.get("max_items") or DEFAULT_MAX_ITEMS)
    lookback_days = int(progress_config.get("lookback_days") or DEFAULT_LOOKBACK_DAYS)

    existing_items = existing.get("items") or []
    manual_items = [item for item in existing_items if not item.get("managed")]
    existing_managed_by_source: dict[str, list[dict]] = {}
    for item in existing_items:
        if item.get("managed"):
            existing_managed_by_source.setdefault(str(item.get("source_key") or ""), []).append(item)

    fetched_items: list[dict] = []
    successful_sources = 0
    for source in sources:
        key = source_key(source)
        try:
            fetched_items.extend(records_for_source(source, now=now, lookback_days=lookback_days))
            successful_sources += 1
        except (requests.RequestException, ProgressFetchError, ValueError) as error:
            fetched_items.extend(existing_managed_by_source.get(key, []))
            sys.stderr.write(f"Progress source {key} failed; kept previous items: {error}\n")

    if sources and successful_sources == 0:
        return existing

    combined = deduplicate(fetched_items + manual_items)
    combined.sort(
        key=lambda item: (str(item.get("date") or ""), not bool(item.get("managed"))),
        reverse=True,
    )
    selected = combined[:max_items]

    if selected == existing_items:
        return existing
    return {
        "updated_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "items": selected,
    }


def write_progress(data: dict) -> None:
    PROGRESS_FILE.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def main() -> None:
    config = read_yaml(CONFIG_FILE)
    if not config.get("progress"):
        print(f"No progress configuration found in {CONFIG_FILE}")
        raise SystemExit(1)

    existing = read_yaml(PROGRESS_FILE)
    updated = build_progress_data(config, existing, now=datetime.now(UTC))
    if updated == existing:
        print("No progress changes detected")
        return

    write_progress(updated)
    print(f"Updated {len(updated.get('items') or [])} recent progress items")


if __name__ == "__main__":
    main()
