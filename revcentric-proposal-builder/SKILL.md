---
name: revcentric-proposal-builder
description: Build a polished, send-ready RevCentric.ai client proposal (Done-For-You Calling, cold email, or combined outbound) as a Word document, grounded in a discovery-call transcript or summary. Trigger this skill aggressively whenever the user mentions building a RevCentric proposal, a DFY calling proposal, a Done-For-You Calling proposal, an outbound proposal, a cold email proposal, or asks to draft, create, or build a proposal for a prospect in any context involving outbound sales services — even if they don't explicitly say "RevCentric." Also trigger when the user has just attached a discovery-call transcript or call summary and wants the next document. The skill bakes in the canonical Terms & Conditions and Appendix A (Completed Conversation Criteria), web-researches the prospect, asks the right clarifying questions, and produces a complete .docx with executive summary, pricing tiers, completed-conversations model, signature block, and full T&Cs.
---

# RevCentric Proposal Builder

## What this skill does

Given a discovery-call transcript or summary plus basic prospect info, produces a complete, send-ready RevCentric.ai proposal as a Word document (.docx). The proposal includes:

- Executive summary grounded in the prospect's specific business and the conversation
- "Our Understanding of the Opportunity" — what they sell, why pipeline is the bottleneck, ICP, conversation math
- Proposed Engagement with one or more pricing tiers (calling, email, or combined)
- "How We Operate" — four-phase 90-day cadence
- Investment Summary table
- Why RevCentric positioning block
- Full Terms & Conditions (23 sections, lightly tailored)
- Next Steps + Acceptance + signature block
- Appendix A — Completed Conversation Criteria (canonical)

## Why this exists

Every RevCentric proposal has the same skeleton: a positioning section grounded in the prospect's business, a pricing block grounded in conversation volume, four standard delivery phases, and a fixed legal tail (T&Cs + Appendix A). The variable work is roughly 30% — the positioning paragraphs, the ICP framing, the pricing tier(s) actually chosen. This skill exists so that you do the variable 30% with care and let the boilerplate 70% come from assets, instead of regenerating everything from scratch each time.

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

1. **Pricing structure** — Which tier(s) to present? Single tier or two side-by-side? Common RevCentric tiers: $5K/mo = 50 conversations, $10K/mo = 100 conversations, $15K/mo = 150 conversations (custom). Cold email standalone typically $5K/mo. Combined channels follow the structure pitched on the call.
2. **Channels** — Calling only, email only, or combined? (Default to what was pitched on the call.)
3. **Exclusivity / lead overlap** — Hard exclusivity clause in T&Cs, mention in body with soft language, or defer to next call? (Defer is the safest default unless the user wants to commit.)
4. **Addressee** — Who signs on the company side? Single signer or joint? Open-ended is acceptable.
5. **Output format** — `.docx` (default), `.md`, or both?

Phrase options as concrete trade-offs and mark a recommendation if one option is obviously stronger for the situation.

### Step 4 — Draft the markdown content

Build the proposal content as markdown first, in this order:

1. **Title block** — `PROPOSAL` / engagement name / subtitle / `PREPARED FOR / PREPARED BY` block / date.
2. **Executive Summary** — 3 paragraphs. Paragraph 1: who the prospect is and the platform/business they've built (use 1–2 facts from web research to show you did your homework). Paragraph 2: what the constraint actually is (almost always: pipeline distribution, not the product) and what the proposal does about it. Paragraph 3: tier summary + projected outcome.
3. **Our Understanding of the Opportunity** — sub-sections:
   - *What [Prospect] Sells* — describe their product/service in their language, including any economics they shared on the call.
   - *Why [Pipeline / Distribution] Is the Bottleneck (Not the Offer)* — name the underlying motion problem, including any specific bad experiences they referenced (e.g., "the Branch problem", "chop-shop pattern"). Reflect their concerns back so they see them in writing.
   - *Ideal Customer Profile* — bullets covering company profile, decision-maker titles, triggers.
   - *Conversation Math* — small table mapping conversations/month → projected meetings (use 10–15% set rate, ~75% show rate as RevCentric's working numbers). Follow with a benchmark paragraph citing relevant proof points the user mentioned on the call.
4. **Proposed Engagement** — one block per pricing tier or per channel. For each tier/channel, use a 2-column label-value table (Duration, Investment, Projected Meetings, Activated Leads, What's Included).
5. **Optional Add-Ons (for next-call discussion)** — exclusivity/non-compete framing, per-conversation + rev-share possibility, additional participants, anything else flagged for follow-up.
6. **How We Operate** — four phases, each a sub-section with 3–4 bullets:
   - Week 1 — Foundations
   - Weeks 2–3 — Launch and Calibrate
   - Weeks 4–10 — Scale and Optimize
   - Weeks 11–12 — Results Review
7. **Investment Summary** — table summarizing tier(s), then sub-sections for Projected Outcomes (bullets) and Payment Terms (bullets).
8. **Why RevCentric** — short intro paragraph + 4–5 bullets. Lead with whatever specific operator credibility applies (e.g., "Kevin's Branch background" for channel/UCaaS prospects).
9. **Terms and Conditions** — read `assets/terms_and_conditions.md` and use verbatim. Update only: company name, engagement description in §1, any agreed-upon exclusivity language in §8. Keep all 23 sections.
10. **Next Steps + Acceptance + signature block.**
11. **Appendix A — Completed Conversation Criteria** — read `assets/appendix_a_completed_conversation_criteria.md` and use verbatim.

#### Voice and style

Confident, founder-to-founder, not corporate. Use the prospect's actual language and metaphors from the call — when they named a problem ("chop-shop", "tire-kickers", "creative fatigue"), echo it back in writing so they see their words reflected. Em-dashes for emphasis (—), smart quotes throughout. Avoid generic marketing language ("synergy", "best-in-class", "leverage" as a verb).

See `references/positioning_and_style.md` for more detail and worked examples.

### Step 5 — Build the .docx

Read `assets/build_proposal_template.js`. It contains the docx-js helpers (cell, table, bullet, h1/h2/h3, etc.) and an annotated structure showing how the Bridgepointe and Homegrown proposals were assembled. Copy it to your working directory, replace the content arrays with the markdown content from Step 4, run it with Node, and write to `outputs/<Prospect>_Proposal.docx`.

Setup:
```bash
npm install docx --silent
node build_proposal.js
```

Page spec: US Letter (12240 × 15840 DXA), 1" margins (1440 DXA), Arial default 11pt, navy headings (`1F3864` for H1, `2E4F8A` for H2). Investment-Summary and disposition tables use color shading (`E8EEF7` headers, `E5F5E5` billable, `FBE5E5` non-billable).

### Step 6 — Validate + visual check

After building, validate:

```bash
python /var/folders/ts/xj8gqz716jq988c_1_3kl44r0000gn/T/claude-hostloop-plugins/ff2b7c23ede51a6e/skills/docx/scripts/office/validate.py outputs/<Prospect>_Proposal.docx
```

Then convert to PDF and render a few spot-check pages — title page, pricing-tier page, signature block, and the Appendix A billable/non-billable tables. Look at them. Confirm tables aren't broken, headings have proper hierarchy, and color shading rendered. Fix any issues before delivery.

### Step 7 — Deliver

Give the user a `computer://` link to the .docx and a short prose summary of the structural choices made (which pricing tier(s), how exclusivity was handled, what positioning hook was used). Do not re-summarize the proposal contents — the user can read it.

## Assets

- `assets/terms_and_conditions.md` — The 23-section Terms & Conditions boilerplate. Use verbatim. Swap only: company name, engagement description in §1, any exclusivity addendum language in §8.
- `assets/appendix_a_completed_conversation_criteria.md` — Canonical Appendix A defining Completed Conversations + all billable / non-billable disposition criteria. Use verbatim.
- `assets/build_proposal_template.js` — Reference docx-js build script with helpers and styling baked in. Copy, adapt content arrays, run.
- `assets/reference_proposal_homegrown.md` — Full Homegrown Ads proposal (calling + email pilot) as a structural reference for combined-channel proposals.

## References

- `references/positioning_and_style.md` — RevCentric voice guide, common metaphors, and patterns for handling specific objections (Branch problem, lead overlap, per-meeting incentive mismatch, deliverability concerns).

## Gotchas

- **Don't bake exclusivity into T&Cs unless explicitly asked.** Default is to mention it in the Optional Add-Ons section and add the soft addendum language in §8. RevCentric wants flexibility on commercial terms early in the relationship.
- **Pricing tiers track conversations, not meetings.** The completed-conversations model is the differentiator. Frame meetings as a *projected outcome* of conversation volume, not as the unit of commitment.
- **Reflect their language back.** If the prospect named a specific bad experience or industry term, use it in the proposal. This is the single highest-signal thing you can do.
- **Don't add `--break-system-packages` flags or other build hacks** unless the environment actually requires them.
- **Always run the docx validator.** If validation fails, fix it before delivering — docx-js can occasionally produce subtle XML issues that render fine in LibreOffice but break in Word.
