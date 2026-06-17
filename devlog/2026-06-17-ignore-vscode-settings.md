# 2026-06-17 — Ignore Local VS Code Settings

- Branch/worktree: `development` / `/Users/taheny/vault/teamt/clip-notes`
- Commit: `pending`
- Goal: Keep local editor settings out of the repository after worktree reconciliation.
- Files changed:
  - `.gitignore` — ignores `.vscode/` as local editor state.
- Decisions:
  - Treat `.vscode/settings.json` as local-only because it only customizes the window title.
- Validation:
  - `git diff --check` — passed.
  - `rg -n "[ \t]+$" .gitignore devlog/2026-06-17-ignore-vscode-settings.md` — no trailing whitespace matches.
- Review:
  - Pending post-cleanup audit.
- Follow-ups:
  - None.
