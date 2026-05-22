# Legacy — script-based pipeline (deprecated for Cowork users)

Everything in this folder is the previous version of the list-builder skill that ran via a Python script and `.env` API keys.

This version was deprecated when the skill was rewritten for Claude Cowork users, who don't have persistent local filesystems for `.env` files and don't manage Python dependencies.

**The active skill is `../SKILL.md`** — it runs entirely through MCP tools and Claude's inline reasoning. No Python, no API keys to manage locally.

## When to use this legacy version

Only if you're running Claude Code locally (CLI) and want:
- Deterministic heuristic scoring
- Email validation waterfall (MillionVerifier → ZeroBounce → Prospeo → LeadMagic)
- Twilio phone line-type validation
- Persistent dedup across runs

For setup, see the files in this folder (`list_builder.py`, `lib/`, `clients/_template.yaml`, `.env.example`).
