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
RAINDROP_INCLUDE_UNSORTED=true
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

## Process Raindrop Inbox and Unsorted Items

List available collections when you need IDs or want to confirm names:

```bash
python3 scripts/raindrop_api.py collections
```

List Inbox and Unsorted candidates:

```bash
python3 scripts/raindrop_api.py inbox --limit 5
```

Unsorted is included by default. To list only the configured Inbox collection, use:

```bash
python3 scripts/raindrop_api.py inbox --limit 5 --no-unsorted
```

After creating and verifying the Apple Note, process the matching raindrop from Inbox or Unsorted:

```bash
python3 scripts/raindrop_api.py process --id 12345 --tags "#clip-notes #reference #ai"
```

If the Processed collection is not present and should be created:

```bash
python3 scripts/raindrop_api.py process --id 12345 --tags "#clip-notes #reference #ai" --create-processed
```

Use `--dry-run` to inspect the update body before moving the bookmark.

For backlog processing, use the batch runner. It creates a compact Apple Note from Raindrop metadata, verifies the note by embedded Raindrop ID, then moves only verified items to Processed:

```bash
python3 scripts/raindrop_clip_notes_batch.py run --max-items 25 --sleep 10
python3 scripts/raindrop_clip_notes_batch.py run --all --sleep 10
```

`--batch-size` defaults to 50 because that is the helper's Raindrop page size. `--sleep` spaces out successful moves, and `--retry-sleep` / `--max-retries` control HTTP 429 backoff. Each run writes HTML note files and `summary.json` under `work/raindrop-clip-notes/`.

## Recurring Processing

Recommended operating model:

1. Save candidate links to Raindrop Inbox throughout the day.
2. Leave uncategorized links in Raindrop Unsorted when that is faster than choosing Inbox.
3. Run `scripts/raindrop_clip_notes_batch.py` for metadata-based queue cleanup, or ask Codex for a smaller deep-extraction batch when source content needs review.
4. For each item, Codex or the batch runner writes the Apple Note, verifies the note, then moves the raindrop to Processed with the same canonical tags.
5. If extraction, save, or verification fails, Codex leaves the item in its current review collection and reports the blocker.

Good Codex automation prompt:

```text
Use $clip-notes to review up to 5 items from Raindrop Inbox and Unsorted. For each item, extract available source content, create and verify an Apple Note in clip-notes, then move the Raindrop item to Processed with the same canonical tags. Leave any item in its current review collection if source extraction, Apple Notes save, or verification fails, and report what blocked it.
```

Good backlog command:

```bash
python3 scripts/raindrop_clip_notes_batch.py run --all --sleep 10
```

Codex recurring automation is preferred over Apple Shortcuts for the full workflow because summarization, source fallback handling, Apple Notes verification, and Raindrop post-processing require agent judgment.

Apple Shortcuts can still be useful as a light trigger or status check. A Shortcut can run:

```bash
cd /Users/taheny/vault/teamt/clip-notes
python3 scripts/raindrop_api.py inbox --limit 5
```

Use Apple Shortcuts for intake/status; use Codex for processing.

## Validation

Current lightweight validation:

```bash
python3 -m py_compile scripts/*.py
python3 -m unittest tests/test_raindrop_api.py
python3 -m unittest tests/test_raindrop_clip_notes_batch.py
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
| `Collection 'Inbox' not found` | Intake collection is named differently. | The helper still includes Unsorted by default; pass `--inbox <name-or-id>` or set `RAINDROP_INBOX_COLLECTION` to include a named collection. |
| Raindrop is not in a review collection | The item was already moved or the wrong ID was supplied. | Confirm the ID; use `--skip-inbox-check` only intentionally. |
| HTTP 429 from Raindrop | The API temporarily rate-limited requests. | Increase `--sleep`, increase `--retry-sleep`, or rerun the batch; verified notes are detected by Raindrop ID to avoid duplicate processing. |

## Rollback

There is no deploy system in this repository. For code or docs changes, rollback is standard Git rollback on the affected branch. For Apple Notes content, rollback is manual: delete or edit the affected note in Apple Notes.

<!-- TODO: Add release and packaging steps if a publish process is adopted. -->
