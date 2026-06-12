"""DriveUploader - upload the rendered deck to Google Drive (converted to Google Slides),
with retry/backoff, and verify the uploaded Slides really contain the CTA link and company.

The Drive create call is injected as ``upload_fn(file_path, name) -> {"id": ...}`` and the
Slides read as ``slides_get(presentation_id) -> presentation_json`` so the retry logic and
the post-upload verification can be tested without Google credentials. ``drive_upload_fn``
and ``slides_getter`` build the real ones from an authorized API client.

The View URL is built from the file id Drive returns, so it always points at the file that
was actually created - never a pattern-matched stub.
"""
import time

from .errors import UploadError

PRESENTATION_MIME = "application/vnd.google-apps.presentation"


def view_url(file_id):
    return f"https://docs.google.com/presentation/d/{file_id}/view"


def slides_text_and_links(presentation):
    """Flatten a Slides presentations().get() response into (visible_text, links) where
    links is a list of (run_text, url) for every text run that carries a hyperlink."""
    chunks = []
    links = []
    for slide in presentation.get("slides", []) or []:
        for element in slide.get("pageElements", []) or []:
            text = (element.get("shape") or {}).get("text") or {}
            for te in text.get("textElements", []) or []:
                run = te.get("textRun")
                if not run:
                    continue
                content = run.get("content", "")
                chunks.append(content)
                link = ((run.get("style") or {}).get("link") or {}).get("url")
                if link:
                    links.append((content.strip(), link))
    return "".join(chunks), links


class VerifyResult:
    def __init__(self, found_company, found_cta):
        self.found_company = found_company
        self.found_cta = found_cta

    @property
    def ok(self):
        return self.found_company and self.found_cta


class DriveUploader:
    def __init__(self, upload_fn, *, slides_get=None, sleep=None, max_retries=3, base_delay=1.0):
        self._upload_fn = upload_fn
        self._slides_get = slides_get
        self._sleep = sleep if sleep is not None else time.sleep
        self.max_retries = max_retries
        self.base_delay = base_delay

    def upload(self, file_path, name):
        attempt = 0
        last_error = None
        while attempt < self.max_retries:
            try:
                response = self._upload_fn(file_path, name)
                file_id = response["id"]
                return {"id": file_id, "view_url": view_url(file_id)}
            except Exception as exc:  # transient Drive errors: back off and retry
                last_error = exc
                attempt += 1
                if attempt >= self.max_retries:
                    break
                self._sleep(self.base_delay * attempt)
        raise UploadError(
            f"Drive upload failed after {self.max_retries} attempts: {last_error}"
        ) from last_error

    def verify_slides(self, presentation_id, *, cta_url, cta_text, company):
        presentation = self._slides_get(presentation_id)
        text, links = slides_text_and_links(presentation)
        found_company = company in text
        found_cta = any(url == cta_url and cta_text in content for content, url in links)
        return VerifyResult(found_company, found_cta)


def drive_upload_fn(drive_service):
    """Real Drive create callable: upload the local file converting it to a Google Slides
    presentation, returning the create response (which carries the new file id)."""

    def upload(file_path, name):
        from googleapiclient.http import MediaFileUpload

        media = MediaFileUpload(
            file_path,
            mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            resumable=False,
        )
        return (
            drive_service.files()
            .create(
                body={"name": name, "mimeType": PRESENTATION_MIME},
                media_body=media,
                fields="id",
            )
            .execute()
        )

    return upload


def slides_getter(slides_service):
    """Real Slides read callable for post-upload verification."""

    def get(presentation_id):
        return slides_service.presentations().get(presentationId=presentation_id).execute()

    return get
