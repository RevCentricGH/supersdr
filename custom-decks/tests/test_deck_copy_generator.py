"""DeckCopyGenerator: build the copy prompt, parse Claude's output tolerantly, validate
required keys, and honor INSUFFICIENT_SIGNAL.

Covers validation-contract assertions 10-15 and the required tests 38-42.
"""
import pytest

from customdecks.deck_copy_generator import DeckCopyGenerator, REQUIRED_KEYS
from customdecks.errors import CopyValidationError, InsufficientSignalError

PROSPECT = {"name": "Jane Doe", "company": "Acme Corp", "website": "https://acme.test"}
GOOD = {
    "headline": "Acme ships faster",
    "problem": "Manual handoffs",
    "solution": "Automate them",
    "proof": "30% faster",
    "cta_text": "Book a call",
    "cta_url": "https://book.test/jane",
}


def _fenced(payload):
    import json

    return "Here you go:\n```json\n" + json.dumps(payload) + "\n```\nthanks"


class SpyClaude:
    def __init__(self, response):
        self.response = response
        self.prompts = []

    def __call__(self, prompt):
        self.prompts.append(prompt)
        return self.response


def test_build_prompt_includes_all_four_data_sources():
    gen = DeckCopyGenerator(SpyClaude(""))
    prompt = gen.build_prompt(PROSPECT, "we discussed onboarding pain", "Acme builds widgets")
    for piece in ("Jane Doe", "Acme Corp", "https://acme.test",
                  "we discussed onboarding pain", "Acme builds widgets"):
        assert piece in prompt
    # the four data sources are labeled, not just concatenated
    low = prompt.lower()
    assert "transcript" in low and "site" in low


def test_generate_sends_data_to_claude_and_returns_validated_dict():
    claude = SpyClaude(_fenced(GOOD))
    out = DeckCopyGenerator(claude).generate(PROSPECT, "transcript text here", "site text here")
    assert out == GOOD
    assert isinstance(claude.prompts[0], str)
    assert "transcript text here" in claude.prompts[0]
    assert "site text here" in claude.prompts[0]


def test_extract_reads_fenced_json_block():
    out = DeckCopyGenerator(SpyClaude("")).extract(_fenced(GOOD))
    assert out == GOOD


def test_extract_reads_prose_wrapped_json():
    import json

    raw = "Sure! Here is the copy:\n" + json.dumps(GOOD) + "\nLet me know if you want changes."
    out = DeckCopyGenerator(SpyClaude("")).extract(raw)
    assert out == GOOD


def test_extract_reads_fenced_block_without_language_tag():
    import json

    raw = "```\n" + json.dumps(GOOD) + "\n```"
    out = DeckCopyGenerator(SpyClaude("")).extract(raw)
    assert out == GOOD


def test_validate_raises_listing_missing_keys():
    partial = {"headline": "h", "problem": "p", "solution": "s"}  # missing proof, cta_text, cta_url
    with pytest.raises(CopyValidationError) as exc:
        DeckCopyGenerator(SpyClaude("")).validate(partial)
    for key in ("proof", "cta_text", "cta_url"):
        assert key in exc.value.missing_keys
        assert key in str(exc.value)


def test_insufficient_signal_raises_distinct_error():
    raw = "INSUFFICIENT_SIGNAL - I could not find real information about this company."
    with pytest.raises(InsufficientSignalError):
        DeckCopyGenerator(SpyClaude(raw)).extract(raw)


def test_required_keys_are_the_contracted_six():
    assert set(REQUIRED_KEYS) == {"headline", "problem", "solution", "proof", "cta_text", "cta_url"}
