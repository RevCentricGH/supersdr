---
name: pre-brief
description: Turn a booking-call transcript into a one-page Google Doc meeting brief — paste the transcript or link a Drive/Gemini/Fireflies recording, and get back 5-8 bullets covering the concerns, objections, asks, and commitments from the call, each anchored to the exact transcript line it came from. Trigger when the user says "brief me on this call", "prep me for this meeting", "run pre-brief", pastes a transcript and wants meeting prep, shares a Drive/Gemini/Fireflies link and asks for a brief, or says "what do I need to know going into this meeting".
---

# pre-brief

Paste a booking-call transcript or link a Drive/Gemini/Fireflies recording and get back a one-page Google Doc meeting brief. The brief covers what matters going into the meeting — concerns, objections, asks, and commitments — with each point anchored to the exact transcript line so you can verify and recall the context fast.

Requires: Google Drive connector with write access in Cowork settings.

## What to give it

Either:
- Paste the full transcript text directly in your message, or
- Share a Drive, Gemini, or Fireflies link to the transcript.

If a link is given, fetch and read the full document before doing anything else. Do not classify or extract bullets until the full text is loaded.

## What it produces

1. **Read the full transcript.** If a link was given, fetch the complete document via the Google Drive connector. Confirm the full text is loaded before proceeding.

2. **Extract 5-8 bullets** covering the substantive moments from the call: concerns raised, objections, asks or requests, and commitments made. Leave out small talk and filler. Each bullet must come from a real, specific moment in the transcript — no interpretation or gap-filling.

3. **Anchor each bullet** to the transcript. Identify the line or exchange it came from. Include a short direct quote or speaker label so the reader can find it without re-reading the whole call.

4. **Build the Google Doc** via the Google Drive connector:
   - Title: "Pre-Brief: [prospect or meeting name]"
   - Section "What matters going in" — numbered list of the 5-8 bullets, each with its anchor reference
   - Section "Transcript anchors" — the source line for each bullet, bolded and labeled (e.g., "Point 3")

5. **Return the View link** so the brief can be opened on any device or shared.

## Voice rules

No AI-tell openers, no hedging, no AI vocabulary, no em-dashes. Each bullet is one sentence. If a point cannot be grounded in a specific transcript moment, leave it out.
