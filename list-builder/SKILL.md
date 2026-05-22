---
name: list-builder
description: Build an enriched, dial-ready contact list from a client's SPOT doc using Apollo MCP. Pure Claude Cowork — no API keys, no scripts, no local files. Outputs a Google Sheet (or inline table) ready for downstream channel tools. Use when user says "build me a list for [client]", "dial list for [client]", "build the list", "run list builder", or "build contacts for [client]".
---

# List Builder

Builds a dial-ready contact list using the client's SPOT doc as the ICP source and Apollo MCP for sourcing + enrichment. Everything runs through MCP tools and Claude's reasoning. Zero local setup.

---

## Prerequisites (check at startup)

Required MCPs the user must have connected to their Claude account:
- **Apollo MCP** (`apollo-io`) — sourcing + enrichment

Optional but useful:
- **Google Drive / Sheets MCP** — reading the SPOT doc + writing the output sheet
- **Perplexity MCP** — richer signal research in Layer 4

If Apollo MCP isn't available, stop and tell the user:

> "Apollo MCP isn't connected. Add it in Claude → Settings → MCP Servers → Apollo. Then ask me again."

Don't try to substitute — Apollo is the core dependency.

---

## Starting

Parse the client name from the user's message. If missing, ask once: "Which client?"

Find the SPOT doc:
1. User pasted a Google Docs URL → use that
2. Search Drive for "{Client Name} SPOT" or "{Client Name} Single Point of Truth"
3. Nothing found → "No SPOT doc for [Client]. Run `/client-spot` first to create one, or paste the link."

Read **Tab 9 (Apollo Campaign Setup)** from the SPOT doc — that tab is built specifically to feed this skill. Tab 5 (ICP & Buyer Persona) is the fallback if Tab 9 is incomplete.

Extract the ICP into context (no file needed — just hold it):
- target_titles (Primary decision-makers + Secondary influencers)
- employee_range (e.g. 11-50, 51-200, 201-500)
- locations (countries/regions)
- industries (Apollo tag matches)
- tech_signals (include — confirms ICP fit)
- exclusions: competitor domains, do-not-target titles, red-flag company types
- apollo_label_id (if the SPOT lists one — TAM mode; otherwise fresh mode)

Show one confirmation:
> "Pulled ICP from [Client] SPOT doc. Building [N] contacts from Apollo — [TAM/fresh] mode. Go?"

Default batch: 100.

---

## Pipeline

All stages run inline using MCP tools and Claude's reasoning. No external scripts.

### Stage 1 — Source contacts (Apollo MCP)

Call Apollo MCP's people search tool with the extracted filters. Use the appropriate Apollo MCP tool for the mode:
- **TAM mode**: pull contacts from the saved label / list ID
- **Fresh mode**: live search with person_titles, employee ranges, locations, tech signals

Page until you hit the batch size.

### Stage 2 — Heuristic ICP scoring (inline)

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

### Stage 3 — ICP qualification (inline web research, Tier 1+2 only)

For unique companies in Tier 1+2, do a quick check against the SPOT's ICP description and exclusions. Drop:
- Frontier LLM builders, LLM router/gateway competitors
- Universities, research labs
- VC funds, consulting agencies
- Hardware/semiconductor companies
- Government, non-commercial foundations
- Tiny hobby projects (1-2 person)
- Anything matching the SPOT doc's explicit exclusion list

Use native web search. If Perplexity MCP is connected, use that for richer checks.

### Stage 4 — Reveal contact info (Apollo MCP)

For contacts with locked emails, call Apollo MCP's enrich/match tool to reveal email + phone. Apollo MCP returns email status (verified/unverified) — use that as the email validation signal.

### Stage 5 — Layer 4 enrichment (Tier 1 only)

For each Tier 1 contact, do signal research and apply compound intent scoring. This is the high-leverage step.

**Search per company:**
- Funding round in last 90 days
- Hiring signals (engineering / sales / leadership scaling)
- Job change for the contact specifically (14-45 days in role = sweet spot)
- Tech stack changes
- Product launches / news
- Self-authored content from the contact (for hooks)

If Perplexity MCP / Apollo MCP / other research tools are connected, use them automatically.

**Compound INTENT_SCORE:**
```
INTENT_SCORE = Σ (trigger_points × recency_multiplier)
```

Trigger points: job change in window 40 | funding round 35 | hiring signal 20 | tech stack change 15 | content engagement 10

Recency multipliers: yesterday 1.5× | this week 1.2× | this month 1.0× | 30+ days 0.3×

**Urgency tier:**
- 150+ → Red Hot (escalate to AE, <1hr SLA)
- 100-149 → Hot (<24hr SLA)
- 50-99 → Warm
- 20-49 → Cool
- <20 → Cold

**Top Signals:** 3-5 strongest with recency, semicolon-separated.

**Hook generation (7-bucket framework, ranked by value):**
1. Self-authored content (posts, articles, podcasts) → Strong
2. Engaged content (likes, shares) → Strong
3. Self-identified traits (LinkedIn headline) → Lite
4. Junk drawer (interests, schools) → Lite
5. Background (tenure, awards) → Lite
6. Company-level (funding, news) → Lite
7. Technographics (tools, stack) → Lite

Try in order, stop at first hit. Bucket 1-2 = Personalization Depth `strong`. Bucket 3+ = `lite`.

Red Hot requires Strong Hook — if no Bucket 1-2 found, try escalating to a different contact at the same company.

---

## Output

**If Google Sheets MCP is connected:** Create a new sheet titled `{Client} List — {date}` and write all rows. Share the URL with the user.

**Otherwise:** Output as a markdown table inline. Offer to write it to a CSV file using the local file tools if the user wants.

Either way, the column schema is the same. This is the contract downstream channel tools read.

### Output schema (the contract)

| Column | Filled by | Notes |
|---|---|---|
| First Name, Last Name, Title, Company, Company Domain | Apollo MCP | Identity |
| Email, Email Status, **Email Ready** (bool) | Apollo MCP | Email Ready = status is verified |
| Phone, **Phone Ready** (bool) | Apollo MCP | Phone Ready = number is present (no line-type detection in Cowork — see trade-offs) |
| LinkedIn URL, **LinkedIn Ready** (bool) | Apollo MCP | LinkedIn Ready = URL present |
| **Fit Score** (0-100) | Claude inline | Heuristic ICP score |
| Fit Tier (1-3) | Claude inline | Tier 1 = ≥75 |
| **Intent Score** (0-200+) | Claude inline (Tier 1 only) | Compound signal × recency |
| **Urgency Tier** | Claude inline | Red Hot / Hot / Warm / Cool / Cold |
| **Top Signals** | Claude inline | 3-5 strongest with recency |
| **Hook** | Claude inline | 1-line opener using 7-bucket framework |
| **Personalization Depth** | Claude inline | strong / lite |
| List Source Tier | SPOT doc | A / B / C (defaults to C — Apollo firmographic) |
| List Status | Derived | READY / EMAIL_ONLY / MOBILE_ONLY / etc. |

---

## Final summary to the user

```
Built [N] contacts for [Client].

Channel readiness:
  Email valid:    [X] ([pct]%)
  Phones found:   [X] ([pct]%)
  LinkedIn URLs:  [X] ([pct]%)

Layer 4 enrichment (Tier 1, [N] contacts):
  Red Hot:   [X] (<1hr SLA — escalate to AE)
  Hot:       [X] (<24hr SLA — personalized sequence)
  Warm:      [X]
  Cool:      [X]
  Cold:      [X]

Strong hooks found: [X]

Top intent signals:
  1. [Company A] — [signal summary]
  2. [Company B] — [signal summary]
  3. [Company C] — [signal summary]

Output: [Google Sheet URL] or [CSV path or "inline above"]

Next: Red Hot needs AE attention today. Hot contacts → sequence today.
```

---

## Honest trade-offs vs the legacy script version

Because Cowork runs on connected MCPs (not local API keys), some pieces of the original pipeline don't have MCP equivalents yet:

- **Email validation waterfall** (MillionVerifier → ZeroBounce → Prospeo → LeadMagic): no MCPs exist. We rely on Apollo MCP's verified/unverified status. For sender reputation-critical sends, recommend running the output CSV through a validation service before loading into sequences.
- **Phone line-type detection** (mobile vs landline vs VoIP via Twilio Lookup): no Twilio MCP. Phones come back from Apollo as just numbers — line type isn't detected.
- **Persistent dedup across runs**: no local cache. Use Apollo's contact tagging / "already contacted" filters if you need to suppress prior outreach.

For SuperSDR users who need any of those: the legacy script version (in `legacy/`) still works if you run Claude Code locally with API keys in a `.env` file.

---

## No SPOT doc yet?

If the client doesn't have a SPOT doc:

> "No SPOT doc found for [Client]. Run `/client-spot` first to generate one — it'll capture the ICP, exclusions, target titles, and everything else this skill needs."

Don't accept ad-hoc ICP via chat for ongoing work. The SPOT doc is the source of truth; if it's not there, build it first.

If the user really wants a quick one-off list without a SPOT doc, you can take the ICP details inline (titles, size, location, exclusions) and proceed — but surface this as a one-time path and recommend creating a SPOT doc after.
