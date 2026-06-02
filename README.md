# SuperSDR Skills

Claude Cowork skills for the SuperSDR community.

## Skills

| Skill | What it does | |
|-------|-------------|---|
| [apollo-account-setup](apollo-account-setup/) | One-time Apollo account setup, run once before any campaigns — link workspace email, register your outbound number (FCR), and configure the 19 dispositions, 11 contact stages, and 19 disposition→stage triggers | [Download ZIP](https://github.com/RevCentricGH/supersdr/releases/download/latest/apollo-account-setup.zip) |
| [client-spot](client-spot/) | Generate a complete multi-tab Single Point of Truth (SPOT) Google Doc for a new client — campaign status, company overview, problem/solution, ICP, competitive landscape, objections, screenplay, and Apollo campaign setup | [Download ZIP](https://github.com/RevCentricGH/supersdr/releases/download/latest/client-spot.zip) |
| [cold-calling-screenplay](cold-calling-screenplay/) | Generate a verbatim cold call screenplay (Short or Full version) for any B2B company — pulls live case studies from the client's website automatically | [Download ZIP](https://github.com/RevCentricGH/supersdr/releases/download/latest/cold-calling-screenplay.zip) |
| [tam-contact-mapper](tam-contact-mapper/) | Apply a client's ICP filters in Apollo's People tab and save the search as a named TAM view — broad contact universe, no enrichment, stays in Apollo | [Download ZIP](https://github.com/RevCentricGH/supersdr/releases/download/latest/tam-contact-mapper.zip) |
| [list-builder](list-builder/) | Build an enriched, intent-scored, dial-ready contact list from the client's SPOT doc — uses Apollo MCP for sourcing/enrichment, Claude inline for ICP qualification, Layer 4 signal research, and 7-bucket hook generation. Outputs a Google Sheet with channel routing per contact (Red Hot / Hot / Warm / Cool / Cold) | [Download ZIP](https://github.com/RevCentricGH/supersdr/releases/download/latest/list-builder.zip) |
| [apollo-campaign-builder](apollo-campaign-builder/) | Set up all 7 outreach sequences + 4 workflow plays for a new client in the Apollo UI using browser automation (run after list-builder) | [Download ZIP](https://github.com/RevCentricGH/supersdr/releases/download/latest/apollo-campaign-builder.zip) |
| [objection-drill](objection-drill/) | Cold call objection handling trainer — Quick Drill or Live Roleplay modes across the 5 core objection families | [Download ZIP](https://github.com/RevCentricGH/supersdr/releases/download/latest/objection-drill.zip) |
| [client-proposal-doc-builder](client-proposal-doc-builder/) | Build a send-ready outbound agency proposal (DFY Calling, cold email, or combined outbound) as a Google Doc from a discovery-call transcript — includes pricing tiers, completed-conversations model, T&Cs, and signature block | [Download ZIP](https://github.com/RevCentricGH/supersdr/releases/download/latest/client-proposal-doc-builder.zip) |

## Stay updated

Skills improve over time. **Watch this repo** — click **Watch → Custom → Releases only** at the top of this page. GitHub will email you whenever a new version ships. Takes 10 seconds. When a release lands, re-download and re-upload the affected skill's ZIP.

---

## Setup

Complete this once before running any skills that require external connections.

**Claude Desktop App Installation** — Required to use Cowork and Code https://claude.com/download

**Project Instructions (recommended — one-time)** — enforces natural, non-AI-sounding output across all sessions

Go to Claude → Settings → Project → Instructions in Cowork and paste this:

```
Voice rules — apply to all output:
- No AI-tell openers: "Great question", "Absolutely", "Certainly", "Of course"
- No hedging: "I think", "it seems", "potentially", "it's worth noting"
- No AI vocabulary: "delve", "leverage", "utilize", "robust", "seamless", "comprehensive", "cutting-edge"
- No em-dashes. Hyphen or rewrite.
- Short paragraphs. Write like a person, not a vendor.
```

Each skill also has these rules embedded — this just ensures they apply globally even outside any skill context.

**Google Drive connector** — required by `tam-contact-mapper`, `list-builder`, and `client-proposal-doc-builder`
Go to Settings → Connectors → Google Drive in Cowork. Connect your Google account and enable edit access (read-only is not enough for the proposal builder or list-builder).

**Apollo MCP** — required by `list-builder`
Go to Settings → MCP Servers in Cowork and connect Apollo (`apollo-io`). One-time setup. The skill calls Apollo through the MCP — no API key needed in the skill itself.

**Browser automation** — required by `tam-contact-mapper` and `apollo-campaign-builder`
Go to Settings → Computer Use in Cowork and enable browser control. Log into Apollo in Chrome and keep that tab open when running these skills.

**Gmail connector** - required by `post-discovery-followup`
Go to Settings → Connectors → Gmail in Cowork and connect your Google account with send access. The skill sends the approved follow-up email through this connector, and only after you approve the recipient, subject, and body. It never sends on its own.

**Optional MCPs for `list-builder`** — each unlocks a stage of the pipeline if connected:

| MCP | What it adds |
|---|---|
| Perplexity | Richer Layer 4 signal research (otherwise falls back to native web search) |
| ZeroBounce | Real email validation (otherwise relies on Apollo's verified/unverified flag) |
| Twilio | Phone line-type detection (mobile / landline / VoIP) |
| Clay | Fallback contact enrichment when Apollo's hit rate is low |
| Common Room | Intent signals (website visitors, community engagement) |
| Smartlead / Instantly | Push the finished list directly to a cold email campaign |
| HeyReach | Push the finished list to a LinkedIn outreach sequence |
| HubSpot | Sync contacts into CRM as leads |

All optional MCPs degrade gracefully — connect whichever ones you have access to.

| Skill | Google Drive | Apollo MCP | Browser automation (Claude in Chrome) | Gmail | Other MCPs |
|---|---|---|---|---|---|
| apollo-account-setup | | | required | | |
| client-spot | | | | | |
| cold-calling-screenplay | | | | | |
| tam-contact-mapper | required | | required | | |
| list-builder | required | required | | | many optional (see table above) |
| apollo-campaign-builder | | | required | | |
| objection-drill | | | | | |
| client-proposal-doc-builder | required (write) | | | | |
| post-discovery-followup | | | required | required | |

## How to use

**Recommended (1-click per skill):**

1. Click the **Download ZIP** link next to the skill you want in the table above. You get a ZIP of just that skill folder.
2. Extract the ZIP.
3. In Claude Cowork, upload the entire extracted folder (not just SKILL.md — some skills need companion files).
4. Follow the instructions in the skill.

**Alternative (whole repo):** Click the green **Code** button at the top of this page → **Download ZIP** to grab everything, then extract and upload the folder for the skill you want.

> Some skills (`apollo-account-setup`, `apollo-campaign-builder`, `client-proposal-doc-builder`) include Python scripts and asset files that Claude needs alongside SKILL.md. Uploading the whole folder ensures nothing is missing.
>
> `list-builder` is now a single SKILL.md file — it runs entirely through MCP tools and Claude's reasoning. No scripts, no API keys to manage.

## Optional — async notifications via Channels

If you want to interact with the skills from your phone (Telegram, Discord, iMessage) or trigger them via webhooks from services like Smartlead, see [CHANNELS.md](CHANNELS.md). Skip this entirely if you only use Cowork from your desktop.

## Data flow

```
apollo-account-setup (run once per Apollo account, before any campaigns)

SPOT (client-spot)
  ├── Tab 3 + Tab 4 → cold-calling-screenplay
  ├── Tab 9         → tam-contact-mapper → list-builder → apollo-campaign-builder
  └── discovery call transcript → client-proposal-doc-builder
```

Run `apollo-account-setup` once per Apollo account. Then run `client-spot` first for each client — everything else builds off it.
