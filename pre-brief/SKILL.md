---
name: pre-brief
description: Turn a booking-call transcript into a one-page branded .docx meeting brief. Paste the transcript or share a Drive, Fireflies, or Gemini link, and get back 5 to 8 bullets covering the concerns, objections, asks, and commitments from the call, each anchored to the transcript timestamp it came from, followed by a transcript-anchors section, delivered as a branded .docx. Trigger this skill when the user says brief me on this call, prep me for this meeting, run pre-brief, what do I need to know going into this meeting, pastes a call transcript and wants meeting prep, or shares a Drive, Fireflies, or Gemini recording link and asks for a brief or a pre-read before a meeting.
---

# pre-brief

## Purpose

Turn one booking-call transcript into a one-page branded .docx meeting brief and deliver the file. The brief covers what matters going into the next meeting: the concerns raised, the objections, the asks, and the commitments made. Every point is anchored to the transcript timestamp it came from, so the reader can jump straight to the moment and verify it.

Per-meeting and interactive. No dialer, no transcription, no sheet. It reads a transcript and renders a branded .docx with the bundled `assets/build_docx.py`. It does NOT write Google Docs.

**Runtime: Claude Cowork**

## Getting started

When this skill loads, greet the user:

> "I'm pre-brief. Paste a booking-call transcript or share a Drive, Fireflies, or Gemini link, and I'll turn it into a one-page meeting brief: the concerns, objections, asks, and commitments, each anchored to the moment in the call it came from. You get back a branded .docx."

Proceed once the user provides a transcript or a link. The .docx is rendered locally with the bundled builder; the Google Drive connector is used only to upload the finished file for a View link.

**Only if rendering or upload fails:** if `render.sh` reports no Python with `python-docx`, say so and print the install hint it gives. If Drive upload fails, tell the user Google Drive is not connected with write access in Cowork (Settings -> Connectors -> Google Drive, enable edit permission), then hand them the rendered .docx directly. Do not paste the brief into chat as a substitute; the .docx is the deliverable (matches Step 3).

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

### Step 3 - Render the branded .docx

Map the brief into the `build_docx.py` JSON schema, then render. Do NOT create a Google Doc. The full schema is documented in the docstring of `assets/build_docx.py`. Mapping:

- `title_block`: eyebrow `PRE-BRIEF`, title `Pre-Brief: {prospect or meeting name}`, `columns` for Meeting / Date / Prepared by (infer the name from the transcript; if unclear, ask the user in one line), optional `footer` like "Read before the call. Every point is anchored in Transcript anchors."
- An `h1` block `What matters going in`, then a `numbered` block: one `{n, label, text}` item per point, in priority order (the things most likely to come up first). `label` carries the kind tag and anchor (e.g. `Concern, 00:14:32`); `text` is the one-sentence point grounded in that moment.
- An `h1` block `Transcript anchors`, then one `p` block per point with the verbatim source line so the reader can verify without reopening the call. Lead each with a bold point number that matches the list above:

  `**Point 3** [00:14:32] "verbatim line or short exchange from the transcript"`

Use `**bold**` inside strings for emphasis; the builder converts it to real bold, so never leave literal asterisks in the output text. On an unstamped transcript, use the short verbatim quote plus speaker label in place of the timestamp anchor.

Write the JSON to a temp file, then render through the bundled wrapper (not a bare `python3`, which may hit a Python without `python-docx`):

```
bash <skill_dir>/assets/render.sh content.json "Pre-Brief - {name}.docx"
```

`render.sh` selects a Python that has `python-docx` (prefers `~/.venv`) and exits with an install hint if none does. This is how Cowork runs the styled-.docx builder; it is separate from the Drive connector (which only uploads plain text).

No em dashes anywhere in the content. The builder hard-fails on `—`; rewrite into separate sentences or use a comma, colon, or parentheses (never a hyphen).

**If no Python has python-docx:** render.sh prints the install command. If you cannot render, say which capability is missing. Don't paste the brief into chat as a substitute. The .docx is the deliverable.

### Step 4 - Deliver the .docx

Upload the rendered .docx through the Google Drive connector and share the View link, or hand the user the file directly if Drive is not connected. Add a one-line summary of what is in it (how many points, the spread across concerns/objections/asks/commitments). Do not re-list the points; the user can open the file.

## Voice rules

These apply to everything this skill produces - the .docx and Claude's own messages:

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
- **Build the full JSON before rendering.** Assemble the whole `content.json` in one pass, then render once. If a point lands out of order, fix the JSON and re-render; do not patch the .docx by hand.
- **No em dashes.** The builder hard-fails on `—`. Keep every point and anchor em-dash-free; use a comma, colon, or parentheses, never a hyphen.
