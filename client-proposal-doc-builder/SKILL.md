---
name: client-proposal-doc-builder
description: Build a polished, send-ready outbound agency proposal (Done-For-You Calling, cold email, or combined outbound) as a Google Doc, grounded in a discovery-call transcript or summary, then draft the follow-up email to send the prospect the proposal link. Trigger this skill aggressively whenever the user mentions building a proposal, a DFY calling proposal, a Done-For-You Calling proposal, an outbound proposal, a cold email proposal, or asks to draft, create, or build a proposal for a prospect in any context involving outbound sales services. Also trigger when the user has just attached a discovery-call transcript or call summary and wants the next document. The skill bakes in your agency's Terms & Conditions and Appendix A (Completed Conversation Criteria), web-researches the prospect, asks the right clarifying questions, produces a complete Google Doc with executive summary, pricing tiers, completed-conversations model, signature block, and full T&Cs, and then drafts the follow-up email (proposal-link or soft follow-up route).
---

# Outbound Proposal Doc Builder

## What this skill does

Given a discovery-call transcript or summary plus basic prospect info, produces a complete, send-ready proposal as a Google Doc and drafts the follow-up email to send with the proposal link. The proposal includes:

- Executive summary grounded in the prospect's specific business and the conversation
- "Our Understanding of the Opportunity" — what they sell, why pipeline is the bottleneck, ICP, conversation math
- Proposed Engagement with one or more pricing tiers (calling, email, or combined)
- "How We Operate" — four-phase 90-day cadence
- Investment Summary table
- Why [Agency] positioning block
- Full Terms & Conditions (lightly tailored)
- Next Steps + Acceptance + signature block
- Appendix A — Completed Conversation Criteria

## Why this exists

Every outbound agency proposal has the same skeleton: a positioning section grounded in the prospect's business, a pricing block grounded in conversation volume, four standard delivery phases, and a fixed legal tail (T&Cs + Appendix A). The variable work is roughly 30% — the positioning paragraphs, the ICP framing, the pricing tier(s) actually chosen. This skill exists so that you do the variable 30% with care and let the boilerplate 70% come from assets, instead of regenerating everything from scratch each time.

## Setup (first use)

Before using this skill, confirm your agency's assets are in place:

- `assets/terms_and_conditions.md` — Your T&Cs with `{COMPANY}` and `{AGENCY_LEGAL_NAME}` placeholders. Replace `{AGENCY_LEGAL_NAME}` with your legal entity name once before use.
- `assets/appendix_a_completed_conversation_criteria.md` — Your Completed Conversations definition. Edit to match your billing model if it differs.
- `references/positioning_and_style.md` — Voice guide and objection patterns. Update the worked examples and proof points with your agency's actual results.

## Workflow

Follow these steps in order. The proposal is only as good as the parameters set in steps 1–3, so don't rush past them.

### Step 1 — Read inputs thoroughly

Read every attached file in full — call transcript, call summary PDF, any reference proposal the user attached. Extract and hold onto:

- The prospect's business model and primary value proposition
- What was specifically pitched on the call (channels, model, proof points cited)
- Pricing options that were discussed and any commitment levels named
- Concerns the prospect raised (these become things you address in the proposal)
- Decision-maker context — who's signing, who's on the next call
- Next steps the user committed to on the call

If a key fact is missing or ambiguous, plan to ask about it in Step 3 rather than guessing.

### Step 2 — Web-research the prospect (light touch)

Run 1–2 web searches to ground the executive summary in current context. Look for:

- Recent funding or strategic moves (e.g., "<company> funding 2026", "<company> acquisition")
- Public positioning and ICP signals from their site
- Headline statistics about their market or category

Don't over-research. The proposal is grounded in the call, not in market analysis. Two searches is plenty. If the prospect has no meaningful web presence, skip this step.

### Step 3 — Ask clarifying questions

Use the AskUserQuestion tool. Ask only the questions you don't already have clear answers to from the call and prior conversation. The default question set:

1. **Pricing structure** — Which tier(s) to present? Single tier or two side-by-side? Ask the user to confirm the conversation volumes and monthly investment for each tier they want to include.
2. **Channels** — Calling only, email only, or combined? (Default to what was pitched on the call.)
3. **Exclusivity / lead overlap** — Hard exclusivity clause in T&Cs, mention in body with soft language, or defer to next call? (Defer is the safest default unless the user wants to commit.)
4. **Addressee** — Who signs on the company side? Single signer or joint? Open-ended is acceptable.

Phrase options as concrete trade-offs and mark a recommendation if one option is obviously stronger for the situation.

### Step 4 — Draft the markdown content

Build the proposal content as markdown first, in this order:

1. **Title block** — Use this exact layout (plain text, no markdown headings):

   ```
   [Agency Name] Proposal — {Company}
   PROPOSAL
   {Engagement Subtitle}
   {Engagement Tagline}
   PREPARED FOR
   {Company}
   {Contact Full Name}, {Contact Title}
   PREPARED BY
   {Agency Name}
   {Agent Name} — {agent@agency.com}
   {Date}
   ```

   Subtitle examples: "Outbound Lead Generation Engagement", "Fractional SDR Training Engagement"
   Tagline examples: "Cold Calling + Cold Email Pilot", "90-Day Outbound Build-Out"
   Infer contact name and title from the call transcript if not stated directly.
2. **Executive Summary** — Exactly 3 paragraphs:
   - Para 1 (3–5 sentences): What the prospect has built — product, market position, one traction signal. Anchor with **one specific fact from your web research** (recent funding, supplier count, ARR milestone, customer reference). This fact signals you did homework; omitting it signals a template.
   - Para 2 (3–5 sentences): The constraint — almost always pipeline distribution, not the offer. Lead with: *"The product works. The constraint is X."* If they named a specific bad vendor experience on the call, echo it verbatim here.
   - Para 3 (3–5 sentences): One-line investment summary (channels + total) and the projected outcome in numbers, not adjectives.
3. **Our Understanding of the Opportunity** — sub-sections:
   - *What [Prospect] Sells* (4–6 sentences) — product, market position, differentiation. Go deeper than the Exec Summary: mechanics, pricing model, customer types, any economics they shared on the call.
   - *Why [Pipeline / Distribution] Is the Bottleneck (Not the Offer)* (3–5 sentences) — name the underlying motion problem. Tie it to a specific dynamic from the call, not a generic market observation. Include any specific bad experiences they referenced (e.g., "the Branch problem", "chop-shop pattern") — use their words.
   - *Ideal Customer Profile* — 3–5 bullets (format: `- {Concrete ICP filter}`), covering company profile, revenue signals, decision-maker titles, and behavioral triggers. Follow with 1 paragraph (3–5 sentences) on how the list will be built — name specific data sources and signals (e.g., Shopify $1M+ revenue list, Meta ad library signals, Apollo intent filters, LinkedIn targeting). Only reference a prior client campaign by name if it was explicitly mentioned in the call — never fabricate campaign names or numbers.
   - *Conversation Math* — small table mapping conversations/month → projected meetings (use 10–15% set rate, ~75% show rate as working benchmarks). Follow with a benchmark paragraph citing relevant proof points the user mentioned on the call.
4. **Proposed Engagement** — one block per pricing tier or per channel. For each tier/channel, use a 2-column label-value table (Duration, Investment, Projected Meetings, Activated Leads, What's Included).
5. **Optional Add-Ons (for next-call discussion)** — exclusivity/non-compete framing, per-conversation + rev-share possibility, additional participants, anything else flagged for follow-up.
6. **How We Operate** — four phases, each a sub-section with 3–4 bullets:
   - Week 1 — Foundations
   - Weeks 2–3 — Launch and Calibrate
   - Weeks 4–10 — Scale and Optimize
   - Weeks 11–12 — Results Review
7. **Investment Summary** — markdown table summarizing tier(s):

   | Channel | Monthly | Months | Total |
   |---|---|---|---|
   | {Channel 1} | ${X} | {N} | ${Total} |
   | **Total Investment** | ${X} | {N} | **${Total}** |

   Then:
   - *Projected Outcomes* (3–4 bullets): meetings volume, validated playbook, infrastructure built, ICP data. Tailor to scope — no generic bullets.
   - *Payment Terms* (3 bullets, substitute {N} with actual engagement length):
     - Monthly invoicing, due upon receipt.
     - First month due on execution of this agreement to kick off list build and infrastructure.
     - Month-to-month after the initial {N}-day pilot, cancelable with 30 days' notice.
8. **Why [Agency Name]** — 1 paragraph (3–4 sentences) + 4 bullets. The paragraph is nearly verbatim across proposals — adapt only the final clause to the prospect's segment:

   > "[Agency Name] is a revenue-ops and outbound firm focused specifically on founder-led and early-stage B2B sales motions. We run outbound the way top-tier operators run it in-house — with senior callers, infrastructure ownership, and obsessive iteration on what's working in-market this week, not last quarter."

   Then lead with whatever operator credibility is most relevant to this prospect's world before the standard bullets. Standard bullets:
   - **Senior operators.** Callers and GTM operators who have run outbound at scale.
   - **Custom dialing infrastructure.** AI-powered calling produces 8–10x the conversation volume of traditional single-line SDR teams.
   - **Deliverability-first email.** Purpose-built sending domains protect {Company Domain} so your marketing and transactional email stays in the inbox. (Substitute the prospect's domain if you can infer it; otherwise drop the parenthetical.)
   - **Meeting quality > meeting quantity.** We qualify against ICP and intent before booking — no tire-kickers on your calendar.

   See `references/positioning_and_style.md` for proof points and vertical-specific credibility openers.
9. **Terms and Conditions** — read `assets/terms_and_conditions.md` and use verbatim. Update only: `{COMPANY}` → prospect's legal name, `{ENGAGEMENT_DESCRIPTION}` in §1, any agreed-upon exclusivity language in §8. Keep all sections intact.
10. **Next Steps + Acceptance + signature block.**
11. **Appendix A — Completed Conversation Criteria** — read `assets/appendix_a_completed_conversation_criteria.md` and use verbatim.

#### Voice and style

Confident, founder-to-founder, not corporate. Anchored in what this prospect said on this call — not a generic agency pitch.

- Refer to the prospect by company name throughout. Never "you" or "your company."
- When the prospect named a problem ("chop-shop", "tire-kickers", "creative fatigue"), use that word in the proposal. This is the single highest-signal move.
- Every industry observation must tie back to something they said on the call. No generic market takes.
- Em-dashes for emphasis and parenthetical asides (—). No hedging ("we believe", "potentially", "we hope"). No fluffy marketing ("world-class", "industry-leading", "synergy", "best-in-class").
- Short paragraphs: 2–4 sentences. Use bullets only when there are 3+ parallel items — prose feels like a person, over-bulleted decks feel like a vendor.
- Target: 1,500–2,500 words for the dynamic portion (everything before Terms and Conditions).

See `references/positioning_and_style.md` for objection-handling copy, channel vocabulary, and worked examples.

### Step 5 — Create the Google Doc

Use the Google Drive connector (Settings → Connectors → Google Drive in Cowork) to create and populate the proposal doc. The connector must have write permission enabled.

1. **Create a new Google Doc** titled `[Agency Name] Proposal — {Prospect}` using the connector.
2. **Write the proposal content** from Step 4 into the doc section by section — title block first, then each named section in order. Use the connector's write/append capability for each section.
3. **Capture the doc URL** once creation is confirmed.

If the Google Drive connector is not connected or does not have write permission, output the full proposal as formatted markdown instead and tell the user:

> "Paste this into a new Google Doc titled '[Agency Name] Proposal — {Prospect}'. Enable tabs in Google Docs if you want to keep T&Cs and Appendix A on separate tabs."

### Step 6 — Validate

Read back the doc using the connector and confirm these sections are present and in the right order: title block, Executive Summary, at least one Proposed Engagement pricing block, Investment Summary, Terms & Conditions, and Appendix A. If any section is missing, write it using the connector before proceeding.

### Step 7 — Deliver the doc

Give the user the Google Doc URL and a short prose summary of the structural choices made (which pricing tier(s), how exclusivity was handled, what positioning hook was used). Do not re-summarize the proposal contents — the user can read it.

### Step 8 — Draft the follow-up email

After the doc is delivered, immediately draft the follow-up email Hunter will send with the proposal link. Present `subject` and `body` as plain text the user can copy straight into Gmail.

#### Route selection

- **Proposal-link route** — a Google Doc URL was produced in Step 5. Default route.
- **Needs-followup route** — no proposal yet (e.g., pricing wasn't discussed on the call or the user indicated the proposal comes later). Use when `proposal_link` is null.

#### Context to pull from the prior steps

| Variable | Source |
|---|---|
| `first_name` | Derived from call transcript, event title, or recipient email |
| `company_name` | Prospect company |
| `summary` | Full call summary |
| `pricing_discussed` | Pricing covered on call, or "not discussed" |
| `key_objections` | Objections raised on the call |
| `next_steps` | Agreed next steps from the call |
| `proposal_link` | Google Doc URL from Step 5, or null |

#### Voice rules

Direct, conversational, warm-confident. Founder-to-founder, not vendor-to-buyer.

- Short paragraphs (1–3 sentences each).
- Lowercase `i` is acceptable in casual mid-sentence usage ("i think this will be a slam dunk").
- Hyphens only. Never em-dashes.
- **Banned phrases:** "I hope this finds you well", "As discussed", "Please don't hesitate", "Circle back", "Touch base", "Bandwidth", "Synergy", "Going forward".
- **Banned openings:** "I wanted to", "Just wanted to", "I'm reaching out", "Following up to". Lead with substance — never a meta-statement about the fact that you're emailing.

#### Structure — proposal-link route

```
Hey {first_name},

Hook — one-line reference to the call + a specific observation about their company /
product / stage, drawn from summary. Never invent details.

Bridge — "As promised, I've put together a customized proposal for the {scope}
engagement we discussed." Infer scope from summary + pricing_discussed (e.g.,
"3-month cold email + cold calling", "fractional SDR training build-out").

[Optional confidence line] — only if a concrete past RevCentric campaign result was
explicitly mentioned in the call summary. Never fabricate campaign names or numbers.
Skip entirely if no signal exists.

A few highlights from the proposal:
- *{Component}* - {one-liner of what + why for THEM}
- *{Component}* - {one-liner of what + why for THEM}
- *{Component}* - {one-liner of what + why for THEM}

Exactly 3 bullets. Components reflect actual scope (Cold Calling, Cold Email,
X-Month Commitment, ICP Targeting, SuperSDR Coaching, etc.). Value lines must be
tailored to their context, never generic.

CTA — "Take a look {with your team / co-founder / business partner} and note any
questions - happy to walk through everything {on our follow-up / on Friday / at our
next call}." Use real names from the call if available ("with your brother/co-founder").

[Optional next-meeting line] — only if next_steps names a specific day/time:
*{Day} Follow-Up: {Time} {TZ}* - cal invite should already be in your inbox.
Append "{Other RC Attendee} will also be looped in." only if explicitly known.

Talk soon,
Hunter
```

Do not append title, phone, or email after Hunter — Gmail signature handles that.

**Length:** 100–180 words.

#### Structure — needs-followup route

```
Hey {first_name},

Hook (same rule — call reference + specific observation).

One direct sentence on where we left off.

Soft CTA — book a follow-up call, share more context, or reply with timing.

Talk soon,
Hunter
```

**Length:** 60–130 words.

#### Subject line patterns

- `{Company} x RevCentric Proposal + {Day} Follow-Up`
- `{Company} - Quick Follow-Up`
- `{Company} Proposal`

Always include the company name. Match the pattern to the route — use the first pattern for proposal-link, second or third for needs-followup.

#### Reference output (Pinprick, 2026-05-05)

```
Subject: Pinprick x RevCentric Proposal + Friday Follow-Up

Hey Nick,

Really great catching up today love what you're building with Pinprick.

As promised, I've put together a customized proposal for the 3-month cold email +
cold calling engagement we discussed. Given the results from our Crux campaign, i
think this will be a slam dunk.

A few highlights from the proposal:
- *Cold Calling* - dedicated dialing for higher-touch conversion with qualified prospects
- *Cold Email* - high-volume, personalized sequences targeting your ICP (companies
  spending $50K-7 figures/month on paid ads)
- *3-Month Commitment* - enough runway to optimize, iterate, and deliver real pipeline

Take a look with your brother/co-founder and note any questions - happy to walk through
everything on Friday.

*Friday Follow-Up: 9:30 AM PST* - should've already received the cal invite. Jace will
also be looped in.

Talk soon,
Hunter
```

## Assets

- `assets/terms_and_conditions.md` — T&Cs boilerplate. Replace `{AGENCY_LEGAL_NAME}` with your legal entity name once. Then per-proposal: swap `{COMPANY}`, `{ENGAGEMENT_DESCRIPTION}`, `{FEES_LANGUAGE}`, and optional §8 exclusivity addendum language.
- `assets/appendix_a_completed_conversation_criteria.md` — Appendix A defining Completed Conversations + all billable / non-billable disposition criteria.
- `assets/reference_proposal_homegrown.md` — Full example proposal (calling + email pilot) as a structural reference for combined-channel proposals.

## References

- `references/positioning_and_style.md` — Voice guide, common objection patterns, and channel-specific vocabulary. Update proof points and worked examples with your agency's actual results.

## Gotchas

- **Don't bake exclusivity into T&Cs unless explicitly asked.** Default is to mention it in the Optional Add-Ons section and add the soft addendum language in §8. Preserving flexibility on commercial terms early in the relationship is usually the right call.
- **Pricing tiers track conversations, not meetings.** The completed-conversations model is the differentiator. Frame meetings as a *projected outcome* of conversation volume, not as the unit of commitment.
- **Reflect their language back.** If the prospect named a specific bad experience or industry term, use it in the proposal. This is the single highest-signal thing you can do.
- **Never fabricate prior campaign references.** Only cite a past client campaign by name if the user explicitly mentioned it in the call context. Making up campaign names or numbers destroys trust if the prospect asks.
- **Write the doc in one pass if possible.** If the connector supports overwrite, use it with the full content. If you write section by section and something gets out of order, re-read the doc and patch the affected section before delivering.
