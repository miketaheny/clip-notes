# 2026-06-17 — Dedupe Raindrop collection records

- Branch/worktree: `fix/raindrop-live-processing` / `/Users/taheny/vault/teamt/clip-notes-raindrop-live-fix`
- Commit: `fix: dedupe Raindrop collections`
- Goal: Let live Raindrop Inbox processing resolve the configured `Processed` collection when the API returns the same collection from both root and child collection endpoints.
- Files changed:
  - `scripts/raindrop_api.py` — dedupes collection records by `_id` before listing or resolving collection names.
  - `tests/test_raindrop_api.py` — adds regression coverage for duplicate collection IDs.
- Decisions:
  - Keep the first collection record for each `_id`, preserving existing API order while preventing false multiple-name errors.
  - Keep name collision errors for genuinely distinct collection IDs with the same title.
- Validation:
  - `python3 -m py_compile scripts/*.py` — passed.
  - `python3 -m unittest tests/test_raindrop_api.py` — passed, 10 tests.
  - `git diff --check` — passed.
  - `python3 scripts/raindrop_api.py --env-file /Users/taheny/vault/teamt/clip-notes/.env collections` — passed; live duplicate collection rows were deduped in helper output.
- Review:
  - Focused diff review completed; the change is limited to collection dedupe behavior and regression coverage.
- Follow-ups:
  - Resume the live Raindrop batch after this helper fix is merged to `development`.
