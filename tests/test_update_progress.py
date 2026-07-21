import importlib.util
import sys
from datetime import UTC, datetime
from pathlib import Path

import requests


sys.dont_write_bytecode = True

MODULE_PATH = Path(__file__).resolve().parents[1] / "bin" / "update_progress.py"
SPEC = importlib.util.spec_from_file_location("update_progress", MODULE_PATH)
update_progress = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = update_progress
SPEC.loader.exec_module(update_progress)


def test_parse_feed_reads_rss_and_atom_entries():
    rss = """
    <rss><channel>
      <item>
        <title>Kun Zhan presents a new VLA system</title>
        <link>https://example.com/one</link>
        <pubDate>Mon, 20 Jul 2026 10:00:00 GMT</pubDate>
        <description><![CDATA[<p>Li Auto update</p>]]></description>
      </item>
    </channel></rss>
    """
    atom = """
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>Second update</title>
        <link href="https://example.com/two" />
        <updated>2026-07-21T12:00:00Z</updated>
        <summary>Summary</summary>
      </entry>
    </feed>
    """

    rss_records = update_progress.parse_feed(rss)
    atom_records = update_progress.parse_feed(atom)

    assert rss_records == [
        {
            "title": "Kun Zhan presents a new VLA system",
            "url": "https://example.com/one",
            "published": "Mon, 20 Jul 2026 10:00:00 GMT",
            "summary": "Li Auto update",
        }
    ]
    assert atom_records[0]["url"] == "https://example.com/two"
    assert atom_records[0]["published"] == "2026-07-21T12:00:00Z"


def test_build_source_url_constructs_localized_google_news_feed():
    url = update_progress.build_source_url(
        {
            "google_news_query": '"Kun Zhan" when:30d',
            "locale": {"language": "en-US", "country": "US", "edition": "US:en"},
        }
    )

    assert url.startswith("https://news.google.com/rss/search?")
    assert "%22Kun+Zhan%22+when%3A30d" in url
    assert "ceid=US%3Aen" in url


def test_records_for_source_filters_keywords_and_old_items(monkeypatch):
    feed = """
    <rss><channel>
      <item><title>Li Auto VLA launch</title><link>https://example.com/new</link><pubDate>Mon, 20 Jul 2026 10:00:00 GMT</pubDate></item>
      <item><title>Unrelated delivery update</title><link>https://example.com/unrelated</link><pubDate>Mon, 20 Jul 2026 10:00:00 GMT</pubDate></item>
      <item><title>Old VLA update</title><link>https://example.com/old</link><pubDate>Mon, 20 Jan 2025 10:00:00 GMT</pubDate></item>
    </channel></rss>
    """
    monkeypatch.setattr(update_progress, "fetch_feed", lambda url: feed)
    source = {
        "key": "li-auto-ai",
        "name": "Li Auto AI",
        "category": "company",
        "url": "https://example.com/feed.xml",
        "include_any": ["VLA"],
    }

    records = update_progress.records_for_source(
        source,
        now=datetime(2026, 7, 22, tzinfo=UTC),
        lookback_days=120,
    )

    assert len(records) == 1
    assert records[0]["title"] == "Li Auto VLA launch"
    assert records[0]["managed"] is True
    assert records[0]["source_key"] == "li-auto-ai"


def test_build_progress_preserves_manual_and_failed_source_items(monkeypatch):
    existing = {
        "updated_at": "2026-07-01T00:00:00Z",
        "items": [
            {
                "id": "manual",
                "managed": False,
                "date": "2026-06-01",
                "title": "Manual milestone",
                "url": "https://example.com/manual",
            },
            {
                "id": "feed-old",
                "managed": True,
                "source_key": "broken",
                "date": "2026-07-01",
                "title": "Previous feed item",
                "url": "https://example.com/previous",
            },
        ],
    }
    config = {
        "progress": {
            "max_items": 6,
            "sources": [{"key": "broken", "name": "Broken", "enabled": True}],
        }
    }

    def fail_source(source, *, now, lookback_days):
        raise requests.RequestException("offline")

    monkeypatch.setattr(update_progress, "records_for_source", fail_source)

    result = update_progress.build_progress_data(
        config,
        existing,
        now=datetime(2026, 7, 22, tzinfo=UTC),
    )

    assert result == existing


def test_build_progress_replaces_managed_source_items(monkeypatch):
    existing = {
        "updated_at": "2026-07-01T00:00:00Z",
        "items": [
            {
                "id": "feed-old",
                "managed": True,
                "source_key": "news",
                "date": "2026-07-01",
                "title": "Old feed item",
                "url": "https://example.com/old",
            }
        ],
    }
    replacement = {
        "id": "feed-new",
        "managed": True,
        "source_key": "news",
        "date": "2026-07-21",
        "title": "New feed item",
        "url": "https://example.com/new",
    }
    monkeypatch.setattr(
        update_progress,
        "records_for_source",
        lambda source, *, now, lookback_days: [replacement],
    )

    result = update_progress.build_progress_data(
        {"progress": {"sources": [{"key": "news", "enabled": True}]}},
        existing,
        now=datetime(2026, 7, 22, tzinfo=UTC),
    )

    assert result["items"] == [replacement]
    assert result["updated_at"] == "2026-07-22T00:00:00Z"
