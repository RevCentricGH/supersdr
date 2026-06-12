# Hermes-Adapted SuperSDR Skills

These are the Hermes-native versions of the SuperSDR skills. They replace Cowork/Claude Code dependencies with Hermes tools and APIs.

## How to Use

Upload each skill folder (e.g., `hermes-adapted/list-builder/`) directly into your Hermes instance via `/skill` or by placing it in your `.hermes/skills/` directory.

## Differences from Cowork Versions

| Aspect | Cowork Version | Hermes-Adapted Version |
|--------|---------------|----------------------|
| **Google Drive** | Cowork Drive connector | `google-workspace` skill (`google_docs_create`, `google_docs_update`) |
| **Gmail** | Cowork Gmail connector | `himalaya` CLI tool |
| **Apollo API** | Browser automation only | `revcentric-tools/apollo_client.py` REST calls where available |
| **Browser Automation** | Claude-in-Chrome / Cowork browser tools | Hermes `browser_*` tools (headless Chrome) |
| **MCP Integration** | Not supported | Apollo MCP, Google Sheets MCP, ZeroBounce, Twilio, etc. |

## Skills Included

- `apollo-account-setup` — Browser-dependent (Apollo has no API for dispositions/stages/triggers)
- `apollo-campaign-builder` — Browser-dependent (Apollo has no API for sequences/workflows)
- `client-spot` — Hermes-native via google-workspace skill
- `cold-calling-screenplay` — Self-contained reasoning skill
- `custom-decks` — Terminal-based Python/Claude Code
- `disco-deck` — Self-contained reasoning skill
- `list-builder` — Hermes-native via Apollo MCP + google-workspace
- `master-tracker` — Terminal-based cron/Python system
- `objection-drill` — Self-contained roleplay tool
- `post-discovery-followup` — Hermes-native (himalaya + apollo_client.py)
- `pre-brief` — Self-contained reasoning skill
- `tam-contact-mapper` — Hermes-native via apollo_client.py REST API

## Prerequisites for Hermes Users

Before using these skills, ensure you have:

1. **Hermes installed** with the `default` profile active
2. **Apollo MCP server** connected (for list-builder, tam-contact-mapper)
3. **Google Workspace skill** loaded (for client-spot, post-discovery-followup)
4. **himalaya CLI** configured with Gmail credentials (for email sending)
5. **APOLLO_API_KEY** set in your `.env` file (for tam-contact-mapper, apollo_client.py calls)

## Browser-Dependent Skills

Two skills (`apollo-account-setup`, `apollo-campaign-builder`) require browser automation because Apollo's platform does not expose REST API endpoints for:
- Dispositions and contact stages
- Workflow plays and triggers
- Sequence creation

These skills use Hermes `browser_*` tools (headless Chrome) to automate the Apollo UI. If browser automation is unavailable, they output manual checklists with all data so you can enter entries by hand.

## Migration Notes

The Cowork versions remain in the root of this repo and are unchanged. The Hermes-adapted versions live here under `hermes-adapted/`. Both sets coexist — use whichever matches your runtime environment.
