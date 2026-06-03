---
name: list-builder
description: Build an enriched, dial-ready contact list from a client's SPOT doc using Apollo MCP. Pure Claude Cowork - no API keys, no scripts, no local files. Outputs a Google Sheet (or inline table) ready for downstream channel tools. Use when user says "build me a list for [client]", "dial list for [client]", "build the list", "run list builder", or "build contacts for [client]".
---

# List Builder

## Purpose

Builds a dial-ready, intent-scored contact list using a client's SPOT doc as the ICP source and Apollo MCP for sourcing + enrichment. Outputs a Google Sheet (or inline table) with email status, phone line-type, fit score, intent score, urgency tier, and a hook per contact. Everything runs through MCP tools - no scripts, no API keys, no local files.

_Cowork skill - upload the ZIP and run from the Claude desktop app._

---

## Getting started

When this skill is loaded, greet the user:

> "I'm the List Builder. I'll pull enriched, dial-ready contacts from Apollo using your client's ICP from their SPOT doc.
>
> Tell me the client name - I'll find the SPOT doc and run the full pipeline."

---

## Prerequisites (check at startup)

Required MCPs the user must have connected to their Claude account:
- **Apollo MCP** (`apollo-io`) - sourcing + contact enrichment

Optional MCPs - each adds a stage to the pipeline if connected, otherwise that stage is skipped or downgraded:

| MCP | What it adds |
|---|---|
| **Google Drive / Sheets** | SPOT doc reading + Google Sheet output |
| **ZeroBounce** | Email validation (replaces "trust Apollo's verified status" with a real deliverability check) |
| **Twilio** | Phone line-type detection (mobile / landline / VoIP) via Twilio Lookup |
| **Perplexity** | Richer signal research in Layer 4 |
| **Clay** | Additional enrichment passes if Apollo's hit rate is low |
| **Common Room** | Intent signals (website visitors, community engagement) for Layer 4 |
| **Smartlead** / **Instantly** | Push the final list to a cold email campaign in one step |
| **HeyReach** | Push the final list to a LinkedIn outreach sequence in one step |
| **HubSpot** | Sync the final contacts into CRM as leads |

Detect what's available at startup. Use what you have. Don't ask the user to set things up they don't need.

If Apollo MCP isn't available, stop and tell the user:

> "Apollo MCP isn't connected. Add it in Claude → Settings → MCP Servers → Apollo. Then ask me again."

Don't try to substitute - Apollo is the core dependency.

---

## Getting started

Parse the client name from the user's message. If missing, ask once: "Which client?"

Find the SPOT doc:
1. User pasted a Google Docs URL → use that
2. Search Drive for "{Client Name} SPOT" or "{Client Name} Single Point of Truth"
3. Nothing found → "No SPOT doc for [Client]. Run `/client-spot` first to create one, or paste the link."

Read **Tab 9 (Apollo Campaign Setup)** from the SPOT doc - that tab is built specifically to feed this skill. Tab 5 (ICP & Buyer Persona) is the fallback if Tab 9 is incomplete.

Extract the ICP into context (no file needed - just hold it):
- target_titles (Primary decision-makers + Secondary influencers)
- employee_range (e.g. 11-50, 51-200, 201-500)
- locations (countries/regions)
- industries (Apollo tag matches)
- tech_signals (include - confirms ICP fit)
- exclusions: competitor domains, do-not-target titles, red-flag company types
- apollo_label_id (if the SPOT lists one - TAM mode; otherwise fresh mode)

Show one confirmation:
> "Pulled ICP from [Client] SPOT doc. Building [N] contacts from Apollo - [TAM/fresh] mode. Go?"

Default batch: 100.

---

## Pipeline

All stages run inline using MCP tools and Claude's reasoning. No external scripts.

### Stage 1 - Source contacts (Apollo MCP)

Call Apollo MCP's people search tool with the extracted filters. Use the appropriate Apollo MCP tool for the mode:
- **TAM mode**: pull contacts from the saved label / list ID
- **Fresh mode**: live search with person_titles, employee ranges, locations, tech signals

Page until you hit the batch size.

### Stage 2 - Heuristic ICP scoring (inline)

Score each contact 0-100. Baseline 50, then add/subtract:

**Domain signals**
- `.ai` TLD → +15
- `.io` / `.dev` / `.xyz` / `.app` → +5

**Company name**
- Contains "AI" as word → +10
- Contains "labs" / "intelligence" / "cognition" / "llm" → +5
- Contains "copilot" / "agent" / "gpt" → +8

**Industry**
- AI / ML → +15
- Software / IT → +5

**Employee count**
- <50 → +10
- 50-199 → +5
- 500-1999 → -5
- 2000+ → -15

**Funding stage**
- Seed / Series A → +5
- Series D+ / IPO / Public → -5

**Title seniority**
- C-suite (CTO, CEO, Chief X) → +10
- VP / Head of → +7
- Director → +4
- ML / AI / LLM / Prompt in title → +3

Clamp to 0-100. Assign tiers:
- ≥75 → Tier 1
- 50-74 → Tier 2
- <50 → Tier 3 (drop)

### Stage 3 - ICP qualification on a sample (inline web research, Tier 1+2 only)

Don't qualify the whole list yet. Take the first 10-15 Tier 1+2 contacts (highest Fit Score first) as a sample. For the unique companies in that sample, do a quick check against the SPOT's ICP description and exclusions. Drop:
- Frontier LLM builders, LLM router/gateway competitors
- Universities, research labs
- VC funds, consulting agencies
- Hardware/semiconductor companies
- Government, non-commercial foundations
- Tiny hobby projects (1-2 person)
- Anything matching the SPOT doc's explicit exclusion list

Record one short reason for every kept and every dropped contact in the sample - this is what the operator confirms next.

Use native web search. If Perplexity MCP is connected, use that for richer checks.

### Stage 4 - Sample confirm-then-scale checkpoint

Stop here. The reveal and Layer 4 enrichment are the expensive stages, so don't spend them on a wrong ICP read. Show the operator the sample split and wait.

Show kept vs dropped for the sample, with the one-line reason on each:

> Qualified a sample of [N] Tier 1+2 contacts against [Client]'s ICP.
>
> Kept ([K]):
>   - [Name], [Title] @ [Company] - [reason]
>   - ...
>
> Dropped ([D]):
>   - [Name], [Title] @ [Company] - [reason]
>   - ...
>
> Confirm to lock this read and scale to the rest, or tell me what to tune (exclusions, scoring weights, target titles).

Wait for the operator. Two paths:
- **Confirm** - lock the scoring weights and exclusion list exactly as they stand, then continue.
- **Tune** - the operator adjusts exclusions, scoring weights, or target titles. Re-score the sample (Stage 2) and re-qualify it (Stage 3) under the new criteria, show the updated split, and ask again. Loop until they confirm.

Once locked, apply the locked criteria to the full Tier 1+2 list: re-run Stage 2 scoring and Stage 3 qualification across every remaining contact, dropping the same way the sample did. The locked criteria, not the originals, govern the full list. The contacts that survive are the only input to the reveal and enrichment stages below - that's how a wrong ICP read stops costing enrichment spend.

### Stage 5 - Reveal contact info (Apollo MCP)

For contacts with locked emails, call Apollo MCP's enrich/match tool to reveal email + phone. Apollo MCP returns its own email status (verified/unverified) - keep it as a first-pass signal, but the next stage does the real validation if the right MCPs are connected.

### Stage 6 - Validate emails + phones (optional MCPs)

This stage runs only if the relevant MCPs are connected. If neither is, mark everything as "Not validated - dial and see" and continue.

**Email validation (ZeroBounce MCP):**
- For every contact with an email, call ZeroBounce's `validate_email` (single) or `validate_email_batch` (bulk) tool
- Map results: `valid` → Email Ready = true; `catch-all` → Email Ready = true (lower confidence); `invalid` / `do_not_mail` / `spamtrap` → Email Ready = false; `unknown` → Email Ready = false but keep the row
- Drop rows with `invalid` emails AND no phone

**Phone line-type (Twilio MCP):**
- For every contact with a phone, call Twilio Lookup's phone number lookup tool with `line_type_intelligence` enabled
- Map: `mobile` → MOBILE; `landline` → LANDLINE; `voip` / `nonFixedVoip` → VOIP; 404 → INVALID
- Phone Ready = MOBILE or LANDLINE (VoIP usually has low connect rate - flag but don't drop)

If a user has Clay MCP connected and Apollo's enrichment hit rate was low (<40%), offer to run a Clay enrichment pass on the unrevealed contacts before validating.

### Stage 7 - Layer 4 enrichment (Tier 1 only)

For each Tier 1 contact, do signal research and apply compound intent scoring. This is the most expensive step in the pipeline, so it runs only on the contacts that survived the locked criteria.

**Use parallel sub-agents.** Layer 4 is research-heavy - sequential web search across 30+ unique companies is slow and burns context. Spawn parallel sub-agents instead:

- Batch Tier 1 contacts by unique company (typically 30-50 companies for a 100-contact pull)
- Split into 4-6 batches of ~5-10 companies each
- Spawn one sub-agent per batch using the Agent tool (`Explore` subagent type works well for read-heavy research)
- Each sub-agent's prompt: list of companies + the signal taxonomy below + instructions to return structured findings per contact
- Run all sub-agents in parallel (single message, multiple Agent tool calls)
- Synthesize results when they return

This typically cuts Layer 4 wall time by 5-10× and keeps your main context clean.

**Each sub-agent searches per company:**
- Funding round in last 90 days
- Hiring signals (engineering / sales / leadership scaling)
- Job change for the contact specifically (14-45 days in role = sweet spot)
- Tech stack changes
- Product launches / news
- Self-authored content from the contact (for hooks)

If Perplexity MCP / Apollo MCP / other research tools are connected, sub-agents use them automatically - they inherit the user's MCP environment.

Load `reference/output-schema.md` for the INTENT_SCORE formula, urgency tier thresholds, and hook bucket framework. Apply them here.

---

### Stage 8 - Output

**If Google Sheets MCP is connected:** Create a new sheet titled `{Client} List - {date}` and write all rows. Share the URL with the user.

**Otherwise:** Output as a markdown table inline. Offer to write it to a CSV file using the local file tools if the user wants.

Either way, the column schema is the same. This is the contract downstream channel tools read.

### Stage 9 - Push to downstream channel (optional)

After the sheet/CSV is written, check which campaign MCPs are connected. If any are available, ask:

> "List is ready. Want me to push it directly to [Smartlead / Instantly / HeyReach / HubSpot]?"

If yes:

- **Smartlead MCP** → create a new campaign named `{Client} - {date}` and upload all `Email Ready = true` contacts. Default to paused state for safety.
- **Instantly MCP** → same pattern. Always start paused.
- **HeyReach MCP** → for LinkedIn outreach. Push contacts where `LinkedIn Ready = true` into a new sequence.
- **HubSpot MCP** → create contacts in CRM with lead source tagged as the client list. Useful for tracking even without immediate outreach.

If multiple are connected, offer them as a multi-select. Always default to paused/draft state - the user reviews before activating.

If no campaign MCPs are connected, skip this stage. Just tell the user where the sheet is.

### Output schema (the contract)

See `reference/output-schema.md` for the full column definitions, urgency tier thresholds, intent score formula, and hook bucket framework. Load it before Stage 8.

---

## Final summary to the user

Include a Mermaid funnel diagram showing how contacts moved through each stage. Cowork renders this natively - the user sees the drop-off visually instead of just reading numbers.

````
Built [N] contacts for [Client].

```mermaid
flowchart LR
    A[Apollo Pull<br/>{total}] --> B[After Tier Filter<br/>{after_tier}]
    B --> C[After ICP Qual<br/>{after_qual}]
    C --> D[After Reveal<br/>{revealed} emails]
    D --> E[Email Valid<br/>{valid_email}]
    E --> F[Phone Mobile/Landline<br/>{good_phone}]
    F --> G[Ready to Dial<br/>{ready}]
    style A fill:#e1f5ff
    style G fill:#c8e6c9
```

Channel readiness:
  Email valid:    [X] ([pct]%)
  Phones found:   [X] ([pct]%)
  LinkedIn URLs:  [X] ([pct]%)

Layer 4 enrichment (Tier 1, [N] contacts):
  Red Hot:   [X] (<1hr SLA - escalate to AE)
  Hot:       [X] (<24hr SLA - personalized sequence)
  Warm:      [X]
  Cool:      [X]
  Cold:      [X]

Strong hooks found: [X]

Top intent signals:
  1. [Company A] - [signal summary]
  2. [Company B] - [signal summary]
  3. [Company C] - [signal summary]

Output: [Google Sheet URL] or [CSV path or "inline above"]

Next: Red Hot needs AE attention today. Hot contacts → sequence today.
````

Fill the diagram's `{placeholder}` values from the actual stage counts. If a stage was skipped (e.g. no email validation MCPs), omit that node and reconnect the arrows.

---

## Gotchas

- **Persistent dedup across runs**: no local cache. Use Apollo's contact tagging or `already_contacted` filters to suppress prior outreach. Tag contacts from previous lists so they're excluded on the next pull.
- **Apollo MCP hit rate low (<40%)**: offer a Clay enrichment pass on unrevealed contacts before proceeding to validation.
- **Layer 4 wall time**: always spawn parallel sub-agents for Tier 1 enrichment - sequential web search across 30+ companies is too slow and burns context.

---

## No SPOT doc yet?

If the client doesn't have a SPOT doc:

> "No SPOT doc found for [Client]. Run `/client-spot` first to generate one - it'll capture the ICP, exclusions, target titles, and everything else this skill needs."

Don't accept ad-hoc ICP via chat for ongoing work. The SPOT doc is the source of truth; if it's not there, build it first.

If the user really wants a quick one-off list without a SPOT doc, you can take the ICP details inline (titles, size, location, exclusions) and proceed - but surface this as a one-time path and recommend creating a SPOT doc after.

---

## Voice Rules

Apply to all Claude-authored output - greetings, confirmations, stage summaries, error messages.

- No AI-tell openers: "Great question", "Absolutely", "Certainly", "Of course"
- No hedging: "I think", "it seems", "potentially", "it's worth noting"
- No AI vocabulary: "delve", "leverage", "utilize", "robust", "seamless", "comprehensive"
- No em-dashes. Hyphen or rewrite.
- Short. Direct. One idea per sentence.
