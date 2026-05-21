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

Some skills require a one-time configuration before they'll work. See **[SETUP.md](SETUP.md)** for the full guide — covers Google Drive connector, Apollo API key, and browser automation.

## How to use

1. Open the skill folder you want (e.g. `client-spot`)
2. Click `SKILL.md` → click **Raw** → save the file to your computer
3. In Claude Cowork, upload the file or paste the contents at the start of your session
4. Follow the instructions in the skill

## Data flow

```
SPOT (client-spot)
  ├── Tab 3 + Tab 4 → cold-calling-screenplay
  ├── Tab 9         → list-building → apollo-campaign-builder
  └── discovery call transcript → client-proposal-doc-builder
```

Run `client-spot` first. Everything else builds off it.
