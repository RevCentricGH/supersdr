"""Typed errors raised across the custom-decks pipeline.

Each failure mode has its own type so callers (and tests) can distinguish "the caller
gave us nothing to work with" from "transcription came back empty" from "the model said
there is not enough signal to build an honest deck". A bare ``Exception`` would collapse
those into one indistinguishable failure.
"""


class CustomDecksError(Exception):
    """Base class for every error this skill raises on purpose."""


class InputError(CustomDecksError):
    """The caller supplied neither a transcript nor an audio URL, or a prospect field
    is missing. Raised before any network call so a bad invocation costs nothing."""


class TranscriptionError(CustomDecksError):
    """Both Deepgram and Groq returned empty (or raised), so there is no transcript to
    build a deck from. Never silently swallowed into an empty string."""


class InsufficientSignalError(CustomDecksError):
    """The copy model judged there is not enough real signal about the company to build
    an honest deck (it returned the ``INSUFFICIENT_SIGNAL`` sentinel). The product refuses
    to ship generic boilerplate, so this stops the pipeline rather than rendering filler."""


class CopyParseError(CustomDecksError):
    """No parseable copy JSON was found in the model's response: either no JSON object was
    present at all (no fence, no braces) or the candidate text would not parse. Distinct
    from CopyValidationError, which means the JSON parsed fine but a required key was
    absent - so a debugging operator is not misled into looking for missing keys."""


class CopyValidationError(CustomDecksError):
    """The parsed copy JSON is missing one or more required keys. The message lists the
    specific missing keys."""

    def __init__(self, missing_keys):
        self.missing_keys = list(missing_keys)
        super().__init__("copy JSON missing required keys: " + ", ".join(self.missing_keys))


class UploadError(CustomDecksError):
    """The Drive upload failed on every attempt, including retries."""


class QualityGateError(CustomDecksError):
    """The rendered deck failed one or more refuse-boilerplate checks, so the View link is
    not written. The deck is kept locally for inspection. ``failures`` lists a distinct,
    non-empty reason for every check that did not pass."""

    def __init__(self, failures):
        self.failures = list(failures)
        super().__init__("deck did not pass the quality gate: " + "; ".join(self.failures))
