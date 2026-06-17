# Clip Notes

Clip Notes is an Agent Skill for turning shared sources into concise, tagged Apple Notes. It is designed for URLs, articles, Apple News links, social posts, videos, emails, PDFs, documents, screenshots, and pasted text that the user wants to save for quick consumption and later retrieval.

The skill is local-first. It summarizes content the user provided or authorized, formats the result as HTML, saves it through macOS Apple Notes automation, and verifies that the note exists in the `clip-notes` folder.

## Repository Map

| Path | Purpose |
| --- | --- |
| `SKILL.md` | Canonical skill contract, source workflow, note template, lifecycle rules, and done criteria. |
| `scripts/save_to_apple_notes.py` | Apple Notes helper for creating folders, saving notes, verifying notes, moving notes, listing notes, and normalizing note spacing. |
| `scripts/extract_media_captions.py` | Optional `yt-dlp` wrapper for video/social metadata and caption extraction. |
| `scripts/raindrop_api.py` | Raindrop.io REST API helper for reviewing Inbox bookmarks and moving processed bookmarks to a Processed collection with matching note tags. |
| `references/source-strategies.md` | Edge-case guidance for videos, articles, social posts, email, documents, and extraction failures. |
| `references/share-workflows.md` | Usage guidance for Codex on macOS, ChatGPT, iOS Share Sheet, and macOS Share Sheet flows. |
| `agents/openai.yaml` | Agent-facing display metadata. |
| `.env.example` | Safe template for local Raindrop.io configuration. |
| `docs/` | Project documentation for maintainers, operators, users, and future agents. |

## Requirements

- macOS with Apple Notes available for note saving and verification.
- Python 3 for the helper scripts.
- `osascript` access to Apple Notes.
- Optional: `yt-dlp` on `PATH` for media caption extraction.
- Optional: `RAINDROP_ACCESS_TOKEN` or `RAINDROP_TOKEN` for Raindrop.io Inbox processing.

Apple Notes defaults are `--account iCloud` and `--folder clip-notes`.
Raindrop defaults are collections named `Inbox` and `Processed`.

For Raindrop setup:

```bash
cp .env.example .env
```

Then edit `.env` and set `RAINDROP_ACCESS_TOKEN`. The helper auto-loads `.env` by default, and real `.env` files are ignored by Git.

## Common Commands

Create or confirm the target Apple Notes folder:

```bash
python3 scripts/save_to_apple_notes.py ensure-folder
```

Save a prepared HTML note:

```bash
python3 scripts/save_to_apple_notes.py save --title "Example - Clip Notes" --html-file /absolute/path/note.html
```

Verify a note exists:

```bash
python3 scripts/save_to_apple_notes.py verify --title "Example - Clip Notes"
```

List notes in the target folder:

```bash
python3 scripts/save_to_apple_notes.py list
```

Restyle spacing in one note or all notes in the folder:

```bash
python3 scripts/save_to_apple_notes.py restyle --title "Example - Clip Notes"
python3 scripts/save_to_apple_notes.py restyle
```

Extract metadata and captions for a supported media URL:

```bash
python3 scripts/extract_media_captions.py "https://example.com/video"
```

List Raindrop Inbox bookmarks:

```bash
python3 scripts/raindrop_api.py inbox --limit 5
```

After a matching Apple Note is saved and verified, move a raindrop to Processed and tag it with the same canonical note tags:

```bash
python3 scripts/raindrop_api.py process --id 12345 --tags "#clip-notes #reference #ai"
```

Recommended recurring use: save links to Raindrop Inbox throughout the day, then have Codex process a small batch on demand or on a Codex recurring automation. Codex should create and verify each Apple Note before running the Raindrop `process` command.

Run the current lightweight syntax check:

```bash
python3 -m py_compile scripts/*.py
python3 -m unittest tests/test_raindrop_api.py
```

## Skill Workflow

1. Identify the source type and available content.
2. Collect source metadata such as title, author, date, URL, duration, or page count when available.
3. Classify the source with one lifecycle, one primary category, and 3-8 search tags.
4. Extract content using the least invasive reliable method.
5. Create a compact HTML note using the template in `SKILL.md`.
6. Save the note with `scripts/save_to_apple_notes.py save`.
7. Verify the saved note with `scripts/save_to_apple_notes.py verify`.
8. For Raindrop Inbox sources, process the raindrop only after verification succeeds.

For source-specific tactics, read `references/source-strategies.md`. For user-facing sharing patterns, read `references/share-workflows.md`.

## Documentation

- `docs/REQUIREMENTS.md` records user-visible behavior and constraints.
- `docs/ARCHITECTURE.md` explains components, data flow, and trust boundaries.
- `docs/RUNBOOK.md` covers setup, common operations, validation, and troubleshooting.
- `docs/SECURITY.md` covers privacy, authorization, local artifacts, and AppleScript risks.
- `docs/USER-GUIDE.md` shows how to use the skill from common source types.
- `docs/VISUALS.md` tracks diagrams, screenshot recommendations, and demo ideas.
- `docs/DOCS-STRATEGY.md` records documentation stewardship decisions and open questions.

<!-- TODO: Confirm the intended installation and release path for users outside this local Codex skill directory. -->
