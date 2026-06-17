# User Guide

Clip Notes creates a searchable Apple Note from a source you want to keep. Use it when you want the useful parts of a link, article, video, email, document, or pasted text saved in the `clip-notes` folder.

## Start a Clip Note

In Codex on macOS, invoke the skill with a source:

```text
Use $clip-notes on this article and save it to Apple Notes: https://example.com/article
```

You can also provide pasted text:

```text
Use $clip-notes on the pasted text below and save it as a reference note.
```

Or provide a local file path:

```text
Use $clip-notes on /absolute/path/to/report.pdf and save the key points.
```

Or ask to review Raindrop.io Inbox and Unsorted:

```text
Use $clip-notes to review my Raindrop Inbox and Unsorted. Save each processed source to Apple Notes, then move it to Processed with the same tags.
```

## What Gets Saved

Each note usually includes:

- Source link or file name.
- Author, source, date, and retrieval date when available.
- Lifecycle, category, tags, revisit date when useful, and "why keep this."
- TL;DR.
- Key points.
- Details worth keeping.
- Action items or follow-up.
- Limitations.

## Lifecycle Labels

| Lifecycle | Use For |
| --- | --- |
| `short-lived` | News, launches, policy changes, events, or time-sensitive commentary. |
| `reference` | Durable background, explainers, profiles, research, and evergreen material. |
| `how-to` | Tutorials, workflows, troubleshooting, recipes, scripts, or repeatable steps. |
| `decision` | Material that supports a purchase, strategy, vendor, policy, or tradeoff decision. |
| `watchlist` | Emerging or unresolved topics that should be checked again later. |
| `archive` | Low-priority material saved mainly for memory or provenance. |

## Tags

Every note should include:

- `#clip-notes`
- one lifecycle tag, such as `#reference`
- one category tag, such as `#engineering`
- useful topic tags, such as `#apple-notes`, `#ai`, or `#vendor-review`

Tags are lowercase and use kebab case.

## Source-Specific Guidance

For accessible webpages and articles, the skill uses available page content and source metadata.

For Apple News or publisher pages that are gated, share the full article text, Reader output, PDF, or screenshots. The skill should not infer the full article from a preview.

For YouTube, TikTok, X video, or other supported media URLs, the skill prefers captions or subtitles. If captions are automatic or incomplete, the note should say so.

For emails, summarize only the email content you provide or content exposed by an authorized mailbox connector. Action items should keep owner names, deadlines, and commitments explicit.

For PDFs and documents, provide a local file path or the document content. Long documents should get an executive summary, key sections, decisions, risks, and open questions.

For Raindrop.io review, the skill lists bookmarks from the configured Inbox collection and Unsorted by default, uses the saved link as the source, creates and verifies the Apple Note, then moves the bookmark to the Processed collection with matching tag names. If the note cannot be saved or verified, the bookmark stays where it is.

For backlog cleanup, the batch runner can create metadata-based notes directly from Raindrop title, excerpt, note, URL, domain, and saved date metadata:

```bash
python3 scripts/raindrop_clip_notes_batch.py run --all --sleep 10
```

Use the batch runner when the goal is to make saved links searchable and clear the queue. Ask Codex for a smaller manual review when you need full article text, thread extraction, captions, or deeper synthesis.

## Regular Inbox Review

The intended workflow is simple:

1. Save links, videos, documents, or articles to Raindrop Inbox or leave them in Unsorted whenever you find them.
2. Run the batch helper for metadata-based cleanup, or ask Codex to review a small batch for deeper extraction.
3. Codex or the helper creates Apple Notes for the useful content.
4. Successfully saved and verified items move to Processed with matching tags.
5. Blocked items stay in their current review collection with an explanation.

Use this request when you want Codex to deeply review a few items:

```text
Use $clip-notes to review up to 5 items from my Raindrop Inbox and Unsorted. Save each good summary to Apple Notes, verify it, then move the Raindrop item to Processed with the same tags.
```

Use this command when you want the queue cleaned up with metadata-based notes:

```bash
python3 scripts/raindrop_clip_notes_batch.py run --all --sleep 10
```

## Good Requests

```text
Use $clip-notes on this YouTube tutorial. Keep timestamps and save it as a how-to note.
```

```text
Use $clip-notes on this email thread. Focus on deadlines, owners, and follow-up.
```

```text
Use $clip-notes on this article text. Classify it as a decision note and include objections or risks.
```

## If Saving Fails

If Apple Notes cannot be reached, the agent should still create a readable HTML or Markdown note artifact and explain what blocked saving or verification.

Common blockers are missing Notes automation permission, a different account or folder name, unavailable source content, or missing `yt-dlp` for media captions.

For Raindrop processing, another common blocker is a missing `RAINDROP_ACCESS_TOKEN` or a collection named differently from `Inbox` / `Processed`.

<!-- TODO: Add screenshots after a real saved-note flow is captured on the target Mac. -->
