---
name: rc-objection-drill
description: Cold call objection handling drill and roleplay tool for RC SDRs. Two modes — Quick Drill (paste an objection, get framed responses) and Live Roleplay (skill plays the prospect, you respond, get graded). Use when user says "drill me on objections", "how do I handle [objection]", "I keep getting hit with [X]", "roleplay me as a [persona]", "objection drill", "practice objections", "give me responses to [objection]", or pastes a real objection from a recent call. Also use when the user asks for help mid-call prep or wants to train on a specific client's objection set.
---

# RC Objection Drill Skill

## Purpose

Two-mode cold call objection trainer for RC SDRs and closers. Built on the Workstreet/SuperSDR objection handling framework — Universal Loop, 5 Objection Families, low-and-slow tone. Works for any RC client when the per-client objection library (SPOT Tab 7) is provided.

---

## The Framework (always apply)

### 5 Objection Families

Every objection maps to one of these. Identify which family before responding — the response strategy depends on it.

| Family | What's really going on | Right move |
|---|---|---|
| **Ownership** | They don't own this decision | Get a referral up or sideways, don't try to convert them |
| **No Pain** | They don't feel the problem | Surface pain OR reframe the meeting as benchmarking, not pitch |
| **Priority** | They feel it but can't act now | Split: bandwidth vs importance. Most people mean bandwidth |
| **Timing** | Future yes, present no | Probe: "What's changing between now and then?" |
| **Sales Resistance** | They're blocking the interaction itself | Recontextualize as value, not sales |

### The Universal Loop (7-step skeleton)

Use this for every objection unless it's a hard no:

1. **Listen** — don't interrupt
2. **Address + Empathize** — substantive, not just "got it." Match their actual concern.
3. **Probe one layer deeper** — "Out of curiosity, [specific question]?"
4. **Confirm ownership** — "Are you the one handling this day-to-day?"
5. **Context-set with social proof** — "Most folks we talk to are in that exact situation"
6. **Reframe the session** — benchmarking, coffee-style chat, not a pitch
7. **Assertive close** — "Would that be a terrible use of 15-20 minutes?"

### Tone rules

- **Low and slow.** Calm, confident, not eager. Status through control.
- Never use "feel free to take it or leave it" — it telegraphs supplication. Use "That's actually why I'm really glad that I called."
- No customer-service energy. No "I'm so excited to chat!"
- Don't bash competitors. Acknowledge them, then differentiate.
- Don't over-talk. Let silence do work.

---

## Mode 1 — Quick Drill (default)

When the user pastes an objection or says "how do I handle [X]," respond with this structure:

```
OBJECTION: "[exact objection paraphrased]"

WHAT'S REALLY GOING ON:
[1-2 sentences naming the family and the underlying concern]

RESPONSE OPTION 1 — [approach name, e.g., "Empathy + bandwidth probe"]
"[Verbatim spoken response, low and slow tone, with delivery cues if useful]"

RESPONSE OPTION 2 — [approach name, e.g., "Reframe as benchmarking"]
"[Verbatim response]"

RESPONSE OPTION 3 — [approach name, e.g., "Math the deal"]
"[Verbatim response]"

LIKELY FOLLOW-UP OBJECTIONS:
- [next objection they'll throw] → [one-line how to chain]
- [another likely chain]

DO NOT SAY:
- "[bad phrase 1]" — [why it backfires]
- "[bad phrase 2]" — [why it backfires]
```

Always give 3 options because different prospect personas respond to different angles.

---

## Mode 2 — Live Roleplay

Trigger phrases: "drill me," "roleplay me," "let's drill," "play the prospect," "be the [title]."

How it runs:

1. **Set the scene.** Confirm: which client (Cekura/MeshAPI/Crux/Workstreet)? Which persona (CTO/CMO/Founder)? Which objection bucket — or random?
2. **Stay in character as the prospect.** Throw the objection naturally, in their voice. Sound busy, mildly skeptical, not hostile. Use realistic speech patterns ("yeah look, honestly...").
3. **Wait for the user's response.** Don't help mid-call.
4. **Continue the back-and-forth.** Layer follow-up objections, throw curveballs, push back on weak responses. 3-5 exchanges total.
5. **Break character at the end.** Grade the call:
   - What worked (specific lines that landed)
   - What missed (specific lines or tone issues)
   - The better move would have been: [specific alternative response]
   - Score: [Strong / Solid / Needs work]

Example opener for roleplay:

```
Setting up: You're calling me. I'm [persona] at [fictional company]. Throw your opener whenever you're ready.
```

---

## Common RC Objections — Quick Reference

Use these as the default playbook. If the user provides a client's SPOT Tab 7, override with client-specific responses.

### "Just send me an email"
- **Family:** Sales Resistance
- **Real concern:** Not yet convinced it's worth their time on a call.
- **Response (default):** "Yeah totally — happy to. Out of curiosity, what would make you open it vs delete it? I'll skip the boilerplate and just send what's relevant."
- **Stronger move:** "Yeah I can — but honestly the email's gonna be 80% the same context I just gave you. If I'm wasting your time, just say so and I'm out. Otherwise 4 minutes right now beats 20 emails."
- **Do not say:** "Sure! What's your email?" (gives up the call)

### "We already use [Competitor]"
- **Family:** No Pain (likely)
- **Real concern:** They've stopped looking. Not necessarily happy.
- **Response:** "Got it — and most folks we talk to are using [competitor]. The reason I called isn't to swap you out — it's that [specific gap or new capability] usually isn't on their roadmap, and we're seeing folks bolt us on alongside. Would 15 min to see if it's even relevant be a terrible use of time?"
- **Do not say:** "Oh but we're better than [competitor]" (instant credibility loss)

### "Not a priority right now"
- **Family:** Priority — split bandwidth vs importance
- **Probe:** "Totally fair — out of curiosity, is it more that the problem isn't pressing right now, or that you just don't have the bandwidth to look at it?"
- **If bandwidth:** "That's actually exactly why folks bring us in — we do the heavy lifting so your team doesn't have to."
- **If importance:** "Got it — what would have to be true for it to move up?"

### "Call me back in 3-6 months"
- **Family:** Timing — but often a soft no in disguise
- **Probe:** "Yeah I can do that — quick question, what's changing between now and then? Just want to make sure I time it right."
- **If they have a real answer:** Confirm the timing, set a calendar reminder, ask for a referral now.
- **If they don't:** "Sounds like maybe the timing isn't really the issue — what would make this a yes?"

### "No budget"
- **Family:** Priority OR Sales Resistance (depends on context)
- **Probe:** "Totally hear you — is it that there's literally no budget anywhere, or that this isn't a line item yet?"
- **If no budget:** "Got it — when does next year's budget cycle start? Worth being on your radar before then."
- **If not a line item:** "What would the ROI need to look like for it to become one?"

### "We're building it ourselves"
- **Family:** No Pain (they think they've solved it)
- **Response:** "Smart — most teams that try end up with [specific shortcoming] and shift to a partner around month 6. Out of curiosity, where are you on the build? I'd hate for you to spend 6 months and find out we could've saved you the cycle."
- **Do not say:** "But buying is faster than building!" (lecture-y)

### "How did you get my number?"
- **Family:** Sales Resistance — they're testing
- **Response:** "Honestly? I'd be a bad SDR if I didn't know how to find a [their title]. The real question is — now that you're on the line, is what we do worth 60 seconds?"

### "We're not the right fit"
- **Family:** Either No Pain (they don't see the fit) or polite Sales Resistance
- **Probe:** "Got it — out of curiosity, what about us made you say that? Just want to make sure I'm not pitching the wrong angle."
- **Use their answer to redirect.**

### "I need to talk to my team"
- **Family:** Ownership OR stalling
- **Probe:** "Totally — who else is involved? Happy to set up something with all of you so you don't have to play telephone."
- **Push for the call:** Calendaring three people is harder if you wait.

### "Just send me info"
- **Family:** Sales Resistance
- **Response:** "Yeah — what specifically would help? If it's pricing, I can give it to you on the call. If it's case studies, same. The reason I'd rather chat for 10 min is the info dump usually doesn't answer the question that actually matters to you."

---

## Per-Client Objection Sets

If the user references a specific RC client (Cekura, MeshAPI, Crux, Workstreet), pull objections from that client's SPOT Tab 7 if available. If not, use the defaults above and flag that client-specific responses haven't been provided yet.

For Workstreet specifically: 13 consolidated objection categories exist in the Workstreet Battle Card. The most common are "Compliance is easy," "We use Vanta/Drata," "Already audited," "Bandwidth," and "Call me back."

---

## When to break the rules

If the prospect is genuinely angry, hostile, or asks you to never call again — drop the loop entirely. One clean apology, confirm the do-not-call, end the call. Don't try to recover hostile prospects.
