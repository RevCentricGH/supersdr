---
name: custom-decks
description: Generate a tailored prospect deck end-to-end from a single prospect (name, company, website) plus a call transcript or audio URL, rendered to Google Slides and PDF, returning a View link. Trigger when the user wants to build a custom deck for a specific prospect, says things like "build a deck for this prospect", "make a custom deck", "generate a pitch deck from this call", or "run custom-decks". This is a Claude Code skill that runs in a terminal with real Python, Node/Marp, local API keys, and a Google OAuth token file, not a Cowork skill. It transcribes audio with Deepgram and a Groq fallback, scrapes the prospect site within character budgets, drafts grounded copy with Claude (refusing on insufficient signal), renders a Marp deck to PDF and PPTX, uploads it to Drive as Google Slides with a clickable CTA, and returns the Slides View URL.
---

# custom-decks

> **Claude Code skill - runs in a terminal, NOT Cowork.** This skill is real Python that needs
> a shell, the filesystem, Node (for Marp), local API keys (Deepgram, Groq, Anthropic), and a
> Google OAuth token file. Do not upload it into the Cowork desktop app. Run it from a terminal
> with `python3 run.py`.

Build a deck tailored to one prospect, grounded in their call and their website, rendered to
Google Slides + PDF, and returned as a View link. This is the ad-hoc, single-prospect tracer
bullet for the deck pipeline. Branding config, section auto-omit, the refuse-boilerplate quality
gate, and queue mode (reading activated leads off the master-tracker sheet) are later slices.

## What it does on a run

1. **Transcribe** (only if you pass an audio URL). Deepgram is the primary provider; Groq is the
   fallback, and it fires only when Deepgram comes back empty. If both come back empty, the run
   stops with a clear error rather than building a deck on no transcript. If you already have a
   transcript, pass it and this step is skipped.
2. **Scrape the site.** It fetches the prospect's site across a configured subpage list, strips
   the HTML, and keeps the text within a per-subpage budget and a total budget so the copy prompt
   stays grounded without blowing up.
3. **Generate copy with Claude.** It builds a prompt from the prospect, the transcript, and the
   scraped site, then parses the model's JSON (fenced, bare-fenced, or prose-wrapped) and checks
   the required keys. If the model judges there is not enough real signal it returns
   `INSUFFICIENT_SIGNAL`, and the run stops rather than shipping boilerplate.
4. **Process tokens.** Each copy token is capped at a per-token character budget (the excess is
   logged, never silently dropped) and wrapped to a line width.
5. **Render.** A Marp deck source is built (with the company name and a clickable CTA) and rendered
   to a PDF and a PPTX.
6. **Upload.** The PPTX is uploaded to Google Drive, converted to a Google Slides presentation,
   with retry/backoff on transient failures. The run returns the Slides View URL and verifies the
   uploaded slides actually carry the configured CTA link and the company name.

## Setup

One-time per operator. Everything runs on your own accounts.

1. **Install dependencies** (Python 3.10+ and Node 18+):

   ```
   cd custom-decks
   python3 -m pip install -r requirements.txt
   # Marp is run via npx; no global install needed. For Slides with selectable text and
   # live hyperlinks, also install LibreOffice (soffice) so the editable-PPTX path is used.
   ```

2. **Create your config.** Copy the template and fill it in. Your real config is gitignored.

   ```
   cp config.template.json config.json
   ```

   Fields:
   - `deepgram_api_key` / `groq_api_key` - transcription keys. Groq is only used as a fallback.
   - `anthropic_api_key` - the key the copy step uses.
   - `subpages` - the path list scraped off the prospect site (`""` is the homepage).
   - `per_subpage_char_budget` / `total_char_budget` - how much scraped text to keep, per page
     and in total.
   - `per_token_char_budget` / `line_width` - the per-token cap and wrap width for copy.
   - `required_copy_keys` - the keys the copy JSON must contain.
   - `cta_text` / `cta_url` - your booking link. This is the CTA stamped on the deck (the deck
     always uses your configured CTA, not whatever the model writes).
   - `google_oauth.credentials_file` / `google_oauth.token_file` - your Google OAuth client
     secret and the token file written after the first authorization.

3. **Set up Google OAuth.** In Google Cloud Console, enable the Google Drive API and the Google
   Slides API, create an OAuth client (Desktop app), download the client secret JSON, and point
   `credentials_file` at it. The first run opens a browser to authorize and writes `token_file`.

## Run

```
python3 run.py --name "Jane Doe" --company "Acme Corp" --website https://acme.com \
    --transcript path/to/call.txt
python3 run.py --name "Jane Doe" --company "Acme Corp" --website https://acme.com \
    --audio-url https://.../call.mp3
```

It prints the Google Slides View URL for the generated deck.

## How it is built

The logic lives in the `customdecks` package and is unit-tested with injected fakes (no live
credentials needed to run the tests):

- `transcriber.py` - `Transcriber`: Deepgram primary, Groq fallback only when Deepgram is empty.
- `site_scraper.py` - `SiteScraper`: fetch + tag-strip within per-subpage and total budgets.
- `deck_copy_generator.py` - `DeckCopyGenerator`: prompt build, tolerant JSON parse, key
  validation, and the `INSUFFICIENT_SIGNAL` refusal.
- `token_processor.py` - `TokenProcessor`: per-token char budget and line-wrap.
- `template_renderer.py` - `TemplateRenderer`: Marp source build + render to PDF and PPTX.
- `drive_uploader.py` - `DriveUploader`: upload with retry/backoff, View-URL build, and a
  post-upload Slides verification of the CTA link and company name.
- `build_deck.py` - wires the above into the full pipeline and the `main` CLI entry point.

Run the tests from the repo root:

```
python3 -m pytest custom-decks
```
