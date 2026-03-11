import importlib.util
import sys
from pathlib import Path

import pytest


sys.dont_write_bytecode = True

MODULE_PATH = Path(__file__).resolve().parents[1] / "bin" / "update_scholar.py"
SPEC = importlib.util.spec_from_file_location("update_scholar", MODULE_PATH)
update_scholar = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = update_scholar
SPEC.loader.exec_module(update_scholar)


def make_entry(key, *, title, author, year, html, scholar_id=""):
    return update_scholar.BibEntry(
        entry_type="misc",
        key=key,
        fields={
            "title": title,
            "author": author,
            "year": year,
            "html": html,
            "google_scholar_id": scholar_id,
        },
        field_order=update_scholar.FIELD_ORDER.copy(),
    )


def test_read_scholar_id_reads_from_yaml(tmp_path, monkeypatch):
    data_file = tmp_path / "socials.yml"
    data_file.write_text("scholar_userid: scholar-123\n", encoding="utf-8")
    monkeypatch.setattr(update_scholar, "DATA_FILE", data_file)

    assert update_scholar.read_scholar_id() == "scholar-123"


def test_http_get_returns_response_text(monkeypatch):
    calls = {}

    class DummyResponse:
        text = "page body"

        def raise_for_status(self):
            calls["raised"] = True

    def fake_get(url, timeout, headers):
        calls["url"] = url
        calls["timeout"] = timeout
        calls["headers"] = headers
        return DummyResponse()

    monkeypatch.setattr(update_scholar.requests, "get", fake_get)

    result = update_scholar.http_get("https://example.com/profile")

    assert result == "page body"
    assert calls["raised"] is True
    assert calls["url"] == "https://example.com/profile"
    assert calls["timeout"] == update_scholar.REQUEST_TIMEOUT
    assert "Mozilla/5.0" in calls["headers"]["User-Agent"]


def test_parse_publications_from_markdown_extracts_entries():
    text = """
ignored
Markdown Content:
[Paper Title](https://scholar.google.com/citations?view_op=view_citation&hl=en&user=user123&citation_for_view=user123:gsid123&oi=ao)
Alice Smith, Bob Jones

Journal of Testing, 2024
[Second Paper](https://scholar.google.com/citations?view_op=view_citation&hl=en&user=user123&citation_for_view=user123:gsid456&oi=ao)
Carol Lee

Conference Track 2023
""".strip()

    publications = update_scholar.parse_publications_from_markdown(text)

    assert len(publications) == 2
    assert publications[0].fields["title"] == "Paper Title"
    assert publications[0].fields["author"] == "Alice Smith, Bob Jones"
    assert publications[0].fields["year"] == "2024"
    assert publications[0].fields["google_scholar_id"] == "gsid123"
    assert publications[1].fields["title"] == "Second Paper"
    assert publications[1].fields["year"] == "2023"


def test_parse_publications_from_markdown_raises_without_marker():
    with pytest.raises(update_scholar.ScholarFetchError):
        update_scholar.parse_publications_from_markdown("no scholar content here")


def test_merge_entries_prefers_existing_fields_when_requested():
    fetched = [
        make_entry(
            "",
            title="Paper Title",
            author="Fresh Author",
            year="2024",
            html="https://new.example/paper",
            scholar_id="gs123",
        )
    ]
    existing = [
        make_entry(
            "paper2024",
            title="Paper Title",
            author="Existing Author",
            year="2024",
            html="https://old.example/paper",
            scholar_id="gs123",
        )
    ]

    merged = update_scholar.merge_entries(fetched, existing, prefer_existing=True)

    assert len(merged) == 1
    assert merged[0].key == "paper2024"
    assert merged[0].fields["author"] == "Existing Author"
    assert merged[0].fields["html"] == "https://old.example/paper"


def test_write_bib_writes_expected_bibliography(tmp_path, monkeypatch):
    bib_file = tmp_path / "papers.bib"
    monkeypatch.setattr(update_scholar, "BIB_FILE", bib_file)

    update_scholar.write_bib(
        [
            make_entry(
                "paper2024",
                title="Paper Title",
                author="Alice Smith",
                year="2024",
                html="https://example.com/paper",
                scholar_id="gs123",
            ),
            make_entry(
                "note2025",
                title="Untitled Note",
                author="",
                year="",
                html="https://example.com/note",
            ),
        ]
    )

    content = bib_file.read_text(encoding="utf-8")
    assert content.startswith("---\n---\n\n@misc{paper2024,\n")
    assert "  title={ Paper Title }," in content
    assert "  author={ Alice Smith }," in content
    assert "  year={ 2024 }," in content
    assert "  html={ https://example.com/paper }," in content
    assert "  google_scholar_id={ gs123 }," in content
    assert "@misc{note2025," in content
    assert "author={" not in content.split("@misc{note2025,")[1]
    assert "year={" not in content.split("@misc{note2025,")[1]


def test_main_exits_when_scholar_id_is_missing(monkeypatch, capsys):
    monkeypatch.setattr(update_scholar, "read_scholar_id", lambda: "")

    with pytest.raises(SystemExit) as exc_info:
        update_scholar.main()

    captured = capsys.readouterr()
    assert exc_info.value.code == 1
    assert "No scholar_userid found" in captured.out


def test_main_loads_merges_and_writes_publications(monkeypatch, capsys):
    fetched_entries = [make_entry("paper2024", title="Paper", author="Author", year="2024", html="https://example.com")]
    existing_entries = [make_entry("paper2023", title="Older", author="Author", year="2023", html="https://older.example.com")]
    merged_entries = fetched_entries + existing_entries
    calls = {}

    monkeypatch.setattr(update_scholar, "read_scholar_id", lambda: "scholar-123")
    monkeypatch.setattr(
        update_scholar,
        "load_publications",
        lambda scholar_id: calls.__setitem__("load_publications", scholar_id) or ("scholar", fetched_entries),
    )
    monkeypatch.setattr(
        update_scholar,
        "parse_existing_bib",
        lambda: calls.__setitem__("parse_existing_bib", True) or existing_entries,
    )
    monkeypatch.setattr(
        update_scholar,
        "merge_entries",
        lambda fetched, existing, prefer_existing: calls.__setitem__(
            "merge_entries",
            (fetched, existing, prefer_existing),
        )
        or merged_entries,
    )
    monkeypatch.setattr(
        update_scholar,
        "write_bib",
        lambda entries: calls.__setitem__("write_bib", entries),
    )

    update_scholar.main()

    captured = capsys.readouterr()
    assert calls["load_publications"] == "scholar-123"
    assert calls["parse_existing_bib"] is True
    assert calls["merge_entries"] == (fetched_entries, existing_entries, False)
    assert calls["write_bib"] == merged_entries
    assert "Updated 2 publications from scholar" in captured.out
