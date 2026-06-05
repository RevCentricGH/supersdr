# Call-type templates

Single source of truth for how `pre-brief` frames a brief per call type. `SKILL.md` reads
this file at Step 1c (to confirm the inferred type) and at Step 2 (to extract points using the
active template). The framing question, point kinds, Doc title pattern, and one-page rule for
each call type live here and nowhere else. If any of those need to change, change them here.

## Which types are selectable

The confirm prompt in `SKILL.md` offers exactly two types: `pre-disco` and `pre-onboarding`.
Both are fully implemented below. `pre-closing` is a stub, NOT YET IMPLEMENTED, and is never
offered in the prompt. If an operator names `pre-closing` or any other string, the skill keeps
the inferred template, tells the operator that type is not available, and asks them to confirm
`pre-disco` or `pre-onboarding`.

The one-page rule applies to every type: the "What matters going in" section is 5 to 8 points,
one sentence each. Do not pad to a number. A point that cannot be anchored to a specific moment
in the transcript is left out.

---

## pre-disco (Discovery)

The existing default. The reader is the seller going into a discovery or booking call with a
prospect. The brief is framed on what the seller needs to know to run the call well: what the
prospect is worried about, where they pushed back, what they asked for, and what each side
committed to.

**Framing question:** What do I need to know going into this call to move the deal forward?

**Point kinds** (tag each point with exactly one):

- **Concern** - something the prospect is worried about.
- **Objection** - a reason they gave for hesitating or pushing back.
- **Ask** - a request, a question they want answered, or something they want to see.
- **Commitment** - something either side agreed to do next.

**Doc title pattern:** `Pre-Brief (Discovery): {prospect or meeting name}`

This is the framing `pre-brief` shipped with before call-type awareness. An operator who accepts
the inferred `pre-disco` type, or overrides to it, gets the same brief they got before.

---

## pre-onboarding (Onboarding)

The reader is the person running the first active session with a client who just signed. The
sale is done. The brief is framed on what the new client needs and expects going into onboarding,
not on what the seller needs to close. The goal is to walk into the kickoff already knowing what
this client is counting on, what they are nervous about, and what was promised during the sale.

**Framing question:** What does this new client need and expect going into their first active
session?

**Point kinds** (tag each point with exactly one):

- **Expectation** - an outcome, timeline, or standard the client is counting on.
- **Concern** - something the client is nervous or uncertain about going into onboarding.
- **Commitment from sale** - something promised or agreed during the sales process that the
  client expects to be honored.
- **Open question** - something unresolved that the first session needs to answer.

**Doc title pattern:** `Pre-Brief (Onboarding): {client or account name}`

**Prior artifacts:** an onboarding brief is stronger when it can reference what was promised
before the call. If the operator pasted prior artifacts at Step 1b (a proposal, a prior brief,
Apollo notes), use them to ground **Commitment from sale** and **Expectation** points. Summarize
only the call-relevant fact in the point. Anchor the point to the transcript moment where the
client referenced or relied on that commitment, not to the artifact. Do not copy raw artifact
text, private URLs, or any secrets into the Doc. If a commitment appears only in an artifact and
never surfaces in the transcript, leave it out: every point still anchors to the transcript.

---

## pre-closing (Closing)

NOT YET IMPLEMENTED - do not select. Use `pre-disco` or `pre-onboarding`.

This block is a placeholder for a future closing-call variant (framing on what it takes to get
the prospect to sign). It is absent from the confirm prompt in `SKILL.md` on purpose. The skill
must not extract points using this block. If an operator asks for `pre-closing`, redirect them
to an implemented variant.
