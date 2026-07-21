import importlib.util
import sys
from pathlib import Path


sys.dont_write_bytecode = True

MODULE_PATH = Path(__file__).resolve().parents[1] / "bin" / "profile_update_report.py"
SPEC = importlib.util.spec_from_file_location("profile_update_report", MODULE_PATH)
profile_update_report = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = profile_update_report
SPEC.loader.exec_module(profile_update_report)


def test_build_report_summarizes_metrics_publications_and_progress(monkeypatch):
    before_scholar = {
        "profile": {"papers": 10, "citations": 100, "h_index": 5, "i10_index": 4},
        "publications": [
            {"google_scholar_id": "old", "title": "Old paper", "citation_count": 10}
        ],
    }
    after_scholar = {
        "profile": {"papers": 11, "citations": 112, "h_index": 6, "i10_index": 4},
        "publications": [
            {"google_scholar_id": "old", "title": "Old paper", "citation_count": 15},
            {
                "google_scholar_id": "new",
                "title": "New paper",
                "year": "2026",
                "citation_count": 1,
                "external_url": "https://example.com/paper",
            },
        ],
    }
    before_progress = {"items": []}
    after_progress = {
        "items": [
            {
                "id": "progress-new",
                "category": "company",
                "title": "VLA launch",
                "url": "https://example.com/news",
            }
        ]
    }

    monkeypatch.setattr(
        profile_update_report,
        "read_yaml_from_git",
        lambda ref, path: before_scholar if path == profile_update_report.SCHOLAR_FILE else before_progress,
    )
    monkeypatch.setattr(
        profile_update_report,
        "read_yaml",
        lambda path: after_scholar if path == profile_update_report.SCHOLAR_FILE else after_progress,
    )
    monkeypatch.setattr(
        profile_update_report,
        "changed_files",
        lambda ref: ["_data/scholar.yml | 10 +++++-----"],
    )

    report = profile_update_report.build_report("HEAD")

    assert "Papers: 10 → 11 (+1)" in report
    assert "Citations: 100 → 112 (+12)" in report
    assert "[New paper (2026)](https://example.com/paper)" in report
    assert "Old paper: 10 → 15 (+5)" in report
    assert "[Company · VLA launch](https://example.com/news)" in report
    assert "Nothing in this proposal is published" in report


def test_signed_delta_ignores_non_integer_values():
    assert profile_update_report.signed_delta("N/A", 10) == ""
    assert profile_update_report.signed_delta(10, 10) == ""
    assert profile_update_report.signed_delta(10, 8) == " (-2)"
