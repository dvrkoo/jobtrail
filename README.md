# JobTrail

JobTrail is a local-first CLI that reconstructs a job-search timeline from mailbox metadata.

MVP status: v0.1.0 is tagged. v0.2 is focused on making the CLI feel like a real product: interactive startup, onboarding, settings, multiple provider accounts, and per-account sync windows.

## Privacy

JobTrail stores application records, email metadata, classifier reasons, confidence scores, and short snippets. It does not store full email bodies by default and never deletes email.

Local paths:

- Config: `~/.config/jobtrail/config.toml`
- Database: `~/.local/share/jobtrail/jobtrail.db`
- Tokens: `~/.local/share/jobtrail/tokens/`

Override paths with `JOBTRAIL_CONFIG_DIR` and `JOBTRAIL_DATA_DIR`.

## Install

```bash
uv sync
```

## Interactive Startup

Run:

```bash
uv run jobtrail
```

If config or the database is missing, JobTrail starts onboarding. Otherwise it shows a Rich home screen with a greeting, motivational phrase, provider status, last sync status, quick stats, and suggested next actions.

## Onboarding

```bash
uv run jobtrail onboard
```

The wizard asks for display name, motivational greeting settings, ghosting threshold, and provider accounts. It is safe to rerun and does not delete data.

## Providers

Gmail works. Outlook exists as a configuration stub for v0.2; Microsoft Graph sync is planned.

Each provider account has its own sync window. Examples:

- Gmail personal: last 12 months
- Gmail university: last 24 months
- Outlook: last 6 months

Supported windows:

- Absolute: `YYYY-MM-DD` start and optional end date
- Relative: last 30 days, 90 days, 6 months, 12 months, 24 months
- All available

Commands:

```bash
uv run jobtrail providers list
uv run jobtrail providers add
uv run jobtrail providers remove 1
```

## Gmail Setup

Create a Google OAuth desktop app, download `credentials.json` into the project directory, then run:

```bash
uv run jobtrail providers add
uv run jobtrail sync --provider gmail --dry-run
```

OAuth starts on first sync if needed. Labels are never applied unless `label-emails --apply` is used.

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
jobtrail list --status rejected
jobtrail show 1
jobtrail stats
jobtrail export --format markdown
jobtrail label-emails --provider gmail --dry-run
jobtrail label-emails --provider gmail --apply
```

## Try It Without Gmail

```bash
uv run jobtrail init
uv run jobtrail sync --from-sample-json examples/sample_gmail_messages.json
uv run jobtrail list
uv run jobtrail stats
uv run jobtrail export --format csv
uv run pytest
```

## Manual GitHub Remote

If `gh` is unavailable or unauthenticated:

```bash
git remote add origin git@github.com:<you>/jobtrail.git
git push -u origin main --tags
git push -u origin feat/v0.2-onboarding
```

## Roadmap

- Better company and role extraction.
- Phrase packs beyond English.
- Microsoft Graph sync for Outlook.
- Optional full-body storage with explicit opt-in.
- Richer deduplication.
- No web dashboard until the CLI earns it.
