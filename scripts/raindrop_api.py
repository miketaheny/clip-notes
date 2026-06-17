#!/usr/bin/env python3
"""Review and process Raindrop.io Inbox items through the REST API."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


DEFAULT_BASE_URL = "https://api.raindrop.io/rest/v1"
DEFAULT_INBOX = "Inbox"
DEFAULT_PROCESSED = "Processed"
UNSORTED_COLLECTION_ID = -1
TOKEN_ENV_NAMES = ("RAINDROP_ACCESS_TOKEN", "RAINDROP_TOKEN")
ENV_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SYSTEM_COLLECTION_TITLES = {
    0: "All",
    UNSORTED_COLLECTION_ID: "Unsorted",
    -99: "Trash",
}


class RaindropApiError(Exception):
    """Raised when Raindrop.io returns an error or required config is missing."""


def env_token() -> str | None:
    for name in TOKEN_ENV_NAMES:
        value = os.environ.get(name)
        if value:
            return value
    return None


def normalize_token(value: str | None) -> str | None:
    if value is None:
        return None
    token = value.strip()
    if token.casefold().startswith("bearer "):
        token = token[7:].strip()
    return token or None


def parse_env_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if stripped.startswith("export "):
        stripped = stripped[len("export ") :].lstrip()
    if "=" not in stripped:
        return None

    key, value = stripped.split("=", 1)
    key = key.strip()
    if not ENV_KEY_RE.match(key):
        return None

    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return key, value


def load_env_file(env_file: str | None, *, override: bool = False) -> list[str]:
    if not env_file:
        return []

    path = pathlib.Path(env_file).expanduser()
    if not path.is_absolute():
        path = pathlib.Path.cwd() / path
    if not path.is_file():
        return []

    loaded: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parsed = parse_env_line(line)
        if not parsed:
            continue
        key, value = parsed
        if override or key not in os.environ:
            os.environ[key] = value
            loaded.append(key)
    return loaded


def is_int_string(value: str) -> bool:
    try:
        int(value)
    except ValueError:
        return False
    return True


def env_flag(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().casefold() not in {"0", "false", "no", "off"}


def should_include_unsorted(args: argparse.Namespace) -> bool:
    if args.no_unsorted:
        return False
    return env_flag("RAINDROP_INCLUDE_UNSORTED", True)


def system_collection(collection_id: int) -> dict[str, Any]:
    return {
        "_id": collection_id,
        "title": SYSTEM_COLLECTION_TITLES.get(collection_id, str(collection_id)),
    }


def normalize_tag(tag: str, keep_hash: bool = False) -> str:
    cleaned = tag.strip().strip(",")
    if not keep_hash and cleaned.startswith("#"):
        cleaned = cleaned[1:]
    return cleaned.strip()


def parse_tags(tags: list[str], keep_hash: bool = False) -> list[str]:
    parsed: list[str] = []
    for value in tags:
        for piece in value.replace(",", " ").split():
            tag = normalize_tag(piece, keep_hash=keep_hash)
            if tag:
                parsed.append(tag)
    return dedupe_tags(parsed)


def dedupe_tags(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for tag in tags:
        key = tag.casefold()
        if key not in seen:
            seen.add(key)
            result.append(tag)
    return result


def merge_tags(existing: list[str], added: list[str]) -> list[str]:
    return dedupe_tags([*existing, *added])


def compact_raindrop(item: dict[str, Any]) -> dict[str, Any]:
    collection = item.get("collection") or {}
    return {
        "id": item.get("_id"),
        "title": item.get("title"),
        "link": item.get("link"),
        "domain": item.get("domain"),
        "excerpt": item.get("excerpt"),
        "note": item.get("note"),
        "tags": item.get("tags") or [],
        "created": item.get("created"),
        "collection_id": collection.get("$id"),
    }


def collection_summary(collection: dict[str, Any]) -> dict[str, Any]:
    return {"id": collection.get("_id"), "title": collection.get("title")}


def combine_raindrops(
    batches: list[list[dict[str, Any]]],
    *,
    limit: int,
    sort: str,
) -> list[dict[str, Any]]:
    seen: set[Any] = set()
    items: list[dict[str, Any]] = []
    for batch in batches:
        for item in batch:
            item_id = item.get("_id")
            if item_id in seen:
                continue
            seen.add(item_id)
            items.append(item)

    if sort in {"-created", "created"}:
        items.sort(key=lambda item: str(item.get("created") or ""), reverse=sort == "-created")
    return items[:limit]


class RaindropClient:
    def __init__(self, token: str, base_url: str = DEFAULT_BASE_URL) -> None:
        self.token = token
        self.base_url = base_url.rstrip("/")

    def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        if query:
            cleaned_query = {
                key: value
                for key, value in query.items()
                if value is not None and value != ""
            }
            if cleaned_query:
                url = f"{url}?{urllib.parse.urlencode(cleaned_query, doseq=True)}"

        data = None
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                response_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            error_body = error.read().decode("utf-8", errors="replace")
            raise RaindropApiError(
                f"Raindrop API {method} {url} failed with HTTP {error.code}: {error_body}"
            ) from error
        except urllib.error.URLError as error:
            raise RaindropApiError(f"Raindrop API request failed: {error}") from error

        if not response_body:
            return {}
        try:
            payload = json.loads(response_body)
        except json.JSONDecodeError as error:
            raise RaindropApiError(f"Raindrop API returned non-JSON response: {response_body}") from error

        if payload.get("result") is False:
            raise RaindropApiError(f"Raindrop API returned result=false: {payload}")
        return payload

    def collections(self) -> list[dict[str, Any]]:
        root = self.request("GET", "collections").get("items") or []
        child = self.request("GET", "collections/childrens").get("items") or []
        return [*root, *child]

    def create_collection(self, title: str) -> dict[str, Any]:
        payload = self.request("POST", "collection", body={"title": title})
        item = payload.get("item")
        if not isinstance(item, dict):
            raise RaindropApiError(f"Collection create response did not include item: {payload}")
        return item

    def resolve_collection(
        self,
        identifier: str,
        *,
        create_if_missing: bool = False,
    ) -> dict[str, Any]:
        if is_int_string(identifier):
            return system_collection(int(identifier))

        collections = self.collections()
        matches = [
            collection
            for collection in collections
            if str(collection.get("title", "")).casefold() == identifier.casefold()
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            ids = ", ".join(str(collection.get("_id")) for collection in matches)
            raise RaindropApiError(f"Multiple collections named {identifier!r}: {ids}")
        if create_if_missing:
            return self.create_collection(identifier)
        raise RaindropApiError(
            f"Collection {identifier!r} not found. Use a collection ID, create it in Raindrop.io, "
            "or pass --create-processed for the Processed collection."
        )

    def raindrops(
        self,
        collection_id: int,
        *,
        page: int,
        perpage: int,
        sort: str,
        search: str | None,
        nested: bool,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {
            "page": page,
            "perpage": perpage,
            "sort": sort,
            "search": search,
        }
        if nested:
            query["nested"] = "true"
        return self.request("GET", f"raindrops/{collection_id}", query=query).get("items") or []

    def raindrop(self, raindrop_id: int) -> dict[str, Any]:
        payload = self.request("GET", f"raindrop/{raindrop_id}")
        item = payload.get("item")
        if not isinstance(item, dict):
            raise RaindropApiError(f"Raindrop response did not include item: {payload}")
        return item

    def update_raindrop(self, raindrop_id: int, body: dict[str, Any]) -> dict[str, Any]:
        payload = self.request("PUT", f"raindrop/{raindrop_id}", body=body)
        item = payload.get("item")
        return item if isinstance(item, dict) else payload


def build_client(args: argparse.Namespace) -> RaindropClient:
    token = normalize_token(args.token or env_token())
    if not token:
        raise RaindropApiError(
            "Missing Raindrop API token. Set RAINDROP_ACCESS_TOKEN or RAINDROP_TOKEN."
        )
    return RaindropClient(token=token, base_url=args.base_url)


def handle_collections(args: argparse.Namespace) -> dict[str, Any]:
    client = build_client(args)
    collections = [
        {
            "id": collection.get("_id"),
            "title": collection.get("title"),
            "count": collection.get("count"),
            "parent_id": (collection.get("parent") or {}).get("$id"),
        }
        for collection in client.collections()
    ]
    return {"collections": collections}


def review_collections(
    client: RaindropClient,
    args: argparse.Namespace,
) -> tuple[list[dict[str, Any]], list[str]]:
    inbox_name = args.inbox or os.environ.get("RAINDROP_INBOX_COLLECTION", DEFAULT_INBOX)
    include_unsorted = should_include_unsorted(args)
    warnings: list[str] = []
    collections: list[dict[str, Any]] = []

    try:
        collections.append(client.resolve_collection(inbox_name))
    except RaindropApiError as error:
        if not include_unsorted:
            raise
        warnings.append(str(error))

    if include_unsorted and not any(
        collection.get("_id") == UNSORTED_COLLECTION_ID for collection in collections
    ):
        collections.append(system_collection(UNSORTED_COLLECTION_ID))

    if not collections:
        raise RaindropApiError("No review collections resolved.")
    return collections, warnings


def handle_inbox(args: argparse.Namespace) -> dict[str, Any]:
    client = build_client(args)
    collections, warnings = review_collections(client, args)
    batches = [
        client.raindrops(
            int(collection["_id"]),
            page=args.page,
            perpage=args.limit,
            sort=args.sort,
            search=args.search,
            nested=args.nested,
        )
        for collection in collections
    ]
    items = combine_raindrops(batches, limit=args.limit, sort=args.sort)
    return {
        "collection": collection_summary(collections[0]),
        "collections": [collection_summary(collection) for collection in collections],
        "warnings": warnings,
        "items": [compact_raindrop(item) for item in items],
    }


def handle_process(args: argparse.Namespace) -> dict[str, Any]:
    client = build_client(args)
    raindrop = client.raindrop(args.id)
    original = compact_raindrop(raindrop)

    processed_name = args.processed or os.environ.get("RAINDROP_PROCESSED_COLLECTION", DEFAULT_PROCESSED)
    source_collections, warnings = review_collections(client, args)
    source_ids = {collection.get("_id") for collection in source_collections}
    current_collection_id = original.get("collection_id")
    if not args.skip_inbox_check and current_collection_id not in source_ids:
        source_text = ", ".join(
            f"{collection.get('title')} ({collection.get('_id')})"
            for collection in source_collections
        )
        raise RaindropApiError(
            f"Raindrop {args.id} is in collection {current_collection_id}, "
            f"not a review collection: {source_text}. Pass --skip-inbox-check to override."
        )

    processed = client.resolve_collection(
        processed_name,
        create_if_missing=args.create_processed,
    )
    added_tags = parse_tags([*args.tag, *(args.tags or [])], keep_hash=args.keep_hash_tags)
    if not added_tags:
        raise RaindropApiError("No tags provided. Pass --tags or one or more --tag values.")

    existing_tags = [str(tag) for tag in original.get("tags") or []]
    final_tags = merge_tags(existing_tags, added_tags)
    update_body = {
        "tags": final_tags,
        "collection": {"$id": int(processed["_id"])},
    }

    result: dict[str, Any] = {
        "id": args.id,
        "title": original.get("title"),
        "dry_run": args.dry_run,
        "collection": {
            "from": current_collection_id,
            "to": processed.get("_id"),
            "to_title": processed.get("title"),
            "review_sources": [collection_summary(collection) for collection in source_collections],
        },
        "tags": {
            "existing": existing_tags,
            "added": added_tags,
            "final": final_tags,
        },
        "warnings": warnings,
    }
    if args.dry_run:
        result["update_body"] = update_body
        return result

    client.update_raindrop(args.id, update_body)
    verified = compact_raindrop(client.raindrop(args.id))
    result["verified"] = {
        "collection_id": verified.get("collection_id"),
        "tags": verified.get("tags"),
    }
    return result


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review and process Raindrop.io Inbox bookmarks.")
    parser.add_argument("--token", help="Raindrop API token. Defaults to RAINDROP_ACCESS_TOKEN or RAINDROP_TOKEN.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"API base URL. Default: {DEFAULT_BASE_URL}")
    parser.add_argument("--env-file", default=".env", help="Optional dotenv file to load before reading env vars.")
    parser.add_argument("--no-env-file", action="store_true", help="Disable automatic .env loading.")
    parser.add_argument("--env-override", action="store_true", help="Let dotenv values override existing env vars.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("collections", help="List collection IDs and titles.")

    inbox_parser = subparsers.add_parser("inbox", help="List raindrops from Inbox and Unsorted.")
    inbox_parser.add_argument("--inbox", help=f"Inbox collection name or ID. Default: {DEFAULT_INBOX}.")
    inbox_parser.add_argument(
        "--no-unsorted",
        action="store_true",
        help="Do not include Raindrop's Unsorted system collection.",
    )
    inbox_parser.add_argument("--limit", type=int, default=10, help="Number of items to fetch. Max 50.")
    inbox_parser.add_argument("--page", type=int, default=0)
    inbox_parser.add_argument("--sort", default="-created")
    inbox_parser.add_argument("--search")
    inbox_parser.add_argument("--nested", action="store_true")

    process_parser = subparsers.add_parser(
        "process",
        help="Move one Inbox or Unsorted raindrop to Processed and add the Apple Note tags.",
    )
    process_parser.add_argument("--id", type=int, required=True, help="Raindrop ID to process.")
    process_parser.add_argument("--inbox", help=f"Inbox collection name or ID. Default: {DEFAULT_INBOX}.")
    process_parser.add_argument(
        "--no-unsorted",
        action="store_true",
        help="Do not allow Raindrop's Unsorted system collection as a review source.",
    )
    process_parser.add_argument(
        "--processed",
        help=f"Processed collection name or ID. Default: {DEFAULT_PROCESSED}.",
    )
    process_parser.add_argument(
        "--create-processed",
        action="store_true",
        help="Create the Processed collection if it is missing.",
    )
    process_parser.add_argument(
        "--skip-inbox-check",
        action="store_true",
        help="Allow processing a raindrop that is not currently in a review collection.",
    )
    process_parser.add_argument(
        "--tags",
        action="append",
        help="Whitespace or comma separated Apple Note tags, for example '#clip-notes #reference #ai'.",
    )
    process_parser.add_argument("--tag", action="append", default=[], help="One tag to add. Can be repeated.")
    process_parser.add_argument(
        "--keep-hash-tags",
        action="store_true",
        help="Keep leading # in Raindrop tag names. By default Apple Note hashtags are stored without #.",
    )
    process_parser.add_argument("--dry-run", action="store_true", help="Show the update without calling PUT.")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not args.no_env_file:
        load_env_file(args.env_file, override=args.env_override)
    try:
        if args.command == "collections":
            print_json(handle_collections(args))
        elif args.command == "inbox":
            if args.limit < 1 or args.limit > 50:
                raise RaindropApiError("--limit must be between 1 and 50.")
            print_json(handle_inbox(args))
        elif args.command == "process":
            print_json(handle_process(args))
    except RaindropApiError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
