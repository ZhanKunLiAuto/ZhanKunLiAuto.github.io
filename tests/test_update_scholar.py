import importlib.util
import sys
from pathlib import Path


sys.dont_write_bytecode = True

MODULE_PATH = Path(__file__).resolve().parents[1] / "bin" / "update_scholar.py"
SPEC = importlib.util.spec_from_file_location("update_scholar", MODULE_PATH)
update_scholar = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(update_scholar)


def test_read_scholar_id_reads_from_yaml(tmp_path, monkeypatch):
    data_file = tmp_path / "socials.yml"
    data_file.write_text("scholar_userid: scholar-123\n", encoding="utf-8")
    monkeypatch.setattr(update_scholar, "DATA_FILE", data_file)

    assert update_scholar.read_scholar_id() == "scholar-123"


def test_fetch_page_returns_response_text(monkeypatch):
    calls = {}

    class DummyResponse:
        text = "page body"

        def raise_for_status(self):
            calls["raised"] = True

    def fake_get(url):
        calls["url"] = url
        return DummyResponse()

    monkeypatch.setattr(update_scholar.requests, "get", fake_get)

    result = update_scholar.fetch_page("abc123")

    assert result == "page body"
    assert calls["raised"] is True
    assert "abc123" in calls["url"]


def test_parse_publications_extracts_publications_after_marker():
    text = """
ignored
Markdown Content:
[Paper Title](https://scholar.google.com/citations?view_op=view_citation&hl=en&user=user123&citation_for_view=user123:gsid123&oi=ao)
Alice Smith, Bob Jones

Journal of Testing, 2024
not a publication line
[Second Paper](https://scholar.google.com/citations?view_op=view_citation&hl=en&user=user123&citation_for_view=user123:gsid456&oi=ao)
Carol Lee

Conference Track 2023
[Missing Year](https://scholar.google.com/citations?view_op=view_citation&hl=en&user=user123&citation_for_view=user123:gsid789&oi=ao)
Dana Ray

No date here
""".strip()

    publications = update_scholar.parse_publications(text)

    assert publications == [
        {
            "key": "paper2024",
            "title": "Paper Title",
            "authors": "Alice Smith, Bob Jones",
            "year": "2024",
            "link": "https://scholar.google.com/citations?view_op=view_citation&hl=en&user=user123&citation_for_view=user123:gsid123&oi=ao",
            "gs_id": "gsid123",
        },
        {
            "key": "second2023",
            "title": "Second Paper",
            "authors": "Carol Lee",
            "year": "2023",
            "link": "https://scholar.google.com/citations?view_op=view_citation&hl=en&user=user123&citation_for_view=user123:gsid456&oi=ao",
            "gs_id": "gsid456",
        },
    ]


def test_parse_publications_returns_empty_list_without_marker():
    assert update_scholar.parse_publications("no scholar content here") == []


def test_write_bib_writes_expected_bibliography(tmp_path, monkeypatch):
    bib_file = tmp_path / "papers.bib"
    monkeypatch.setattr(update_scholar, "BIB_FILE", bib_file)

    update_scholar.write_bib(
        [
            {
                "key": "paper2024",
                "title": "Paper Title",
                "authors": "Alice Smith",
                "year": "2024",
                "link": "https://example.com/paper",
                "gs_id": "gs123",
            },
            {
                "key": "note2025",
                "title": "Untitled Note",
                "authors": "",
                "year": "",
                "link": "https://example.com/note",
                "gs_id": "",
            },
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


def test_main_prints_message_when_scholar_id_is_missing(monkeypatch, capsys):
    monkeypatch.setattr(update_scholar, "read_scholar_id", lambda: "")

    update_scholar.main()

    captured = capsys.readouterr()
    assert "No scholar_userid found" in captured.out


def test_main_fetches_parses_and_writes_publications(monkeypatch, capsys):
    calls = {}
    publications = [{"key": "paper2024"}]

    monkeypatch.setattr(update_scholar, "read_scholar_id", lambda: "scholar-123")
    monkeypatch.setattr(
        update_scholar,
        "fetch_page",
        lambda scholar_id: calls.__setitem__("fetch_page", scholar_id) or "page",
    )
    monkeypatch.setattr(
        update_scholar,
        "parse_publications",
        lambda text: calls.__setitem__("parse_publications", text) or publications,
    )
    monkeypatch.setattr(
        update_scholar,
        "write_bib",
        lambda entries: calls.__setitem__("write_bib", entries),
    )

    update_scholar.main()

    captured = capsys.readouterr()
    assert calls == {
        "fetch_page": "scholar-123",
        "parse_publications": "page",
        "write_bib": publications,
    }
    assert "Updated 1 publications" in captured.out
