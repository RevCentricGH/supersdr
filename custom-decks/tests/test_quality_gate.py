"""QualityGate: the refuse-boilerplate gate that blocks the View-link write unless a
rendered deck passes every check.

Covers validation-contract assertions 1-8 and the per-check failure-mode tests 14-21.
The gate is read-only: it never deletes or rewrites the deck, so the failure-mode tests
assert the deck file still exists on disk after the gate returns.
"""
import os
from types import SimpleNamespace

import pytest

from customdecks.build_deck import publish_if_passing
from customdecks.errors import QualityGateError
from customdecks.quality_gate import (
    MIN_PDF_BYTES,
    DEFAULT_TOKEN_BUDGET,
    DeckArtifact,
    QualityGate,
)


class WriteSpy:
    def __init__(self):
        self.calls = []

    def __call__(self, view_url):
        self.calls.append(view_url)


def _publish(artifact, gate):
    """Drive the artifact through the production gate-and-publish seam with a write spy.
    Returns (write_spy, raised_error_or_None)."""
    write = WriteSpy()
    deps = SimpleNamespace(quality_gate=gate, write_view_link=write)
    error = None
    try:
        publish_if_passing(deps, artifact, "https://docs.google.com/presentation/d/X/view")
    except QualityGateError as exc:
        error = exc
    return write, error


def _write_pdf(path, size):
    """Write a fake but real on-disk PDF of exactly ``size`` bytes."""
    body = b"%PDF-1.4\n" + b"0" * max(0, size - 9)
    with open(path, "wb") as fh:
        fh.write(body[:size] if size >= 9 else b"%PDF-1.4\n")
    return path


def _reachable(url):
    return 200


def _good_artifact(tmp_path, **overrides):
    pdf = _write_pdf(str(tmp_path / "deck.pdf"), MIN_PDF_BYTES + 2000)
    fields = dict(
        pdf_path=pdf,
        preview_link="https://docs.google.com/presentation/d/OK/view",
        token_consumption=600,
        pdf_text="Acme ships faster. The problem is manual handoffs. We automate them.",
        slide_backgrounds=["", "", "", "", "", ""],
    )
    fields.update(overrides)
    return DeckArtifact(**fields)


def _gate(link_checker=_reachable):
    return QualityGate(link_checker=link_checker)


def test_min_pdf_floor_is_several_kilobytes():
    # A stub/empty PDF (a few hundred bytes) must not be able to satisfy the floor.
    assert MIN_PDF_BYTES >= 4096


def test_clean_deck_passes_every_check(tmp_path):
    result = _gate().check(_good_artifact(tmp_path))
    assert result.passed is True
    assert result.failures == []


def test_clean_deck_writes_view_link_exactly_once(tmp_path):
    write, error = _publish(_good_artifact(tmp_path), _gate())
    assert error is None
    assert write.calls == ["https://docs.google.com/presentation/d/X/view"]


def test_pdf_absent_fails_no_write_and_reason_references_missing_pdf(tmp_path):
    artifact = _good_artifact(tmp_path, pdf_path=str(tmp_path / "nope.pdf"))
    write, error = _publish(artifact, _gate())
    assert error is not None  # failing result
    assert write.calls == []  # View link not written
    assert any("pdf" in r.lower() and "missing" in r.lower() for r in error.failures)


def test_below_size_floor_fails_no_write_and_leaves_file_on_disk(tmp_path):
    pdf = _write_pdf(str(tmp_path / "tiny.pdf"), 200)
    assert os.path.getsize(pdf) < MIN_PDF_BYTES
    artifact = _good_artifact(tmp_path, pdf_path=pdf)
    write, error = _publish(artifact, _gate())
    assert error is not None
    assert write.calls == []
    assert any("size" in r.lower() for r in error.failures)
    assert os.path.exists(pdf)  # gate is read-only; the deck is kept locally


def test_unreachable_preview_link_fails_no_write_and_leaves_file_on_disk(tmp_path):
    def not_found(url):
        return 404

    artifact = _good_artifact(tmp_path)
    write, error = _publish(artifact, _gate(link_checker=not_found))
    assert error is not None
    assert write.calls == []
    assert any("link" in r.lower() for r in error.failures)
    assert os.path.exists(artifact.pdf_path)


def test_connection_error_preview_link_fails_no_write(tmp_path):
    def boom(url):
        raise ConnectionError("connection refused")

    artifact = _good_artifact(tmp_path)
    write, error = _publish(artifact, _gate(link_checker=boom))
    assert error is not None
    assert write.calls == []
    assert any("link" in r.lower() for r in error.failures)
    assert os.path.exists(artifact.pdf_path)


def test_token_budget_overflow_fails_no_write_and_leaves_file_on_disk(tmp_path):
    artifact = _good_artifact(tmp_path, token_consumption=DEFAULT_TOKEN_BUDGET + 1)
    write, error = _publish(artifact, _gate())
    assert error is not None
    assert write.calls == []
    assert any("budget" in r.lower() and "overflow" in r.lower() for r in error.failures)
    assert os.path.exists(artifact.pdf_path)


def test_transcript_artifact_text_fails_no_write_and_leaves_file_on_disk(tmp_path):
    bad_text = "Our solution. Speaker 2: yeah we totally need that [00:14] for sure."
    artifact = _good_artifact(tmp_path, pdf_text=bad_text)
    write, error = _publish(artifact, _gate())
    assert error is not None
    assert write.calls == []
    assert any("transcript" in r.lower() and "text" in r.lower() for r in error.failures)
    assert os.path.exists(artifact.pdf_path)


def test_generic_wallpaper_fails_no_write_and_leaves_file_on_disk(tmp_path):
    # A known generic background on the title and closing slides (and every slide between).
    artifact = _good_artifact(tmp_path, slide_backgrounds=["generic-wallpaper"] * 6)
    write, error = _publish(artifact, _gate())
    assert error is not None
    assert write.calls == []
    assert any("wallpaper" in r.lower() for r in error.failures)
    assert os.path.exists(artifact.pdf_path)


def test_uniform_nonempty_background_trips_wallpaper_guard(tmp_path):
    # Not a known signature, but the same image on every slide reads as a generic template.
    backgrounds = ["a1b2c3hash"] * 5
    result = _gate().check(_good_artifact(tmp_path, slide_backgrounds=backgrounds))
    assert result.passed is False
    assert any("wallpaper" in r.lower() for r in result.failures)


def test_two_non_adjacent_checks_fail_without_short_circuit(tmp_path):
    # Preview-link (2nd check) and wallpaper (5th, last check) both fail, while the
    # token-budget and transcript checks between them pass. If the gate returned on the
    # first failure, the wallpaper reason would be absent and this assertion would fail.
    def not_found(url):
        return 503

    artifact = _good_artifact(tmp_path, slide_backgrounds=["generic-wallpaper"] * 6)
    result = _gate(link_checker=not_found).check(artifact)
    assert result.passed is False
    link_reasons = [r for r in result.failures if "link" in r.lower()]
    wallpaper_reasons = [r for r in result.failures if "wallpaper" in r.lower()]
    assert len(link_reasons) == 1
    assert len(wallpaper_reasons) == 1  # would be 0 if the gate short-circuited on the link
    # every reported reason is a distinct, non-empty message
    assert all(r.strip() for r in result.failures)
    assert len(set(result.failures)) == len(result.failures)


def test_every_check_can_fail_with_its_own_distinct_reason(tmp_path):
    # All five checks fail at once; the gate reports a distinct, non-empty reason for each.
    def boom(url):
        raise ConnectionError("refused")

    artifact = DeckArtifact(
        pdf_path=str(tmp_path / "missing.pdf"),
        preview_link="https://broken.test/x",
        token_consumption=DEFAULT_TOKEN_BUDGET + 500,
        pdf_text="Speaker 1: hello [00:01]",
        slide_backgrounds=["generic-wallpaper"] * 4,
    )
    result = _gate(link_checker=boom).check(artifact)
    assert result.passed is False
    assert len(result.failures) == 5
    assert all(r.strip() for r in result.failures)
    assert len(set(result.failures)) == 5
