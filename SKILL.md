---
name: clip-notes
description: Summarize shared sources into searchable Apple Notes. Use when the user provides or shares an article, Apple News link, X/Twitter post, YouTube/TikTok/social video, email, PDF, document, webpage, pasted text, or other saveable source and wants concise notes saved for quick consumption and later reference. Create an Apple Note in the clip-notes folder with source metadata, lifecycle classification, search tags, TL;DR, key points, action items, useful quotes, and limitations. Do not use for unrelated note editing or for summarizing a source the user has not provided or authorized access to.
---

# Clip Notes

Create concise, source-grounded notes from shareable content and save them to Apple Notes in the `clip-notes` folder.

## Default Contract

- Folder: `clip-notes` in the user's default Apple Notes account, usually `iCloud`.
- Output: one Apple Note per source unless the user asks for a roundup.
- Note format: HTML body saved through Notes AppleScript.
- Searchability: include a metadata block with lifecycle, category, tags, and a short "why keep this" reason.
- Verification: always confirm the target folder exists and read back the note title after saving.
- Privacy: use local/shared content first. Do not broaden to internet search for private email, documents, or account-gated content unless the user explicitly asks.
- Raindrop Inbox: when reviewing a Raindrop.io Inbox or Unsorted bookmark, move it to the processed collection and apply the same note tag names only after the Apple Note has been saved and verified.

## Workflow

1. Identify the source type: URL, video, social post, email, document, PDF, image, pasted text, or mixed bundle.
2. Collect source metadata: title, author/source, date, URL or file name, duration/page count when available, and retrieval date.
3. Classify the source for future search:
   - Set one lifecycle: `short-lived`, `reference`, `how-to`, `decision`, `watchlist`, or `archive`.
   - Set one primary category, such as `news`, `ai`, `business`, `marketing`, `operations`, `product`, `engineering`, `health`, `finance`, `legal`, `personal`, or a user-specific domain.
   - Add 3-8 lowercase hashtag tags in kebab case. Always include `#clip-notes`, one lifecycle tag such as `#short-lived`, and one category tag such as `#news`.
   - Add a revisit date only for `short-lived` or `watchlist` notes when a follow-up date is obvious or useful.
4. Extract content using the least invasive reliable method:
   - For YouTube, TikTok, X video, and other supported video URLs, prefer available caption/subtitle tracks. Use `scripts/extract_media_captions.py` when `yt-dlp` is available.
   - For webpages and Apple News links, use the page content when accessible. If the article is gated or blocked, ask the user to share the article text or Reader output instead of inventing details.
   - For email, summarize only the message/thread content the user provided or that an authorized connector exposes.
   - For local documents, use the appropriate document/PDF/spreadsheet parser or available Codex document skills.
   - For images or screenshots, use OCR only when available; otherwise ask for text.
5. Create a summary that is compact but useful. Do not include a raw transcript unless the user asks.
6. Save the note with `scripts/save_to_apple_notes.py save --title "<title>" --html-file <file>`.
7. Verify with `scripts/save_to_apple_notes.py verify --title "<title>"`.
8. If the source was reviewed from Raindrop.io Inbox, process it with `scripts/raindrop_api.py process` using the same lifecycle/category/topic tags from the Apple Note.

Read `references/source-strategies.md` when handling a source type with edge cases. Read `references/share-workflows.md` when the user asks how to use this from iOS, macOS, ChatGPT, or Codex.

## Raindrop Inbox Workflow

Use the direct Raindrop.io REST API for free-account compatible Inbox review. The helper auto-loads `.env` when present, then reads the API token from `RAINDROP_ACCESS_TOKEN` or `RAINDROP_TOKEN`. It defaults to a review queue made from the collection named `Inbox` plus Raindrop's Unsorted system collection, and moves completed items to `Processed`. Override with `RAINDROP_INBOX_COLLECTION`, `RAINDROP_PROCESSED_COLLECTION`, `--inbox`, or `--processed`. Disable Unsorted with `RAINDROP_INCLUDE_UNSORTED=false` or `--no-unsorted`.

List Inbox and Unsorted candidates:

```bash
python3 scripts/raindrop_api.py inbox --limit 5
```

Use each raindrop's link, title, excerpt, note, existing tags, and collection as source metadata. Extract the linked source content using the normal source strategies. If the source is gated or inaccessible, save a limitation note instead of fabricating details.

After the Apple Note is saved and verified, move the raindrop to the processed collection and apply the same canonical note tags:

```bash
python3 scripts/raindrop_api.py process --id 12345 --tags "#clip-notes #reference #category-tag #topic-tag"
```

If the processed collection does not exist and the user wants the helper to create it, pass `--create-processed`:

```bash
python3 scripts/raindrop_api.py process --id 12345 --tags "#clip-notes #reference #category-tag #topic-tag" --create-processed
```

By default, leading `#` is stripped when writing Raindrop tag names because Raindrop.io tags are plain labels. Use `--keep-hash-tags` only when the user explicitly wants the literal hash prefix in Raindrop.

Do not move or tag the raindrop if the Apple Note save or verification step fails. Leave it in Inbox and explain the blocker.

## Note Template

Use this structure by default. Omit irrelevant sections and add source-specific sections when useful, such as timestamps for videos or sender/action ownership for emails.

```html
<html>
<body>
<h1>Clean Source Title</h1>
<p><b>Source:</b> <a href="SOURCE_URL">SOURCE_URL</a><br>
<b>Creator/Author:</b> AUTHOR_OR_SOURCE<br>
<b>Date:</b> SOURCE_DATE<br>
<b>Notes created:</b> YYYY-MM-DD<br>
<b>Lifecycle:</b> short-lived | reference | how-to | decision | watchlist | archive<br>
<b>Category:</b> PRIMARY_CATEGORY<br>
<b>Tags:</b> #clip-notes #lifecycle-tag #category-tag #topic-tag<br>
<b>Revisit:</b> YYYY-MM-DD or none<br>
<b>Why keep this:</b> One sentence explaining how this note may be useful later.</p>

<p><br></p>
<h2>TL;DR</h2>
<ul>
<li>Three to five bullets capturing the gist.</li>
</ul>

<p><br></p>
<h2>Key Points</h2>
<ul>
<li>Important ideas, claims, lessons, or decisions.</li>
</ul>

<p><br></p>
<h2>Details Worth Keeping</h2>
<ul>
<li>Specific examples, frameworks, numbers, names, and caveats.</li>
</ul>

<p><br></p>
<h2>Action Items / Follow-up</h2>
<ul>
<li>Concrete next steps, questions to revisit, or things to try.</li>
</ul>

<p><br></p>
<h2>Limitations</h2>
<ul>
<li>Call out if captions were automatic, content was paywalled, only a snippet was available, or any source detail was uncertain.</li>
</ul>
</body>
</html>
```

## Summary Standards

- Be faithful to the source. Separate source claims from your own synthesis.
- Optimize for quick consumption. The user should not need to review the whole source to decide whether it matters.
- Keep Apple Notes readable: separate metadata labels with line breaks and insert a blank paragraph before each major section heading.
- Keep direct quotes short and only include them when they are memorable or decision-relevant.
- Preserve useful timestamps for videos longer than a few minutes.
- For emails and documents, keep names, deadlines, commitments, and requested actions explicit.
- For medical, legal, financial, or safety content, include a short caution and avoid overstating certainty.
- If content extraction fails, save a note that includes the source link, what could not be accessed, and the exact next input needed.

## Lifecycle Rules

- `short-lived`: News, launches, time-sensitive commentary, price/policy changes, event announcements, or anything likely to decay soon. Include the event date and a revisit date when useful.
- `reference`: Evergreen background, durable explanations, profiles, frameworks, research summaries, lists, or source material worth searching later.
- `how-to`: Tutorials, setup guides, recipes, workflows, troubleshooting, scripts, commands, or repeatable procedures.
- `decision`: Material that supports a choice, purchase, strategy, hiring/vendor decision, policy position, or tradeoff analysis.
- `watchlist`: Emerging topics, unresolved claims, rumors, developing stories, or things to check again later.
- `archive`: Interesting but low-priority material saved mainly for memory, provenance, or possible future use.

Prefer the most useful future retrieval label over the source format. For example, a YouTube tutorial is `how-to`, a video news segment is `short-lived`, and a long article explaining a durable concept is `reference`.

## Apple Notes Helpers

Use the bundled helper from the skill directory:

```bash
python3 scripts/save_to_apple_notes.py ensure-folder
python3 scripts/save_to_apple_notes.py save --title "Example - Clip Notes" --html-file /absolute/path/note.html
python3 scripts/save_to_apple_notes.py verify --title "Example - Clip Notes"
python3 scripts/save_to_apple_notes.py move --title "Existing note title"
```

Default options are `--account iCloud` and `--folder clip-notes`. Override them only when the user's Notes setup requires it.

## Raindrop.io Helper

Use the bundled helper from the skill directory:

```bash
python3 scripts/raindrop_api.py collections
python3 scripts/raindrop_api.py inbox --limit 5
python3 scripts/raindrop_api.py process --id 12345 --tags "#clip-notes #reference #ai"
```

The helper uses the official REST API endpoint `https://api.raindrop.io/rest/v1` with a bearer token. It does not use Raindrop.io MCP.

For local setup, copy `.env.example` to `.env` and fill `RAINDROP_ACCESS_TOKEN`. The real `.env` file is ignored by Git.

## Done Criteria

- The note exists in Apple Notes under `clip-notes`.
- The final response names the created note and mentions any extraction limitations.
- For Raindrop Inbox or Unsorted sources, the raindrop is moved to the processed collection and tagged with the same canonical tags as the Apple Note, or it is explicitly left in place because saving or verification failed.
- If saving to Apple Notes was impossible, a user-facing HTML or Markdown note file exists and the final response explains the blocker.
