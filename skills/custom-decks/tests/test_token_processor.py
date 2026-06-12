"""TokenProcessor: per-token char budget and line-wrap.

Covers validation-contract assertions 16-17 and the required tests 43-44.
"""
from customdecks.token_processor import TokenProcessor


def test_truncates_to_exactly_the_budget_length():
    tp = TokenProcessor(char_budget=10, line_width=100)
    assert len(tp.truncate("x" * 50)) == 10


def test_truncation_is_recorded_not_silently_dropped():
    logged = []
    tp = TokenProcessor(char_budget=10, line_width=100, logger=logged.append)
    tp.truncate("x" * 50, key="headline")
    assert tp.truncations, "the dropped excess must be recorded"
    assert logged, "truncation must be logged, not silently discarded"


def test_no_truncation_when_within_budget():
    tp = TokenProcessor(char_budget=100, line_width=100)
    assert tp.truncate("short") == "short"
    assert tp.truncations == []


def test_wraps_long_text_into_multiple_lines():
    tp = TokenProcessor(char_budget=1000, line_width=20)
    wrapped = tp.wrap("a" * 50)
    assert len(wrapped.splitlines()) >= 2
    assert all(len(line) <= 20 for line in wrapped.splitlines())


def test_process_applies_budget_and_wrap_per_token():
    tp = TokenProcessor(char_budget=10, line_width=5)
    out = tp.process({"headline": "x" * 50, "cta_text": "Book"})
    # truncated to budget, then wrapped: no line exceeds the width
    assert all(len(line) <= 5 for line in out["headline"].splitlines())
    assert sum(len(line) for line in out["headline"].splitlines()) == 10
    assert out["cta_text"] == "Book"


def test_truncations_do_not_carry_over_between_process_calls():
    # reusing one processor across decks (batch/queue mode) must not accumulate truncations
    tp = TokenProcessor(char_budget=10, line_width=100)
    tp.process({"headline": "x" * 50})
    assert len(tp.truncations) == 1
    tp.process({"cta_text": "Book"})  # within budget, nothing truncated
    assert tp.truncations == []
