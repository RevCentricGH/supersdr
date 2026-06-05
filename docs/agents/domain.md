# Domain docs

Read this before designing anything. It is the public, agent-facing summary of the
project's language and shaping decisions.

A fuller internal `CONTEXT.md` and `docs/adr/` exist on the maintainer's machine but are
gitignored, so they are NOT in this clone. Everything an agent needs to build the open
slices is here, in the issue bodies, in `CLAUDE.md`, and in the existing skill folders.

## Glossary

- **Skill** — a self-contained capability: a folder with a `SKILL.md` plus any companion
  files. Frontmatter `name:` must equal the folder name; `description:` is the trigger and
  must be non-empty and at most 1024 chars (Claude rejects the skill at upload past that).
  Each top-level dir is one skill. Skills ship publicly as per-skill ZIPs, so assume
  anything committed is public.
- **Runtime** — a skill is exactly one of two kinds.
  - **Cowork skill** — runs interactively in the Claude Cowork desktop app. No cron, no
    unattended loops, no local API keys, no OAuth token files, no Python that *executes* as a
    job. External systems are reached through MCP connectors (Apollo, Google Drive/Sheets/Docs,
    Gmail) and browser automation (Claude in Chrome). Where a Cowork skill ships `.py` files,
    they are data + browser EXECUTION_GUIDEs that Claude reads into context, not scripts that run.
  - **Claude Code skill** — runs in a terminal, where there is a shell, filesystem, cron, and
    real Python. Reserved for work that needs a runtime (unattended accumulation, binary
    rendering). These carry a "Claude Code skill — runs in a terminal, NOT Cowork" banner.
- **Transcript** — always user-supplied: pasted text or a linked Fireflies/Gemini/Drive doc.
  Skills never fetch call audio from a dialer and never run their own transcription.
- **SPOT doc** — a client "Single Point of Truth": the multi-tab Google Doc that holds the
  ICP/positioning the other skills build off.

## Principles

- **Chain, don't duplicate.** When another skill already does a job (proposal docs, follow-up
  emails), hand off to it rather than copying its logic. Improvements there benefit every caller.
- **Productized, not internal.** Skills are built for any operator to run on their own accounts
  and branding. Nothing hardcoded to one company, one person, or one machine.
- **Voice rules apply to Claude's own messages**, not just skill content: no AI-tell openers,
  no hedging, no AI vocabulary, no em-dashes. Write like a person.

## Active wave: post-discovery-followup

A single self-contained Cowork skill that reproduces a post-discovery-call workflow with the
human present in the session. Full detail is in PRD #14 and slices #15-19.

- **Flow:** user-supplied discovery transcript, then triage (the skill proposes 1 of 7
  outcomes with one line of reasoning; the operator confirms or overrides), then branch.
- **Seven outcomes:** `proposal`, `needs_followup`, `closed_won`, `closed_lost`, `fridge`,
  `disqualified`, `stay_in_proposal`. The taxonomy and the outcome-to-Apollo-stage map live in
  one `reference/outcome-taxonomy.md` module that later slices read.
- **proposal / needs_followup:** hand the transcript to the existing `client-proposal-doc-builder`
  skill (proposal doc, or email-only for `needs_followup`), the operator approves, send via the
  Gmail connector, then update Apollo.
- **The other five outcomes:** report the outcome plus the manual next step. No draft, no Apollo write.
- **Apollo stage update:** browser automation (Claude in Chrome). Search by company name, show the
  matched opportunity and its current stage, require explicit confirmation, then flip. On zero or
  multiple matches the operator picks or supplies the opportunity. No silent top-match write.
- **Connectors:** Google Drive (transcript + proposal doc), Gmail (send — the first send-capable
  skill in the repo), Claude in Chrome logged into Apollo (stage update).
