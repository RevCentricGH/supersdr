# SuperSDR Skills

Public Claude Cowork skills for the SuperSDR community (RevCentric). Each top-level dir is one skill.

## Structure
- A skill is a folder with a `SKILL.md`. Frontmatter `name:` MUST equal the folder name; `description:` must be non-empty (it's the trigger). Optional `reference/` holds supporting docs.
- Skills ship publicly as GitHub release ZIPs (`.github/workflows/build-skill-zips.yml`). Assume anything committed is public.

## Deeper context (read on demand, not auto-loaded)
- `CONTEXT.md` — domain glossary (Cowork vs Claude Code skills, transcripts, SPOT) and the revcentric port decisions. Internal/gitignored, present locally; open it when a task needs domain detail.
- `docs/adr/` — architecture decision records. Internal/gitignored, present locally.

## Rules
- `CONTEXT.md`, `docs/adr/`, `DEV_STATUS.md`, and `.internal/` are gitignored internal-only — never commit them, and never commit `__pycache__/`. CI (`validate-skills.yml`) fails the PR if `DEV_STATUS.md`/`.internal` appear or if frontmatter is wrong.
- Validation/dry-run status goes in `DEV_STATUS.md`, not in the public skill files.
- Skill-content voice: no AI-tell openers, no hedging, no AI vocabulary, no em-dashes. Write like a person.

## Agent skills

### Issue tracker

Issues live in GitHub Issues. See `docs/agents/issue-tracker.md`.

### Triage labels

`needs-triage`, `needs-info`, `afk`, `hitl`, `tracking`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

`docs/agents/domain.md` is the public, agent-facing domain summary (in the clone). The detailed
`CONTEXT.md` and `docs/adr/` are gitignored and local-only — not available to ralph's managed clone.

### Tests

`.ralph.json` sets `testCmd` to `python3 scripts/validate_skills.py` — the same validator CI runs.
