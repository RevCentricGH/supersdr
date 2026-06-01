# SuperSDR Skills

Public Claude Cowork skills for the SuperSDR community (RevCentric). Each top-level dir is one skill.

## Structure
- A skill is a folder with a `SKILL.md`. Frontmatter `name:` MUST equal the folder name; `description:` must be non-empty (it's the trigger). Optional `reference/` holds supporting docs.
- Skills ship publicly as GitHub release ZIPs (`.github/workflows/build-skill-zips.yml`). Assume anything committed is public.

## Rules
- `DEV_STATUS.md` and `.internal/` are gitignored internal-only — never commit them, and never commit `__pycache__/`. CI (`validate-skills.yml`) fails the PR if they appear or if frontmatter is wrong.
- Validation/dry-run status goes in `DEV_STATUS.md`, not in the public skill files.
- Skill-content voice: no AI-tell openers, no hedging, no AI vocabulary, no em-dashes. Write like a person.
