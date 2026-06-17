# Share Workflows

## Codex on macOS

Use `$clip-notes` with a URL, file path, pasted email, or copied article text. Codex can run local extraction tools and save directly to Apple Notes with the bundled AppleScript helper.

Example:

```text
Use $clip-notes on this YouTube video and save it to Apple Notes: https://...
```

## ChatGPT

Skills are portable across OpenAI products that support Agent Skills, but they do not sync automatically between products. Install or upload the `clip-notes` skill separately in ChatGPT when the account/workspace supports Skills.

ChatGPT can summarize shared content into the same note format. Direct Apple Notes saving depends on available local tools or integrations. If ChatGPT cannot write to Apple Notes, have it produce the final note HTML/Markdown, then hand it to Codex on macOS or an Apple Shortcut that creates the note.

When ChatGPT Skills are not available, use a dedicated ChatGPT Project or custom GPT named `Clip Notes` with this instruction:

```text
When I share a URL, article text, video transcript, PDF, email, screenshot text, or other source, create a compact clip note for fast consumption and later retrieval. Do not make me review the whole source. Include source metadata, lifecycle, category, tags, why keep this, TL;DR, key points, details worth keeping, action items/follow-up, and limitations. Use lifecycle values: short-lived, reference, how-to, decision, watchlist, archive. Add 3-8 lowercase kebab-case hashtags, always including #clip-notes, one lifecycle tag, and one category tag. If you cannot access the source, say exactly what input you need next.
```

Use this Project or GPT as the fast intake surface on mobile and web. Send the finished note text to Codex on macOS when it needs to be saved directly into Apple Notes.

## iOS Share Sheet

Recommended path:

1. Share the URL, article text, selected email text, PDF, or document to the `Clip Notes` ChatGPT Project/GPT.
2. Ask for a clip note using the standard metadata, lifecycle, and tags.
3. If direct Notes saving is unavailable, have ChatGPT produce the formatted note text.
4. Save with an iOS Shortcut that accepts Share Sheet input and appends/creates a note in the `clip-notes` folder, or send the result to Codex on macOS for Apple Notes automation.

## macOS Share Sheet

Recommended path:

1. Share or copy the item URL/text/file path.
2. Open Codex and invoke `$clip-notes` with that shared input.
3. Let Codex extract, summarize, save, and verify in Apple Notes.

## Practical Shortcut Fields

For a future Apple Shortcut, pass these fields when available:

- `source_url`
- `source_title`
- `source_text`
- `source_file`
- `source_app`
- `shared_at`
- `lifecycle`
- `category`
- `tags`
- `revisit_date`

The skill can work with any subset, but source URL plus text/file content is the most reliable combination.
