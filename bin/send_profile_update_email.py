#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

DEFAULT_SMTP_PORT = 465


def required_env(name: str) -> str:
    value = str(os.getenv(name) or "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def smtp_config() -> dict[str, str | int]:
    port_value = str(os.getenv("SMTP_PORT") or DEFAULT_SMTP_PORT).strip()
    try:
        port = int(port_value)
    except ValueError as error:
        raise RuntimeError("SMTP_PORT must be an integer") from error

    security = str(os.getenv("SMTP_SECURITY") or "ssl").strip().lower()
    if security not in {"ssl", "starttls", "plain"}:
        raise RuntimeError("SMTP_SECURITY must be ssl, starttls, or plain")

    username = required_env("SMTP_USERNAME")
    return {
        "host": required_env("SMTP_HOST"),
        "port": port,
        "username": username,
        "password": required_env("SMTP_PASSWORD"),
        "security": security,
        "sender": str(os.getenv("SMTP_FROM") or username).strip(),
        "recipient": required_env("PROFILE_UPDATE_EMAIL"),
    }


def summary_html(summary: str) -> str:
    paragraphs: list[str] = []
    for line in summary.splitlines():
        escaped = html.escape(line)
        if line.startswith("### "):
            paragraphs.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("## "):
            paragraphs.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("- "):
            paragraphs.append(f"<p>• {html.escape(line[2:])}</p>")
        elif line.startswith("```"):
            continue
        elif escaped:
            paragraphs.append(f"<p>{escaped}</p>")
    return "\n".join(paragraphs)


def message_content(status: str, summary: str, review_url: str) -> tuple[str, str, str]:
    if status == "proposal":
        subject = "[需要确认] 个人主页定期更新提案"
        intro = "系统发现了可同步到个人主页的新内容。当前只是候选更新，尚未发布。"
        action = f"请在 GitHub 审阅变更：{review_url}\n确认无误后，在 PR 中评论 /approve。"
    elif status == "published":
        subject = "[已发布] 个人主页定期更新"
        intro = "你批准的个人主页更新已经合并并进入发布流程。"
        action = f"查看已合并的更新：{review_url}"
    else:
        subject = "[已取消] 个人主页定期更新"
        intro = "本次个人主页候选更新已取消，没有发布。"
        action = f"查看记录：{review_url}"

    plain = f"{intro}\n\n{summary.strip()}\n\n{action}\n"
    action_html = html.escape(review_url)
    html_body = (
        "<html><body>"
        f"<p>{html.escape(intro)}</p>"
        f"{summary_html(summary)}"
        f'<p><a href="{action_html}">在 GitHub 查看并确认</a></p>'
        + ("<p>确认无误后，请在 PR 中评论 <code>/approve</code>。</p>" if status == "proposal" else "")
        + "</body></html>"
    )
    return subject, plain, html_body


def send_email(config: dict[str, str | int], message: EmailMessage) -> None:
    context = ssl.create_default_context()
    security = str(config["security"])
    if security == "ssl":
        with smtplib.SMTP_SSL(str(config["host"]), int(config["port"]), context=context) as client:
            client.login(str(config["username"]), str(config["password"]))
            client.send_message(message)
        return

    with smtplib.SMTP(str(config["host"]), int(config["port"])) as client:
        if security == "starttls":
            client.starttls(context=context)
        client.login(str(config["username"]), str(config["password"]))
        client.send_message(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send profile update review emails")
    parser.add_argument("--check-config", action="store_true")
    parser.add_argument("--status", choices=["proposal", "published", "rejected"], default="proposal")
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--review-url", default="")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = smtp_config()
    if args.check_config:
        print("SMTP configuration is present")
        return
    if not args.summary or not args.summary.exists():
        raise RuntimeError("--summary must point to an existing Markdown file")
    if not args.review_url:
        raise RuntimeError("--review-url is required")

    summary = args.summary.read_text(encoding="utf-8")
    subject, plain, html_body = message_content(args.status, summary, args.review_url)
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = str(config["sender"])
    message["To"] = str(config["recipient"])
    message.set_content(plain)
    message.add_alternative(html_body, subtype="html")
    send_email(config, message)
    print(f"Sent {args.status} email")


if __name__ == "__main__":
    main()
