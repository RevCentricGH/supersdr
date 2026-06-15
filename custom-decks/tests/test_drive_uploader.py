"""DriveUploader: upload with retry/backoff, build the View URL from the returned file id,
and verify the uploaded Slides actually contain the CTA link and the company name.

Covers validation-contract assertions 20-23, 46 and the required test 45.
"""
import pytest

from customdecks.drive_uploader import DriveUploader, slides_text_and_links
from customdecks.errors import UploadError


class FlakyUpload:
    """Raises ``fail_times`` times, then returns a Drive create response."""

    def __init__(self, fail_times, file_id="FILE123"):
        self.fail_times = fail_times
        self.file_id = file_id
        self.calls = 0

    def __call__(self, file_path, name):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError("transient Drive 503")
        return {"id": self.file_id}


def _slides_presentation(runs):
    """Build a minimal Slides API presentations().get() shape from (content, link_url) runs."""
    text_elements = []
    for content, link in runs:
        style = {"link": {"url": link}} if link else {}
        text_elements.append({"textRun": {"content": content, "style": style}})
    return {"slides": [{"pageElements": [{"shape": {"text": {"textElements": text_elements}}}]}]}


def test_retries_after_failure_and_sleeps_between_attempts():
    upload = FlakyUpload(fail_times=1)
    slept = []
    uploader = DriveUploader(upload, sleep=slept.append, max_retries=3, base_delay=0.5)
    result = uploader.upload("/tmp/deck.pptx", "Deck")
    assert upload.calls == 2
    assert len(slept) >= 1
    assert result["id"] == "FILE123"


def test_raises_typed_error_after_exhausting_retries():
    upload = FlakyUpload(fail_times=99)
    uploader = DriveUploader(upload, sleep=lambda s: None, max_retries=3)
    with pytest.raises(UploadError):
        uploader.upload("/tmp/deck.pptx", "Deck")
    assert upload.calls == 3  # exactly max_retries (3) attempts, then it raises


def test_view_url_is_built_from_returned_file_id():
    upload = FlakyUpload(fail_times=0, file_id="ABC987")
    uploader = DriveUploader(upload, sleep=lambda s: None)
    result = uploader.upload("/tmp/deck.pptx", "Deck")
    assert result["view_url"] == "https://docs.google.com/presentation/d/ABC987/view"
    assert "ABC987" in result["view_url"]


def test_verify_slides_passes_when_cta_link_and_company_present():
    pres = _slides_presentation([
        ("Acme Corp", None),
        ("Book a call", "https://book.test/jane"),
    ])
    uploader = DriveUploader(lambda *a: {"id": "x"}, slides_get=lambda pid: pres)
    result = uploader.verify_slides("pid", cta_url="https://book.test/jane",
                                    cta_text="Book a call", company="Acme Corp")
    assert result.found_company is True
    assert result.found_cta is True
    assert result.ok is True


def test_verify_slides_fails_when_cta_link_missing():
    pres = _slides_presentation([("Acme Corp", None), ("Learn more", None)])
    uploader = DriveUploader(lambda *a: {"id": "x"}, slides_get=lambda pid: pres)
    result = uploader.verify_slides("pid", cta_url="https://book.test/jane",
                                    cta_text="Book a call", company="Acme Corp")
    assert result.found_cta is False
    assert result.ok is False


def test_slides_text_and_links_extracts_runs():
    pres = _slides_presentation([("Hello ", None), ("link", "https://x.test")])
    text, links = slides_text_and_links(pres)
    assert "Hello" in text and "link" in text
    assert ("link", "https://x.test") in links
