# SuperSDR skill pack — agent install guide

This repo is a universal skill pack for AI-native cold-calling agencies (the SuperSDR community, supported by RevCentric). Every skill lives under [`skills/`](skills/) — one folder per skill, each with a `SKILL.md` that defines what it does and what it needs. Skills name their capabilities in plain English; you, the host model, bind each capability to whatever equivalent tool your harness provides.

The pack works in any agentic harness: Claude Code, Claude Cowork, Codex, Hermes, or anything else that can read a folder of instructions.

## Install protocol

1. **Pick skills with the user.** Read the skill list in [`skills/`](skills/) (or the README tables) and ask which jobs they want covered. Don't install everything by default — each skill is self-contained and one is enough to start.
2. **Copy the folder.** Copy the whole `skills/<name>/` folder (not just `SKILL.md` — some skills ship `reference/` docs or helper code) into wherever your harness loads skills from. If your harness has no skills directory, keep the folder anywhere readable and load `SKILL.md` as instructions when the user invokes the skill.
3. **Bind capabilities to your tools.** Each skill states what it needs in plain English — read a Google Doc, search Apollo, send an email, run a Python script. Map each need to your own equivalent: a connector, an MCP server, a CLI, browser automation, whatever you have. There is no per-runtime mapping table; you improvise the binding.
4. **Hard-stop on missing capabilities.** If the user's harness has no tool that covers a capability a skill needs, say so and stop. Don't fake the step or silently degrade.

## Layout

- `skills/<name>/SKILL.md` — the skill itself. Frontmatter `name:` matches the folder; `description:` is the trigger.
- `skills/<name>/reference/` — supporting docs some skills bundle. Ship them with the skill.
- A few skills (`custom-decks`, `master-tracker`, `weekly-checkin`) are standalone `python3 run.py` CLIs and need a harness with shell access.

## Path note

Skills used to live at the repo root (`<name>/SKILL.md`). As of the `skills/` reorg, root-level skill paths are no longer valid — anything referencing skills by repo path must use `skills/<name>/`.
