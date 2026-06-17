#!/usr/bin/env python3
"""Extract metadata and captions for video/social URLs with yt-dlp."""

from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
import shutil
import subprocess
import sys


DEFAULT_LANGS = "en,en-orig,eng-US"


def run(cmd: list[str], cwd: pathlib.Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


def clean_vtt(vtt_path: pathlib.Path) -> str:
    raw = vtt_path.read_text(encoding="utf-8", errors="replace")
    blocks = re.split(r"\n\s*\n", raw)
    cues: list[tuple[str, str]] = []

    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        timing_index = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if timing_index is None:
            continue
        start = lines[timing_index].split("-->", 1)[0].strip()
        text = " ".join(lines[timing_index + 1 :])
        text = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", "", text)
        text = re.sub(r"</?c[^>]*>", "", text)
        text = re.sub(r"<[^>]+>", "", text)
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            cues.append((start, text))

    pieces: list[str] = []
    previous = ""
    for _, text in cues:
        new_text = text
        if previous and text.startswith(previous):
            new_text = text[len(previous) :].strip()
        elif previous:
            prev_words = previous.split()
            words = text.split()
            best = 0
            for size in range(1, min(len(prev_words), len(words)) + 1):
                if prev_words[-size:] == words[:size]:
                    best = size
            if best:
                new_text = " ".join(words[best:]).strip()
        if new_text:
            pieces.append(new_text)
        previous = text

    transcript = " ".join(pieces)
    transcript = re.sub(r"\s+([,.!?;:])", r"\1", transcript)
    return re.sub(r"\s+", " ", transcript).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Download metadata and captions for a media URL.")
    parser.add_argument("url", help="Video or social-media URL supported by yt-dlp.")
    parser.add_argument("--out-dir", default="work/clip-notes-media", type=pathlib.Path)
    parser.add_argument("--langs", default=DEFAULT_LANGS, help=f"Subtitle languages, default: {DEFAULT_LANGS}")
    args = parser.parse_args()

    if not shutil.which("yt-dlp"):
        raise SystemExit("yt-dlp is not installed or not on PATH.")

    out_dir = args.out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    metadata_path = out_dir / "metadata.json"
    metadata = run(["yt-dlp", "--skip-download", "--dump-single-json", "--no-warnings", args.url])
    if metadata.returncode != 0:
        print(metadata.stderr.strip(), file=sys.stderr)
        raise SystemExit(metadata.returncode)
    metadata_path.write_text(metadata.stdout, encoding="utf-8")

    try:
        video_id = json.loads(metadata.stdout).get("id") or "media"
    except json.JSONDecodeError:
        video_id = "media"

    download = run(
        [
            "yt-dlp",
            "--skip-download",
            "--write-subs",
            "--write-auto-subs",
            "--sub-langs",
            args.langs,
            "--sub-format",
            "vtt",
            "--output",
            str(out_dir / "%(id)s.%(ext)s"),
            args.url,
        ]
    )
    if download.returncode != 0:
        print(download.stderr.strip(), file=sys.stderr)

    vtt_files = sorted(out_dir.glob(f"{video_id}*.vtt")) or sorted(out_dir.glob("*.vtt"))
    transcript_path = out_dir / "transcript.txt"
    if vtt_files:
        transcript = "\n\n".join(clean_vtt(path) for path in vtt_files if path.is_file()).strip()
        transcript_path.write_text(transcript + "\n", encoding="utf-8")
        print(f"metadata={metadata_path}")
        print(f"captions={','.join(str(path) for path in vtt_files)}")
        print(f"transcript={transcript_path}")
    else:
        print(f"metadata={metadata_path}")
        print("captions=")
        print("transcript=")


if __name__ == "__main__":
    main()
