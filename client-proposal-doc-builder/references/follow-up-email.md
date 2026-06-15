# Follow-Up Email Templates

### Step 8 — Draft the follow-up email

After the doc is delivered, immediately draft the follow-up email you will send with the proposal link. Present `subject` and `body` as plain text the user can copy straight into Gmail.

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

Here's the proposal: {proposal_link}

[Optional confidence line] — only if a concrete past campaign result from your agency was
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
[Your Name]
```

Do not append title, phone, or email after the sign-off name — Gmail signature handles that.

**Length:** 100–180 words.

#### Structure — needs-followup route

```
Hey {first_name},

Hook (same rule — call reference + specific observation).

One direct sentence on where we left off.

Soft CTA — book a follow-up call, share more context, or reply with timing.

Talk soon,
[Your Name]
```

**Length:** 60–130 words.

#### Subject line patterns

- `{Company} x [Your Agency] Proposal + {Day} Follow-Up`
- `{Company} - Quick Follow-Up`
- `{Company} Proposal`

Always include the company name. Match the pattern to the route — use the first pattern for proposal-link, second or third for needs-followup.

#### Reference output

```
Subject: {Company} x [Your Agency] Proposal + Friday Follow-Up

Hey {First Name},

Really great catching up today, love what you're building with {Company}.

As promised, I've put together a customized proposal for the 3-month cold email +
cold calling engagement we discussed.

Here's the proposal: {proposal_link}

Given the results from our {Prior Client} campaign, i think this will be a slam dunk.

A few highlights from the proposal:
- *Cold Calling* - dedicated dialing for higher-touch conversion with qualified prospects
- *Cold Email* - high-volume, personalized sequences targeting your ICP ({relevant ICP signal})
- *3-Month Commitment* - enough runway to optimize, iterate, and deliver real pipeline

Take a look with your {co-founder/partner} and note any questions - happy to walk through
everything on Friday.

*Friday Follow-Up: 9:30 AM PST* - should've already received the cal invite. {Colleague}
will also be looped in.

Talk soon,
[Your Name]
```
