# Documentation Strategy

This strategy was created during an `af-docs` backfill pass because the repository had no `README.md`, `docs/`, or `devlog/` files.

## Assumptions

- Primary audience: maintainers and future agents updating the skill.
- Secondary audience: users invoking the skill from Codex on macOS or adapting it to ChatGPT and share-sheet workflows.
- Documentation style: concise operational reference with task-based user guidance.
- Source of truth: `SKILL.md`, `references/`, helper scripts, and Git history.
- Visual format: Mermaid diagrams for workflows; screenshots only after real non-sensitive runs.
- The repository currently operates on `development`, which is also aligned with `main` at the time this strategy was written.

## Docs Map

| Document | Audience | Purpose |
| --- | --- | --- |
| `README.md` | users, maintainers, agents | Fast orientation, repo map, prerequisites, commands, and docs navigation. |
| `docs/REQUIREMENTS.md` | maintainers, reviewers | User-visible behavior, constraints, and non-functional requirements. |
| `docs/ARCHITECTURE.md` | maintainers, agents | Components, data flow, Apple Notes boundary, media extraction boundary, trust boundaries. |
| `docs/RUNBOOK.md` | operators, maintainers, agents | Setup, common commands, validation, troubleshooting, rollback. |
| `docs/SECURITY.md` | maintainers, users | Privacy, local artifacts, AppleScript access, dependency risks, reporting gaps. |
| `docs/USER-GUIDE.md` | users, support | How to request clip notes and what to expect in saved notes. |
| `docs/VISUALS.md` | maintainers, stakeholders | Diagram inventory, screenshot plan, demo plan, visual standards. |

## Existing Docs Inventory

No existing project docs were found during backfill.

| File | Classification | Decision |
| --- | --- | --- |
| `SKILL.md` | Current and authoritative | Keep as the canonical skill contract. |
| `references/source-strategies.md` | Current and useful | Keep as source-specific guidance. |
| `references/share-workflows.md` | Current and useful | Keep as user workflow guidance. |
| `agents/openai.yaml` | Current and useful | Keep as agent-facing metadata. |
| `README.md` | Missing before backfill | Created as the top-level entry point. |
| `docs/*` | Missing before backfill | Created as a concise baseline. |

## Maintenance Triggers

Update docs when any of these change:

- Skill invocation rules, note template, lifecycle values, categories, tags, or done criteria.
- Apple Notes helper commands, defaults, AppleScript behavior, or spacing normalization.
- Media extraction behavior, output paths, dependency assumptions, or transcript cleaning.
- Raindrop API helper commands, token environment variables, `.env` loading, collection defaults, or processing rules.
- Source-specific privacy or fallback rules.
- Installation, packaging, release, or distribution process.
- Security posture, local artifact handling, or Apple Notes account/folder assumptions.
- User workflows for Codex, ChatGPT, iOS, or macOS sharing.

## Validation Expectations

For docs-only changes:

- Inspect Markdown links and referenced paths.
- Confirm Mermaid diagrams are syntactically plausible by inspection or rendering when a renderer is available.
- Run `python3 -m py_compile scripts/*.py` if script behavior is referenced or nearby files changed.
- Run `python3 -m unittest tests/test_raindrop_api.py` if Raindrop tag parsing or processing behavior is changed.

For behavior changes:

- Run `python3 -m py_compile scripts/*.py`.
- Run Raindrop helper unit tests when `scripts/raindrop_api.py` changes.
- Exercise the affected helper command when local Apple Notes or `yt-dlp` access makes it safe.
- Update `docs/RUNBOOK.md`, `docs/REQUIREMENTS.md`, and `docs/SECURITY.md` as needed.

## Open Questions

<!-- TODO: Confirm the intended installation path for users outside this local skill checkout. -->
<!-- TODO: Confirm whether this repository should include a canonical `AGENT-FLOW.md`. -->
<!-- TODO: Confirm whether there is a release process for `dist/clip-notes.zip`. -->
<!-- TODO: Confirm a security reporting contact if this skill is distributed outside the private workspace. -->
<!-- TODO: Capture non-sensitive screenshots for `docs/assets/` after a real saved-note flow. -->
