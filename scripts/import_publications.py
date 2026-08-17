#!/usr/bin/env python3
"""Convert the previous homepage's Scholar YAML snapshot to portable JSON."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml


def normalize_preview_path(raw_path: str) -> str:
    filename = Path(raw_path).name if raw_path else ""
    return f"../assets/img/publications/{filename}" if filename else ""


def normalize_publication(publication: dict) -> dict:
    return {
        "key": str(publication.get("key", "")),
        "title": str(publication.get("title", "")).strip(),
        "authors": str(publication.get("authors", "")).strip(),
        "year": str(publication.get("year", "")).strip(),
        "venue": str(publication.get("venue", "")).strip(),
        "citationCount": int(publication.get("citation_count") or 0),
        "scholarUrl": str(publication.get("scholar_url", "")).strip(),
        "externalUrl": str(publication.get("external_url", "")).strip(),
        "pdfUrl": str(publication.get("pdf_url", "")).strip(),
        "previewImage": normalize_preview_path(
            str(publication.get("preview_image", "")).strip()
        ),
    }


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: import_publications.py SOURCE_SCHOLAR_YML OUTPUT_JSON"
        )

    source_path = Path(sys.argv[1]).expanduser().resolve()
    output_path = Path(sys.argv[2]).expanduser().resolve()
    snapshot = yaml.safe_load(source_path.read_text(encoding="utf-8"))

    publications = [
        normalize_publication(publication)
        for publication in snapshot.get("publications", [])
        if publication.get("title")
    ]
    publications.sort(
        key=lambda item: (int(item["year"] or 0), item["citationCount"]),
        reverse=True,
    )

    payload = {
        "profile": snapshot.get("profile", {}),
        "publications": publications,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
