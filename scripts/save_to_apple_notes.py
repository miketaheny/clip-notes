#!/usr/bin/env python3
"""Create, verify, and move Apple Notes for the clip-notes skill."""

from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys


DEFAULT_ACCOUNT = "iCloud"
DEFAULT_FOLDER = "clip-notes"


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
    return name of notes of targetFolder
end tell
"""
    return run_applescript(script)


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
    elif args.command == "list":
        print(list_notes(args.account, args.folder))


if __name__ == "__main__":
    main()
