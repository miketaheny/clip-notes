# Runbook

This runbook covers local setup, routine operations, validation, and troubleshooting for maintainers and agents working on Clip Notes.

## Local Setup

1. Use macOS with Apple Notes configured.
2. Confirm Python 3 is available:

```bash
python3 --version
```

3. Confirm the target Notes folder exists or create it:

```bash
python3 scripts/save_to_apple_notes.py ensure-folder
```

4. Optional: install `yt-dlp` if media caption extraction is needed:

```bash
yt-dlp --version
```

5. Optional: configure Raindrop.io API access if Inbox processing is needed:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
RAINDROP_ACCESS_TOKEN=...
RAINDROP_INBOX_COLLECTION=Inbox
RAINDROP_PROCESSED_COLLECTION=Processed
```

The Raindrop helper auto-loads `.env` by default. Existing shell environment variables take precedence over values in `.env`.

## Save and Verify a Note

Prepare an HTML file using the template in `SKILL.md`, then run:

```bash
python3 scripts/save_to_apple_notes.py save --title "Example - Clip Notes" --html-file /absolute/path/note.html
python3 scripts/save_to_apple_notes.py verify --title "Example - Clip Notes"
```

Expected verification output:

```text
FOUND: Example - Clip Notes
```

## Move an Existing Note

Move a note with a matching title from another folder in the same Apple Notes account into `clip-notes`:

```bash
python3 scripts/save_to_apple_notes.py move --title "Existing note title"
```

## Restyle Spacing

Improve spacing for one note:

```bash
python3 scripts/save_to_apple_notes.py restyle --title "Existing note title"
```

Improve spacing for every note in the folder:

```bash
python3 scripts/save_to_apple_notes.py restyle
```

The restyle command reads the existing note body, normalizes metadata label breaks and section heading spacing, then writes the body back only when it changes.

## Extract Media Captions

Run:

```bash
python3 scripts/extract_media_captions.py "https://example.com/video"
```

Expected successful outputs include paths such as:

```text
metadata=/absolute/path/work/clip-notes-media/metadata.json
captions=/absolute/path/work/clip-notes-media/<id>.en.vtt
transcript=/absolute/path/work/clip-notes-media/transcript.txt
```

If no captions are available, the command still writes metadata when `yt-dlp` can read the URL.

## Process Raindrop Inbox Items

List available collections when you need IDs or want to confirm names:

```bash
python3 scripts/raindrop_api.py collections
```

List Inbox candidates:

```bash
python3 scripts/raindrop_api.py inbox --limit 5
```

If the intake collection is Raindrop's Unsorted system collection, use:

```bash
python3 scripts/raindrop_api.py inbox --inbox -1 --limit 5
```

After creating and verifying the Apple Note, process the matching raindrop:

```bash
python3 scripts/raindrop_api.py process --id 12345 --tags "#clip-notes #reference #ai"
```

If the Processed collection is not present and should be created:

```bash
python3 scripts/raindrop_api.py process --id 12345 --tags "#clip-notes #reference #ai" --create-processed
```

Use `--dry-run` to inspect the update body before moving the bookmark.

## Validation

Current lightweight validation:

```bash
python3 -m py_compile scripts/*.py
python3 -m unittest tests/test_raindrop_api.py
```

Before changing behavior, also manually inspect:

- `SKILL.md` for workflow and done criteria.
- `references/source-strategies.md` for source-specific edge cases.
- `references/share-workflows.md` for user-facing workflow text.
- This `docs/` folder for docs that need matching updates.

## Troubleshooting

| Symptom | Likely Cause | Response |
| --- | --- | --- |
| `MISSING_FOLDER: clip-notes` | Target Notes folder does not exist or account name differs. | Run `ensure-folder` or pass `--account` / `--folder`. |
| `MISSING: <title>` after save | Title mismatch, save failure, or wrong account/folder. | Verify exact title and account/folder flags. |
| AppleScript permission error | macOS automation permission has not been granted. | Grant terminal or Codex automation access to Notes in System Settings. |
| `yt-dlp is not installed or not on PATH.` | Optional media dependency missing. | Install `yt-dlp` or ask the user for transcript/text. |
| Empty caption output | Source has no captions or captions are unavailable to `yt-dlp`. | Use metadata, description, or ask for transcript/source text. |
| Gated article has only preview text | Source is blocked. | Ask for full article text, Reader output, PDF, or screenshots. |
| Missing Raindrop API token | `RAINDROP_ACCESS_TOKEN` or `RAINDROP_TOKEN` is unset. | Add it to `.env` or export it from the shell. |
| `Collection 'Inbox' not found` | Intake collection is named differently or uses Unsorted. | Pass `--inbox <name-or-id>` or set `RAINDROP_INBOX_COLLECTION`. |
| Raindrop is not in Inbox | The item was already moved or the wrong ID was supplied. | Confirm the ID; use `--skip-inbox-check` only intentionally. |

## Rollback

There is no deploy system in this repository. For code or docs changes, rollback is standard Git rollback on the affected branch. For Apple Notes content, rollback is manual: delete or edit the affected note in Apple Notes.

<!-- TODO: Add release and packaging steps if a publish process is adopted. -->
