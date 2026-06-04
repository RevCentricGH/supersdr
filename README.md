# SuperSDR Skills

The ultimate toolkit of AI skills for running your AI-native cold-calling agency. Specifically curated for the SuperSDR community and supported by RevCentric.

Each skill teaches Claude to do one piece of the job such as: research a client, write a call script, build a dial-ready list, set up campaigns, follow up after a call, and track results.

## What this is

This toolkit covers the two jobs that make up the business:

1. **Win a client.** Land an agency customer: prep for the call, follow up after discovery, and send the proposal.
2. **Run outbound.** Do the calling work for that client: set up Apollo, build the client brief, write the pitch, build the list, launch campaigns, and track performance.

Each skill is self-contained. You can run one on its own, or run several in sequence to cover a whole motion. Start with one skill and add more as you get comfortable.

## How it works (the 60-second model)

Four things to know:

- **A skill is a packaged job.** It is a folder of instructions (and sometimes helper files) that teaches Claude exactly how to do one task the SuperSDR way. You do not configure anything in code.
- **You run skills inside Claude.** Most run in the Claude Cowork desktop app: download the skill's ZIP, upload the folder into a chat, and follow the prompts. 
- **Two motions.** The skills split into **Win a client** and **Run outbound**. Pick the motion you are in and work down the list.
- **One doc ties outbound together: the client SPOT.** A client SPOT is a client's Single Point of Truth, a multi-tab Google Doc with their positioning, ICP, and pain. You build it once per client with `client-spot`, and every other outbound skill reads from it.

Any jargon you hit along the way (ICP, TAM, disposition, sequence) is defined in the [Glossary](#glossary) at the bottom.

Here is how the outbound skills connect once the SPOT exists:

```
apollo-account-setup   (run once per Apollo account, before any campaigns)

client-spot  ->  the SPOT doc
  |
  |-- Tab 3 + Tab 4  ->  cold-calling-screenplay
  |-- Tab 7          ->  objection-drill   (optional rep training, anytime)
  |-- Tab 9          ->  tam-contact-mapper  ->  list-builder  ->  apollo-campaign-builder
  |-- activated leads ->  custom-decks
  |-- dialer calls    ->  master-tracker
```

Run `apollo-account-setup` once per Apollo account. Then run `client-spot` first for each client. Everything else builds off the SPOT.

## The autonomy ladder

Every skill sits on one of three rungs. The rung tells you what setup it needs before you start. As your comfort with AI tools grows, you climb the ladder.

- **Tier 1 · Cowork.** You upload the skill into the Claude desktop app and run it in a Cowork chat or session. No terminal, no code, nothing to install beyond the app and a few connectors that are already available in Cowork. This is where everyone starts, and most of the toolkit lives here.
- **Tier 2 · Claude Code.** The skill runs in a terminal as real software, with Python, local credentials, API connections. This rung is for jobs that need a runtime: pulling call data on a schedule, or rendering files like slide decks. You install it once and run a command. Two skills live here: `master-tracker` and `custom-decks`.
- **Tier 3 · n8n + Claude Code.** Fully automated pipelines where n8n triggers and orchestrates the work and Claude Code carries it out, with no human in the loop. This is the top rung and the direction the toolkit is heading. Nothing here yet, we are currently shipping it for RevCentric stay tuned :)

**Level up your stack.** Start at Tier 1 and get a feel for running skills in the Claude desktop app. When you want unattended reporting or branded decks, install the two Tier 2 skills. Tier 3 (n8n + Claude Code) is the horizon: the same skills, wired to run on their own. If you want a middle step toward automation, you can also push events into a live Cowork session from your phone or a webhook; see [CHANNELS.md](CHANNELS.md).

The tier is shown as a badge on every skill in the tables below.

## The skills

Skills are grouped by the job you are doing. Each row shows the skill, what it does, its tier badge, and a one-click download.

### Win a client

The acquisition motion: book the call, work the call, make the offer. The three skills run in call order, and `post-discovery-followup` hands off to `client-proposal-doc-builder` when the call ends in a proposal:

```
pre-brief  ->  discovery call  ->  post-discovery-followup
                                     |
                                     |-- proposal or follow-up outcome  ->  client-proposal-doc-builder
```

**Stage 1 - Prep for the call**

| Skill | What it does | Tier | |
|-------|-------------|------|---|
| [pre-brief](pre-brief/) | Turn a booking-call transcript into a one-page meeting brief so you walk in prepared. Pulls the concerns, objections, asks, and commitments, each anchored to the moment in the call, and returns a Google Doc. | Tier 1 · Cowork | [Download ZIP](https://github.com/RevCentricGH/supersdr/releases/download/latest/pre-brief.zip) |

**Stage 2 - After the call**

| Skill | What it does | Tier | |
|-------|-------------|------|---|
| [post-discovery-followup](post-discovery-followup/) | Read a discovery-call transcript, decide the outcome, and take the next step. On a proposal or follow-up outcome it hands off to `client-proposal-doc-builder` for the draft, sends the approved email through Gmail, and updates the deal stage in Apollo. You approve every action. | Tier 1 · Cowork | [Download ZIP](https://github.com/RevCentricGH/supersdr/releases/download/latest/post-discovery-followup.zip) |

**Stage 3 - Make the offer**

| Skill | What it does | Tier | |
|-------|-------------|------|---|
| [client-proposal-doc-builder](client-proposal-doc-builder/) | Build a send-ready outbound agency proposal from your discovery call as a Google Doc, with pricing tiers, the completed-conversations model, and T&Cs, then draft the follow-up email that sends the link. | Tier 1 · Cowork | [Download ZIP](https://github.com/RevCentricGH/supersdr/releases/download/latest/client-proposal-doc-builder.zip) |

### Run outbound

The fulfillment motion: the functional stages of running outbound for a signed client, in order.

**Stage 1 - Set up Apollo (one time)**

| Skill | What it does | Tier | |
|-------|-------------|------|---|
| [apollo-account-setup](apollo-account-setup/) | One-time Apollo setup before any campaigns: link your workspace email, register your outbound number with the Free Caller Registry, and configure the 19 dispositions, 11 contact stages, and 19 disposition-to-stage triggers. Run once per Apollo account. | Tier 1 · Cowork | [Download ZIP](https://github.com/RevCentricGH/supersdr/releases/download/latest/apollo-account-setup.zip) |

**Stage 2 - Brief the client**

| Skill | What it does | Tier | |
|-------|-------------|------|---|
| [client-spot](client-spot/) | Build the client's SPOT: a multi-tab Google Doc covering campaign status, company overview, problem and solution, ICP, competitive landscape, objections, screenplay, and Apollo campaign setup. Every outbound skill reads from it. | Tier 1 · Cowork | [Download ZIP](https://github.com/RevCentricGH/supersdr/releases/download/latest/client-spot.zip) |

**Stage 3 - Build the pitch**

| Skill | What it does | Tier | |
|-------|-------------|------|---|
| [cold-calling-screenplay](cold-calling-screenplay/) | Write a word-for-word cold call script (Short or Full version) for any B2B company, built from the client's SPOT and live case studies pulled from their website. | Tier 1 · Cowork | [Download ZIP](https://github.com/RevCentricGH/supersdr/releases/download/latest/cold-calling-screenplay.zip) |
| [objection-drill](objection-drill/) | Train reps on objections. Quick Drill gives three ready responses to a pasted objection; Live Roleplay plays the prospect, you respond, and it grades you. Covers the 5 core objection families. | Tier 1 · Cowork | [Download ZIP](https://github.com/RevCentricGH/supersdr/releases/download/latest/objection-drill.zip) |

**Stage 4 - Build the list**

| Skill | What it does | Tier | |
|-------|-------------|------|---|
| [tam-contact-mapper](tam-contact-mapper/) | Apply the client's ICP filters in Apollo's People tab and save the search as a named TAM view. Maps the full contact universe with no enrichment; nothing is imported. Run it before `list-builder`. | Tier 1 · Cowork | [Download ZIP](https://github.com/RevCentricGH/supersdr/releases/download/latest/tam-contact-mapper.zip) |
| [list-builder](list-builder/) | Build an enriched, dial-ready contact list from the SPOT using Apollo. Scores fit and intent, routes each contact by temperature (Red Hot to Cold), and outputs a Google Sheet ready to dial. | Tier 1 · Cowork | [Download ZIP](https://github.com/RevCentricGH/supersdr/releases/download/latest/list-builder.zip) |

**Stage 5 - Launch the campaigns**

| Skill | What it does | Tier | |
|-------|-------------|------|---|
| [apollo-campaign-builder](apollo-campaign-builder/) | Set up the client's full Apollo campaign: all 7 outreach sequences and 4 workflow plays, built in the Apollo UI for you. Run after `list-builder`. | Tier 1 · Cowork | [Download ZIP](https://github.com/RevCentricGH/supersdr/releases/download/latest/apollo-campaign-builder.zip) |

**Stage 6 - Advance the deal**

| Skill | What it does | Tier | |
|-------|-------------|------|---|
| [custom-decks](custom-decks/) | Terminal skill - runs in Claude Code, not Cowork (see [Claude Code path](#advanced-claude-code-path) below). Builds a tailored prospect deck from a call transcript and the prospect's website, branded as your agency, rendered to Google Slides and PDF with a View link. | Tier 2 · Claude Code | [Download ZIP](https://github.com/RevCentricGH/supersdr/releases/download/latest/custom-decks.zip) |

**Stage 7 - Track and measure**

| Skill | What it does | Tier | |
|-------|-------------|------|---|
| [master-tracker](master-tracker/) | Terminal skill - runs in Claude Code, not Cowork (see [Claude Code path](#advanced-claude-code-path) below). Pulls each rep's Apollo dialer calls into per-rep tabs of a Google Sheet, filtered to the dispositions you care about, deduped, and safe to re-run. Reads campaign health at a glance. | Tier 2 · Claude Code | [Download ZIP](https://github.com/RevCentricGH/supersdr/releases/download/latest/master-tracker.zip) |

### Work smarter

Cross-cutting utilities that improve every other skill and task.

| Skill | What it does | Tier | |
|-------|-------------|------|---|
| [grill-me](grill-me/) | A question loop for planning anything. Interviews you one question at a time until Claude fully understands the goal, inputs, outputs, and tools - then hands you a one-page brief to run in a fresh session. A sharp brief beats a smart model. | Tier 1 · Cowork | [Download ZIP](https://github.com/RevCentricGH/supersdr/releases/download/latest/grill-me.zip) |

## Getting started

Start with the Cowork path. It is the simplest and covers every Tier 1 skill, which is most of the toolkit. The Claude Code path is for the two Tier 2 skills and is kept separate below; skip it until you naturally find gaps with Cowork and you genuinely feel the need to advance. You'll know when it happens, don't overengineer for a solution or pain you don't even feel yet.

### Cowork path (start here)

**Run a skill, in four steps:**

1. Pick a skill from the tables above and click its **Download ZIP**. You get a ZIP of just that skill folder.
2. Extract the ZIP.
3. Open the Claude desktop app, start a chat, and upload the entire extracted folder, not just `SKILL.md`. Some skills need their companion files.
4. Follow the skill's prompts.

Whole-repo alternative: click the green **Code** button at the top of this page, choose **Download ZIP**, extract it, and upload the folder for the skill you want.

**One-time Cowork setup**

Do this once before running skills that reach external systems.

- **Install the Claude desktop app.** Required for Cowork. Download it at https://claude.com/download.
- **Paste the voice rules into Project Instructions (recommended).** Go to Claude, then Settings, then Project, then Instructions, and paste this so output sounds like a person across every session:

  ```
  Voice rules - apply to all output:
  - No AI-tell openers: "Great question", "Absolutely", "Certainly", "Of course"
  - No hedging: "I think", "it seems", "potentially", "it's worth noting"
  - No AI vocabulary: "delve", "leverage", "utilize", "robust", "seamless", "comprehensive", "cutting-edge"
  - No em-dashes. Hyphen or rewrite.
  - Short paragraphs. Write like a person, not a vendor.
  ```

  Each skill embeds these rules too; this just applies them globally.

- **Connect the connectors each skill needs.** A connector links Claude to an outside service.
  - **Google Drive:** Settings, then Connectors, then Google Drive. Connect your account and enable edit access (read-only is not enough for the proposal builder or list-builder).
  - **Gmail:** Settings, then Connectors, then Gmail, with send access. Used by `post-discovery-followup` to send the approved follow-up, and only after you approve the recipient, subject, and body.
  - **Apollo MCP:** Settings, then MCP Servers, and connect Apollo (`apollo-io`). The skill calls Apollo through the connector, so no API key lives in the skill.
  - **Browser automation (Claude in Chrome):** Settings, then Computer Use, and enable browser control. Log into Apollo in Chrome and keep that tab open while running these skills.

**Which connectors each skill needs:**

| Skill | Google Drive | Apollo MCP | Browser automation (Claude in Chrome) | Gmail | Other MCPs |
|---|---|---|---|---|---|
| apollo-account-setup | | | required | | |
| client-spot | | | | | |
| cold-calling-screenplay | | | | | |
| tam-contact-mapper | required | | required | | |
| list-builder | required | required | | | many optional (see below) |
| apollo-campaign-builder | | | required | | |
| objection-drill | | | | | |
| client-proposal-doc-builder | required (write) | | | | |
| post-discovery-followup | required | | required | required | |
| pre-brief | required (write) | | | | |

**Optional MCPs for `list-builder`.** Each one unlocks a stage of the pipeline if connected, and the skill degrades gracefully without it. Connect whichever you have.

| MCP | What it adds |
|---|---|
| Perplexity | Richer Layer 4 signal research (otherwise falls back to native web search) |
| ZeroBounce | Real email validation (otherwise relies on Apollo's verified flag) |
| Twilio | Phone line-type detection (mobile / landline / VoIP) |
| Clay | Fallback contact enrichment when Apollo's hit rate is low |
| Common Room | Intent signals (website visitors, community engagement) |
| Smartlead / Instantly | Push the finished list to a cold email campaign |
| HeyReach | Push the finished list to a LinkedIn outreach sequence |
| HubSpot | Sync contacts into CRM as leads |

### Advanced: Claude Code path

Skip this section if you only use the desktop app. It covers the two Tier 2 skills, `master-tracker` and `custom-decks`, which run in a terminal with real Python, local API keys, and a Google OAuth token file. **Do not upload them to Cowork.** They cannot run there.

You drive these the same way you drive any skill, by asking Claude. The only difference is the home: instead of the desktop app, you run **Claude Code** in a terminal and tell it what you want in plain English ("set up master-tracker", "build a deck for this prospect"). Claude Code does the terminal work, so you should never have to type raw commands to run a skill.

**Install your terminal and agent (one time).**

- **Warp** - the terminal we recommend. It is an AI terminal, so on the rare command Claude Code cannot run itself (an interactive login, a bit of debugging) Warp can help you directly. Download the desktop app at https://www.warp.dev/download and sign in.
- **Claude Code** - the agent that runs the skills. Open Warp, install it with `curl -fsSL https://claude.ai/install.sh | bash`, then type `claude` to launch it and sign in. (Docs: https://code.claude.com/docs/en/setup.)

That install command is the only thing you type by hand. From here on you talk to Claude Code.

**Credentials.** These come from web dashboards, so you grab them yourself, then paste them to Claude Code and it writes them into the skill's `config.json` for you.

- **Apollo API key** - required by both skills for call data and contact lookup. Apollo, then Settings, then Integrations, then API.
- **Google OAuth token** - required by both to read and write Google Sheets and Drive. Each skill walks you through the OAuth setup and needs its own `token.json`.
- **Deepgram API key** - required by `custom-decks` for audio transcription. Sign up at deepgram.com.
- **Groq API key** - required by `custom-decks` as a transcription fallback; fires only when Deepgram returns empty. Sign up at console.groq.com.

**Run it.** With Claude Code open in the skill's folder, ask it to "set up and run master-tracker" or "build a custom deck for this prospect". It installs the dependencies, fills in `config.json` from the credentials you pasted, and runs the skill.

Prefer to run the commands yourself? Here is what Claude Code does under the hood:

```bash
# master-tracker
cd master-tracker
pip install -r requirements.txt
cp config.template.json config.json   # fill in your credentials
python3 run.py

# custom-decks (also needs Node and Marp for deck rendering)
cd custom-decks
pip install -r requirements.txt
npm install -g @marp-team/marp-cli
cp config.template.json config.json   # fill in your credentials
python3 run.py
```

## Recommended path by situation

- **Brand-new agency, no clients yet.** Run the **Run outbound** pipeline on yourself to book your first meetings, with your own agency as the client: `apollo-account-setup`, then `client-spot` for your own offer, then down the stages. Use **Win a client** to work the calls you book.
- **Just signed a client.** Move to **Run outbound** and work the stages in order. Run `apollo-account-setup` once (only the first time on a new Apollo account), then `client-spot` to build the SPOT, then down the list: pitch, list, campaigns.
- **Already running campaigns.** Install `master-tracker` (Tier 2) to pull call data into a sheet and read campaign health. Use `custom-decks` (Tier 2) to build decks for prospects who are warming up.
- **Debugging a campaign that is not working.** Re-read the SPOT first; weak positioning shows up everywhere downstream. Re-run `list-builder` on a small sample to sanity-check the ICP before scaling. Check `master-tracker` for conversion rates by rep. If reps stall on calls, run `objection-drill`.

## Glossary

Plain-language definitions of the jargon you will hit.

- **Skill** - a packaged job for Claude: a folder with instructions and sometimes helper files. You run it; you do not edit it.
- **Cowork vs Claude Code** - two ways to run a skill. **Cowork** is the Claude desktop app, where you upload a skill and run it in a chat (Tier 1). **Claude Code** is the terminal, where a skill runs as real software (Tier 2).
- **SPOT** - a client's Single Point of Truth: the multi-tab Google Doc holding their positioning, ICP, and pain. Built once per client by `client-spot`; the outbound skills read from it.
- **ICP** - Ideal Customer Profile: the type of company and person a client wants to reach (industry, size, title, signals). It drives who lands on the dial list.
- **TAM** - Total Addressable Market: the full universe of contacts that fit the ICP. `tam-contact-mapper` saves this as an Apollo search before any enrichment.
- **Dialer** - the software reps use to make calls. In this toolkit, reps dial in Apollo's dialer, which logs each call.
- **Disposition** - the outcome you tag on a call (for example "Connected - Meeting Booked" or "No Answer"). `apollo-account-setup` configures the standard set, and `master-tracker` filters and counts by disposition.
- **MCP connector** - a link that lets Claude talk to an outside service (Apollo, Google Drive, Gmail) without you handing it an API key inside a skill. You connect it once in settings.
- **Browser automation (Claude in Chrome)** - Claude controlling a real Chrome tab to click through a web app, used for the Apollo UI work where there is no connector.
- **Sequence and workflow play** - Apollo outreach building blocks. A sequence is a series of steps (calls, emails) a contact moves through; a workflow play automates an action when a condition is met. `apollo-campaign-builder` sets these up.

## Cost

What you pay for, plain:

- **A paid Claude plan (required).** Cowork runs in the Claude desktop app, which needs a paid Claude subscription. The two Tier 2 skills also use your Claude access from the terminal. This is the one cost everyone has. Start with the pro plan, if you start maxing out your usage quickly upgrade to Max.
- **An Apollo plan (required for outbound).** Apollo provides the database, contact data, and the MCP connector. A paid Apollo plan is what the outbound skills run on.
- **Optional add-ons (only if you connect them).** The Tier 2 `custom-decks` skill uses Deepgram and Groq for transcription, both with free tiers and pay-as-you-go pricing. The `list-builder` optional MCPs (ZeroBounce, Twilio, Clay, Perplexity, and the rest) are each separate accounts you only pay for if you turn them on. Everything optional degrades gracefully when it is off, so you can start with none of them.

You do not pay this project anything. The skills are free and open. Your only costs are the third-party accounts above.

## Compliance

Outbound calling is regulated. You are responsible for running it legally. A few things to get right before you dial:

- **Call-recording consent.** Some jurisdictions require every party on a call to consent before you record. Know the rules where you and the prospect are, and get consent when it is required.
- **Do Not Call.** Honor Do Not Call lists and any opt-out a prospect gives you. `list-builder`'s dial-ready gate excludes do-not-call and already-pulled contacts, but the responsibility to scrub and honor DNC and suppression is yours.
- **This is not legal advice.** Rules vary by country, state, and industry. When in doubt, check with counsel before launching a campaign.

## Stay updated, contributing, and license

**Stay updated.** Skills improve over time. Watch this repo: click **Watch**, then **Custom**, then **Releases only** at the top of this page. GitHub emails you whenever a new version ships. When a release lands, re-download and re-upload the affected skill's ZIP. All releases live at https://github.com/RevCentricGH/supersdr/releases.

**Contributing.** Found a bug or have an improvement? Open a GitHub issue, or send a pull request. Note that everything in this repo ships publicly as per-skill ZIPs, so do not commit anything private.

**License.** These skills are published openly for the SuperSDR community. Anything committed here is public. No formal license is attached yet; if you plan to reuse the skills outside the community, open an issue to ask.
