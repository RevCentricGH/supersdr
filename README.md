# SuperSDR Skills

Claude Cowork skills for the SuperSDR community.

## Skills

| Skill | What it does |
|-------|-------------|
| [client-spot](client-spot/) | Generate a complete multi-tab Single Point of Truth (SPOT) Google Doc for a new client — campaign status, company overview, problem/solution, ICP, competitive landscape, objections, screenplay, and Apollo campaign setup |
| [cold-calling-screenplay](cold-calling-screenplay/) | Generate a verbatim cold call screenplay (Short or Full version) for any B2B company — pulls live case studies from the client's website automatically |
| [list-building](list-building/) | Read a client's SPOT doc and build a named Apollo contact list from their ICP filters — searches Apollo by titles, location, employee range, keywords, and tech signals, then creates the list in the user's Apollo workspace |
| [apollo-campaign-builder](apollo-campaign-builder/) | Set up all 7 outreach sequences + 3 workflow plays for a new client in the Apollo UI using browser automation (run after list-building) |
| [objection-drill](objection-drill/) | Cold call objection handling trainer — Quick Drill or Live Roleplay modes across the 5 core objection families |
| [client-proposal-doc-builder](client-proposal-doc-builder/) | Build a send-ready outbound agency proposal (DFY Calling, cold email, or combined outbound) as a Google Doc from a discovery-call transcript — includes pricing tiers, completed-conversations model, T&Cs, and signature block |

## Setup

Complete this once before running any skills that require external connections.

**Google Drive connector** — required by `list-building` and `client-proposal-doc-builder`
Go to Settings → Connectors → Google Drive in Cowork. Connect your Google account and enable edit access (read-only is not enough for the proposal builder).

**Apollo API key** — required by `list-building`
Go to Apollo → Settings → Integrations → API and copy your key. Requires an Apollo paid plan. The skill will ask for it on first run.

**Browser automation** — required by `apollo-campaign-builder`
Go to Settings → Computer Use in Cowork and enable browser control. Log into Apollo in Chrome and keep that tab open when running the skill.

| Skill | Google Drive | Apollo API key | Browser automation |
|---|---|---|---|
| client-spot | | | |
| cold-calling-screenplay | | | |
| list-building | required | required | |
| apollo-campaign-builder | | | required |
| objection-drill | | | |
| client-proposal-doc-builder | required (write) | | |

## How to use

1. Click the green **Code** button at the top of this page → **Download ZIP**
2. Extract the ZIP and open the folder for the skill you want (e.g. `client-spot`)
3. In Claude Cowork, upload the entire skill folder (not just SKILL.md — some skills need companion files)
4. Follow the instructions in the skill

> Some skills (`list-building`, `apollo-campaign-builder`, `client-proposal-doc-builder`) include Python scripts and asset files that Claude needs alongside SKILL.md. Uploading the whole folder ensures nothing is missing.

## Data flow

```
SPOT (client-spot)
  ├── Tab 3 + Tab 4 → cold-calling-screenplay
  ├── Tab 9         → list-building → apollo-campaign-builder
  └── discovery call transcript → client-proposal-doc-builder
```

Run `client-spot` first. Everything else builds off it.
