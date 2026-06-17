# 2026-06-17 — Normalize Raindrop Token Prefix

- Branch/worktree: `development` / `/Users/taheny/vault/teamt/clip-notes`
- Commit: `pending`
- Goal: Accept Raindrop API tokens pasted either as a raw token or as a `Bearer <token>` value.
- Files changed:
  - `scripts/raindrop_api.py` — strips a leading `Bearer ` prefix before building the Authorization header.
  - `tests/test_raindrop_api.py` — adds token normalization coverage.
- Decisions:
  - Keep `.env` untouched; normalize at runtime so existing local token values keep working.
- Validation:
  - `python3 -m py_compile scripts/*.py` — passed.
  - `python3 -m unittest tests/test_raindrop_api.py` — passed, 9 tests.
  - `git diff --check` — passed.
  - `rg -n "[ \t]+$" scripts/raindrop_api.py tests/test_raindrop_api.py devlog/2026-06-17-raindrop-token-normalization.md` — no trailing whitespace matches.
- Review:
  - Focused diff review completed.
- Follow-ups:
  - None.
