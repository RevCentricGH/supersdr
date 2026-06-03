---
name: client-spot
description: Generate a client single point of truth (SPOT) document - multi-tab Google Doc covering campaign status, company overview, problem/solution, ICP, competitive landscape, objections, screenplay, and Apollo campaign setup. One-shot generation that pulls from onboarding call transcripts, meeting summaries, and web research. Use when user says "create SPOT doc for [client]", "build the client KB for [client]", "set up SPOT for [client]", "generate client brief for [client]", "onboard [client]", or pastes a client onboarding transcript / meeting notes and asks to turn it into a SPOT.
---

# Client SPOT Skill

## Purpose

One-shot generates a complete single point of truth document for a new client, structured as 9 separate tabs.

The skill takes whatever info is in the trigger message, pulls the rest via web search, and outputs all 9 tabs in a single response. No clarifying questions, no back-and-forth. Anything not findable becomes `[TBD]`.

The output is organized tab-by-tab so the user can create each tab in Google Docs and paste the matching content block.

**Runtime: Claude Cowork**

## Downstream consumers

The SPOT is incomplete if either of these skills can't run cleanly off it:

| Skill | Tabs it reads | What it needs |
|---|---|---|
| `list-builder` + `apollo-campaign-builder` | Tab 5, Tab 9 | ICP filters, keyword passes, tech signals, exclusion lists, target titles |
| `cold-calling-screenplay` | Tab 3, Tab 4 | Status markers, insider pain in symptomese, structural differentiator, persona context |

Treat both as the readers when generating. Don't write generic copy - make every field actionable.

---

## Getting started

When this skill is loaded, greet the user:

> "I'm the Client SPOT skill. I'll build a complete knowledge base for your new client.
>
> Share meeting notes from your strategy call with them - an onboarding call, a post-closing call, or any combination of calls. Paste them in, or share a doc/transcript link.
>
> If you don't have notes yet, just give me the client's name and website and I'll do deep research instead - I'll spawn parallel research agents to dig into their product, customers, competitors, and market."

**If the user provides meeting notes or a transcript** → proceed with the standard Workflow (Step 1 onward), using the notes as the highest-priority input.

**If the user provides only a name and/or website (no first-party material)** → switch to deep research mode. Spawn multiple Explore subagents in parallel to research the company from different angles - product/positioning, customers/case studies, competitors, funding, market context, target buyer pain. Synthesize results into the SPOT.

---

## Workflow - One-Shot Generation

This skill generates the full 9-tab SPOT doc in a single response. Do not ask the user clarifying questions before generating. Extract everything possible from inputs (trigger message, attached transcripts, meeting summaries) and web research, then output all 9 tabs.

### Input priority

Use these sources in order. Earlier sources override later ones - first-party client info beats web research every time.

1. **Onboarding meeting transcripts or recordings (highest priority)** - anything pasted, attached, or referenced from a kickoff call, discovery call, or onboarding meeting. This is direct client voice and beats anything else.
2. **Meeting summaries / call notes** - Gemini summaries, Fireflies notes, manual notes from client calls. Lower fidelity than raw transcripts but still first-party.
3. **Trigger message details** - anything you typed directly into the prompt
4. **Web research (fallback)** - only used to fill gaps left by 1–3

### Step 1 - Extract from provided client material

If the user pasted or attached a transcript, summary, or meeting notes, extract:
- Client's exact words on what they do, who they sell to, why now
- Pain points they described in their own customers' words
- Competitors they mentioned (direct and indirect)
- Objections they expect to hear or have already heard
- ICP signals: titles they want targeted, companies to avoid, geo, size
- Messaging the client wants used (or specifically does NOT want)
- Open questions or unresolved items raised on the call
- Names of contacts at the client (founders, ops, engineering)

Quote directly from the transcript when possible - these become the highest-credibility lines in the SPOT doc.

### Step 2 - Extract what else is in the trigger message

Pull anything you typed: client name, website, campaign type, anything else not in the transcript.

### Step 3 - Research to fill remaining gaps

**If meeting notes or a transcript were provided:** run a light pass of 4–6 web searches to fill remaining gaps.
- "[Client name] company" → website, what they do, headquarters, founders
- "[Client name] customers" → notable logos, case studies
- "[Client name] funding" → backers, latest round, total raised
- "[Client name] competitors" → market positioning
- "[Client name] [target buyer title]" → buyer persona context

**If no first-party material was provided (deep research mode):** spawn parallel Explore subagents to dig deeper from multiple angles in one shot. Recommended split:

- Agent 1: Product, positioning, founding story, traction milestones (read their site + recent press)
- Agent 2: Customers and case studies (logos, named results, segments served)
- Agent 3: Competitors and market positioning (direct, indirect, build-in-house)
- Agent 4: Target buyer pain in symptomese (what does the buyer's Tuesday afternoon actually look like - search forums, podcasts, LinkedIn, review sites)

Synthesize agent reports into the SPOT. No search cap in deep research mode - it's the substitute for first-party material.

### Step 4 - Generate all 9 tabs in one response

Output every tab as its own labeled code block. Mark anything still unknown as `[TBD]`. Do not pause mid-generation to confirm.

When a transcript was provided, add a line at the top of Tab 1 (Campaign Status) under Key Direction:
```
SOURCE: Onboarding call with [client contact name] on [date]
```

### Step 5 - Hand off

After all 9 tabs are output, append the hand-off instructions at the bottom.

If the trigger message gave nothing but a client name, generate anyway with web research and `[TBD]` covering the rest. The user can edit before pasting into Docs.

---

## Tab Structure (9 tabs)

| # | Tab Name | Purpose | Downstream consumer |
|---|----------|---------|---------------------|
| 1 | Campaign Status | Living tab - action items, open questions, call feedback, meetings booked | Operator |
| 2 | Campaign Brief | Executive summary - snapshot + contents + version history | Operator |
| 3 | Company Overview | Positioning, differentiator, awards, customers | Screenplay (status thumbnail) |
| 4 | Problem / Solution Overview | Status markers, change in world, day-in-the-life pain, big question, UVP, measurable impact | Screenplay (full pitch) |
| 5 | ICP & Buyer Persona | Apollo keywords, firmographics, tech signals, exclusions, target titles | Apollo Campaign Builder |
| 6 | Competitor Overview & Battlecards | Direct, indirect, build-in-house, battlecards | Operator + screenplay objection handling |
| 7 | Objection Handling | Objection → response table | Operator + cold email reply handling |
| 8 | Screenplay | Cold call main pitch (use cold-calling-screenplay skill) | Operator |
| 9 | Apollo Campaign Setup | Structured ICP and messaging brief - feeds directly into the Apollo Campaign Builder skill | Apollo Campaign Builder |

---

## Tab Content Templates

The full field-by-field templates for all 9 tabs are in `reference/tab-templates.md`. Load this file when generating tab content in Step 4.


## Hand-off Instructions

After generating all 9 tabs, do the following automatically - do not wait to be asked:

### Step 1 - Tell the user what to do with the Google Doc

```
Next steps:
1. Open Google Docs and create a new doc titled "[Client Name] Single Point of Truth"
2. Enable tabs: Insert → Tabs (or right-click in the left sidebar)
3. Create 9 tabs: Campaign Status / Campaign Brief / Company Overview / Problem Solution / ICP & Buyer Persona / Competitor Overview / Objection Handling / Screenplay / Apollo Campaign Setup
4. Paste each content block into the matching tab
5. For Tab 8 (Screenplay): run the cold-calling-screenplay skill using Tabs 3 and 4 as input
6. For Tab 9 (Apollo Campaign Setup): run list-building first (builds the contact list), then apollo-campaign-builder (sets up 7 sequences and 4 workflow plays)
```

### Step 2 - Flag any [TBD] blockers

Scan all generated tabs for `[TBD]` values. Flag any that block the downstream skills from running:

```
Blockers — fill these before running downstream skills:
- [field]: [TBD]
```

Critical for Apollo Campaign Builder: Target Titles, Employee Range, Locations, Keyword Passes.
Critical for Screenplay: Status Markers (Tab 4.1), Day-in-life pain (Tab 4.3), Big Question (Tab 4.6).

---

## Voice Rules

Apply to all Claude-authored output - greetings, hand-off instructions, blocker flags, questions.

- No AI-tell openers: "Great question", "Absolutely", "Certainly", "Of course"
- No hedging: "I think", "it seems", "potentially", "it's worth noting"
- No AI vocabulary: "delve", "leverage", "utilize", "robust", "seamless", "comprehensive"
- No em-dashes. Hyphen or rewrite.
- Short. Direct. One idea per sentence.
