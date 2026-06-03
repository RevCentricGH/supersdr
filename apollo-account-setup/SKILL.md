---
name: apollo-account-setup
description: One-time Apollo account setup for new SuperSDR students — link workspace email, register outbound number with Free Caller Registry, configure 19 custom dispositions, add 11 contact stages, and wire the 19 disposition→stage triggers. Run once before any client campaigns are built. Use when user says "set up my Apollo account", "configure Apollo", "Apollo account setup", "set up dispositions", "set up contact stages", "set up triggers", "Apollo onboarding", or is setting up Apollo for the first time.
---

# Apollo Account Setup

## Purpose

One-time onboarding skill for a new Apollo account. Configure everything that only needs to be set up once — before any client campaigns are built.

This runs once per Apollo account, not per client. Dispositions and contact stages are account-wide. A student building their second client campaign in the same account does not run this again.

Run this skill first. Run the Apollo Campaign Builder after.

_Cowork skill - upload the ZIP and run from the Claude desktop app._

## Files

- `dispositions_builder.py` — the 19 custom dispositions (`DISPOSITIONS` list) + browser execution guide
- `stages_builder.py` — the 11 contact stages (`STAGES` list) + browser execution guide
- `triggers_builder.py` — the 19 disposition→stage triggers (`TRIGGERS` list) + browser execution guide

---

## Load Data Files First

Before executing Steps 3, 4, and 5, read all three files into context:

- `dispositions_builder.py`
- `stages_builder.py`
- `triggers_builder.py`

These are the source of truth for all disposition, stage, and trigger data. Do not proceed until all three are loaded.

---

## Prerequisites

- Logged in at app.apollo.io in Chrome
- Workspace email credentials ready
- Outbound phone number(s) ready to register

---

## Getting started

When this skill is loaded, greet the user:

> "I'm the Apollo Account Setup skill. I'll get your Apollo account ready before you build any campaigns — email linking, caller registration, dispositions, and contact stages. This runs once per account."

Then work through the steps in order.

---

## Step 1 — Email Linking

Prompt the user to complete these items in Apollo (Settings → Email):

```
EMAIL LINKING
[ ] Workspace email connected to Apollo
[ ] Daily send limits reviewed
[ ] Email signature set
[ ] Open/click tracking settings confirmed
```

Ask: "Confirm each item above is done before we continue."
Do not proceed until all four are confirmed.

---

## Step 2 — FCR Number Registration

Prompt:

```
FCR REGISTRATION
[ ] Outbound number(s) registered at freecallerregistry.com
[ ] Display name documented: _______________
[ ] Company name documented: _______________
    (keep these consistent — required again if you add numbers later)
```

Ask: "Confirm you've registered your number(s) and written down the display name + company name."
Do not proceed until confirmed.

---

## Step 3 — Dispositions Setup (Browser Automation)

Issue this warning before doing anything else:

> "This will delete all existing dispositions in your Apollo account and replace them with 19 custom entries. Type 'yes' to continue."

Wait for the user to type 'yes'. Do not proceed on any other response. Do not interpret "sure", "ok", or "yeah" as confirmation — require 'yes' exactly.

Once confirmed: execute the setup using `DISPOSITIONS` and `EXECUTION_GUIDE` from `dispositions_builder.py`. Delete all existing dispositions first, then add all 19 in order.

After completion, report:

```
Dispositions: 19 entries added
[ ] Total count: 19
[ ] "Left Voicemail" → Not Connected (verified)
[ ] "Meeting Scheduled" → Connected / Positive (verified)
```

If the count is not 19, stop and flag it before moving on.

---

## Step 4 — Contact Stages Setup (Browser Automation)

Execute using `STAGES` and `EXECUTION_GUIDE` from `stages_builder.py`. Add all 11 stages in order, Approaching first through Social/Email Only last.

After completion, report:

```
Contact Stages: 11 stages added
[ ] All 11 present, in order from Approaching to Social/Email Only
```

---

## Step 5 — Triggers Setup (Browser Automation)

Triggers auto-flip a contact's stage when a call is dispositioned. They handle stage changes; the Apollo Campaign Builder workflows handle sequence routing. Build both or the lifecycle will not move.

This step depends on Steps 3 and 4 — all 19 dispositions and all 11 stages must already exist before triggers can be saved.

Execute using `TRIGGERS` and `EXECUTION_GUIDE` from `triggers_builder.py`. The triggers section lives at the bottom of the same Dispositions page from Step 3. Add one trigger per disposition (19 total), each mapping a disposition to its target stage.

After completion, report:

```
Triggers: 19 disposition→stage triggers added
[ ] All 19 dispositions mapped, none left unmapped
[ ] "Meeting Scheduled" → "Meeting Pending" (verified)
[ ] "Left Voicemail" → "Approaching" (verified)
```

---

## Step 6 — Completion Summary

```
APOLLO ACCOUNT SETUP COMPLETE

[ ] Email Linking       confirmed
[ ] FCR Registration    confirmed
[ ] Dispositions        19 entries
[ ] Contact Stages      11 stages
[ ] Triggers            19 mappings

Your Apollo account is ready.
Next: run the Apollo Campaign Builder to set up your first client campaign.
```

---

## Voice Rules

Apply to all Claude-authored output — greetings, confirmations, step reports, error messages.

- No AI-tell openers: "Great question", "Absolutely", "Certainly", "Of course"
- No hedging: "I think", "it seems", "potentially", "it's worth noting"
- No AI vocabulary: "delve", "leverage", "utilize", "robust", "seamless", "comprehensive"
- No em-dashes. Hyphen or rewrite.
- Short. Direct. One idea per sentence.
