"""build_deck: the full ad-hoc pipeline from one prospect + transcript/audio to a View URL.

Also covers the QualityGate integration: the View link is written via the single production
write path only on a full pass, never on failure, and no code path reaches the write without
first passing through the gate (validation-contract assertions 9, 10, 13, 14).
"""
import ast
import pathlib

import pytest

from customdecks.build_deck import Deps, build_deck
from customdecks.deck_copy_generator import DeckCopyGenerator
from customdecks.drive_uploader import DriveUploader
from customdecks.errors import InputError, QualityGateError
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


class WriteSpy:
    def __init__(self):
        self.calls = []

    def __call__(self, view_url):
        self.calls.append(view_url)


class _Result:
    def __init__(self, failures):
        self.failures = list(failures)

    @property
    def passed(self):
        return not self.failures


class FakeGate:
    """Stands in for QualityGate so build_deck wiring is tested independently of the checks."""

    def __init__(self, failures=()):
        self._failures = list(failures)
        self.calls = []

    def check(self, artifact):
        self.calls.append(artifact)
        return _Result(self._failures)


def _deps(deepgram, groq, fetcher, claude, upload_fn, *, gate=None, write_view_link=None):
    return Deps(
        transcriber=Transcriber(deepgram, groq),
        scraper=SiteScraper(fetcher, per_subpage_budget=1000, total_budget=5000),
        copy_generator=DeckCopyGenerator(claude),
        token_processor=TokenProcessor(char_budget=200, line_width=40),
        renderer=FakeRenderer(),
        uploader=DriveUploader(upload_fn, sleep=lambda s: None),
        quality_gate=gate if gate is not None else FakeGate(),
        write_view_link=write_view_link if write_view_link is not None else WriteSpy(),
        pdf_text_extractor=lambda path: "",
        slide_background_extractor=lambda path: [],
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


def test_passing_gate_writes_link_exactly_once_and_returns_url():
    gate = FakeGate()  # no failures -> passes
    write = WriteSpy()
    deps = _deps(Spy(), Spy(), Spy("<p>site</p>"), Spy(COPY_JSON), Spy({"id": "DECKID42"}),
                 gate=gate, write_view_link=write)
    url = build_deck(PROSPECT, transcript="we discussed onboarding", audio_url=None,
                     deps=deps, subpages=["about"], out_dir="/tmp")
    assert url == "https://docs.google.com/presentation/d/DECKID42/view"
    assert len(gate.calls) == 1  # the gate ran before the write
    assert write.calls == [url]  # written exactly once, via the production write path


def test_failing_gate_does_not_write_link_and_raises_with_reasons():
    reasons = ["missing PDF: no rendered deck PDF was found", "preview link unreachable: HTTP 404"]
    gate = FakeGate(failures=reasons)
    write = WriteSpy()
    deps = _deps(Spy(), Spy(), Spy("<p>site</p>"), Spy(COPY_JSON), Spy({"id": "BAD"}),
                 gate=gate, write_view_link=write)
    with pytest.raises(QualityGateError) as excinfo:
        build_deck(PROSPECT, transcript="t", audio_url=None, deps=deps,
                   subpages=[], out_dir="/tmp")
    assert write.calls == []  # no partial write, no placeholder
    assert excinfo.value.failures == reasons  # every failing check's reason is reported


def test_no_code_path_writes_the_view_link_without_passing_the_gate():
    # Static guarantee: the single write_view_link call in build_deck is reached only after
    # quality_gate.check, and only inside the pass-guarded branch. There is no bypass.
    from customdecks import build_deck as module

    src = pathlib.Path(module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    # The whole module must contain exactly one View-link write, in the gate-and-publish seam
    # that build_deck delegates to. Walk the entire module so no other function can write it.
    fn = tree
    for node in ast.walk(fn):
        for child in ast.iter_child_nodes(node):
            child._parent = node

    def attr_calls(name):
        return [n for n in ast.walk(fn)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == name]

    writes = attr_calls("write_view_link")
    checks = attr_calls("check")
    assert len(writes) == 1, "there must be exactly one View-link write path"
    assert checks, "build_deck must call the quality gate"
    write_call = writes[0]
    assert min(c.lineno for c in checks) < write_call.lineno  # gate runs before the write

    # the write is nested inside an `if <result>.passed:` block
    guarded = False
    node = write_call
    while getattr(node, "_parent", None) is not None:
        node = node._parent
        if isinstance(node, ast.If) and "passed" in ast.unparse(node.test):
            guarded = True
            break
    assert guarded, "the View-link write must be guarded by the gate's pass result"
