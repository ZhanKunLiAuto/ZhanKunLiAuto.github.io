# Google Scholar Update Automation

This repository refreshes Google Scholar statistics and publication metadata on a weekly schedule. Generated changes are never published directly: the workflow emails the repository owner, opens a review PR, and waits for an explicit owner-only approval command.

## What is synchronized

- Google Scholar paper count, total citations, h-index, and i10-index
- Publication metadata, per-paper citations, links, and homepage preview cards
- New publications discovered on the configured Scholar profile
- The English and Chinese homepage Scholar sections backed by `_data/scholar.yml`

The Google Scholar profile ID is read from `_data/socials.yml`. The automation does not fetch or modify personal news, company news, or other homepage content.

## Safe publication flow

1. `Propose Google Scholar Update` runs every Monday at 09:00 Asia/Shanghai, or on demand from GitHub Actions.
2. It refreshes Scholar data, formats the generated YAML, runs the unit tests, and builds the site.
3. If generated content changed, it creates a candidate branch and a draft PR.
4. It emails the full summary and PR link to the configured owner address.
5. Only after email delivery succeeds does the PR receive the `scholar-update:emailed` label and become confirmable.
6. The repository owner reviews the diff and comments exactly `/approve` to publish, or `/reject` to cancel.
7. The approval workflow verifies the commenter, repository, base branch, automation branch, open state, and email-delivery label before merging.
8. It explicitly starts the homepage deployment after the merge, so the approved content is published even though the merge itself was performed by a workflow token.

Only files related to Google Scholar are included in the candidate commit. Other homepage content remains unchanged.

## Required GitHub configuration

Open `Settings → Actions → General → Workflow permissions`, select `Read and write permissions`, and enable `Allow GitHub Actions to create and approve pull requests`. The workflow creates the candidate PR, but publication approval still requires the repository owner's `/approve` comment.

Open `Settings → Secrets and variables → Actions` and configure these repository secrets:

| Name            | Required | Example / purpose                                                 |
| --------------- | -------- | ----------------------------------------------------------------- |
| `SMTP_HOST`     | yes      | SMTP server hostname supplied by the mail provider                |
| `SMTP_PORT`     | no       | Defaults to `465`                                                 |
| `SMTP_SECURITY` | no       | `ssl` (default), `starttls`, or `plain`                           |
| `SMTP_USERNAME` | yes      | SMTP login, normally the sender email address                     |
| `SMTP_PASSWORD` | yes      | SMTP authorization code or app password, not the account password |
| `SMTP_FROM`     | no       | Sender address; defaults to `SMTP_USERNAME`                       |

The recipient defaults to `zk_1028@aliyun.com`. To change it without editing the workflow, add the repository variable `PROFILE_UPDATE_EMAIL`.

Never commit SMTP credentials to this repository. The proposal workflow validates all required mail settings before it creates a confirmable update.

## Manual operation

To request an immediate refresh:

1. Open `Actions → Propose Google Scholar Update`.
2. Select `Run workflow`.
3. Wait for the confirmation email and open the linked PR.
4. Review the `Files changed` tab and the generated summary.
5. Comment `/approve` or `/reject` on its own line.

Do not merge the automation PR manually if you want the email-confirmation audit trail; use `/approve` so the owner checks are recorded.

## Local verification

```bash
python -m pip install -r requirements.txt pytest
pytest
python bin/update_scholar.py
npx prettier _data/scholar.yml --write
python bin/profile_update_report.py --base HEAD
bundle exec jekyll build
```

The Scholar update command uses the public network. Tests do not send email or require live Scholar access.

## Failure behavior

- Scholar fetch failure: the proposal stops and no update is made.
- Tests or site build fail: no review PR is created.
- Email configuration or delivery fails: the PR stays unconfirmable and cannot be merged by the approval workflow.
- Unauthorized `/approve`: the workflow rejects the command.
- `/reject`: the candidate PR and its automation branch are closed without changing the homepage.
