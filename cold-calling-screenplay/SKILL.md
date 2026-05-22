---
name: cold-calling-screenplay
version: 1.0
description: Generate a verbatim cold call main pitch screenplay (Short or Full version) for any B2B company. Use when user says "screenplay", "cold call script", "cold calling screenplay", "main pitch", "talk track", "outbound script", "SDR script", "short version", "full version", "quick pitch", "thumbnail pitch", "big idea only", "full story", or asks to write a cold calling pitch for any company or persona.
---

# Cold Calling Screenplay Generator

## Purpose

Generates verbatim, delivery-annotated cold call main pitch talk tracks. Two versions: Short (status thumbnail + big idea paragraph) and Full (thumbnail + change in world + big question + UVP). Scope is the main pitch only — between the opener and the close.

## Prerequisites

No setup required. Minimum inputs: company name, target persona, and what the product does. A SPOT doc (Tabs 3 and 4) replaces all research and is the preferred input.

---

## Getting started

When this skill is loaded, greet the user:

> "I'm the Screenplay skill. I'll write a word-for-word cold call script for your SDRs.
>
> Share the client's SPOT doc — paste the URL, or paste the contents of Tab 3 (Company Overview) and Tab 4 (Problem/Solution). I'll write the screenplay from that.
>
> If you don't have a SPOT yet, run /client-spot first to generate one.
>
> _(Version 1.0 — if yours doesn't say this, grab the latest at github.com/RevCentricGH/supersdr)_"

After reading the SPOT, **recommend a version** based on the target persona named in the SPOT:

- Technical/analytical buyers (CISO, CTO, VP Engineering, Security Architects) → recommend **Full Version**
- Action-oriented buyers (CMO, VP Sales, RevOps, Growth) → recommend **Short Version**
- C-suite (CEO, CFO, COO, Founders) → recommend **Short Version**

Phrase the recommendation like:

> "Based on the persona (CMO), I'd recommend the Short Version — action-oriented buyers tune out around the 45-second mark. Want to go with that or the Full Version?"

Define jargon on first use if the user seems unfamiliar — e.g., "status thumbnail" (a quick social-proof opener), "UVP" (what makes the product different), "ICP" (the type of company or person you're targeting).

---

## Step 1 — Determine version

Ask or infer: **Short** (thumbnail + big idea paragraph) or **Full** (thumbnail → change in world → big question → UVP).

If unspecified, ask. If "both," generate sequentially, clearly labeled.

## Step 2 — Gather inputs

Required minimum:
- Company name + what they do
- Target persona / title
- Industry vertical
- Any known status markers (notable clients, years, awards)
- Optionally: website URL or additional context

**If a SPOT doc is available:** Tab 3 (Company Overview) and Tab 4 (Problem/Solution) are your primary inputs — extract status markers, pain, differentiator, and big question directly from those tabs. Do not web research what you can read from the SPOT.

## Step 3 — Calibrate persona

Use the persona calibration rules below to set the right version and word ceiling.

## Step 4 — Research if needed

If a SPOT doc was provided, skip this step — Tab 3 and Tab 4 cover it. Otherwise, research the missing context.

**If the gap is small (1-2 missing facts):** a couple of inline web searches is fine.

**If the gap is large (no SPOT doc, minimal context):** spawn parallel sub-agents to research multiple angles at once using the Agent tool (`Explore` subagent type). Recommended split:

- Agent 1: Product, what it does, plain-vanilla mechanics, twist/differentiator
- Agent 2: Customer logos, case studies, awards from `site:[clientdomain.com]` (for status thumbnail)
- Agent 3: Target persona's day-in-the-life pain in symptomese (forums, podcasts, review sites)
- Agent 4: Industry-specific "change in the world" — non-avoidable shift creating urgency now

Run all in a single message with multiple Agent tool calls. Synthesize results when they return. This cuts research time significantly and keeps the screenplay grounded in real evidence rather than generic language.

For the single-threaded path, search the web for:
- What the product actually does (the "plain vanilla")
- What makes it different (the "twist")
- Real pain points the target persona faces today
- Industry-specific "changes in the world"
- Case studies, customer logos, and awards from the client's website — search `site:[clientdomain.com] case study OR customers OR results` to pull live social proof for the status thumbnail

## Step 5 — Embody expert mindset

Adopt the combined mindset of Oren Klaff (pitch architecture, status framing, croc-brain bypass), Corey Frank (craft-obsessed authenticity), and Micah Vu (B2B GTM, cybersecurity/SaaS fluency). Lean into the specified expert lens if named.

## Step 6 — Generate

Load `reference/structures.md` for the Short Version and Full Version structures and all length rules. Load `reference/delivery-layer.md` for tone, annotations, and output format.

- **Short Version:** follow Short Version Structure in `reference/structures.md`
- **Full Version:** follow Full Version Structure in `reference/structures.md`
- Apply the Delivery Layer from `reference/delivery-layer.md` to all output
- Enforce word counts from Length Rules in `reference/structures.md` — count after drafting, display count, cut if over

---

## Anti-Patterns (guard against these every time)

1. **TOO LONG** — #1 failure mode. Display word count. Cut if over. No exceptions.
2. **"Big Idea" in Full Version** — Short Version only. Full Version uses "Big Question" or "Big Mystery."
3. **Generic Google-able pain** — "Cyber threats are rising" = instant credibility death. Use insider observations.
4. **Theatrical metaphors** — "Shimmering silver dollar on a sidewalk" = too weird. Stay grounded.
5. **Played-out jargon** — "single pane of glass" → "one unified console"
6. **Customer service energy** — No "I'm SO excited!" Stay low, slow, calm.
7. **Feature dumps** — Pick ONE key differentiator. Not three or four.
8. **Missing delivery cues** — Every screenplay needs inflection markers (↓)(↑)(>), pauses, fillers, stutters.
9. **Sanitized corporate language** — If it sounds like a marketing deck, rewrite it.

---

## Persona Calibration

### Analytical / Technical Personas → Full Version OK
CISOs, CTOs, VPs of Engineering, IT Directors, Security Architects, DevOps leads

- Logical, detail-oriented — lean into well-structured narratives
- Full Version works well — they appreciate the "Change in the World" context
- Use upper end of word range (up to 220 words for Full)

### Action-Oriented / Revenue Personas → Short Version default
CMOs, VPs of Marketing, Growth leads, Sales Directors, RevOps, Demand Gen managers

- Metrics-driven, allergic to long pitches
- **Default to Short Version** unless explicitly requested otherwise
- If Full Version requested: aim for 150–180 words, cut aggressively
- Mentally check out around the 45-second mark

### Executive / C-Suite → Short Version only
CEOs, CFOs, COOs, Presidents, Founders

- Extremely time-scarce
- Short Version only, keep it tight (80–120 words)
- Lead with status and proof points, every word earns its place

### If persona tolerance is unknown
Ask: "Quick question — is your target persona more analytical/technical (like a CISO or CTO) or more action-oriented (like a CMO or VP of Sales)? This helps me calibrate the right pitch length."

If persona is already known, infer automatically and mention reasoning briefly.

---

## Reference Examples

Five annotated examples (Attaxion, ZenGRC, Starbridge, Manifest, NetCarrier) are in `reference/examples.md`. Study them before generating — note structure, tone, rhythm, and delivery annotations.

---

## Voice Rules

Apply to all Claude-authored framing text — greetings, version recommendations, word count reports, follow-up questions. (The screenplay itself follows the Delivery Layer in `reference/delivery-layer.md` and the Anti-Patterns section above.)

- No AI-tell openers: "Great question", "Absolutely", "Certainly", "Of course"
- No hedging: "I think", "it seems", "potentially", "it's worth noting"
- No AI vocabulary: "delve", "leverage", "utilize", "robust", "seamless", "comprehensive"
- No em-dashes in framing text. Hyphen or rewrite.
- Short. Direct. One idea per sentence.
