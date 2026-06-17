#!/usr/bin/env python3
"""Batch Raindrop Inbox/Unsorted items into verified Apple Notes."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import pathlib
import re
import sys
import time
from typing import Any, Callable, TypeVar


SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import raindrop_api
import save_to_apple_notes


MAX_RAINDROP_PAGE_SIZE = 50
DEFAULT_OUTPUT_DIR = pathlib.Path("work") / "raindrop-clip-notes"
AI_TERMS = {
    "ai",
    "agent",
    "agents",
    "anthropic",
    "chatgpt",
    "claude",
    "codex",
    "cursor",
    "gpt",
    "llm",
    "openai",
    "prompt",
    "prompts",
}
HOW_TO_TERMS = {
    "blueprint",
    "build",
    "checklist",
    "example",
    "framework",
    "guide",
    "how to",
    "playbook",
    "setup",
    "step-by-step",
    "template",
    "tips",
    "tutorial",
    "workflow",
}
CATEGORY_TERMS = {
    "ai": AI_TERMS,
    "business": {"business", "company", "customer", "growth", "market", "sales", "startup"},
    "engineering": {
        "api",
        "code",
        "developer",
        "devtool",
        "github",
        "javascript",
        "nextjs",
        "postgres",
        "python",
        "react",
        "security",
        "supabase",
        "typescript",
    },
    "finance": {"bank", "budget", "crypto", "finance", "invest", "market", "money", "stock"},
    "health": {"fitness", "health", "medical", "nutrition", "sleep", "workout"},
    "legal": {"contract", "law", "legal", "policy", "regulation"},
    "marketing": {"content", "google search", "marketing", "seo", "social", "traffic"},
    "news": {"breaking", "ceasefire", "election", "iran", "news", "president", "trump", "war"},
    "operations": {"asana", "calendar", "meeting", "ops", "operations", "process", "project"},
    "personal": {"bible", "family", "home", "personal", "prayer", "recipe", "yard"},
    "product": {"feature", "launch", "product", "roadmap", "saas", "ux"},
}
DOMAIN_TAGS = {
    "apple.news": "apple-news",
    "github.com": "github",
    "tiktok.com": "tiktok",
    "twitter.com": "x",
    "x.com": "x",
    "youtu.be": "youtube",
    "youtube.com": "youtube",
}
WHY_KEEP = {
    "archive": "Saved for provenance, memory, or possible future retrieval.",
    "decision": "May support a future choice, comparison, or tradeoff review.",
    "how-to": "Potentially repeatable workflow or tactic worth searching later.",
    "reference": "Likely useful background or source material for later search.",
    "short-lived": "Time-sensitive item saved so it can be reviewed or discarded after it changes.",
    "watchlist": "Developing topic worth checking again before relying on it.",
}


T = TypeVar("T")


def text_blob(item: dict[str, Any]) -> str:
    values = [
        str(item.get("title") or ""),
        str(item.get("domain") or ""),
        str(item.get("excerpt") or ""),
        str(item.get("note") or ""),
        str(item.get("link") or ""),
    ]
    return " ".join(values).casefold()


def clean_title(value: str | None) -> str:
    title = html.unescape(value or "").strip()
    title = re.sub(r"\s+", " ", title)
    return title or "Untitled Raindrop"


def short_note_title(item: dict[str, Any], max_base_length: int = 72) -> str:
    rd_id = int(item["id"])
    base = clean_title(str(item.get("title") or ""))
    base = re.sub(rf"\s*\[RD\s+{rd_id}\]\s*-\s*Clip Notes\s*$", "", base)
    if len(base) > max_base_length:
        base = base[: max_base_length - 3].rstrip() + "..."
    return f"RD {rd_id} - {base} - Clip Notes"


def domain_tag(domain: str) -> str | None:
    domain = domain.casefold()
    for suffix, tag in DOMAIN_TAGS.items():
        if domain == suffix or domain.endswith(f".{suffix}"):
            return tag
    return None


def category_for(item: dict[str, Any]) -> str:
    blob = text_blob(item)
    domain = str(item.get("domain") or "").casefold()
    if "apple.news" in domain:
        return "news"
    best_category = "personal"
    best_score = 0
    for category, terms in CATEGORY_TERMS.items():
        score = sum(1 for term in terms if term in blob)
        if score > best_score:
            best_category = category
            best_score = score
    if best_score == 0:
        if domain.endswith(("github.com", "supabase.com", "vercel.com")):
            return "engineering"
        if domain.endswith(("x.com", "twitter.com", "tiktok.com", "youtube.com", "youtu.be")):
            return "personal"
    return best_category


def lifecycle_for(item: dict[str, Any], category: str) -> str:
    blob = text_blob(item)
    if category == "news":
        return "short-lived"
    if any(term in blob for term in HOW_TO_TERMS):
        return "how-to"
    if any(term in blob for term in {"compare", "comparison", "decision", "tradeoff", "vs", "versus"}):
        return "decision"
    if any(term in blob for term in {"developing", "rumor", "watch", "watchlist"}):
        return "watchlist"
    if str(item.get("domain") or "").casefold().endswith(("tiktok.com", "youtu.be", "youtube.com")):
        return "archive"
    return "reference"


def topic_tags(item: dict[str, Any], category: str) -> list[str]:
    blob = text_blob(item)
    tags: list[str] = []
    domain = str(item.get("domain") or "")
    tag = domain_tag(domain)
    if tag:
        tags.append(tag)

    keyword_tags = [
        ("apple-news", "apple.news"),
        ("agents", "agent"),
        ("claude", "claude"),
        ("codex", "codex"),
        ("github", "github"),
        ("google-search", "google search"),
        ("nextjs", "nextjs"),
        ("prompting", "prompt"),
        ("python", "python"),
        ("react", "react"),
        ("seo", "seo"),
        ("supabase", "supabase"),
        ("workflow", "workflow"),
    ]
    for tag_name, needle in keyword_tags:
        if needle in blob:
            tags.append(tag_name)

    if category == "engineering" and "developer-tools" not in tags:
        tags.append("developer-tools")
    return raindrop_api.dedupe_tags(tags)


def classify_raindrop(item: dict[str, Any], today: dt.date | None = None) -> dict[str, Any]:
    today = today or dt.date.today()
    category = category_for(item)
    lifecycle = lifecycle_for(item, category)
    tags = raindrop_api.dedupe_tags(
        [f"#{tag}" for tag in ["clip-notes", lifecycle, category, *topic_tags(item, category)]]
    )
    tags = tags[:8]
    revisit = today + dt.timedelta(days=7) if lifecycle in {"short-lived", "watchlist"} else None
    return {
        "lifecycle": lifecycle,
        "category": category,
        "tags": tags,
        "tags_text": " ".join(tags),
        "revisit": revisit.isoformat() if revisit else "none",
        "why_keep": WHY_KEEP[lifecycle],
    }


def html_list(items: list[str]) -> str:
    return "\n".join(f"<li>{html.escape(item, quote=True)}</li>" for item in items)


def note_html(item: dict[str, Any], classification: dict[str, Any], title: str, today: dt.date) -> str:
    link = str(item.get("link") or "")
    source_title = clean_title(str(item.get("title") or ""))
    excerpt = str(item.get("excerpt") or "").strip()
    note = str(item.get("note") or "").strip()
    domain = str(item.get("domain") or "unknown")
    source_collection = item.get("collection_id")

    summary = excerpt or note or "No Raindrop excerpt or note was available for this item."
    details = [
        f"Raindrop ID: {item.get('id')}",
        f"Domain: {domain}",
        f"Raindrop collection ID: {source_collection}",
    ]
    if excerpt:
        details.append(f"Excerpt: {excerpt}")
    if note:
        details.append(f"Raindrop note: {note}")

    return f"""<html>
<body>
<h1>{html.escape(title, quote=True)}</h1>
<p><b>Source:</b> <a href="{html.escape(link, quote=True)}">{html.escape(link, quote=True)}</a><br>
<b>Creator/Author:</b> {html.escape(domain, quote=True)}<br>
<b>Date:</b> saved in Raindrop {html.escape(str(item.get("created") or "unknown"), quote=True)}<br>
<b>Notes created:</b> {today.isoformat()}<br>
<b>Lifecycle:</b> {classification["lifecycle"]}<br>
<b>Category:</b> {classification["category"]}<br>
<b>Tags:</b> {html.escape(classification["tags_text"], quote=True)}<br>
<b>Revisit:</b> {classification["revisit"]}<br>
<b>Why keep this:</b> {html.escape(classification["why_keep"], quote=True)}</p>

<p><br></p>
<h2>TL;DR</h2>
<ul>
{html_list([
    f"Raindrop metadata describes this as: {summary}",
    "This note was generated from the Raindrop review queue as a searchable quick-reference note.",
    "Open the source before treating claims, instructions, or quoted material as complete.",
])}
</ul>

<p><br></p>
<h2>Key Points</h2>
<ul>
{html_list([
    source_title,
    f"Primary category: {classification['category']}; lifecycle: {classification['lifecycle']}.",
    "Saved from Raindrop Inbox or Unsorted for later retrieval.",
])}
</ul>

<p><br></p>
<h2>Details Worth Keeping</h2>
<ul>
{html_list(details)}
</ul>

<p><br></p>
<h2>Action Items / Follow-up</h2>
<ul>
{html_list([
    "Review the original source if this item becomes actionable, decision-relevant, or worth turning into a deeper note.",
    f"Search Apple Notes with {classification['tags_text']} to find this item later.",
])}
</ul>

<p><br></p>
<h2>Limitations</h2>
<ul>
{html_list([
    "Batch run used Raindrop title, excerpt, note, URL, and domain metadata.",
    "No full article, thread, transcript, or account-gated content was extracted unless it appeared in the Raindrop metadata above.",
])}
</ul>
</body>
</html>
"""


def parse_found_note(result: str) -> str | None:
    if result.startswith("FOUND: "):
        return result[len("FOUND: ") :]
    return None


def is_rate_limit(error: Exception) -> bool:
    return "HTTP 429" in str(error)


def retry_call(
    label: str,
    func: Callable[[], T],
    *,
    max_retries: int,
    retry_sleep: float,
) -> T:
    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except raindrop_api.RaindropApiError as error:
            if not is_rate_limit(error) or attempt >= max_retries:
                raise
            delay = retry_sleep * attempt
            print(f"{label}: rate limited, sleeping {delay:g}s before retry {attempt + 1}", flush=True)
            time.sleep(delay)
    raise RuntimeError(f"unreachable retry state for {label}")


def fetch_review_batch(
    client: raindrop_api.RaindropClient,
    collections: list[dict[str, Any]],
    args: argparse.Namespace,
    *,
    skip_ids: set[int],
) -> list[dict[str, Any]]:
    raw_items: list[list[dict[str, Any]]] = []
    for collection in collections:
        collection_id = int(collection["_id"])
        page = 0
        while True:
            page_items = retry_call(
                f"fetch collection {collection_id} page {page}",
                lambda collection_id=collection_id, page=page: client.raindrops(
                    collection_id,
                    page=page,
                    perpage=args.batch_size,
                    sort=args.sort,
                    search=args.search,
                    nested=args.nested,
                ),
                max_retries=args.max_retries,
                retry_sleep=args.retry_sleep,
            )
            if not page_items:
                break
            raw_items.append(page_items)
            combined = raindrop_api.combine_raindrops(
                raw_items,
                limit=sum(len(batch) for batch in raw_items),
                sort=args.sort,
            )
            available = [
                item
                for item in combined
                if item.get("_id") is not None and int(item["_id"]) not in skip_ids
            ]
            if len(available) >= args.batch_size or len(page_items) < args.batch_size:
                break
            page += 1

    combined = raindrop_api.combine_raindrops(
        raw_items,
        limit=sum(len(batch) for batch in raw_items),
        sort=args.sort,
    )
    compact_items = [raindrop_api.compact_raindrop(item) for item in combined]
    return [
        item
        for item in compact_items
        if item.get("id") is not None and int(item["id"]) not in skip_ids
    ][: args.batch_size]


def save_and_verify_note(
    item: dict[str, Any],
    classification: dict[str, Any],
    args: argparse.Namespace,
    output_dir: pathlib.Path,
    today: dt.date,
) -> tuple[str, pathlib.Path]:
    rd_id = int(item["id"])
    found = parse_found_note(
        save_to_apple_notes.find_note_by_raindrop_id(args.account, args.folder, rd_id)
    )
    if found:
        return found, output_dir / f"{rd_id}.html"

    title = short_note_title(item)
    html_path = output_dir / f"{rd_id}.html"
    html_path.write_text(note_html(item, classification, title, today), encoding="utf-8")
    save_to_apple_notes.save_note(args.account, args.folder, title, html_path, show=False)
    found = parse_found_note(
        save_to_apple_notes.find_note_by_raindrop_id(args.account, args.folder, rd_id)
    )
    if not found:
        raise RuntimeError(f"Apple Note save was not verifiable for Raindrop {rd_id}")
    return found, html_path


def process_verified_raindrop(
    client: raindrop_api.RaindropClient,
    item: dict[str, Any],
    classification: dict[str, Any],
    source_ids: set[int],
    processed_collection: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    rd_id = int(item["id"])
    current = retry_call(
        f"fetch raindrop {rd_id}",
        lambda: client.raindrop(rd_id),
        max_retries=args.max_retries,
        retry_sleep=args.retry_sleep,
    )
    original = raindrop_api.compact_raindrop(current)
    current_collection_id = original.get("collection_id")
    if current_collection_id not in source_ids:
        return {
            "status": "already_moved_or_not_in_review",
            "collection_id": current_collection_id,
        }

    added_tags = raindrop_api.parse_tags([classification["tags_text"]], keep_hash=args.keep_hash_tags)
    existing_tags = [str(tag) for tag in original.get("tags") or []]
    final_tags = raindrop_api.merge_tags(existing_tags, added_tags)
    update_body = {"tags": final_tags, "collection": {"$id": int(processed_collection["_id"])}}

    if args.dry_run:
        return {
            "status": "dry_run",
            "collection_id": current_collection_id,
            "update_body": update_body,
        }

    retry_call(
        f"update raindrop {rd_id}",
        lambda: client.update_raindrop(rd_id, update_body),
        max_retries=args.max_retries,
        retry_sleep=args.retry_sleep,
    )
    verified = retry_call(
        f"verify raindrop {rd_id}",
        lambda: client.raindrop(rd_id),
        max_retries=args.max_retries,
        retry_sleep=args.retry_sleep,
    )
    compact_verified = raindrop_api.compact_raindrop(verified)
    return {
        "status": "processed",
        "collection_id": compact_verified.get("collection_id"),
        "tags": compact_verified.get("tags"),
    }


def process_item(
    client: raindrop_api.RaindropClient,
    item: dict[str, Any],
    source_ids: set[int],
    processed_collection: dict[str, Any],
    args: argparse.Namespace,
    output_dir: pathlib.Path,
    today: dt.date,
) -> dict[str, Any]:
    rd_id = int(item["id"])
    row: dict[str, Any] = {
        "id": rd_id,
        "title": item.get("title"),
        "link": item.get("link"),
        "status": None,
        "note_title": None,
        "html_file": None,
        "tags": None,
        "error": None,
    }
    classification = classify_raindrop(item, today=today)
    row["tags"] = classification["tags_text"]

    try:
        if args.dry_run:
            row["note_title"] = short_note_title(item)
            row["status"] = "dry_run"
            row["process"] = process_verified_raindrop(
                client,
                item,
                classification,
                source_ids,
                processed_collection,
                args,
            )
            return row

        note_title, html_path = save_and_verify_note(item, classification, args, output_dir, today)
        row["note_title"] = note_title
        row["html_file"] = str(html_path)
        row["process"] = process_verified_raindrop(
            client,
            item,
            classification,
            source_ids,
            processed_collection,
            args,
        )
        row["status"] = row["process"]["status"]
    except SystemExit as error:
        row["status"] = "failed"
        row["error"] = f"Apple Notes helper exited with status {error.code}"
    except Exception as error:
        row["status"] = "failed"
        row["error"] = str(error)
    return row


def write_summary(output_dir: pathlib.Path, payload: dict[str, Any]) -> pathlib.Path:
    path = output_dir / "summary.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def handle_run(args: argparse.Namespace) -> dict[str, Any]:
    if args.batch_size < 1 or args.batch_size > MAX_RAINDROP_PAGE_SIZE:
        raise raindrop_api.RaindropApiError(
            f"--batch-size must be between 1 and {MAX_RAINDROP_PAGE_SIZE}."
        )
    if args.max_items is not None and args.max_items < 1:
        raise raindrop_api.RaindropApiError("--max-items must be at least 1.")
    if args.max_retries < 1:
        raise raindrop_api.RaindropApiError("--max-retries must be at least 1.")
    if args.sleep < 0 or args.retry_sleep < 0:
        raise raindrop_api.RaindropApiError("--sleep and --retry-sleep must be non-negative.")

    today = dt.date.today()
    started = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = pathlib.Path(args.output_dir).expanduser() / started
    output_dir.mkdir(parents=True, exist_ok=True)

    save_to_apple_notes.ensure_folder(args.account, args.folder)
    client = raindrop_api.build_client(args)
    source_collections, warnings = raindrop_api.review_collections(client, args)
    source_ids = {int(collection["_id"]) for collection in source_collections}
    processed_name = args.processed or os.environ.get(
        "RAINDROP_PROCESSED_COLLECTION",
        raindrop_api.DEFAULT_PROCESSED,
    )
    processed_collection = client.resolve_collection(
        processed_name,
        create_if_missing=args.create_processed,
    )

    skipped_ids: set[int] = set()
    results: list[dict[str, Any]] = []
    max_items = None if args.all else args.max_items or args.batch_size

    payload: dict[str, Any] = {
        "started": started,
        "dry_run": args.dry_run,
        "source_collections": [raindrop_api.collection_summary(collection) for collection in source_collections],
        "processed_collection": raindrop_api.collection_summary(processed_collection),
        "warnings": warnings,
        "items": results,
        "summary": {},
    }

    while True:
        remaining = None if max_items is None else max_items - len(results)
        if remaining is not None and remaining <= 0:
            break

        batch = fetch_review_batch(client, source_collections, args, skip_ids=skipped_ids)
        if not batch:
            break
        if remaining is not None:
            batch = batch[:remaining]

        for item in batch:
            rd_id = int(item["id"])
            print(f"Processing RD {rd_id}: {clean_title(str(item.get('title') or ''))}", flush=True)
            row = process_item(
                client,
                item,
                source_ids,
                processed_collection,
                args,
                output_dir,
                today,
            )
            results.append(row)
            skipped_ids.add(rd_id)
            print(f"  {row['status']}: {row.get('note_title') or row.get('error')}", flush=True)
            write_summary(output_dir, payload)

            if args.sleep and row["status"] == "processed":
                time.sleep(args.sleep)

        if not args.all:
            break

    counts: dict[str, int] = {}
    for row in results:
        counts[str(row["status"])] = counts.get(str(row["status"]), 0) + 1
    payload["finished"] = dt.datetime.now().isoformat()
    payload["summary"] = counts
    payload["summary_file"] = str(output_dir / "summary.json")
    write_summary(output_dir, payload)
    return payload


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create Apple Notes for Raindrop Inbox/Unsorted items, then move verified items."
    )
    parser.add_argument("--token", help="Raindrop API token. Defaults to RAINDROP_ACCESS_TOKEN or RAINDROP_TOKEN.")
    parser.add_argument("--base-url", default=raindrop_api.DEFAULT_BASE_URL)
    parser.add_argument("--env-file", default=".env", help="Optional dotenv file to load before reading env vars.")
    parser.add_argument("--no-env-file", action="store_true", help="Disable automatic .env loading.")
    parser.add_argument("--env-override", action="store_true", help="Let dotenv values override existing env vars.")
    parser.add_argument("--account", default=save_to_apple_notes.DEFAULT_ACCOUNT)
    parser.add_argument("--folder", default=save_to_apple_notes.DEFAULT_FOLDER)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))

    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="Run one batch or all available review items.")
    run_parser.add_argument("--all", action="store_true", help="Continue until Inbox and Unsorted are empty.")
    run_parser.add_argument("--max-items", type=int, help="Maximum number of items to process this run.")
    run_parser.add_argument("--batch-size", type=int, default=MAX_RAINDROP_PAGE_SIZE, help="Fetch size, max 50.")
    run_parser.add_argument("--sleep", type=float, default=10.0, help="Seconds to sleep after each moved item.")
    run_parser.add_argument("--retry-sleep", type=float, default=30.0, help="Base seconds to sleep after HTTP 429.")
    run_parser.add_argument("--max-retries", type=int, default=4, help="Maximum API attempts per operation.")
    run_parser.add_argument("--inbox", help=f"Inbox collection name or ID. Default: {raindrop_api.DEFAULT_INBOX}.")
    run_parser.add_argument("--processed", help=f"Processed collection name or ID. Default: {raindrop_api.DEFAULT_PROCESSED}.")
    run_parser.add_argument("--create-processed", action="store_true")
    run_parser.add_argument("--no-unsorted", action="store_true")
    run_parser.add_argument("--sort", default="-created")
    run_parser.add_argument("--search")
    run_parser.add_argument("--nested", action="store_true")
    run_parser.add_argument("--keep-hash-tags", action="store_true")
    run_parser.add_argument("--dry-run", action="store_true", help="Do not save notes or update Raindrop.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not args.no_env_file:
        raindrop_api.load_env_file(args.env_file, override=args.env_override)
    try:
        if args.command == "run":
            print_json(handle_run(args))
    except (raindrop_api.RaindropApiError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
