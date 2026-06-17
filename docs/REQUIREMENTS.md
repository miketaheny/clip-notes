# Requirements

This document describes observed behavior from `SKILL.md`, `references/`, and helper scripts. It does not add product commitments that are not present in the repository.

## Functional Requirements

- The skill must create one Apple Note per source unless the user asks for a roundup.
- Notes must be saved to the `clip-notes` folder in Apple Notes by default.
- The default Apple Notes account must be `iCloud` unless overridden by helper script flags.
- Each note must include source metadata, lifecycle, category, tags, a short "why keep this" reason, summary sections, action items, and limitations when relevant.
- Tags must include `#clip-notes`, one lifecycle tag, one category tag, and useful topic tags.
- Lifecycle must be one of `short-lived`, `reference`, `how-to`, `decision`, `watchlist`, or `archive`.
- The skill must summarize only content the user provided, shared, or authorized through available tools.
- For gated or blocked articles, the skill must ask for article text, Reader output, PDF, screenshots, or another accessible copy instead of inventing missing details.
- For supported videos and social media URLs, the skill should prefer captions or subtitles over downloading media.
- When `yt-dlp` is available, `scripts/extract_media_captions.py` must collect metadata and produce a cleaned transcript when captions exist.
- `scripts/save_to_apple_notes.py` must support folder creation, save, verify, move, list, and restyle operations.
- `scripts/raindrop_api.py` must use the Raindrop.io REST API with `RAINDROP_ACCESS_TOKEN` or `RAINDROP_TOKEN`.
- `scripts/raindrop_api.py` must auto-load `.env` by default when the file exists, while allowing real environment variables to take precedence.
- The Raindrop helper must list bookmarks from the configured Inbox collection.
- After an Apple Note created from a Raindrop Inbox item is saved and verified, the helper must move that raindrop to the configured Processed collection and apply the same canonical tag names as the Apple Note.
- The Raindrop helper must leave a raindrop in Inbox if the Apple Note save or verification fails.
- After saving, the agent must verify the note title in the target Apple Notes folder.
- If saving to Apple Notes fails, the agent must leave a user-facing HTML or Markdown note artifact and explain the blocker.

## Non-Functional Requirements

- Summaries must be faithful to the source and separate source claims from synthesis.
- Notes must be compact enough for quick review.
- Apple Notes output must be readable, with metadata labels split across lines and spacing before major headings.
- The workflow must be privacy-preserving: local or shared content is preferred, and private email or account-gated documents must not trigger broader internet search unless explicitly requested.
- Direct quotes should be short and used only when memorable or decision-relevant.
- Medical, legal, financial, and safety content must include caution and avoid overstating certainty.
- Helper scripts should fail with actionable errors when local dependencies or Apple Notes access are unavailable.

## Current Constraints

- The repository has no automated unit test suite.
- Apple Notes behavior depends on macOS Notes, account names, folder names, and local automation permissions.
- Media extraction depends on a user-installed `yt-dlp`.
- Raindrop Inbox processing depends on a user-provided Raindrop.io API token and collection names or IDs.
- Real `.env` files must remain ignored by Git; `.env.example` is the committed template.
- `work/`, `outputs/`, `dist/`, and Python bytecode are ignored by Git, but local extraction artifacts can still contain source content.
- There is no visible release script or package manifest in the repository.

<!-- TODO: Confirm whether future releases should publish `dist/clip-notes.zip` or rely on direct skill-directory installation. -->
