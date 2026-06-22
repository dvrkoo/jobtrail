# JobTrail

JobTrail is a local-first CLI that reconstructs a job-search timeline from mailbox metadata.

MVP scope: Gmail, SQLite, deterministic rules, and sample JSON sync. No dashboard, no LLM classification, no Outlook yet.

## Privacy

JobTrail stores application records, email metadata, classifier reasons, confidence scores, and short snippets. It does not store full email bodies by default and never deletes email.

## Install

```bash
uv sync
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

## Gmail Setup

Create a Google OAuth desktop app, download `credentials.json` into the project directory, then run:

```bash
uv run jobtrail sync --provider gmail --dry-run
```

Tokens are stored in `~/.local/share/jobtrail/tokens/`. Config is stored in `~/.config/jobtrail/config.toml`. Override paths with `JOBTRAIL_CONFIG_DIR` and `JOBTRAIL_DATA_DIR`.

## Commands

```bash
jobtrail init
jobtrail sync --provider gmail --dry-run
jobtrail sync --from-sample-json examples/sample_gmail_messages.json
jobtrail list --status rejected
jobtrail show 1
jobtrail stats
jobtrail export --format markdown
jobtrail label-emails --provider gmail --dry-run
jobtrail label-emails --provider gmail --apply
```

## Roadmap

- Better company and role extraction.
- Phrase packs beyond English.
- Outlook/Microsoft Graph provider.
- Optional full-body storage with explicit opt-in.
- Richer deduplication.
