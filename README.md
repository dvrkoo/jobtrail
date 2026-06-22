# JobTrail

JobTrail is a local-first CLI that reconstructs your job-search timeline from your mailbox.

Most job trackers require manual entry. JobTrail reads job-related email metadata, classifies application events, stores a local SQLite timeline, and helps you see what is pending, rejected, interviewing, offered, or ghosted.

Status: early MVP. Gmail works. Outlook is a stub for now. No web dashboard, no LLM classifier, and no full email body storage by default.

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
- Gmail provider and OAuth flow
- Multiple provider accounts
- Per-account sync windows
- Sample JSON sync for demos and tests
- List, show, stats, CSV export, Markdown export
- Gmail label dry-run/apply mode
- Outlook provider configuration stub

## Install

```bash
uv sync
```

## Demo Flow

```bash
uv sync
uv run jobtrail
uv run jobtrail sync --from-sample-json examples/sample_gmail_messages.json
uv run jobtrail stats
uv run jobtrail list --status rejected
uv run jobtrail export --format markdown
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
jobtrail sync --account you@example.com
jobtrail sync --from-sample-json examples/sample_gmail_messages.json
jobtrail list --status pending
jobtrail show 1
jobtrail stats
jobtrail export --format csv
jobtrail export --format markdown
jobtrail label-emails --provider gmail --dry-run
```

## Export

```bash
uv run jobtrail export --format csv
uv run jobtrail export --format markdown
```

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
