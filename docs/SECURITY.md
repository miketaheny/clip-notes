# Security

Clip Notes processes user-provided or user-authorized sources and writes summaries to Apple Notes on the local Mac. The main security concerns are privacy, local automation permissions, and handling of private source artifacts.

## Trust Boundaries

- The user controls the source they share with the agent.
- The agent may use local files, shared text, accessible webpages, authorized connectors, and optional media caption extraction.
- `scripts/save_to_apple_notes.py` controls Apple Notes through local `osascript`.
- `scripts/extract_media_captions.py` delegates media metadata and caption extraction to `yt-dlp`.
- `scripts/raindrop_api.py` delegates bookmark listing and updates to the Raindrop.io REST API using a bearer token.
- Apple Notes stores the final note in the user's configured Notes account.

## Privacy Rules

- Prefer local or directly shared content.
- Do not search the web for private email, account-gated documents, or private sources unless the user explicitly asks.
- For gated or blocked sources, ask for article text, Reader output, PDF, screenshots, or another authorized copy.
- Label extraction limitations in the saved note.
- Treat `work/` outputs, transcripts, metadata files, and generated note drafts as private user data.
- Treat Raindrop.io API tokens as secrets. Do not commit them to this repository or include them in notes.

## Local Artifacts

The repository ignores common local output locations:

- `.env` and `.env.*`
- `work/`
- `outputs/`
- `dist/`
- Python bytecode and cache files

Ignored files can still contain sensitive source text or tokens. Do not attach, publish, or commit them without review.

## AppleScript and Notes Access

`scripts/save_to_apple_notes.py` sends AppleScript to Notes. This requires local macOS automation permissions and acts as the current macOS user.

Security expectations:

- Keep note titles and HTML bodies generated from trusted agent output or reviewed source material.
- Avoid embedding untrusted active content. Apple Notes stores note HTML, but the skill should use simple headings, paragraphs, links, and lists.
- Be careful with duplicate titles because helper operations target notes by title.
- Override `--account` and `--folder` only when the user confirms the intended destination.

## External Dependencies

`yt-dlp` is optional and runs only when media caption extraction is needed. It accesses the provided media URL and writes local metadata/caption files.

When using `yt-dlp`:

- Record whether captions were automatic or incomplete in the note limitations.
- Do not download media when captions, metadata, or user-provided transcripts are enough.
- Clean up local transcripts when they are no longer needed if they contain sensitive content.

## Raindrop.io API Access

`scripts/raindrop_api.py` auto-loads `.env` when present, reads `RAINDROP_ACCESS_TOKEN` or `RAINDROP_TOKEN`, lists bookmarks from the configured Inbox collection, and moves a processed bookmark to the configured Processed collection after Apple Notes verification.

Security expectations:

- Store tokens in `.env`, the shell environment, or a local secret manager.
- Commit only `.env.example`, never a real `.env`.
- Use collection names or IDs deliberately; a wrong `--processed` value can move bookmarks to the wrong collection.
- Use `--dry-run` before processing if the collection or tag mapping is uncertain.
- Do not process a Raindrop item until the Apple Note save and verify steps have succeeded.
- Leading `#` is stripped from Apple Note hashtags by default before writing Raindrop tag names.

## Reporting and Ownership

No security contact, owner, or disclosure policy is visible in this repository.

<!-- TODO: Add a security contact or reporting path if this skill is shared beyond the current private workspace. -->
