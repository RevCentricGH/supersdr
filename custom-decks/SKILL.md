---
name: custom-decks
description: Generate a tailored prospect deck end-to-end from a single prospect (name, company, website) plus a call transcript or audio URL, rendered to Google Slides and PDF, returning a View link. Trigger when the user wants to build a custom deck for a specific prospect, says things like "build a deck for this prospect", "make a custom deck", "generate a pitch deck from this call", or "run custom-decks". This is a Claude Code skill that runs in a terminal with real Python, Node/Marp, local API keys, and a Google OAuth token file, not a Cowork skill. It transcribes audio with Deepgram and a Groq fallback, scrapes the prospect site within character budgets, drafts grounded copy with Claude (refusing on insufficient signal), renders a Marp deck to PDF and PPTX, uploads it to Drive as Google Slides with a clickable CTA, and returns the Slides View URL.
---

# custom-decks

> **Claude Code skill - runs in a terminal, NOT Cowork.** This skill is real Python that needs
> a shell, the filesystem, Node (for Marp), local API keys (Deepgram, Groq, Anthropic), and a
> Google OAuth token file. Do not upload it into the Cowork desktop app. Run it from a terminal
> with `python3 run.py`.

Build a deck tailored to one prospect, grounded in their call and their website, branded as
your own agency, rendered to Google Slides + PDF, and returned as a View link only when the
deck passes the refuse-boilerplate quality gate. Agency identity (name, logo, sender, copy
voice) and proof (stat cards, case studies, client logos, founder-authority cards) all come
from config and bundled assets, so the deck is yours and nothing is hardcoded. A proof section
you leave empty is dropped, so you ship a clean shorter deck rather than empty placeholder
slides. Two modes: ad-hoc (one prospect in, one View link out) and queue mode, which reads
the activated leads off the master-tracker sheet and builds a deck for each. The mode is
chosen by config: set `queue.google_sheet_id` to run the queue, leave it blank for ad-hoc.

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
5. **Render.** A Marp deck source is built - branded with your agency identity (name, logo,
   sender, copy voice) and your proof (stat cards, case studies, client logos, founder-authority
   cards) from config, plus the prospect company and a clickable CTA - and rendered to a PDF and
   a PPTX. Proof sections you leave empty in config are dropped from the deck.
6. **Upload.** The PPTX is uploaded to Google Drive, converted to a Google Slides presentation,
   with retry/backoff on transient failures.
7. **Quality gate.** Before the View link is surfaced, the deck must pass the refuse-boilerplate
   gate: a rendered PDF is present and above a size floor, the preview link answers a real HTTP
   request with a 2xx status, the copy did not overflow the token budget, the rendered text
   carries no transcript artifacts (speaker labels, timestamps, inaudible/crosstalk markers), and
   no generic wallpaper is applied across the slides. The gate runs every check and reports all
   failures at once. On a full pass the run writes the Slides View URL and verifies the slides
   carry the configured CTA link and company name. On any failure the deck is kept locally, the
   View link is not published, and every failure reason is printed.

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
   - `token_budget` - the total deck-copy character budget the quality gate enforces. A deck
     whose copy overflows this is rejected as over-stuffed.
   - `required_copy_keys` - the keys the copy JSON must contain.
   - `cta_text` / `cta_url` - your booking link. This is the CTA stamped on the deck (the deck
     always uses your configured CTA, not whatever the model writes).
   - `google_oauth.credentials_file` / `google_oauth.token_file` - your Google OAuth client
     secret and the token file written after the first authorization.
   - `assets_dir` - the bundled assets folder, resolved relative to `config.json` (default
     `assets`). Drop your logo and client logos in here; reference them as `assets/...`. Asset
     paths must be relative and may not point outside the skill folder.
   - `agency.name` / `agency.logo` / `agency.sender` / `agency.voice` - your agency identity.
     `logo` is a path under your assets folder; `sender` is `{name, title, email}`; `voice` is
     the brand line shown on the deck.
   - `proof.stat_cards` / `proof.case_studies` / `proof.client_logos` / `proof.founder_authority`
     - your proof. Each is a list; leave any of them empty and that section is omitted from the
     deck. `client_logos` are paths under your assets folder.

3. **Set up Google OAuth.** In Google Cloud Console, enable the Google Drive API and the Google
   Slides API, create an OAuth client (Desktop app), download the client secret JSON, and point
   `credentials_file` at it. The first run opens a browser to authorize and writes `token_file`.

## Run

Ad-hoc mode (no `queue.google_sheet_id` set):

```
python3 run.py --name "Jane Doe" --company "Acme Corp" --website https://acme.com \
    --transcript path/to/call.txt
python3 run.py --name "Jane Doe" --company "Acme Corp" --website https://acme.com \
    --audio-url https://.../call.mp3
```

It prints the Google Slides View URL for the generated deck.

Queue mode (set `queue.google_sheet_id` to the master-tracker sheet):

```
python3 run.py --config config.json
```

It reads the activated leads (a kept disposition) from each configured rep tab, builds a deck
for every one that has a recording link plus a `Company` and `Website` (add those as manual
columns on the rep tab), and writes the View link into the `Custom Decks` tab. It skips leads
already linked, so re-running only fills the gaps, and a lock file blocks overlapping runs.

## How it is built

The logic lives in the `customdecks` package and is unit-tested with injected fakes (no live
credentials needed to run the tests):

- `transcriber.py` - `Transcriber`: Deepgram primary, Groq fallback only when Deepgram is empty.
- `site_scraper.py` - `SiteScraper`: fetch + tag-strip within per-subpage and total budgets.
- `deck_copy_generator.py` - `DeckCopyGenerator`: prompt build, tolerant JSON parse, key
  validation, and the `INSUFFICIENT_SIGNAL` refusal.
- `token_processor.py` - `TokenProcessor`: per-token char budget and line-wrap.
- `branding.py` - `load_branding`: the agency-identity + proof config schema, with every asset
  path resolved relative to `config.json` (no absolute or escaping paths).
- `template_renderer.py` - `TemplateRenderer`: Marp source build (branded from config, empty
  proof sections auto-omitted) + render to PDF and PPTX.
- `drive_uploader.py` - `DriveUploader`: upload with retry/backoff, View-URL build, and a
  post-upload Slides verification of the CTA link and company name.
- `quality_gate.py` - `QualityGate`: the refuse-boilerplate checks (PDF present + size floor,
  preview link reachable, token-budget overflow, transcript-artifact text, generic-wallpaper
  guard). Read-only; it never deletes the deck. Returns every failure reason; the View link is
  written only on a full pass.
- `build_deck.py` - wires the above into the full pipeline and the `main` CLI entry point.

Run the tests from the repo root:

```
python3 -m pytest custom-decks
```

## Troubleshooting

| Symptom | Likely cause and fix |
| --- | --- |
| `marp: command not found` or `npx: command not found` | Node is missing. Marp runs via `npx`, which ships with Node 18+. Install Node, then re-run. No global Marp install is needed; `npx` fetches it. |
| OAuth fails with `redirect_uri_mismatch`, or no token file is written | The OAuth client is the wrong type. Create the client as an **OAuth client ID, Desktop app** in Google Cloud Console (not Web application), download the client secret JSON, and point `credentials_file` at it. Then delete any stale token file and re-run to re-authorize. |
| Upload fails with an API-not-enabled error | The Google APIs are off for your project. In Google Cloud Console, enable **both** the Google Drive API and the Google Slides API on the same project the OAuth client belongs to, then re-run. |
| Deck renders but links are not clickable / text is not selectable | LibreOffice (`soffice`) is missing, so the fallback image-PPTX path is used instead of the editable path. Install LibreOffice so the editable-PPTX path runs and the CTA stays a live hyperlink. |
| Run stops with an empty-transcription error | Both Deepgram and Groq returned nothing for the audio. Confirm the `--audio-url` is reachable and points at real audio, or skip transcription entirely by passing `--transcript` with the text you already have. |
