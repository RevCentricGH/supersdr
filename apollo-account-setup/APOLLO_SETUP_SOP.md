# Apollo Setup — Finalized SOP

> Single source of truth for SuperSDR Apollo account setup and configuration.
> Merges the official course SOP (Section 3, Lessons 2.5–2.15) with details
> captured from the course videos (vault: `Courses/SuperSDR/Setting Your Foundations/`).
> Sections marked **[+course]** were missing from the written SOP and added from the videos.

---

## Setup Order

Follow this sequence. The course is explicit: dialer before lists, lists before dialing.

1. Understand Apollo (2.5) → 2. Create + log in (2.5a) → 3. **Set up Trellus dialer [+course]** →
4. **Acquire phone numbers [+course]** → 5. Register numbers with FCR (2.6) →
6. Link email (2.7) → 7. Dispositions (2.8) → 8. Stages (2.9) → 9. **Triggers [+course]** →
10. Sequences (2.10) → 11. Email templates (2.10a) → 12. Workflows (2.15) →
13. **Build lists (2.11/2.12) [+course]** → 14. **Deals pipeline [+course]** →
15. **Remove-bad-contacts maintenance [+course]**

Dispositions, stages, triggers, sequences, and workflows are **account-wide, one-time** setup.
Lists and deals are ongoing.

---

## Lesson 2.5 — Apollo General Overview

Apollo is an all-in-one outbound platform: find people/companies, get contact data
(emails + mobiles, credit-based), organize into lists, run outreach, track outcomes,
track deals. "Where I source, organize, contact, and track prospects — end-to-end."

**The Apollo Map — 3 systems in 1:**

- **Data Layer** — search filters, saved searches, people/company data, emails+mobiles,
  enrichment/waterfalling, list building + segmentation, data hygiene, AI PowerUps
- **System of Action** — sequences, templates + snippets, task queue, saved task views,
  call dispositioning, follow-up management
- **System of Record** — contacts + accounts, owners/tags/lists, notes + activity timeline,
  call/email/task history, optional CRM sync (HubSpot/SF); plus pipeline + deals

**Apollo access tiers:**
- **Launch** — 14-day free trial (message the team to claim)
- **Accelerator** — Apollo included, 750 mobile credits/month
- **Inner Circle** — Apollo included, full done-for-you setup by the team

---

## Lesson 2.5a — Setting Up & Logging Into Apollo

1. Claim access for your tier (Launch = message for trial; Accelerator/Inner Circle =
   email `admin@revcentric.ai` with business name + email).
2. Log in at app.apollo.io.

---

## [+course] Lesson 2.5b — Set Up the Trellus Dialer

**This was absent from the written SOP. Trellus is the actual dialer reps use — not Apollo's
native dialer.** It integrates with Apollo; dispositions still live in Apollo. Set it up before
building lists so you can dial the moment lists are ready.

1. Get the Trellus invite. If not received, contact the Student/Community Success Manager —
   they send the invite to your email (subject: "Invitation to join RevCentric").
2. Open the email → Join / View Invitation.
3. Create the account via **Sign in with Google**.
4. Accept the invite → join the **RevCentric team**.
5. Install the **Trellus Chrome extension** (sign in again inside the extension if prompted).
6. Activate the extension.
7. On the Getting Started page, select **Apollo as the primary integration**.
8. Confirm the **Apollo Chrome extension** is also installed (required for Trellus to work).

---

## [+course] Lesson 2.5c — Acquire Phone Numbers

**Absent from the written SOP, which only covered FCR registration (2.6) — not acquiring the
numbers.** Numbers are bought in Trellus.

1. Trellus → **Numbers** → "start choosing numbers."
2. Search by local area code / city matching your target market. Confirm correct geo
   (e.g. "Phoenix, Arizona" not "Phoenix, Oregon").
3. Buy numbers one at a time. Option to **port your own numbers (BYON)** instead.
4. **Acquire 5 numbers** — the standard for initial setup.
5. If you hit "no longer available" or "number limit reached" — **reload the page**;
   acquired numbers often just aren't displaying.

**Apollo-side anti-spam profile (do once LLC/legal name exist):** add a **business profile**
to your number (LLC docs, legal business name) so the number is verified and looks legitimate.
Directly affects connect rates.

---

## Lesson 2.6 — Register Numbers with Free Caller Registry

Registration reduces spam labeling and improves trust for outbound calls.

1. Register your primary outbound numbers at freecallerregistry.com.
2. Document the submitted display name + company name so it stays consistent across systems.

---

## Lesson 2.7 — Link Email Accounts

If email isn't connected correctly, the rest of your automation is fake productivity.

1. Connect Workspace email.
2. Verify: send limits, signature, tracking settings.

---

## Lesson 2.8 — Dispositions (Setup Only)

**Path:** Settings → Team Dialer → Dispositions

**Goal:** one clean disposition list where every option is correctly marked Connected or
Not Connected. Apollo uses this toggle to decide if a contact advances in the sequence:

- **Connected** = contact will NOT advance (Apollo treats it as "we reached them")
- **Not Connected** = contact WILL advance (keep running the cadence)

**Steps:**
1. Delete all existing default dispositions (clean slate).
2. Click **+ Add Disposition**; for each, fill all three fields: **Name** (exact),
   **Connected with desired contact?** (Connected / Not Connected), **Call Sentiment**
   (Positive / Neutral / Negative). Save.

**[+course] Delete gotcha:** when deleting a disposition that already has calls logged against
it, reassign those calls to another disposition in the delete dialog — otherwise their
disposition history is nullified.

**The 19 dispositions:**

| Disposition | Connected? | Sentiment |
|---|---|---|
| Meeting Scheduled | Connected | Positive |
| Activated Lead | Connected | Positive |
| Connect Incomplete | Connected | Neutral |
| Referred Outward | Connected | Neutral |
| Not Me | Connected | Neutral |
| Not Now | Connected | Neutral |
| Meeting Confirmed | Connected | Neutral |
| Meeting Rescheduled | Connected | Neutral |
| Connect Incomplete - Follow Up | Connected | Neutral |
| Nurture | Connected | Neutral |
| Not Interested | Connected | Negative |
| Connect Incomplete - DNC | Connected | Negative |
| Bad / Wrong Number | Connected | Negative |
| Not in Swimlane | Connected | Negative |
| No Longer with Company | Connected | Negative |
| Connect Incomplete - Bad Data | Not Connected | — |
| Left Voicemail | Not Connected | — |
| Gatekeeper | Not Connected | — |
| No Answer / Not Available | Not Connected | — |

**Sanity check:** 19 total dispositions, each with the correct Connected/Not Connected
setting and sentiment.

**Common mistakes:** marking Voicemail as Connected (it must keep advancing the sequence);
creating ad-hoc custom dispositions; renaming dispositions later (breaks team consistency).

**[+course] Bad-data nuance — two deliberately different dispositions:**
- **Connect Incomplete - Bad Data** (Not Connected → stays in sequence): one phone number is
  bad but the contact is still viable via other channels. Manually delete the bad number from
  the contact record; the contact keeps running the cadence.
- **Bad / Wrong Number** (Connected → exits sequence): all contact info is bad. Use as the
  final step after exhausting numbers; pulls the contact out and routes to New Data Needed.

---

## Lesson 2.9 — Contact Stages & Lifecycle

**Path:** Settings → Contact Fields and Stages (search "Stage")

Stages = a lifecycle label ("where is this person right now?"). Distinct from dispositions
(last call outcome), sequences (the cadence), and deal stages (pipeline). **Dispositions
describe the last outcome; stages describe the current lifecycle state.**

**Steps:**
1. **[+course] Delete all existing stages first** (clean slate).
2. Create the 11 stages below in order. **[+course]** Set each stage's Apollo **status** field.

| # | Stage | Apollo Status | Meaning / when to use |
|---|---|---|---|
| 1 | Approaching | In Progress | Actively dialing; no meaningful convo yet, or needs another attempt soon |
| 2 | Meeting Pending | In Progress | Meeting booked; next objective is show-up + confirmation |
| 3 | Activated Lead | In Progress | Interested, understood the offer, but no meeting locked yet |
| 4 | Recycle | Not Succeeded | "No" for now / not a fit; may revisit if strategy changes |
| 5 | Referred Outward | In Progress | Directed to someone else; referral/intro path exists |
| 6 | New Data Needed | In Progress | Can't proceed until data is fixed (bad/wrong/bounced contact) |
| 7 | Not in Swimlane | In Progress | Real, reached person, but not the ICP for this campaign |
| 8 | Nurture | In Progress | Good fit, timing later (30+ days out) with a real reason |
| 9 | Active Client | In Progress | Now a paying customer; out of prospecting workflows |
| 10 | Meeting Held | In Progress | A booked meeting was completed (good or bad) — useful for reporting |
| 11 | Social/Email Only | In Progress | Do not call (DNC / phone restriction / compliance); email/LinkedIn only |

> Status values for stages 5–11 follow the same "In Progress" pattern as active lifecycle
> states; only Recycle is "Not Succeeded." Confirm against the live Apollo UI during dry run.

**Rep rule (daily):** "If I opened this contact tomorrow, would I instantly know what to do?"
If not, the stage is wrong. Daily filter order: Activated Lead → Meeting Pending → Approaching.
Clean up New Data Needed regularly.

**Common mistakes:** using stages like dispositions; leaving contacts in Meeting Pending after
the meeting happened; not using New Data Needed; treating Nurture as a graveyard.

---

## [+course] Lesson 2.9a — Triggers (Disposition → Stage Automation)

**Absent from the written SOP, which folded stage updates into Workflows. They are separate.**
Triggers live under the **Dispositions page** and auto-flip a contact's **stage** when a call
is dispositioned. Workflows (2.15) handle sequence routing; **triggers handle stage changes.**
Build both, or stages won't move.

**Disposition → Stage map:**

| Disposition | → Stage |
|---|---|
| Meeting Scheduled | Meeting Pending |
| Meeting Confirmed | Meeting Pending |
| Meeting Rescheduled | Meeting Pending |
| Activated Lead | Activated Lead |
| Connect Incomplete | Approaching |
| Connect Incomplete - Follow Up | Approaching |
| Connect Incomplete - Bad Data | Approaching |
| Gatekeeper | Approaching |
| No Answer / Not Available | Approaching |
| Left Voicemail | Approaching |
| Referred Outward | Referred Outward |
| Not Me | Referred Outward |
| Not Now | Nurture |
| Nurture | Nurture |
| Not Interested | Nurture |
| Connect Incomplete - DNC | Social/Email Only |
| Bad / Wrong Number | New Data Needed |
| Not in Swimlane | Not in Swimlane |
| No Longer with Company | Recycle |

> "Left Voicemail → Approaching" is inferred from the Not Connected = stays-in-sequence rule
> (not explicitly listed in the course video). Confirm during dry run.

---

## Lesson 2.10 — Sequences & Follow-Up Systems

**Path:** Engage → Sequences → Create a sequence from scratch (or Clone).

**[+course] Conventions:**
- **Name** every sequence with a company prefix for clean stat tracking
  (e.g. `GTM Operator AI - Activated Lead Sequence`).
- **Call priority:** set the first ~4 calls to **High** priority, the rest to **Medium**, so
  the call queue sorts least-dialed contacts to the top.

### Sequence 1 — Call-Only (10 steps, all phone calls, 2/day over 5 days)
| Step | Type | Timing |
|---|---|---|
| 1 | Phone Call | Immediately |
| 2 | Phone Call | +3 hours |
| 3 | Phone Call | +1 day |
| 4 | Phone Call | +3 hours |
| 5–10 | Phone Call | alternating +1 day / +3 hours |

### Sequence 2 — Activated Lead (7 steps; highest-value follow-up)
| Step | Type | Timing | Notes |
|---|---|---|---|
| 1 | Manual Email | Immediately | Reference last convo; attach relevant case study; ask for a 15-min call |
| 2 | Phone Call | +2 days | |
| 3 | Automatic Email | +5 days | Subject: `{first_name}, any thoughts on what I sent you?` (body blank) |
| 4 | Phone Call | +3 days | |
| 5 | Phone Call | +3 days | |
| 6 | Phone Call | +3 days | |
| 7 | Phone Call | +3 days | Final — close or disqualify |

**Step 1 email template:**
```
Subject: Hey {first_name}, {sender.first_name} here - {sender.company_name}

Pleasure speaking with you earlier! Based on our quick chat, I thought it would be
worth continuing the conversation around [Pains solved / Benefits discussed / Questions answered].

I've attached a case study that highlights how we helped [Similar company] achieve
[Result 1] and [Result 2]. I'd be happy to discuss how this applies to your situation
or answer any questions you might have.

Are you open to a brief 15-minute call sometime this week to dive deeper?
```

### Sequence 3 — Nurture (7 steps, ~84-day span)
| Step | Type | Timing |
|---|---|---|
| 1 | Manual Email | Immediately (acknowledge "now isn't the right time") |
| 2 | Automatic Email | +45 days (light check-in) |
| 3 | Phone Call | +15 days |
| 4 | Phone Call | +3 days |
| 5 | Phone Call | +3 days |
| 6 | Phone Call | +3 days |
| 7 | Phone Call | +15 days |

### Sequence 4 — Cold Follow-Up (high-frequency call cadence)
**[+course] Build by cloning the Call-Only sequence**, then extend. Official SOP cadence:
14 phone-call steps alternating +3 hours / +1 day, spacing out toward the end before
marking inactive.

### Sequence 5 — Pending Meeting (2 steps)
| Step | Type | Timing | Notes |
|---|---|---|---|
| 1 | Manual Email | +30 min | Confirmation + details; pull discussed pain points from the **Trellus transcript** |
| 2 | Action Item (manual task) | Immediately | **[+course] Reschedule the task to the day BEFORE the meeting** — it auto-creates as "due immediately." Call + confirm the day before. |

### Sequence 6 — Reschedule (10 phone-call steps)
Immediately → +1 day ×4 → +3 days ×5. Rebook missed/rescheduled meetings.

### Sequence 7 — Referred To (10 phone-call steps)
Same cadence as Reschedule. Work a referral/intro path.

---

## Lesson 2.10a — Email Templates

1. Open the **Fractional SDR Sales Emails** doc.
2. Add each into Apollo → Email Templates.

**[+course]** Personalization pulls specific conversation points from the **Trellus call
transcript** — use it to fill the `[bracketed]` personalization slots.

---

## Lesson 2.15 — Core Workflows

**Path:** Workflows → Add workflow → Start from scratch → Based on a trigger event.

Workflows auto-route a contact into the right follow-up **sequence** after a call is logged.
(Stage changes are handled by Triggers, 2.9a.)

**[+course] Build config for every workflow:**
1. Trigger event: **Call Logged**
2. Source sequence: **Call-Only Sequence**
3. User: by the user
4. Disposition: (varies — see below)
5. Add block → Manage Sequences → **Add contacts to a sequence** → target sequence
6. Check **"Send emails from the contact owner"**
7. Rename clearly, then launch.

**The 4 workflows:**

| Workflow | Trigger Disposition | Adds to Sequence |
|---|---|---|
| Meeting Scheduled | Meeting Scheduled | Pending Meeting Sequence |
| Activated Lead | Activated Lead | Activated Lead Sequence |
| Nurture | Nurture | Nurture Sequence |
| Connect Incomplete | Connect Incomplete | Cold Follow-Up Sequence |

**Verify each workflow:** triggers off the correct disposition → routes to the correct
sequence → (paired trigger updates the lifecycle stage).

---

## [+course] Lesson 2.11 — Building Lists (Sourcing)

**Absent from the written SOP entirely.** Build after the dialer + numbers are ready.

**Path:** Apollo search icon → left-hand filter tree. Start at the **people level**.

**Personas (core mechanic):** build reusable saved personas so you don't rebuild criteria
each time. Components: **Job Titles + Industries + Keywords + Person Location + Number of
Employees**. Save as a reusable starting point.

**Keywords (two levels):** apply keywords both **within the industry selection** and at the
**general search level** to narrow as tightly as possible. Keyword = the term appears somewhere
in the prospect's business.

**Look-alike discovery:** run the **Apollo Chrome extension on an ideal client's website** to
extract descriptive keywords, then feed those back into Apollo search to find similar companies.

**Email-status filters (mandatory):** always apply **safe to send / likely to engage /
verified** — yields better numbers and contacts (cut ~2,000 weak contacts in one demo).

**Exclusions:** exclude unwanted titles (from the list or the persona); exclude your employer,
competitors, non-targets; exclude contacts already in current sequences or existing lists.

**Defer for now:** lead scoring and territory alignment — configure later.

---

## [+course] Lesson 2.13 — Deals Pipeline

**Absent from the written SOP.** This is the SDR's **own** client-closing pipeline, not a
prospect list.

**Path:** Settings → search "deal" → Pipeline → Edit pipeline → **delete default stages first**.
Rename the pipeline (e.g. `GTM Operator AI`). View under **Deals**.

| # | Stage | Probability | Forecast |
|---|---|---|---|
| 1 | Activated Lead | 0% | Open / pipeline |
| 2 | Discovery Booked | 5% | Open |
| 3 | Discovery Held | 10% | Open |
| 4 | Close Call Booked | 20% | Open / Best Case |
| 5 | Proposal | 30% | Open / Best Case |
| 6 | Closed Won | 100% | Commit |
| 7 | Closed Lost | 0% | Omit from forecast |
| 8 | Disqualified | 0% | Omit from forecast |
| 9 | Churned | 10% | Closed Lost, win-back chance; Best Case |

Keep updated; reviewed in one-on-ones.

---

## [+course] Maintenance — Remove Bad Contacts from Sequences

**Absent from the written SOP.** Run weekly.

1. Sequences → select the sequence → **Contacts** tab → **Show Filters**.
2. Filter by **Job Title**; enter each wrong-fit title (CTOs, Engineers, AEs, etc.).
3. Select all filtered contacts → **Remove** from the sequence.

Also tighten list-building criteria upfront to reduce cleanup.

---

## Source Reconciliation Notes

- The written SOP's **19 dispositions** and **11 stages** are the canonical, cleaned versions;
  the course videos showed messier in-progress lists. Defer to the tables above.
- The course videos add: Trellus dialer, phone-number acquisition, triggers, list building,
  deals pipeline, bad-contact maintenance, and the per-section details flagged **[+course]**.
- UI steps (dispositions, stages, triggers) still need **dry-run validation** against the
  live Apollo UI per the skill's status note. Confirm status-field values and the inferred
  "Left Voicemail → Approaching" trigger during that run.
