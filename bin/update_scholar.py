#!/usr/bin/env python3
from __future__ import annotations

import html
import os
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote

import requests
import yaml

try:
    import fitz
except ModuleNotFoundError:
    fitz = None

DATA_FILE = Path("_data/socials.yml")
BIB_FILE = Path("_bibliography/papers.bib")
SCHOLAR_DATA_FILE = Path("_data/scholar.yml")
PREVIEW_IMAGE_DIR = Path("assets/img/publication_preview")
TOP_PUBLICATIONS_LIMIT = 10
MAX_DETAIL_FETCH_FAILURES = 3

SCHOLAR_URL = (
    "https://r.jina.ai/http://scholar.google.com/citations"
    "?user={scholar_id}&hl=en&cstart=0&pagesize=100&sortby=pubdate"
)
SCHOLAR_PROFILE_URL = "https://scholar.google.com/citations?user={scholar_id}&hl=en"
SCHOLAR_PROFILE_LIST_URL = "https://scholar.google.com/citations?user={scholar_id}&hl=en&cstart=0&pagesize=100&sortby=pubdate"
SCHOLAR_DETAIL_URL = (
    "https://scholar.google.com/citations"
    "?view_op=view_citation&hl=en&user={scholar_id}&citation_for_view={scholar_id}:{article_id}"
)
PUBLICATIONS_FALLBACK_URL = os.getenv(
    "SCHOLAR_PUBLICATIONS_FALLBACK_URL",
    "https://zhankunliauto.github.io/publications/",
)
REQUEST_TIMEOUT = 30
FIELD_ORDER = [
    "title",
    "author",
    "year",
    "note",
    "html",
    "doi",
    "arxiv",
    "pdf",
    "preview",
    "thumbnail",
    "google_scholar_id",
]
DETAIL_FETCH_FAILURES = 0
DETAIL_FETCH_DISABLED = False


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
    return yaml.safe_load(DATA_FILE.read_text(encoding="utf-8")) or {}


def read_scholar_id() -> str:
    return str(read_socials().get("scholar_userid") or "").strip()


def read_existing_scholar_data() -> dict:
    if not SCHOLAR_DATA_FILE.exists():
        return {}
    return yaml.safe_load(SCHOLAR_DATA_FILE.read_text(encoding="utf-8")) or {}


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


def http_get_bytes(url: str) -> bytes:
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
    return response.content


def ensure_not_blocked(text: str) -> None:
    lowered = text.lower()
    blocked_markers = [
        "target url returned error 403",
        "we're sorry",
        "automated queries",
        "sorry...",
    ]
    if any(marker in lowered for marker in blocked_markers):
        raise ScholarFetchError("Google Scholar blocked the request")


def fetch_scholar_markdown(scholar_id: str) -> str:
    text = http_get(SCHOLAR_URL.format(scholar_id=scholar_id))
    ensure_not_blocked(text)
    return text


def fetch_scholar_profile_html(scholar_id: str) -> str:
    text = http_get(SCHOLAR_PROFILE_LIST_URL.format(scholar_id=scholar_id))
    ensure_not_blocked(text)
    return text


def fetch_publications_fallback() -> str:
    if not PUBLICATIONS_FALLBACK_URL:
        raise ScholarFetchError("No publications fallback URL configured")
    return http_get(PUBLICATIONS_FALLBACK_URL)


def fetch_profile_stats(scholar_id: str) -> dict[str, int | str]:
    html_text = http_get(SCHOLAR_PROFILE_URL.format(scholar_id=scholar_id))
    ensure_not_blocked(html_text)
    return parse_profile_stats(html_text)


def fetch_publication_details(scholar_id: str, article_id: str) -> dict[str, int | str]:
    html_text = http_get(SCHOLAR_DETAIL_URL.format(scholar_id=scholar_id, article_id=article_id))
    ensure_not_blocked(html_text)

    details: dict[str, int | str] = {
        "citation_count": parse_citation_count(html_text),
        "external_url": extract_title_link_from_html(html_text),
        "pdf_url": extract_pdf_link_from_html(html_text),
    }
    return {key: value for key, value in details.items() if value not in ("", None)}


def normalize_text(value: str) -> str:
    value = html.unescape(value)
    value = value.replace("\xa0", " ")
    return re.sub(r"\s+", " ", value).strip()


def strip_html_tags(value: str) -> str:
    return normalize_text(re.sub(r"<[^>]+>", " ", value))


def normalize_title(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = normalized.encode("ascii", "ignore").decode("ascii").lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def normalize_venue(value: str, year: str) -> str:
    cleaned = strip_html_tags(value)
    if year:
        cleaned = re.sub(rf"[\s,;/()-]*\b{re.escape(year)}\b[\s,;/()-]*", " ", cleaned)
    cleaned = cleaned.strip(" ,;:-")
    return normalize_text(cleaned)


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


def scholar_citation_url(scholar_id: str, article_id: str) -> str:
    return SCHOLAR_DETAIL_URL.format(scholar_id=scholar_id, article_id=article_id)


def parse_profile_stats(text: str) -> dict[str, int | str]:
    def stat_for(label: str) -> int:
        pattern = re.compile(
            rf"<tr[^>]*>\s*<td[^>]*>\s*{re.escape(label)}\s*</td>\s*<td[^>]*>\s*([\d,]+)\s*</td>",
            re.I | re.S,
        )
        match = pattern.search(text)
        if not match:
            raise ScholarFetchError(f"Could not parse Scholar stat: {label}")
        return int(match.group(1).replace(",", ""))

    paper_rows = re.findall(r'class="gsc_a_tr"', text)
    papers = len(paper_rows)
    if papers == 0:
        range_match = re.search(r'class="gsc_a_nn"[^>]*>\s*[\d-]+\s*of\s*(\d+)\s*<', text, re.I)
        if range_match:
            papers = int(range_match.group(1))
    if papers == 0:
        raise ScholarFetchError("Could not determine total paper count")

    return {
        "papers": papers,
        "citations": stat_for("Citations"),
        "h_index": stat_for("h-index"),
        "i10_index": stat_for("i10-index"),
    }


def parse_citation_count(text: str) -> int | None:
    match = re.search(r"Cited by\s+([\d,]+)", text, re.I)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def extract_title_link_from_html(text: str) -> str:
    match = re.search(r'class="gsc_oci_title_link"[^>]*href="([^"]+)"', text, re.I)
    return normalize_text(match.group(1)) if match else ""


def extract_pdf_link_from_html(text: str) -> str:
    match = re.search(r'class="gsc_oci_title_ggi"[^>]*>.*?href="([^"]+)"', text, re.I | re.S)
    return normalize_text(match.group(1)) if match else ""


def extract_open_graph_image(text: str) -> str:
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return normalize_text(match.group(1))
    return ""


def parse_optional_int(value: object) -> int | None:
    normalized = str(value or "").strip().replace(",", "")
    if not normalized.isdigit():
        return None
    return int(normalized)


def absolute_url(url: str, *, base: str) -> str:
    normalized = normalize_text(url)
    if normalized.startswith("//"):
        return f"https:{normalized}"
    if normalized.startswith("/"):
        return f"{base}{normalized}"
    return normalized


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

        raw_info = normalize_text(" ".join(info_lines))
        year = extract_year(raw_info)
        note = normalize_venue(raw_info, year)
        fields = {
            "title": title,
            "author": authors,
            "year": year,
            "html": link,
            "google_scholar_id": extract_scholar_id(link),
        }
        if note:
            fields["note"] = note

        publications.append(
            BibEntry(
                entry_type="misc",
                key="",
                fields=fields,
                field_order=FIELD_ORDER.copy(),
            )
        )
        index = cursor

    return publications


def parse_publications_from_profile_html(text: str) -> list[BibEntry]:
    row_pattern = re.compile(r'<tr[^>]*class="gsc_a_tr"[^>]*>(.*?)</tr>', re.I | re.S)
    publications: list[BibEntry] = []

    for row_html in row_pattern.findall(text):
        title_match = re.search(r'class="gsc_a_at"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', row_html, re.I | re.S)
        if not title_match:
            continue

        title = strip_html_tags(title_match.group(2))
        if not title:
            continue

        gs_gray_matches = re.findall(r'<div[^>]*class="gs_gray"[^>]*>(.*?)</div>', row_html, re.I | re.S)
        authors = strip_html_tags(gs_gray_matches[0]) if gs_gray_matches else ""
        raw_info = strip_html_tags(gs_gray_matches[1]) if len(gs_gray_matches) > 1 else ""

        year_match = re.search(r'class="gsc_a_h[^"]*"[^>]*>\s*(\d{4})\s*<', row_html, re.I | re.S)
        year = year_match.group(1) if year_match else extract_year(raw_info)
        note = normalize_venue(raw_info, year)

        citation_match = re.search(
            r'class="gsc_a_ac[^"]*"[^>]*>\s*(?:<a[^>]*>)?\s*([\d,]+)\s*(?:</a>)?\s*<',
            row_html,
            re.I | re.S,
        )
        citation_count = parse_optional_int(citation_match.group(1) if citation_match else "")

        link = absolute_url(title_match.group(1), base="https://scholar.google.com")
        fields = {
            "title": title,
            "author": authors,
            "year": year,
            "html": link,
            "google_scholar_id": extract_scholar_id(link),
        }
        if note:
            fields["note"] = note
        if citation_count is not None:
            fields["citation_count"] = str(citation_count)

        publications.append(
            BibEntry(
                entry_type="misc",
                key="",
                fields=fields,
                field_order=FIELD_ORDER.copy(),
            )
        )

    if not publications:
        raise ScholarFetchError("Could not parse Scholar publications from profile HTML")
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
        raw_periodical = strip_html_tags(match.group("year"))
        year = extract_year(raw_periodical)
        note = normalize_venue(raw_periodical, year)
        fields = {
            "title": title,
            "author": author,
            "year": year,
            "html": link,
            "google_scholar_id": extract_scholar_id(link),
        }
        if note:
            fields["note"] = note

        publications.append(
            BibEntry(
                entry_type="misc",
                key=normalize_text(match.group("key")),
                fields=fields,
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
    text = BIB_FILE.read_text(encoding="utf-8")
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
    BIB_FILE.write_text(f"---\n---\n\n{body}\n", encoding="utf-8")


def write_scholar_data(data: dict) -> None:
    SCHOLAR_DATA_FILE.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def load_publications(scholar_id: str) -> tuple[str, list[BibEntry]]:
    try:
        profile_html = fetch_scholar_profile_html(scholar_id)
        return "scholar-html", parse_publications_from_profile_html(profile_html)
    except (requests.RequestException, ScholarFetchError) as html_error:
        html_failure = html_error

    try:
        markdown = fetch_scholar_markdown(scholar_id)
        return "scholar", parse_publications_from_markdown(markdown)
    except (requests.RequestException, ScholarFetchError) as scholar_error:
        fallback_page = fetch_publications_fallback()
        publications = parse_publications_from_site(fallback_page)
        sys.stderr.write(f"Scholar fetch failed, used fallback: {html_failure}; {scholar_error}\n")
        return "fallback", publications


def entry_lookup_key(fields: dict[str, str]) -> str:
    scholar_id = fields.get("google_scholar_id", "").strip()
    if scholar_id:
        return scholar_id
    return normalize_title(fields.get("title", ""))


def record_lookup_key(record: dict) -> str:
    scholar_id = str(record.get("google_scholar_id") or "").strip()
    if scholar_id:
        return scholar_id
    return normalize_title(str(record.get("title") or ""))


def publication_sort_key(record: dict) -> tuple[int, int, str]:
    citation_value = record.get("citation_count")
    if citation_value in (None, "", "N/A"):
        citations = -1
    else:
        citations = int(citation_value)
    year_value = record.get("year")
    year = int(year_value) if str(year_value or "").isdigit() else 0
    return (citations, year, normalize_title(str(record.get("title") or "")))


def preferred_external_url(fields: dict[str, str], scholar_url: str) -> str:
    html_url = fields.get("html", "").strip()
    if html_url and "scholar.google.com" not in html_url:
        return html_url
    doi = fields.get("doi", "").strip()
    if doi:
        return doi if "://" in doi else f"https://doi.org/{doi}"
    arxiv = fields.get("arxiv", "").strip()
    if arxiv:
        return arxiv if "://" in arxiv else f"https://arxiv.org/abs/{arxiv}"
    return scholar_url


def preferred_pdf_url(fields: dict[str, str]) -> str:
    pdf_url = fields.get("pdf", "").strip()
    if pdf_url:
        return pdf_url if "://" in pdf_url else f"/assets/pdf/{pdf_url}"
    arxiv = fields.get("arxiv", "").strip()
    if arxiv and "://" not in arxiv:
        return f"https://arxiv.org/pdf/{arxiv}.pdf"
    return ""


def preferred_preview_image(fields: dict[str, str]) -> str:
    preview = fields.get("preview", "").strip()
    if preview:
        return preview if preview.startswith("/") or "://" in preview else f"/assets/img/publication_preview/{preview}"
    thumbnail = fields.get("thumbnail", "").strip()
    if thumbnail:
        return thumbnail
    return ""


def local_file_from_url(url: str) -> Path | None:
    normalized = str(url or "").strip()
    if not normalized:
        return None
    if normalized.startswith("http://") or normalized.startswith("https://"):
        return None
    local_value = normalized[1:] if normalized.startswith("/") else normalized
    path = Path(local_value)
    return path if path.exists() else None


def load_pdf_bytes(pdf_url: str) -> bytes:
    local_path = local_file_from_url(pdf_url)
    if local_path is not None:
        return local_path.read_bytes()
    if not pdf_url.startswith("http"):
        raise ScholarFetchError(f"Unsupported PDF URL: {pdf_url}")
    return http_get_bytes(pdf_url)


def extract_best_pdf_preview(pdf_bytes: bytes) -> tuple[bytes, str] | None:
    if fitz is None:
        return None

    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        best_image: tuple[int, bytes, str] | None = None
        for page_index in range(min(3, document.page_count)):
            page = document.load_page(page_index)
            for image_info in page.get_images(full=True):
                xref = image_info[0]
                try:
                    extracted = document.extract_image(xref)
                except RuntimeError:
                    continue

                image_bytes = extracted.get("image")
                width = int(extracted.get("width") or 0)
                height = int(extracted.get("height") or 0)
                if not image_bytes or width * height < 120_000:
                    continue

                extension = str(extracted.get("ext") or "png").lower()
                score = width * height
                if best_image is None or score > best_image[0]:
                    best_image = (score, image_bytes, extension)

        if best_image is not None:
            _, image_bytes, extension = best_image
            return image_bytes, extension

        first_page = document.load_page(0)
        page_rect = first_page.rect
        clip = fitz.Rect(page_rect.x0, page_rect.y0, page_rect.x1, page_rect.y0 + page_rect.height * 0.58)
        pixmap = first_page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=clip, alpha=False)
        return pixmap.tobytes("png"), "png"
    finally:
        document.close()


def preview_asset_name(record: dict, extension: str) -> str:
    base_key = str(record.get("key") or normalize_title(str(record.get("title") or "")) or "paper")
    safe_key = re.sub(r"[^a-zA-Z0-9._-]+", "-", base_key).strip("-") or "paper"
    return f"{safe_key}-pdf-preview.{extension}"


def generate_pdf_preview(record: dict) -> str:
    pdf_url = str(record.get("pdf_url") or "").strip()
    if not pdf_url:
        return ""

    for extension in ("png", "jpg", "jpeg", "webp"):
        existing_path = PREVIEW_IMAGE_DIR / preview_asset_name(record, extension)
        if existing_path.exists():
            return f"/{existing_path.as_posix()}"

    try:
        pdf_bytes = load_pdf_bytes(pdf_url)
        preview = extract_best_pdf_preview(pdf_bytes)
    except (OSError, RuntimeError, ScholarFetchError, requests.RequestException, ValueError):
        return ""

    if preview is None:
        return ""

    image_bytes, extension = preview
    PREVIEW_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PREVIEW_IMAGE_DIR / preview_asset_name(record, extension)
    output_path.write_bytes(image_bytes)
    return f"/{output_path.as_posix()}"


def resolve_preview_image(record: dict, previous_record: dict | None = None) -> str:
    current_preview = str(record.get("preview_image") or "").strip()
    previous_preview = str(previous_record.get("preview_image") or "").strip() if previous_record else ""

    if current_preview:
        return current_preview

    generated_preview = generate_pdf_preview(record)
    if generated_preview:
        return generated_preview

    candidates = [
        str(record.get("external_url") or "").strip(),
        str(record.get("pdf_url") or "").strip(),
    ]
    for candidate in candidates:
        if not candidate.startswith("http"):
            continue
        try:
            og_image = extract_open_graph_image(http_get(candidate))
        except requests.RequestException:
            og_image = ""
        if og_image and not og_image.lower().endswith(".svg"):
            return og_image

    if previous_preview:
        return previous_preview
    return ""


def build_publication_record(
    entry: BibEntry,
    scholar_id: str,
    previous_record: dict | None = None,
) -> dict:
    global DETAIL_FETCH_DISABLED
    global DETAIL_FETCH_FAILURES

    fields = entry.fields
    article_id = fields.get("google_scholar_id", "").strip()
    scholar_url = scholar_citation_url(scholar_id, article_id) if article_id else fields.get("html", "").strip()
    details: dict[str, int | str] = {}
    citation_count = parse_optional_int(fields.get("citation_count"))
    external_url = preferred_external_url(fields, scholar_url)
    pdf_url = preferred_pdf_url(fields)
    preview_image = preferred_preview_image(fields)

    needs_detail_fetch = article_id and not DETAIL_FETCH_DISABLED and (
        citation_count is None or external_url == scholar_url or not pdf_url
    )

    if needs_detail_fetch:
        try:
            details = fetch_publication_details(scholar_id, article_id)
        except (requests.RequestException, ScholarFetchError) as error:
            details = {}
            DETAIL_FETCH_FAILURES += 1
            if isinstance(error, ScholarFetchError) or DETAIL_FETCH_FAILURES >= MAX_DETAIL_FETCH_FAILURES:
                DETAIL_FETCH_DISABLED = True

    note = fields.get("note", "").strip()
    external_url = str(details.get("external_url") or "").strip() or external_url
    pdf_url = str(details.get("pdf_url") or "").strip() or pdf_url
    citation_count = details.get("citation_count") or citation_count
    if citation_count is None:
        citation_count = None

    if previous_record:
        if citation_count is None:
            citation_count = previous_record.get("citation_count")
        if not external_url or external_url == scholar_url:
            external_url = str(previous_record.get("external_url") or "").strip()
        if not pdf_url:
            pdf_url = str(previous_record.get("pdf_url") or "").strip()

    return {
        "key": entry.key,
        "title": fields.get("title", "").strip(),
        "authors": fields.get("author", "").strip(),
        "year": fields.get("year", "").strip(),
        "venue": note,
        "citation_count": citation_count,
        "scholar_url": scholar_url,
        "external_url": external_url,
        "pdf_url": pdf_url,
        "doi": fields.get("doi", "").strip(),
        "arxiv": fields.get("arxiv", "").strip(),
        "preview_image": preview_image,
        "google_scholar_id": article_id,
    }


def build_scholar_data(
    entries: list[BibEntry],
    scholar_id: str,
    previous_data: dict | None = None,
) -> dict:
    previous_data = previous_data or {}
    previous_publications = previous_data.get("publications") or []
    previous_by_key = {record_lookup_key(record): record for record in previous_publications}

    publications: list[dict] = []
    for entry in entries:
        record = build_publication_record(entry, scholar_id, previous_by_key.get(entry_lookup_key(entry.fields)))
        publications.append(record)

    publications.sort(key=publication_sort_key, reverse=True)
    top_publications: list[dict] = []
    for record in publications[:TOP_PUBLICATIONS_LIMIT]:
        previous_record = previous_by_key.get(record_lookup_key(record))
        enriched = dict(record)
        enriched["preview_image"] = resolve_preview_image(record, previous_record)
        top_publications.append(enriched)

    try:
        profile = fetch_profile_stats(scholar_id)
    except (requests.RequestException, ScholarFetchError):
        profile = dict(previous_data.get("profile") or {})

    profile["updated_at"] = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    return {
        "profile": profile,
        "publications": publications,
        "top_publications": top_publications,
    }


def main() -> None:
    scholar_id = read_scholar_id()
    if not scholar_id:
        print(f"No scholar_userid found in {DATA_FILE}")
        raise SystemExit(1)

    previous_data = read_existing_scholar_data()
    existing_entries = parse_existing_bib()

    try:
        source, fetched_entries = load_publications(scholar_id)
    except (requests.RequestException, ScholarFetchError) as error:
        print(f"Failed to update Scholar publications: {error}")
        raise SystemExit(1) from error

    merged_entries = merge_entries(
        fetched_entries,
        existing_entries,
        prefer_existing=(source == "fallback"),
    )
    scholar_data = build_scholar_data(merged_entries, scholar_id, previous_data)
    write_bib(merged_entries)
    write_scholar_data(scholar_data)
    print(f"Updated {len(merged_entries)} publications from {source}")


if __name__ == "__main__":
    main()
