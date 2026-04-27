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


def make_entry(
    key,
    *,
    title,
    author,
    year,
    html,
    scholar_id="",
    note="",
    preview="",
    thumbnail="",
    doi="",
    arxiv="",
    pdf="",
    citation_count="",
):
    fields = {
        "title": title,
        "author": author,
        "year": year,
        "html": html,
        "google_scholar_id": scholar_id,
    }
    if note:
        fields["note"] = note
    if preview:
        fields["preview"] = preview
    if thumbnail:
        fields["thumbnail"] = thumbnail
    if doi:
        fields["doi"] = doi
    if arxiv:
        fields["arxiv"] = arxiv
    if pdf:
        fields["pdf"] = pdf
    if citation_count != "":
        fields["citation_count"] = str(citation_count)
    return update_scholar.BibEntry(
        entry_type="misc",
        key=key,
        fields=fields,
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


def test_parse_publications_from_markdown_extracts_entries_and_note():
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
    assert publications[0].fields["note"] == "Journal of Testing"
    assert publications[0].fields["google_scholar_id"] == "gsid123"
    assert publications[1].fields["title"] == "Second Paper"
    assert publications[1].fields["note"] == "Conference Track"


def test_parse_publications_from_markdown_raises_without_marker():
    with pytest.raises(update_scholar.ScholarFetchError):
        update_scholar.parse_publications_from_markdown("no scholar content here")


def test_parse_publications_from_profile_html_extracts_citations():
    html = """
    <table id="gsc_a_t">
      <tr class="gsc_a_tr">
        <td class="gsc_a_t">
          <a class="gsc_a_at" href="/citations?view_op=view_citation&hl=en&user=user123&citation_for_view=user123:gsid123">DriveVLM</a>
          <div class="gs_gray">Alice Smith, Bob Jones</div>
          <div class="gs_gray">CoRL 2024</div>
        </td>
        <td class="gsc_a_c"><a class="gsc_a_ac gs_ibl">128</a></td>
        <td class="gsc_a_y"><span class="gsc_a_h gsc_a_hc gs_ibl">2024</span></td>
      </tr>
    </table>
    """

    publications = update_scholar.parse_publications_from_profile_html(html)

    assert len(publications) == 1
    assert publications[0].fields["title"] == "DriveVLM"
    assert publications[0].fields["author"] == "Alice Smith, Bob Jones"
    assert publications[0].fields["note"] == "CoRL"
    assert publications[0].fields["year"] == "2024"
    assert publications[0].fields["citation_count"] == "128"
    assert publications[0].fields["google_scholar_id"] == "gsid123"


def test_parse_profile_stats_extracts_expected_fields():
    html = """
    <table id="gsc_rsb_st">
      <tr><td>Citations</td><td>1,335</td><td>900</td></tr>
      <tr><td>h-index</td><td>15</td><td>12</td></tr>
      <tr><td>i10-index</td><td>21</td><td>18</td></tr>
    </table>
    <tbody id="gsc_a_b">
      <tr class="gsc_a_tr"></tr>
      <tr class="gsc_a_tr"></tr>
      <tr class="gsc_a_tr"></tr>
    </tbody>
    """

    stats = update_scholar.parse_profile_stats(html)

    assert stats == {
        "papers": 3,
        "citations": 1335,
        "h_index": 15,
        "i10_index": 21,
    }


def test_parse_citation_count_and_scholar_links():
    html = """
    <meta name="description" content="DriveVLM, Cited by 128">
    <a class="gsc_oci_title_link" href="https://example.com/paper"></a>
    <div class="gsc_oci_title_ggi"><a href="https://example.com/paper.pdf">[PDF]</a></div>
    """

    assert update_scholar.parse_citation_count(html) == 128
    assert update_scholar.extract_title_link_from_html(html) == "https://example.com/paper"
    assert update_scholar.extract_pdf_link_from_html(html) == "https://example.com/paper.pdf"


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


def test_merge_entries_drops_records_without_valid_year():
    fetched = [
        make_entry(
            "",
            title="Valid Paper",
            author="Author A",
            year="2024",
            html="https://example.com/valid",
            scholar_id="valid",
        ),
        make_entry(
            "",
            title="No Year Paper",
            author="Author B",
            year="",
            html="https://example.com/no-year",
            scholar_id="noyear",
        ),
    ]

    merged = update_scholar.merge_entries(fetched, [], prefer_existing=False)

    assert len(merged) == 1
    assert merged[0].fields["title"] == "Valid Paper"


def test_normalize_authors_strips_empty_markdown_links():
    raw = "A Author, B Author, ...[](http://scholar.google.com/citations?foo=bar)"
    assert update_scholar.normalize_authors(raw) == "A Author, B Author, ..."


def test_build_publication_record_uses_existing_fallbacks(monkeypatch):
    entry = make_entry(
        "drivevlm2024",
        title="DriveVLM",
        author="Alice Smith",
        year="2024",
        html="https://scholar.google.com/citations?view_op=view_citation&citation_for_view=user:gs123",
        scholar_id="gs123",
        note="CoRL",
    )
    previous = {
        "citation_count": 91,
        "external_url": "https://previous.example/paper",
        "pdf_url": "https://previous.example/paper.pdf",
        "preview_image": "https://previous.example/cover.png",
    }

    monkeypatch.setattr(update_scholar, "fetch_publication_details", lambda scholar_id, article_id: {})

    record = update_scholar.build_publication_record(entry, "user123", previous)

    assert record["citation_count"] == 91
    assert record["external_url"] == "https://previous.example/paper"
    assert record["pdf_url"] == "https://previous.example/paper.pdf"
    assert record["preview_image"] == ""
    assert record["venue"] == "CoRL"


def test_resolve_preview_image_prefers_generated_pdf_preview_before_previous_fallback(monkeypatch):
    monkeypatch.setattr(update_scholar, "generate_pdf_preview", lambda record: "/assets/img/publication_preview/generated.png")
    monkeypatch.setattr(update_scholar, "http_get", lambda url: "")

    preview = update_scholar.resolve_preview_image(
        {"key": "paper", "title": "Paper", "pdf_url": "https://example.com/paper.pdf", "preview_image": ""},
        {"preview_image": "https://previous.example/cover.png"},
    )

    assert preview == "/assets/img/publication_preview/generated.png"


def test_resolve_preview_image_keeps_explicit_preview(monkeypatch):
    monkeypatch.setattr(update_scholar, "generate_pdf_preview", lambda record: "/assets/img/publication_preview/generated.png")

    preview = update_scholar.resolve_preview_image(
        {"key": "paper", "title": "Paper", "preview_image": "/assets/img/publication_preview/manual.png"},
        {"preview_image": "https://previous.example/cover.png"},
    )

    assert preview == "/assets/img/publication_preview/manual.png"


def test_build_scholar_data_sorts_top_publications_and_resolves_preview(monkeypatch):
    entries = [
        make_entry(
            "paper-low",
            title="Paper Low",
            author="Alice Smith",
            year="2023",
            html="https://scholar.google.com/citations?view_op=view_citation&citation_for_view=user:gs-low",
            scholar_id="gs-low",
        ),
        make_entry(
            "paper-high",
            title="Paper High",
            author="Bob Lee",
            year="2024",
            html="https://scholar.google.com/citations?view_op=view_citation&citation_for_view=user:gs-high",
            scholar_id="gs-high",
            preview="/assets/img/publication_preview/high.png",
        ),
    ]

    monkeypatch.setattr(
        update_scholar,
        "fetch_publication_details",
        lambda scholar_id, article_id: {
            "gs-low": {"citation_count": 12, "external_url": "https://example.com/low"},
            "gs-high": {"citation_count": 98, "external_url": "https://example.com/high"},
        }[article_id],
    )
    monkeypatch.setattr(
        update_scholar,
        "fetch_profile_stats",
        lambda scholar_id: {"papers": 49, "citations": 1335, "h_index": 15, "i10_index": 21},
    )
    monkeypatch.setattr(update_scholar, "resolve_preview_image", lambda record, previous: record["preview_image"] or "https://example.com/high-og.png")

    scholar_data = update_scholar.build_scholar_data(entries, "user123", {})

    assert scholar_data["profile"]["papers"] == 49
    assert scholar_data["top_publications"][0]["title"] == "Paper High"
    assert scholar_data["top_publications"][0]["citation_count"] == 98
    assert scholar_data["top_publications"][0]["preview_image"] == "/assets/img/publication_preview/high.png"
    assert scholar_data["top_publications"][1]["title"] == "Paper Low"
    assert scholar_data["top_publications"][1]["preview_image"] == "https://example.com/high-og.png"
    assert scholar_data["profile"]["updated_at"].endswith("Z")


def test_build_scholar_data_limits_top_publications_to_ten(monkeypatch):
    entries = [
        make_entry(
            f"paper-{index}",
            title=f"Paper {index}",
            author="Author",
            year="2024",
            html=f"https://example.com/paper-{index}",
            citation_count=index,
        )
        for index in range(12)
    ]

    monkeypatch.setattr(update_scholar, "fetch_publication_details", lambda scholar_id, article_id: {})
    monkeypatch.setattr(
        update_scholar,
        "fetch_profile_stats",
        lambda scholar_id: {"papers": 12, "citations": 660, "h_index": 12, "i10_index": 10},
    )
    monkeypatch.setattr(update_scholar, "resolve_preview_image", lambda record, previous: record["preview_image"])

    scholar_data = update_scholar.build_scholar_data(entries, "user123", {})

    assert len(scholar_data["top_publications"]) == update_scholar.TOP_PUBLICATIONS_LIMIT
    assert scholar_data["top_publications"][0]["title"] == "Paper 11"
    assert scholar_data["top_publications"][-1]["title"] == "Paper 2"


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
                note="CoRL",
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
    assert "  note={ CoRL }," in content
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


def test_main_loads_merges_and_writes_outputs(monkeypatch, capsys):
    fetched_entries = [
        make_entry(
            "paper2024",
            title="Paper",
            author="Author",
            year="2024",
            html="https://example.com",
            scholar_id="gs123",
        )
    ]
    existing_entries = [
        make_entry(
            "paper2023",
            title="Older",
            author="Author",
            year="2023",
            html="https://older.example.com",
        )
    ]
    merged_entries = fetched_entries + existing_entries
    scholar_data = {
        "profile": {"papers": 2, "citations": 10, "h_index": 1, "i10_index": 0, "updated_at": "2026-03-12T00:00:00Z"},
        "publications": [],
        "top_publications": [],
    }
    calls = {}

    monkeypatch.setattr(update_scholar, "read_scholar_id", lambda: "scholar-123")
    monkeypatch.setattr(update_scholar, "read_existing_scholar_data", lambda: {"profile": {"papers": 1}})
    monkeypatch.setattr(update_scholar, "parse_existing_bib", lambda: existing_entries)
    monkeypatch.setattr(
        update_scholar,
        "load_publications",
        lambda scholar_id: calls.__setitem__("load_publications", scholar_id) or ("scholar", fetched_entries),
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
        "build_scholar_data",
        lambda entries, scholar_id, previous_data: calls.__setitem__(
            "build_scholar_data",
            (entries, scholar_id, previous_data),
        )
        or scholar_data,
    )
    monkeypatch.setattr(update_scholar, "write_bib", lambda entries: calls.__setitem__("write_bib", entries))
    monkeypatch.setattr(
        update_scholar,
        "write_scholar_data",
        lambda data: calls.__setitem__("write_scholar_data", data),
    )

    update_scholar.main()

    captured = capsys.readouterr()
    assert calls["load_publications"] == "scholar-123"
    assert calls["merge_entries"] == (fetched_entries, existing_entries, False)
    assert calls["build_scholar_data"] == (merged_entries, "scholar-123", {"profile": {"papers": 1}})
    assert calls["write_bib"] == merged_entries
    assert calls["write_scholar_data"] == scholar_data
    assert "Updated 2 publications from scholar" in captured.out
