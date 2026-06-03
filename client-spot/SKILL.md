---
name: client-spot
description: Generate a client single point of truth (SPOT) document - multi-tab Google Doc covering campaign status, company overview, problem/solution, ICP, competitive landscape, objections, screenplay, and Apollo campaign setup. Pulls from onboarding call transcripts, meeting summaries, Google form responses, and web research. Use when user says "create SPOT doc for [client]", "build the client KB for [client]", "set up SPOT for [client]", "generate client brief for [client]", "onboard [client]", or pastes a client onboarding transcript / meeting notes and asks to turn it into a SPOT.
---

# Client SPOT Skill

## Purpose

Generates a complete single point of truth document for a new client, structured as 9 separate tabs in a Google Doc.

The skill pulls from the trigger message, attached transcripts, Google form responses, and optionally web research, then generates all 9 tabs in one pass and creates the Google Doc via MCP.

**Runtime: Claude Cowork**

## Downstream consumers

The SPOT is incomplete if either of these skills can't run cleanly off it:

| Skill | Tabs it reads | What it needs |
|---|---|---|
| `list-builder` + `apollo-campaign-builder` | Tab 5, Tab 9 | ICP filters, keyword passes, tech signals, exclusion lists, target titles |
| `cold-calling-screenplay` | Tab 3, Tab 4 | Status markers, insider pain in symptomese (high-sensory insider language, not generic pain), structural differentiator, persona context |

Treat both as the readers when generating. Don't write generic copy - make every field actionable.

---

## Getting started

When this skill is loaded, greet the user:

> "I'm the Client SPOT skill. I'll build a complete knowledge base for your new client and create the Google Doc.
>
> Share what you have - onboarding call notes, a Google form response, a transcript, or just the client's name and website. Paste it in directly.
>
> Do you want me to run web research to fill any gaps?"

Wait for the user's answer before proceeding. If they say yes to web research, run it in Step 3. If no, skip Step 3.

If the user provides only a client name and/or website with no first-party material, do not ask - tell them research will run and proceed with full deep research automatically.

---

## Workflow

### Input priority

Use these sources in order. Earlier sources override later ones.

1. **Onboarding meeting transcripts or recordings (highest priority)** - anything pasted, attached, or referenced from a kickoff call, discovery call, or onboarding meeting.
2. **Google form responses** - client intake forms, onboarding questionnaires.
3. **Meeting summaries / call notes** - Gemini summaries, Fireflies notes, manual notes from client calls.
4. **Trigger message details** - anything typed directly into the prompt.
5. **Web research (fallback, only if user said yes)** - used to fill gaps left by 1–4.

### Step 1 - Extract from provided client material

Pull from everything the user shared:
- Client's exact words on what they do, who they sell to, why now
- Pain points described in their own customers' words
- Competitors mentioned (direct and indirect)
- Objections they expect to hear or have already heard
- ICP signals: titles they want targeted, companies to avoid, geo, size
- Messaging the client wants used (or specifically does NOT want)
- Open questions or unresolved items
- Names of contacts at the client (founders, ops, engineering)

Quote directly from transcripts or form responses when possible.

### Step 2 - Extract what else is in the trigger message

Pull anything typed in: client name, website, campaign type, anything not in the attached material.

### Step 3 - Web research (only if user said yes)

**If meeting notes, a transcript, or form responses were provided:** run a light pass of 4–6 web searches to fill remaining gaps.
- "[Client name] company" → website, what they do, headquarters, founders
- "[Client name] customers" → notable logos, case studies
- "[Client name] funding" → backers, latest round, total raised
- "[Client name] competitors" → market positioning
- "[Client name] [target buyer title]" → buyer persona context

**If no first-party material was provided (deep research mode):** skip the web research question - research is not optional when there is no other input. Tell the user you're running full research and proceed. Spawn parallel Explore subagents to dig deeper from multiple angles in one shot. Recommended split:

- Agent 1: Product, positioning, founding story, traction milestones (read their site + recent press)
- Agent 2: Customers and case studies (logos, named results, segments served)
- Agent 3: Competitors and market positioning (direct, indirect, build-in-house)
- Agent 4: Target buyer pain in symptomese (what does the buyer's Tuesday afternoon actually look like - search forums, podcasts, LinkedIn, review sites)

Synthesize agent reports into the SPOT. If subagents aren't available in this runtime, run the four angles as sequential web searches instead.

### Step 4 - Generate all 9 tabs in one pass

Generate all 9 tabs in a single response. Output each as its own labeled block. Mark anything still unknown as `[TBD]`. Do not pause to confirm.

When a transcript was provided, add a line at the top of Tab 1 (Campaign Status) under Key Direction:
```
SOURCE: Onboarding call with [client contact name] on [date]
```

The full field-by-field templates for all 9 tabs are in `reference/tab-templates.md`. Load this file when generating tab content.

### Step 5 - Create the Google Doc

After generating all tab content, use the Google Docs or Google Drive MCP to create the document. Execute in this order:

1. Create a new Google Doc titled "[Client Name] Single Point of Truth"
2. Add 9 tabs with these exact names (in order): Campaign Status, Campaign Brief, Company Overview, Problem Solution, ICP & Buyer Persona, Competitor Overview, Objection Handling, Screenplay, Apollo Campaign Setup
3. For each tab, write the content using proper formatting - do NOT paste raw markdown

**Formatting rules when writing to Google Docs:**
- Strip all markdown syntax before inserting. Do not write `##`, `**`, `*`, backticks, or `|` table pipes into the doc.
- Section titles (lines that were `##` or `###` headings in the generated content) → insert as plain text, then apply `HEADING_2` or `HEADING_3` paragraph style via `updateParagraphStyle`
- Field labels (e.g. `Company Name:`, `4.1 Status Markers`) → insert as plain text with bold applied via `updateTextStyle`
- Body text and list items → insert as `NORMAL_TEXT`
- Tables → convert to plain text with a label on each row (e.g. `Competitor: X | Their angle: Y | Our edge: Z`), one row per line
- After inserting text into a tab, re-read the tab to get fresh indices before applying paragraph styles

Use `addDocumentTab` to create tabs (NOT `createTab`). Insert text with `insertText` using `{"location": {"index": 1, "tabId": tab_id}}`. Apply heading styles with `updateParagraphStyle` including `tabId` in the range.

If the MCP does not support tab creation, create the doc as a single document with each section separated by a clear HEADING_1 title and notify the user that tabs must be added manually.

**If Google Doc creation fails entirely:** output all 9 tab content blocks as labeled sections in the chat so the user can paste manually, and tell them what failed.

### Step 6 - Hand off

After the Google Doc is created, share the link with the user. Then flag any `[TBD]` blockers:

```
Blockers — fill these before running downstream skills:
- [field]: [TBD]
```

Critical for Apollo Campaign Builder: Target Titles, Employee Range, Locations, Keyword Passes.
Critical for Screenplay: Status Markers (Tab 4.1), Day-in-life pain (Tab 4.3), Big Question (Tab 4.6).

Then append next steps:

```
Next steps:
- For Tab 8 (Screenplay): run the cold-calling-screenplay skill using Tabs 3 and 4 as input
- For Tab 9 (Apollo Campaign Setup): run list-building first, then apollo-campaign-builder
```

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

---

## Voice Rules

Apply to all Claude-authored output - greetings, hand-off instructions, blocker flags, questions.

- No AI-tell openers: "Great question", "Absolutely", "Certainly", "Of course"
- No hedging: "I think", "it seems", "potentially", "it's worth noting"
- No AI vocabulary: "delve", "leverage", "utilize", "robust", "seamless", "comprehensive"
- No em-dashes. Hyphen or rewrite.
- Short. Direct. One idea per sentence.
