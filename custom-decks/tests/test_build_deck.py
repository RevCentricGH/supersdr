"""build_deck: the full ad-hoc pipeline from one prospect + transcript/audio to a View URL.

Covers validation-contract assertions 1, 25, 31, 46.
"""
import pytest

from customdecks.build_deck import Deps, build_deck
from customdecks.deck_copy_generator import DeckCopyGenerator
from customdecks.drive_uploader import DriveUploader
from customdecks.errors import InputError
from customdecks.site_scraper import SiteScraper
from customdecks.token_processor import TokenProcessor
from customdecks.transcriber import Transcriber

PROSPECT = {"name": "Jane Doe", "company": "Acme Corp", "website": "https://acme.test"}
COPY_JSON = (
    '{"headline":"Acme ships faster","problem":"Manual handoffs",'
    '"solution":"Automate them","proof":"30% faster",'
    '"cta_text":"Book a call","cta_url":"https://book.test/jane"}'
)


class Spy:
    def __init__(self, returns=None):
        self.returns = returns
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        return self.returns


class FakeRenderer:
    def __init__(self):
        self.calls = []

    def render(self, tokens, prospect, out_dir, basename="deck", branding=None):
        self.calls.append((tokens, prospect, branding))

        class R:
            marp_path = "/tmp/deck.md"
            pptx_path = "/tmp/deck.pptx"
            pdf_path = "/tmp/deck.pdf"

        return R()


def _deps(deepgram, groq, fetcher, claude, upload_fn):
    return Deps(
        transcriber=Transcriber(deepgram, groq),
        scraper=SiteScraper(fetcher, per_subpage_budget=1000, total_budget=5000),
        copy_generator=DeckCopyGenerator(claude),
        token_processor=TokenProcessor(char_budget=200, line_width=40),
        renderer=FakeRenderer(),
        uploader=DriveUploader(upload_fn, sleep=lambda s: None),
    )


def test_no_transcript_and_no_audio_raises_before_any_network_call():
    deepgram, groq, fetcher, claude = Spy(), Spy(), Spy(), Spy()
    upload_fn = Spy({"id": "X"})
    deps = _deps(deepgram, groq, fetcher, claude, upload_fn)
    with pytest.raises(InputError):
        build_deck(PROSPECT, transcript=None, audio_url=None, deps=deps,
                   subpages=["about"], out_dir="/tmp")
    assert deepgram.calls == []
    assert groq.calls == []
    assert fetcher.calls == []
    assert claude.calls == []
    assert upload_fn.calls == []


def test_full_pipeline_returns_view_url_from_uploaded_file_id():
    deepgram, groq = Spy("ignored"), Spy()
    fetcher = Spy("<p>Acme builds widgets</p>")
    claude = Spy(COPY_JSON)
    upload_fn = Spy({"id": "DECKID42"})
    deps = _deps(deepgram, groq, fetcher, claude, upload_fn)
    url = build_deck(PROSPECT, transcript="we discussed onboarding", audio_url=None,
                     deps=deps, subpages=["about"], out_dir="/tmp")
    assert url == "https://docs.google.com/presentation/d/DECKID42/view"
    # pipeline actually ran through render -> upload (no stub short-circuit)
    assert upload_fn.calls and upload_fn.calls[0][0] == "/tmp/deck.pptx"


def test_branding_is_passed_through_to_the_renderer():
    deepgram, groq = Spy("ignored"), Spy()
    fetcher = Spy("<p>Acme builds widgets</p>")
    claude = Spy(COPY_JSON)
    upload_fn = Spy({"id": "ID"})
    deps = _deps(deepgram, groq, fetcher, claude, upload_fn)
    branding = {"agency": {"name": "Northstar Outbound"}, "proof": {"stat_cards": []}}
    build_deck(PROSPECT, transcript="t", audio_url=None, deps=deps, subpages=[],
               out_dir="/tmp", branding=branding)
    assert deps.renderer.calls[0][2] == branding


def test_provided_transcript_skips_transcription():
    deepgram, groq = Spy("dg"), Spy("groq")
    fetcher = Spy("<p>site</p>")
    claude = Spy(COPY_JSON)
    deps = _deps(deepgram, groq, fetcher, claude, Spy({"id": "ID"}))
    build_deck(PROSPECT, transcript="given transcript", audio_url=None, deps=deps,
               subpages=[], out_dir="/tmp")
    assert deepgram.calls == []
    assert groq.calls == []


def test_audio_url_triggers_transcription():
    deepgram, groq = Spy("the transcript"), Spy()
    fetcher = Spy("<p>site</p>")
    claude = Spy(COPY_JSON)
    deps = _deps(deepgram, groq, fetcher, claude, Spy({"id": "ID"}))
    build_deck(PROSPECT, transcript=None, audio_url="https://audio/1", deps=deps,
               subpages=[], out_dir="/tmp")
    assert deepgram.calls == [("https://audio/1",)]
