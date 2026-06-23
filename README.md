# JobTrail

JobTrail is a local-first CLI that reconstructs your job-search timeline from your mailbox.

Most job trackers require manual entry. JobTrail reads job-related email metadata, classifies application events, stores a local SQLite timeline, and helps you see what is pending, rejected, interviewing, offered, or ghosted.

Status: early MVP. Gmail works. Outlook is a stub for now. No LLM classifier, and no full email body storage by default.

## Privacy First

JobTrail never deletes email and does not store full email bodies by default.

Stored locally:

- Application records
- Email metadata
- Short snippets
- Classifier confidence and reasons
- Provider account settings

Local paths:

- Config: `~/.config/jobtrail/config.toml`
- Database: `~/.local/share/jobtrail/jobtrail.db`
- Tokens: `~/.local/share/jobtrail/tokens/`

Override paths with `JOBTRAIL_CONFIG_DIR` and `JOBTRAIL_DATA_DIR`.

## What Works Now

- Interactive `jobtrail` startup screen
- Onboarding wizard
- Settings menu
- SQLite local database
- Rule-based explainable classification
- Gmail IMAP App Password provider
- Gmail API OAuth provider
- Multiple provider accounts
- Per-account sync windows
- Sample JSON sync for demos and tests
- List, show, stats, CSV export, Markdown export
- Gmail label dry-run/apply mode
- Outlook provider configuration stub
- Followup review for stale active applications
- Application edit/archive commands
- CSV, Markdown, Excel, and LaTeX exports
- Local JSON backup export/import

## Install

```bash
uv sync
```

## Local Web UI

Run a local browser UI with demo data:

```bash
uv sync
uv run jobtrail ui --demo
```

Run it against your local JobTrail data:

```bash
uv run jobtrail ui
```

The UI is a local Streamlit app. It can show overview metrics, providers, applications, followups, exports, and settings. Demo mode uses temporary config/data paths and does not touch your real JobTrail database or tokens.

Gmail IMAP with a Google App Password is the easiest local setup. Gmail API OAuth remains available for labels. Outlook remains a planned/stub provider.

Screenshot placeholder: add a terminal/browser screenshot after the first v0.4 smoke recording.

## Demo Flow

```bash
uv sync
uv run jobtrail
uv run jobtrail sync --from-sample-json examples/sample_gmail_messages.json
uv run jobtrail stats
uv run jobtrail followups
uv run jobtrail list --status rejected
uv run jobtrail export --format markdown
```

## Daily Workflow

```bash
jobtrail
jobtrail sync
jobtrail followups
jobtrail applications edit <id>
jobtrail export --format xlsx
```

## First Run

```bash
uv run jobtrail
```

If config or the database is missing, JobTrail starts onboarding. Otherwise it opens a Rich command-center screen with provider status, last sync, quick stats, and contextual next actions.

Run onboarding manually:

```bash
uv run jobtrail onboard
```

## Gmail Setup

Easy Gmail setup uses IMAP with a Google App Password:

1. Enable 2-Step Verification on your Google account.
2. Create a Google App Password for Mail.
3. Run:

```bash
uv run jobtrail providers add
uv run jobtrail sync --provider gmail_imap --dry-run
```

JobTrail stores the App Password in your system keyring when available. If keyring storage is unavailable, set the env var shown by `providers add`, for example `JOBTRAIL_GMAIL_IMAP_PASSWORD_YOU_EXAMPLE_COM`.

Labels are only supported by the Gmail API provider for now.

Advanced Gmail setup with API OAuth:

Create a Google OAuth desktop app, download the OAuth client as `credentials.json` into the project directory, then run:

```bash
uv run jobtrail providers add
uv run jobtrail sync --provider gmail --dry-run
```

OAuth starts on first sync if needed. Labels are never applied unless you explicitly run:

```bash
uv run jobtrail label-emails --provider gmail --apply
```

## Provider Management

```bash
uv run jobtrail providers list
uv run jobtrail providers add
uv run jobtrail providers disable 1
uv run jobtrail providers enable 1
uv run jobtrail providers remove 1
```

Each provider account has its own sync window:

- Absolute: `YYYY-MM-DD` start and optional end date
- Relative: last 30 days, 90 days, 6 months, 12 months, 24 months
- All available

Outlook accounts can be configured, but sync is not implemented yet.

## Commands

```bash
jobtrail
jobtrail init
jobtrail onboard
jobtrail settings
jobtrail status
jobtrail sync
jobtrail sync --provider gmail
jobtrail sync --provider gmail_imap
jobtrail sync --account you@example.com
jobtrail sync --from-sample-json examples/sample_gmail_messages.json
jobtrail list --status pending
jobtrail show 1
jobtrail stats
jobtrail followups
jobtrail followups --all
jobtrail followups --format markdown
jobtrail applications edit 1 --company Daon --role "Data Scientist Face Biometrics"
jobtrail applications archive 1
jobtrail export --format csv
jobtrail export --format markdown
jobtrail export --format xlsx
jobtrail export --format latex
jobtrail export --format all
jobtrail backup export
jobtrail backup import backup.json
jobtrail label-emails --provider gmail --dry-run
```

## Export

```bash
uv run jobtrail export --format csv
uv run jobtrail export --format markdown
uv run jobtrail export --format xlsx
uv run jobtrail export --format latex --status pending
uv run jobtrail export --format all
```

Excel exports include Applications, Stats, and Followups sheets. LaTeX exports use a compact `longtable` and escape special characters.

## Daily Followups

```bash
uv run jobtrail followups
```

Default thresholds:

- applied/pending: 14 days
- assessment: 7 days
- interview: 5 days

Use `--all`, `--status`, `--days`, and `--format markdown` for morning reviews or notes.

Example:

```bash
uv run jobtrail followups --days 21 --format markdown
```

## Application Edits

Fix extraction mistakes without touching SQLite directly:

```bash
uv run jobtrail applications edit 1 --company Daon --role "Data Scientist Face Biometrics" --status interview
uv run jobtrail applications archive 1
uv run jobtrail applications unarchive 1
```

Archived applications are hidden from followups by default.

## Backups

```bash
uv run jobtrail backup export
uv run jobtrail backup import ~/.local/share/jobtrail/backups/jobtrail-backup-2026-06-23.json
```

Backups include applications, email events, provider account settings, and non-secret config. OAuth tokens, credentials, and full email bodies are not exported.

## v0.3 Roadmap

- Make installation with `pipx`/`uvx` painless
- Improve Gmail OAuth setup and credentials wizard
- Expand `jobtrail followups`
- Improve deterministic extraction before considering LLMs
- Add demo recording and README visuals

## Manual GitHub Remote

If `gh` is unavailable or unauthenticated:

```bash
git remote add origin git@github.com:<you>/jobtrail.git
git push -u origin main --tags
git push -u origin feat/v0.2-onboarding
```

## Roadmap

- Better company and role extraction
- Phrase packs beyond English
- Microsoft Graph sync for Outlook
- Optional full-body storage with explicit opt-in
- Richer deduplication
- No web dashboard until the CLI earns it
