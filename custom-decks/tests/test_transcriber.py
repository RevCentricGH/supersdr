"""Transcriber: Deepgram primary, Groq fallback only when Deepgram returns empty.

Covers validation-contract assertions 2-5 and the required tests 32-34.
"""
import pytest

from customdecks.errors import TranscriptionError
from customdecks.transcriber import Transcriber


class Spy:
    """A provider stand-in that records its calls and returns a canned value (or raises)."""

    def __init__(self, returns=None, raises=None):
        self.returns = returns
        self.raises = raises
        self.calls = []

    def __call__(self, audio_url):
        self.calls.append(audio_url)
        if self.raises is not None:
            raise self.raises
        return self.returns


def test_deepgram_is_called_for_every_audio_url():
    deepgram = Spy(returns="a real transcript")
    groq = Spy(returns="groq")
    Transcriber(deepgram, groq).transcribe("https://audio/1")
    assert deepgram.calls == ["https://audio/1"]


def test_deepgram_nonempty_does_not_call_groq():
    deepgram = Spy(returns="the deepgram transcript")
    groq = Spy(returns="the groq transcript")
    out = Transcriber(deepgram, groq).transcribe("https://audio/1")
    assert out == "the deepgram transcript"
    assert groq.calls == []


def test_deepgram_empty_string_falls_back_to_groq_once():
    deepgram = Spy(returns="")
    groq = Spy(returns="the groq transcript")
    out = Transcriber(deepgram, groq).transcribe("https://audio/1")
    assert out == "the groq transcript"
    assert len(groq.calls) == 1


@pytest.mark.parametrize("empty", [None, "", "   ", "\n\t  \n"])
def test_whitespace_or_none_counts_as_empty(empty):
    deepgram = Spy(returns=empty)
    groq = Spy(returns="the groq transcript")
    out = Transcriber(deepgram, groq).transcribe("https://audio/1")
    assert out == "the groq transcript"


def test_deepgram_raising_falls_back_to_groq():
    deepgram = Spy(raises=RuntimeError("deepgram down"))
    groq = Spy(returns="the groq transcript")
    out = Transcriber(deepgram, groq).transcribe("https://audio/1")
    assert out == "the groq transcript"


def test_both_empty_raises_typed_error():
    deepgram = Spy(returns="")
    groq = Spy(returns="   ")
    with pytest.raises(TranscriptionError):
        Transcriber(deepgram, groq).transcribe("https://audio/1")


def test_both_raising_raises_typed_error():
    deepgram = Spy(raises=RuntimeError("dg"))
    groq = Spy(raises=RuntimeError("groq"))
    with pytest.raises(TranscriptionError):
        Transcriber(deepgram, groq).transcribe("https://audio/1")
