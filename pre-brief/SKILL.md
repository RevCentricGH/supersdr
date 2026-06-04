---
name: pre-brief
description: Turn a booking-call transcript into a one-page Google Doc meeting brief. Paste the transcript or share a Drive, Fireflies, or Gemini link, and get back 5 to 8 bullets covering the concerns, objections, asks, and commitments from the call, each anchored to the transcript timestamp it came from, followed by a transcript-anchors section, returned as a View link. Trigger this skill when the user says brief me on this call, prep me for this meeting, run pre-brief, what do I need to know going into this meeting, pastes a call transcript and wants meeting prep, or shares a Drive, Fireflies, or Gemini recording link and asks for a brief or a pre-read before a meeting.
---

# pre-brief

## Purpose

Turn one booking-call transcript into a one-page Google Doc meeting brief and return the View link. The brief covers what matters going into the next meeting: the concerns raised, the objections, the asks, and the commitments made. Every point is anchored to the transcript timestamp it came from, so the reader can jump straight to the moment and verify it.

Per-meeting and interactive. No dialer, no transcription, no sheet, no terminal. It reads a transcript and writes a Doc.

## Getting started

When this skill loads, greet the user:

> "I'm pre-brief. Paste a booking-call transcript or share a Drive, Fireflies, or Gemini link, and I'll turn it into a one-page meeting brief: the concerns, objections, asks, and commitments, each anchored to the moment in the call it came from. You get back a Google Doc View link."

Assume the Google Drive connector is connected with write access. Proceed once the user provides a transcript or a link.

**Only if creating the Doc fails:** "Looks like Google Drive is not connected with write access in Cowork. Go to Settings -> Connectors -> Google Drive, connect your account, and enable edit permission. Then tell me you're ready, or say the word and I'll hand you the brief as text to paste into a Doc yourself."

## What to give it

Either:

- Paste the full transcript text directly in the message, or
- Share a Drive, Fireflies, or Gemini link to the transcript.

If a link is given, fetch and read the complete document through the Google Drive connector before doing anything else. Do not extract points until the full text is loaded.

## Workflow

### Step 1 - Load the full transcript

If the user pasted the transcript, use it as-is. If they gave a link, fetch the whole document through the connector and confirm the full text loaded. Never extract from a partial read.

Note whether the transcript has timestamps (most call tools stamp each line, e.g. `[00:14:32]` or `00:14`). The anchor format depends on this:

- Timestamps present: anchor every point to its timestamp.
- No timestamps: anchor to a short verbatim quote and the speaker label instead, so the reader can still find the moment.

### Step 2 - Extract 5 to 8 points

Pull the 5 to 8 substantive moments from the call. Each point falls into one of four kinds:

- **Concern** - something the prospect is worried about.
- **Objection** - a reason they gave for hesitating or pushing back.
- **Ask** - a request, a question they want answered, or something they want to see.
- **Commitment** - something either side agreed to do next.

Rules for the points:

- Each point is one sentence, grounded in a real, specific moment in the transcript. No interpretation, no gap-filling, no inventing what was not said.
- Tag each point with its kind (Concern, Objection, Ask, or Commitment).
- Anchor each point to its timestamp (or, if the transcript is unstamped, a short verbatim quote plus the speaker).
- Leave out small talk and filler. If you cannot ground a point in a specific moment, drop it rather than padding to hit a count.

### Step 3 - Build the Google Doc

Create the brief with the Google Drive connector. The connector must have write permission.

1. **Create a Doc** titled `Pre-Brief: {prospect or meeting name}`. Infer the name from the transcript; if it is unclear, ask the user in one line.
2. **Write section "What matters going in"** - a numbered list of the 5 to 8 points in priority order (the things most likely to come up first). Each line carries its kind tag and its anchor. Format each as:

   `1. [Concern, 00:14:32] One-sentence point grounded in that moment.`

3. **Write section "Transcript anchors"** - for each point, the source line pulled from the transcript so the reader can verify without reopening the call. Label each with a bolded point number that matches the list above:

   `**Point 3** [00:14:32] "verbatim line or short exchange from the transcript"`

4. **Capture the Doc URL** once creation is confirmed.

The templates above are content specs, not literal text. Apply bold through the connector's formatting, never literal `**` characters - the anchor labels read as bold "Point 3", not `**Point 3**` with asterisks in the Doc. If the connector cannot apply bold, write the label as plain text.

Output is the structured Doc only. Do not build a styled-HTML one-pager or any other artifact.

If the connector is not connected or lacks write permission, output the full brief as formatted text instead and tell the user:

> "Paste this into a new Google Doc titled 'Pre-Brief: {name}'."

### Step 4 - Deliver the View link

Give the user the Google Doc View link and a one-line summary of what is in it (how many points, the spread across concerns/objections/asks/commitments). Do not re-list the points; the user can open the Doc.

## Voice rules

These apply to everything this skill produces - the Doc and Claude's own messages:

- No AI-tell openers: "Great question", "Absolutely", "Certainly", "Of course".
- No hedging: "I think", "it seems", "potentially", "it's worth noting".
- No AI vocabulary: "delve", "leverage", "utilize", "robust", "seamless", "comprehensive".
- No em-dashes. Use a hyphen or rewrite.
- Each point in the brief is one sentence. Short. Direct. One idea per line.
- If a point cannot be grounded in a specific transcript moment, leave it out.

## Gotchas

- **Read the whole transcript first.** A point anchored to a moment you skipped is worse than no point. Load the full text before extracting, especially when the input is a link.
- **Anchor everything.** A bullet with no timestamp (or no quote, on an unstamped transcript) is an unverifiable claim. Every point gets an anchor or it does not ship.
- **Do not pad to a number.** Five well-grounded points beat eight where three are filler. The range is 5 to 8, not a quota.
- **Quote, do not paraphrase, in the anchors section.** The "Transcript anchors" lines are verbatim so the reader can trust them. Paraphrase belongs in the "What matters going in" points, not the anchors.
- **One pass into the Doc.** If you write section by section and something lands out of order, re-read the Doc through the connector and fix it before handing over the link.
