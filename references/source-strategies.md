# Source Strategies

Use these tactics only as needed for edge cases.

## Video and Social Media

- Prefer captions/subtitles over downloading media. Run `scripts/extract_media_captions.py <url>` for YouTube, TikTok, and other `yt-dlp` supported URLs.
- If captions are automatic, state that in the note limitations.
- If no captions are available, try metadata and description first. Only download media or transcribe audio when tools and permissions are available.
- Preserve timestamps for longer videos, talks, interviews, tutorials, and sales/process content.
- For short videos, summarize the argument and add practical self-checks or actions when useful.

## Web Articles and Apple News

- Use the canonical URL, title, author, publisher, and publication date when available.
- If Apple News or a publisher page is gated, blocked, or only exposes a preview, ask the user to share the article text, Reader view, PDF, or screenshot set.
- Do not fill gaps from snippets or search results unless the note explicitly labels them as metadata only.
- For opinion pieces, separate the author's argument from facts and your synthesis.

## X/Twitter, Threads, LinkedIn, and Other Posts

- Capture the post URL, author handle, post date, and visible text.
- Include media alt text, quoted posts, or replies only when available from the shared source.
- For long threads, summarize the arc and keep only the most useful claims/examples.
- Avoid treating engagement metrics as stable facts unless the user asks for them.

## Raindrop.io Inbox and Unsorted

- Use `scripts/raindrop_api.py inbox` to list candidates from the configured Inbox collection and Raindrop's Unsorted system collection.
- Treat the raindrop title, link, excerpt, note, tags, domain, and creation date as source metadata.
- Use the linked source content when accessible. If only Raindrop metadata is available, say that in the note limitations.
- Save and verify the Apple Note before changing the raindrop.
- After verification, run `scripts/raindrop_api.py process --id <id> --tags "<apple note tags>"` to move the item to Processed and add matching tag names.
- Do not process the raindrop if Apple Notes saving or verification fails.

## Email

- Summarize only content the user shared or content from an authorized mailbox connector.
- Preserve subject, sender, recipients when relevant, dates, deadlines, owner names, asks, decisions, and attachments.
- Add an "Action Items" section by owner when the email implies tasks.
- Do not search the web for private email context unless the user explicitly asks.

## Documents and Files

- Use file-specific parsers when possible: PDF extraction/rendering for PDFs, document tooling for DOCX/Word, spreadsheet tooling for XLSX/CSV, and plain text tools for text/Markdown.
- For scanned PDFs or images, use OCR when available. If OCR quality is poor, say so.
- For long documents, include an executive summary, important sections, decisions, risks, and open questions.

## Failure Handling

When extraction is incomplete, still create a useful placeholder note:

- Source link or file name.
- Metadata that was available.
- What failed.
- What the user should share next, such as article text, a PDF export, screenshots, or an email body.
