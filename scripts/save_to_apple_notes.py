#!/usr/bin/env python3
"""Create, verify, and move Apple Notes for the clip-notes skill."""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys


DEFAULT_ACCOUNT = "iCloud"
DEFAULT_FOLDER = "clip-notes"
SPACER = "<div><br></div>"
SECTION_HEADING_RE = re.compile(
    r'(<div><b>(?:<font face="\.AppleSystemUIFontBold">)?'
    r'<span style="font-size: 18px">.*?</span>(?:</font>)?</b>(?:<br>)?</div>)'
)
NUMBERED_HEADING_RE = re.compile(
    r'(<div><b>(?:<font face="\.AppleSystemUIFontBold">)?\d+\.[^<]*(?:</font>)?</b>(?:<br>)?</div>)'
)
METADATA_LABEL_RE = re.compile(
    r"(?<!<br>)(<b>(?:Posted|Published|Length|Notes created|Lifecycle|Category|Tags|Revisit|Why keep this):</b>)"
)


def applescript_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def run_applescript(script: str) -> str:
    proc = subprocess.run(
        ["osascript", "-"],
        input=script,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        if proc.stderr:
            print(proc.stderr.strip(), file=sys.stderr)
        raise SystemExit(proc.returncode)
    return proc.stdout.strip()


def ensure_folder(account: str, folder: str) -> str:
    script = f"""
tell application "Notes"
    set targetAccount to account {applescript_quote(account)}
    if not (exists folder {applescript_quote(folder)} of targetAccount) then
        make new folder at targetAccount with properties {{name:{applescript_quote(folder)}}}
    end if
    return name of folder {applescript_quote(folder)} of targetAccount
end tell
"""
    return run_applescript(script)


def save_note(account: str, folder: str, title: str, html_file: pathlib.Path, show: bool) -> str:
    html_path = str(html_file.expanduser().resolve())
    if not pathlib.Path(html_path).is_file():
        raise SystemExit(f"HTML file not found: {html_path}")

    show_line = "show newNote" if show else ""
    script = f"""
set htmlPath to {applescript_quote(html_path)}
set noteBody to read POSIX file htmlPath as «class utf8»
set noteTitle to {applescript_quote(title)}

tell application "Notes"
    set targetAccount to account {applescript_quote(account)}
    if not (exists folder {applescript_quote(folder)} of targetAccount) then
        make new folder at targetAccount with properties {{name:{applescript_quote(folder)}}}
    end if
    set targetFolder to folder {applescript_quote(folder)} of targetAccount
    set newNote to make new note at targetFolder with properties {{name:noteTitle, body:noteBody}}
    {show_line}
    return id of newNote
end tell
"""
    return run_applescript(script)


def verify_note(account: str, folder: str, title: str) -> str:
    script = f"""
set noteTitle to {applescript_quote(title)}

tell application "Notes"
    set targetAccount to account {applescript_quote(account)}
    if not (exists folder {applescript_quote(folder)} of targetAccount) then
        return "MISSING_FOLDER: " & {applescript_quote(folder)}
    end if
    set targetFolder to folder {applescript_quote(folder)} of targetAccount
    if exists note noteTitle of targetFolder then
        return "FOUND: " & noteTitle
    else
        return "MISSING: " & noteTitle
    end if
end tell
"""
    return run_applescript(script)


def move_note(account: str, folder: str, title: str) -> str:
    script = f"""
set noteTitle to {applescript_quote(title)}

tell application "Notes"
    set targetAccount to account {applescript_quote(account)}
    if not (exists folder {applescript_quote(folder)} of targetAccount) then
        make new folder at targetAccount with properties {{name:{applescript_quote(folder)}}}
    end if
    set targetFolder to folder {applescript_quote(folder)} of targetAccount
    set movedCount to 0
    set alreadyThere to 0

    repeat with sourceFolder in folders of targetAccount
        if exists note noteTitle of sourceFolder then
            if id of sourceFolder is id of targetFolder then
            set alreadyThere to alreadyThere + 1
            else
                move note noteTitle of sourceFolder to targetFolder
                set movedCount to movedCount + 1
            end if
        end if
    end repeat

    if movedCount > 0 then
        return "MOVED: " & noteTitle
    else if alreadyThere > 0 then
        return "FOUND_IN_TARGET: " & noteTitle
    else
        return "MISSING: " & noteTitle
    end if
end tell
"""
    return run_applescript(script)


def list_notes(account: str, folder: str) -> str:
    script = f"""
tell application "Notes"
    set targetAccount to account {applescript_quote(account)}
    if not (exists folder {applescript_quote(folder)} of targetAccount) then
        return "MISSING_FOLDER: " & {applescript_quote(folder)}
    end if
    set targetFolder to folder {applescript_quote(folder)} of targetAccount
    set oldDelimiters to AppleScript's text item delimiters
    set AppleScript's text item delimiters to linefeed
    set noteNames to name of notes of targetFolder
    set noteText to noteNames as text
    set AppleScript's text item delimiters to oldDelimiters
    return noteText
end tell
"""
    return run_applescript(script)


def find_note_by_raindrop_id(account: str, folder: str, raindrop_id: int) -> str:
    rd_id = str(raindrop_id)
    script = f"""
set rdId to {applescript_quote(rd_id)}
set titleNeedle to "RD " & rdId
set bracketNeedle to "[RD " & rdId & "]"
set bodyNeedle to "Raindrop ID: " & rdId

tell application "Notes"
    set targetAccount to account {applescript_quote(account)}
    if not (exists folder {applescript_quote(folder)} of targetAccount) then
        return "MISSING_FOLDER: " & {applescript_quote(folder)}
    end if
    set targetFolder to folder {applescript_quote(folder)} of targetAccount
    repeat with targetNote in notes of targetFolder
        set noteName to name of targetNote as text
        if noteName contains titleNeedle or noteName contains bracketNeedle then
            return "FOUND: " & noteName
        end if
        set noteBody to body of targetNote as text
        if noteBody contains bodyNeedle or noteBody contains titleNeedle or noteBody contains bracketNeedle then
            return "FOUND: " & noteName
        end if
    end repeat
    return "MISSING: " & rdId
end tell
"""
    return run_applescript(script)


def get_note_body(account: str, folder: str, title: str) -> str:
    script = f"""
set noteTitle to {applescript_quote(title)}

tell application "Notes"
    set targetAccount to account {applescript_quote(account)}
    set targetFolder to folder {applescript_quote(folder)} of targetAccount
    return body of note noteTitle of targetFolder
end tell
"""
    return run_applescript(script)


def set_note_body(account: str, folder: str, title: str, html_body: str) -> str:
    script = f"""
set noteTitle to {applescript_quote(title)}
set noteBody to {applescript_quote(html_body)}

tell application "Notes"
    set targetAccount to account {applescript_quote(account)}
    set targetFolder to folder {applescript_quote(folder)} of targetAccount
    set targetNote to note noteTitle of targetFolder
    set body of targetNote to noteBody
    return name of targetNote
end tell
"""
    return run_applescript(script)


def normalize_spacing(html_body: str) -> str:
    body = html_body.strip()
    body = METADATA_LABEL_RE.sub(r"<br>\1", body)
    body = body.replace("<div><br><b>", "<div><b>")

    body = re.sub(rf"(?:{re.escape(SPACER)}\s*)+(?={SECTION_HEADING_RE.pattern})", "", body)
    body = SECTION_HEADING_RE.sub(lambda match: f"{SPACER}\n{match.group(1)}", body)

    body = re.sub(rf"(?:{re.escape(SPACER)}\s*)+(?={NUMBERED_HEADING_RE.pattern})", "", body)
    body = NUMBERED_HEADING_RE.sub(lambda match: f"{SPACER}\n{match.group(1)}", body)

    body = re.sub(rf"(?:{re.escape(SPACER)}\s*){{2,}}", SPACER, body)
    return body


def restyle_note(account: str, folder: str, title: str) -> str:
    body = get_note_body(account, folder, title)
    restyled = normalize_spacing(body)
    if restyled == body:
        return f"UNCHANGED: {title}"
    new_title = set_note_body(account, folder, title, restyled)
    return f"RESTYLED: {new_title}"


def restyle_folder(account: str, folder: str) -> str:
    titles = [title for title in list_notes(account, folder).splitlines() if title.strip()]
    if not titles:
        return f"NO_NOTES: {folder}"
    return "\n".join(restyle_note(account, folder, title) for title in titles)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Save clip-notes summaries to Apple Notes.")
    parser.add_argument("--account", default=DEFAULT_ACCOUNT, help=f"Apple Notes account, default: {DEFAULT_ACCOUNT}")
    parser.add_argument("--folder", default=DEFAULT_FOLDER, help=f"Apple Notes folder, default: {DEFAULT_FOLDER}")

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("ensure-folder", help="Create the target folder if needed.")

    save_parser = subparsers.add_parser("save", help="Create a note from an HTML file.")
    save_parser.add_argument("--title", required=True, help="Exact note title.")
    save_parser.add_argument("--html-file", required=True, type=pathlib.Path, help="HTML file to save as the note body.")
    save_parser.add_argument("--show", action="store_true", help="Show the created note in Notes.")

    verify_parser = subparsers.add_parser("verify", help="Verify a note title exists in the target folder.")
    verify_parser.add_argument("--title", required=True, help="Exact note title.")

    move_parser = subparsers.add_parser("move", help="Move matching note titles into the target folder.")
    move_parser.add_argument("--title", required=True, help="Exact note title.")

    restyle_parser = subparsers.add_parser("restyle", help="Improve spacing in an existing note or all notes.")
    restyle_parser.add_argument("--title", help="Exact note title. If omitted, restyles every note in the folder.")

    find_rd_parser = subparsers.add_parser("find-rd", help="Find a note by embedded Raindrop ID.")
    find_rd_parser.add_argument("--id", type=int, required=True, help="Raindrop ID to find in note title or body.")

    subparsers.add_parser("list", help="List note titles in the target folder.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "ensure-folder":
        print(ensure_folder(args.account, args.folder))
    elif args.command == "save":
        print(save_note(args.account, args.folder, args.title, args.html_file, args.show))
    elif args.command == "verify":
        print(verify_note(args.account, args.folder, args.title))
    elif args.command == "move":
        print(move_note(args.account, args.folder, args.title))
    elif args.command == "restyle":
        if args.title:
            print(restyle_note(args.account, args.folder, args.title))
        else:
            print(restyle_folder(args.account, args.folder))
    elif args.command == "find-rd":
        print(find_note_by_raindrop_id(args.account, args.folder, args.id))
    elif args.command == "list":
        print(list_notes(args.account, args.folder))


if __name__ == "__main__":
    main()
