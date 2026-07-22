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


def test_build_report_summarizes_only_google_scholar_changes(monkeypatch):
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
    monkeypatch.setattr(
        profile_update_report,
        "read_yaml_from_git",
        lambda ref, path: before_scholar,
    )
    monkeypatch.setattr(
        profile_update_report,
        "read_yaml",
        lambda path: after_scholar,
    )
    monkeypatch.setattr(
        profile_update_report,
        "changed_files",
        lambda ref: ["_data/scholar.yml | 10 +++++-----"],
    )

    report = profile_update_report.build_report("HEAD")

    assert "论文数量: 10 → 11（+1）" in report
    assert "总引用量: 100 → 112（+12）" in report
    assert "[New paper (2026)](https://example.com/paper)" in report
    assert "Old paper：10 → 15（+5）" in report
    assert "个人和公司" not in report
    assert "仅包含 Google Scholar 数据" in report


def test_signed_delta_ignores_non_integer_values():
    assert profile_update_report.signed_delta("N/A", 10) == ""
    assert profile_update_report.signed_delta(10, 10) == "（无变化）"
    assert profile_update_report.signed_delta(10, 8) == "（-2）"


def test_removed_publications_are_called_out():
    before = {
        "publications": [
            {"google_scholar_id": "kept", "title": "Kept"},
            {"google_scholar_id": "removed", "title": "Removed paper"},
        ]
    }
    after = {"publications": [{"google_scholar_id": "kept", "title": "Kept"}]}

    assert profile_update_report.removed_publication_lines(before, after) == ["- Removed paper"]


def test_workflow_formats_only_generated_scholar_data():
    workflow = (
        Path(__file__).resolve().parents[1] / ".github" / "workflows" / "update-scholar.yml"
    ).read_text(encoding="utf-8")

    assert "python bin/update_scholar.py" in workflow
    assert "npx prettier _data/scholar.yml --write" in workflow
    assert "SERPAPI_KEY: ${{ secrets.SERPAPI_KEY }}" in workflow
    assert "update_progress" not in workflow
    assert "_data/progress.yml" not in workflow
