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

from customdecks.branding import load_branding
from customdecks.deck_copy_generator import REQUIRED_KEYS
from customdecks.errors import InputError, QualityGateError
from customdecks.quality_gate import DeckArtifact

PROSE_KEYS = ("headline", "problem", "solution", "proof")


class Deps:
    """The pipeline's collaborators. Real ones in ``main``; fakes in tests.

    ``quality_gate`` is the refuse-boilerplate gate; ``write_view_link`` is the single path that
    surfaces the View link to the operator and is invoked only on a full gate pass.
    ``pdf_text_extractor`` and ``slide_background_extractor`` turn the rendered files into the
    facts the gate evaluates.
    """

    def __init__(
        self,
        *,
        transcriber,
        scraper,
        copy_generator,
        token_processor,
        renderer,
        uploader,
        quality_gate,
        write_view_link,
        pdf_text_extractor,
        slide_background_extractor,
    ):
        self.transcriber = transcriber
        self.scraper = scraper
        self.copy_generator = copy_generator
        self.token_processor = token_processor
        self.renderer = renderer
        self.uploader = uploader
        self.quality_gate = quality_gate
        self.write_view_link = write_view_link
        self.pdf_text_extractor = pdf_text_extractor
        self.slide_background_extractor = slide_background_extractor


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
    branding=None,
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

    render = deps.renderer.render(tokens, prospect, out_dir, branding=branding)
    name = deck_name or f"{prospect['company']} - Custom Deck"
    upload = deps.uploader.upload(render.pptx_path, name)
    view_url = upload["view_url"]

    # The upload above is an unshared Drive file; its link is published only if the gate passes.
    artifact = DeckArtifact(
        pdf_path=render.pdf_path,
        preview_link=view_url,
        token_consumption=sum(len(str(v)) for v in prose.values()),
        pdf_text=deps.pdf_text_extractor(render.pdf_path),
        slide_backgrounds=deps.slide_background_extractor(render.pptx_path),
    )
    return publish_if_passing(deps, artifact, view_url)


def publish_if_passing(deps, artifact, view_url):
    """The single gate-and-publish decision. The View link is written via
    ``deps.write_view_link`` only when the refuse-boilerplate gate passes every check. On any
    failure nothing is written (no partial write, no placeholder) and ``QualityGateError`` is
    raised carrying every reason; the deck is left untouched on disk for the operator to inspect.

    This is the only code path that writes the View link, so no deck can be published without
    first passing through the gate.
    """
    result = deps.quality_gate.check(artifact)
    if result.passed:
        deps.write_view_link(view_url)
        return view_url
    raise QualityGateError(result.failures)


# --- real wiring (terminal only; not unit-tested) -----------------------------------------

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/presentations.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]


def pdf_text_extractor():
    """Real PDF text-layer extractor (uses pypdf). The gate scans this for transcript
    artifacts in the *rendered* deck, not the source template."""

    def extract(pdf_path):
        from pypdf import PdfReader

        reader = PdfReader(pdf_path)
        return "\n".join((page.extract_text() or "") for page in reader.pages)

    return extract


def slide_background_extractor():
    """Real PPTX slide-background signature extractor. For each slide, returns the md5 of its
    background image if it has one, else "". Lets the gate spot a generic wallpaper applied
    uniformly across the title..closing slides. Marp output has no slide backgrounds, so this
    returns all-empty signatures (no wallpaper) for the current pipeline."""
    import hashlib
    import re
    import zipfile

    def extract(pptx_path):
        signatures = []
        with zipfile.ZipFile(pptx_path) as zf:
            names = zf.namelist()
            slides = sorted(
                (n for n in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
                key=lambda n: int(re.search(r"(\d+)", n).group(1)),
            )
            for slide in slides:
                xml = zf.read(slide).decode("utf-8", "ignore")
                sig = ""
                m = re.search(r'<p:bg>.*?r:embed="(rId\d+)".*?</p:bg>', xml, re.DOTALL)
                if m:
                    rels = slide.replace("ppt/slides/", "ppt/slides/_rels/") + ".rels"
                    if rels in names:
                        rm = re.search(
                            r'Id="%s"[^>]*Target="([^"]+)"' % m.group(1),
                            zf.read(rels).decode("utf-8", "ignore"),
                        )
                        if rm:
                            target = rm.group(1).replace("../", "ppt/")
                            if target in names:
                                sig = hashlib.md5(zf.read(target)).hexdigest()
                signatures.append(sig)
        return signatures

    return extract


def _build_google_services(oauth_cfg):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    token_file = oauth_cfg.get("token_file", "token.json")
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        if creds.scopes and not set(SCOPES).issubset(set(creds.scopes)):
            creds = None  # token predates a scope addition; force re-consent
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
    from customdecks.quality_gate import DEFAULT_TOKEN_BUDGET, QualityGate, http_link_checker
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
        quality_gate=QualityGate(
            link_checker=http_link_checker(),
            token_budget=config.get("token_budget", DEFAULT_TOKEN_BUDGET),
        ),
        write_view_link=lambda url: print(f"Deck passed the quality gate. View link: {url}"),
        pdf_text_extractor=pdf_text_extractor(),
        slide_background_extractor=slide_background_extractor(),
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

    # Branding (agency identity + proof) and its bundled assets are resolved relative to the
    # config file's own directory, so the deck is the student's agency with no machine paths.
    branding = load_branding(config, args.config)

    try:
        view_url = build_deck(
            prospect,
            transcript=transcript,
            audio_url=args.audio_url,
            deps=deps,
            subpages=config.get("subpages", []),
            out_dir=args.out_dir,
            cta_text=config["cta_text"],
            cta_url=config["cta_url"],
            branding=branding,
        )
    except QualityGateError as exc:
        # The deck did not pass the refuse-boilerplate gate. It is kept locally; the View
        # link is not published. Report every reason so the operator knows what to fix.
        print(f"Deck for {args.company} did NOT pass the quality gate; View link NOT published.")
        for reason in exc.failures:
            print("  - " + reason)
        print(f"The deck is kept locally at: {os.path.join(args.out_dir, 'deck.pdf')}")
        return None

    # build_deck already wrote the View link (gate passed). Confirm the uploaded Slides really
    # carry the CTA link and the company name.
    file_id = view_url.split("/d/")[1].split("/")[0]
    verdict = deps.uploader.verify_slides(
        file_id, cta_url=config["cta_url"], cta_text=config["cta_text"], company=args.company
    )
    status = "OK" if verdict.ok else "WARNING (CTA or company not found on slides)"
    print(f"Slides verification: {status}")
    return view_url


if __name__ == "__main__":
    main()
