"""QualityGate - the refuse-boilerplate gate.

The product promise is "never ship a generic deck". This gate enforces it: a rendered deck's
View link is written only when the deck passes every check. The gate is the last thing between
a finished render and surfacing the link to the operator.

It is pure and read-only. It consumes a ``DeckArtifact`` (the structured facts about a rendered
deck) and returns a ``QualityResult`` carrying every failure reason. It never deletes, rewrites,
or uploads anything, so a deck that fails is left exactly where it is on disk for the operator
to inspect.

Checks, in execution order:
  1. PDF present     - a rendered PDF exists at the artifact's path.
  2. PDF size floor  - that PDF is at least ``MIN_PDF_BYTES`` (a stub/empty PDF must not pass).
  3. Preview link    - the preview link answers a real HTTP request with a 2xx status.
  4. Token budget    - the recorded copy consumption does not exceed ``token_budget``.
  5. Transcript text - the rendered PDF text carries none of the known transcript-artifact
                       patterns (speaker labels, timestamps, inaudible/crosstalk markers).
  6. Wallpaper guard - no slide in the evaluated set (title + closing at minimum) carries a
                       known generic-wallpaper background, and the slides do not all share one
                       identical non-empty background image.

Every check runs on every call; the gate collects all failures rather than short-circuiting on
the first, so the operator sees everything wrong at once.

The link check is injected as ``link_checker(url) -> status_code`` so the gate can be unit-tested
without network access; ``http_link_checker`` builds the real one.
"""
import os
import re

# A valid rendered Marp deck (several slides) is tens of kilobytes. The floor is set well above
# any empty/stub PDF (which is a few hundred bytes) so a blank render can never satisfy it.
MIN_PDF_BYTES = 8 * 1024

# Total characters of deck copy allowed before the deck is judged over-stuffed. A tailored deck's
# prose runs a few hundred chars; a boilerplate wall-of-text blows past this.
DEFAULT_TOKEN_BUDGET = 4000

# Known-bad patterns that mean raw transcript text leaked into the rendered deck. At least two
# distinct patterns so the check is not a single hardcoded string.
TRANSCRIPT_ARTIFACT_PATTERNS = [
    ("speaker label", re.compile(r"\bSpeaker\s*\d+\s*:", re.IGNORECASE)),
    ("timestamp", re.compile(r"\[?\b\d{1,2}:\d{2}(?::\d{2})?\b\]?")),
    ("inaudible marker", re.compile(r"[\[(]\s*inaudible\s*[\])]", re.IGNORECASE)),
    ("crosstalk marker", re.compile(r"[\[(]\s*crosstalk\s*[\])]", re.IGNORECASE)),
]

# Background-image signatures (hashes/identifiers) known to be generic boilerplate wallpaper.
GENERIC_WALLPAPER_SIGNATURES = frozenset(
    {
        "generic-wallpaper",
        "default-template-bg",
        "stock-gradient-001",
    }
)


class DeckArtifact:
    """The structured facts about one rendered deck that the gate evaluates.

    ``pdf_path`` is where the rendered PDF lives (checked for presence and size).
    ``preview_link`` is the URL the gate probes for reachability.
    ``token_consumption`` is the recorded number of copy characters that went into the deck.
    ``pdf_text`` is the extracted text layer of the rendered PDF (scanned for transcript artifacts).
    ``slide_backgrounds`` is the per-slide background signature, in slide order (index 0 is the
    title slide, index -1 is the closing slide).
    """

    def __init__(self, *, pdf_path, preview_link, token_consumption, pdf_text, slide_backgrounds):
        self.pdf_path = pdf_path
        self.preview_link = preview_link
        self.token_consumption = token_consumption
        self.pdf_text = pdf_text
        self.slide_backgrounds = list(slide_backgrounds or [])


class QualityResult:
    def __init__(self, failures):
        self.failures = list(failures)

    @property
    def passed(self):
        return not self.failures


class QualityGate:
    def __init__(self, *, link_checker, min_pdf_bytes=MIN_PDF_BYTES, token_budget=DEFAULT_TOKEN_BUDGET):
        self._link_checker = link_checker
        self.min_pdf_bytes = min_pdf_bytes
        self.token_budget = token_budget

    def check(self, artifact):
        failures = []
        self._check_pdf(artifact, failures)
        self._check_preview_link(artifact, failures)
        self._check_token_budget(artifact, failures)
        self._check_transcript_artifacts(artifact, failures)
        self._check_wallpaper(artifact, failures)
        return QualityResult(failures)

    def _check_pdf(self, artifact, failures):
        path = artifact.pdf_path
        if not path or not os.path.isfile(path):
            failures.append(f"missing PDF: no rendered deck PDF was found at {path!r}")
            return
        size = os.path.getsize(path)
        if size < self.min_pdf_bytes:
            failures.append(
                f"PDF file size {size} bytes is below the minimum floor of "
                f"{self.min_pdf_bytes} bytes (deck looks empty or failed to render)"
            )

    def _check_preview_link(self, artifact, failures):
        url = artifact.preview_link
        try:
            status = self._link_checker(url)
        except Exception as exc:
            failures.append(f"preview link unreachable: requesting {url!r} raised {exc!r}")
            return
        if not (isinstance(status, int) and 200 <= status < 300):
            failures.append(f"preview link unreachable: {url!r} returned HTTP {status}")

    def _check_token_budget(self, artifact, failures):
        if artifact.token_consumption > self.token_budget:
            failures.append(
                f"token-budget overflow: deck copy consumed {artifact.token_consumption} "
                f"characters, over the budget of {self.token_budget}"
            )

    def _check_transcript_artifacts(self, artifact, failures):
        text = artifact.pdf_text or ""
        hits = [name for name, pattern in TRANSCRIPT_ARTIFACT_PATTERNS if pattern.search(text)]
        if hits:
            failures.append(
                "transcript-artifact text leaked into the rendered deck: " + ", ".join(hits)
            )

    def _check_wallpaper(self, artifact, failures):
        backgrounds = artifact.slide_backgrounds
        if not backgrounds:
            return
        # Evaluate the whole set, which always includes the title (first) and closing (last) slide.
        known = sorted({b for b in backgrounds if b in GENERIC_WALLPAPER_SIGNATURES})
        if known:
            failures.append(
                "generic-wallpaper guard tripped: slides carry a known boilerplate background ("
                + ", ".join(known)
                + ")"
            )
            return
        non_empty = [b for b in backgrounds if b]
        if len(backgrounds) >= 2 and len(non_empty) == len(backgrounds) and len(set(non_empty)) == 1:
            failures.append(
                "generic-wallpaper guard tripped: every slide (title through closing) shares one "
                f"identical background image ({non_empty[0]!r}), which reads as a generic template"
            )


def http_link_checker(timeout=10):
    """Real preview-link probe: issue an HTTP request and return the status code.

    Tries HEAD first (cheap), falling back to GET when a server rejects HEAD. A connection-level
    failure (DNS, timeout, refused) propagates as an exception, which the gate treats as
    unreachable. Not unit-tested - the gate tests inject a fake checker.
    """
    import urllib.error
    import urllib.request

    def check(url):
        last_exc = None
        for method in ("HEAD", "GET"):
            req = urllib.request.Request(
                url, method=method, headers={"User-Agent": "custom-decks-quality-gate"}
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return resp.getcode()
            except urllib.error.HTTPError as exc:
                if method == "HEAD" and exc.code in (403, 405, 501):
                    continue  # some servers reject HEAD; retry once with GET
                return exc.code
            except urllib.error.URLError as exc:
                last_exc = exc
        raise last_exc if last_exc is not None else urllib.error.URLError("no response")

    return check
