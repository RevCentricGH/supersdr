"""build_deck - the ad-hoc end-to-end pipeline.

One prospect (name, company, website) plus a transcript or an audio URL go in; a Google
Slides View link comes out. The steps - transcribe (if audio), scrape the site, generate copy
with Claude, process tokens, render Marp to PDF + PPTX, upload to Drive as Slides - each live
in their own module and are passed in via ``Deps`` so the whole pipeline can be exercised with
fakes. ``main`` wires the real collaborators from ``config.json`` and runs a single prospect.

The CTA shown on the deck is the operator's *configured* booking link, not whatever the model
emits, so the clickable call-to-action always points where the operator wants it.
"""
import argparse
import os
import sys
from urllib.parse import urljoin

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from customdecks.deck_copy_generator import REQUIRED_KEYS
from customdecks.errors import InputError

PROSE_KEYS = ("headline", "problem", "solution", "proof")


class Deps:
    """The pipeline's collaborators. Real ones in ``main``; fakes in tests."""

    def __init__(self, *, transcriber, scraper, copy_generator, token_processor, renderer, uploader):
        self.transcriber = transcriber
        self.scraper = scraper
        self.copy_generator = copy_generator
        self.token_processor = token_processor
        self.renderer = renderer
        self.uploader = uploader


def _subpage_urls(website, subpages):
    base = website if website.endswith("/") else website + "/"
    urls = [website]
    for sub in subpages or []:
        sub = str(sub).strip().lstrip("/")
        if not sub:
            continue
        url = urljoin(base, sub)
        if url not in urls:
            urls.append(url)
    return urls


def build_deck(
    prospect,
    *,
    transcript=None,
    audio_url=None,
    deps,
    subpages=None,
    out_dir=".",
    deck_name=None,
    cta_text=None,
    cta_url=None,
):
    # Validate inputs before any network call: a bad invocation must cost nothing.
    if not transcript and not audio_url:
        raise InputError("provide either a transcript or an audio_url")
    for field in ("name", "company", "website"):
        if not prospect.get(field):
            raise InputError(f"prospect is missing required field: {field}")

    if not transcript:
        transcript = deps.transcriber.transcribe(audio_url)

    site = deps.scraper.scrape(_subpage_urls(prospect["website"], subpages))
    copy = deps.copy_generator.generate(prospect, transcript, site.text)

    prose = {k: copy[k] for k in PROSE_KEYS}
    tokens = dict(deps.token_processor.process(prose))
    tokens["cta_text"] = cta_text or copy["cta_text"]
    tokens["cta_url"] = cta_url or copy["cta_url"]

    render = deps.renderer.render(tokens, prospect, out_dir)
    name = deck_name or f"{prospect['company']} - Custom Deck"
    result = deps.uploader.upload(render.pptx_path, name)
    return result["view_url"]


# --- real wiring (terminal only; not unit-tested) -----------------------------------------

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/presentations.readonly",
]


def _build_google_services(oauth_cfg):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    token_file = oauth_cfg.get("token_file", "token.json")
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(oauth_cfg["credentials_file"], SCOPES)
            creds = flow.run_local_server(port=0)
        fd = os.open(token_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(creds.to_json())
    drive = build("drive", "v3", credentials=creds)
    slides = build("slides", "v1", credentials=creds)
    return drive, slides


def _build_deps(config):
    from customdecks.deck_copy_generator import DeckCopyGenerator, anthropic_client
    from customdecks.drive_uploader import DriveUploader, drive_upload_fn, slides_getter
    from customdecks.site_scraper import SiteScraper, requests_fetcher
    from customdecks.template_renderer import TemplateRenderer
    from customdecks.token_processor import TokenProcessor
    from customdecks.transcriber import Transcriber, deepgram_provider, groq_provider

    drive, slides = _build_google_services(config.get("google_oauth", {}))
    return Deps(
        transcriber=Transcriber(
            deepgram_provider(config["deepgram_api_key"]),
            groq_provider(config["groq_api_key"]),
        ),
        scraper=SiteScraper(
            requests_fetcher(),
            per_subpage_budget=config["per_subpage_char_budget"],
            total_budget=config["total_char_budget"],
        ),
        copy_generator=DeckCopyGenerator(
            anthropic_client(config["anthropic_api_key"]),
            required_keys=config.get("required_copy_keys", REQUIRED_KEYS),
        ),
        token_processor=TokenProcessor(
            char_budget=config["per_token_char_budget"],
            line_width=config["line_width"],
            logger=lambda msg: print("  " + msg),
        ),
        renderer=TemplateRenderer(),
        uploader=DriveUploader(
            drive_upload_fn(drive),
            slides_get=slides_getter(slides),
        ),
    )


def main(argv=None):
    import json

    parser = argparse.ArgumentParser(description="Generate a tailored prospect deck (ad-hoc).")
    parser.add_argument("--config", default="config.json", help="path to config.json")
    parser.add_argument("--name", required=True, help="prospect contact name")
    parser.add_argument("--company", required=True, help="prospect company name")
    parser.add_argument("--website", required=True, help="prospect website URL")
    parser.add_argument("--transcript", help="path to a transcript text file")
    parser.add_argument("--audio-url", help="URL of call audio to transcribe")
    parser.add_argument("--out-dir", default="out", help="where to write the rendered deck")
    args = parser.parse_args(argv)

    with open(args.config, encoding="utf-8") as fh:
        config = json.load(fh)

    transcript = None
    if args.transcript:
        with open(args.transcript, encoding="utf-8") as fh:
            transcript = fh.read()

    prospect = {"name": args.name, "company": args.company, "website": args.website}
    deps = _build_deps(config)

    view_url = build_deck(
        prospect,
        transcript=transcript,
        audio_url=args.audio_url,
        deps=deps,
        subpages=config.get("subpages", []),
        out_dir=args.out_dir,
        cta_text=config["cta_text"],
        cta_url=config["cta_url"],
    )

    # Confirm the uploaded Slides really carry the CTA link and the company name.
    file_id = view_url.split("/d/")[1].split("/")[0]
    verdict = deps.uploader.verify_slides(
        file_id, cta_url=config["cta_url"], cta_text=config["cta_text"], company=args.company
    )
    status = "OK" if verdict.ok else "WARNING (CTA or company not found on slides)"
    print(f"Deck for {args.company}: {view_url}")
    print(f"Slides verification: {status}")
    return view_url


if __name__ == "__main__":
    main()
