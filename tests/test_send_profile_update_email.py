import importlib.util
import sys
from pathlib import Path

import pytest


sys.dont_write_bytecode = True

MODULE_PATH = Path(__file__).resolve().parents[1] / "bin" / "send_profile_update_email.py"
SPEC = importlib.util.spec_from_file_location("send_profile_update_email", MODULE_PATH)
send_profile_update_email = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = send_profile_update_email
SPEC.loader.exec_module(send_profile_update_email)


def set_smtp_environment(monkeypatch):
    values = {
        "SMTP_HOST": "smtp.example.com",
        "SMTP_PORT": "465",
        "SMTP_USERNAME": "bot@example.com",
        "SMTP_PASSWORD": "secret",
        "SMTP_SECURITY": "ssl",
        "PROFILE_UPDATE_EMAIL": "owner@example.com",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)


def test_smtp_config_reads_and_validates_environment(monkeypatch):
    set_smtp_environment(monkeypatch)

    config = send_profile_update_email.smtp_config()

    assert config["host"] == "smtp.example.com"
    assert config["port"] == 465
    assert config["sender"] == "bot@example.com"
    assert config["recipient"] == "owner@example.com"


def test_smtp_config_rejects_missing_password(monkeypatch):
    set_smtp_environment(monkeypatch)
    monkeypatch.delenv("SMTP_PASSWORD")

    with pytest.raises(RuntimeError, match="SMTP_PASSWORD"):
        send_profile_update_email.smtp_config()


def test_message_content_requires_explicit_approval():
    subject, plain, html_body = send_profile_update_email.message_content(
        "proposal",
        "## Google Scholar 更新\n- 总引用量：10 → 12（+2）",
        "https://github.com/example/repo/pull/1",
    )

    assert "需要确认" in subject
    assert "Google Scholar" in subject
    assert "/approve" in plain
    assert "尚未发布" in plain
    assert "不会修改其他个人主页内容" in plain
    assert "https://github.com/example/repo/pull/1" in html_body
    assert "<code>/approve</code>" in html_body
