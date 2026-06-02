"""RecordingSource - resolve a recording link for a call, whatever dialer logged it.

Students dial in Apollo, not Trellus, so the dialer is abstracted behind one interface:
``resolve(call) -> recording link``. Callers never branch on the dialer; they hold one
``RecordingSource`` selected from config and ask it to resolve each call.

Adapters:
  - ``apollo``     - surface the recording URL Apollo's API already attached to the call.
  - ``trellus``    - parse the Trellus session id out of the call note and build the link.
  - ``manual-url`` - return a recording URL the operator attached to the call by hand
    (also accepts the aliases ``manual_url`` and ``manual``).

An adapter never raises on a malformed or unresolvable record; it returns "" so the caller
leaves the recording-link column blank. ``safe_resolve`` adds a second belt: even an adapter
that does raise (or a missing source) degrades to "" rather than crashing the run.
"""
import re

APOLLO = "apollo"
TRELLUS = "trellus"
MANUAL_URL = "manual-url"
# Accepted spellings of the manual-url type, so a config that writes "manual_url" or
# "manual" still selects the manual adapter. Listed in the build error so the aliases are
# documented, not hidden.
MANUAL_URL_ALIASES = ("manual_url", "manual")
VALID_TYPES = (APOLLO, TRELLUS, MANUAL_URL)


class UnknownRecordingSource(ValueError):
    """Raised at build time when config names a source type we do not have an adapter for."""


class RecordingSource:
    """Resolve a recording link / audio URL for a normalized call record.

    Subclasses return a non-empty link when they can resolve one, or "" when they cannot.
    """

    def resolve(self, call):  # pragma: no cover - interface
        raise NotImplementedError


class ApolloRecordingSource(RecordingSource):
    """Apollo's API attaches the recording URL to the call record (``recording_url``).
    The adapter surfaces it; a record without one resolves to "".
    """

    def resolve(self, call):
        if not isinstance(call, dict):
            return ""
        return _clean_url(call.get("recording_url"))


class TrellusRecordingSource(RecordingSource):
    """The Trellus dialer writes a session id (a ``sess_``-prefixed token) into the call
    note. The adapter parses it out and builds the Trellus recording link. A note with no
    session id, or only a partial / corrupt token, resolves to "".

    ``base_url`` is overridable from config for a student whose Trellus tenant differs.
    """

    SESSION_RE = re.compile(r"sess_[A-Za-z0-9]{8,}")
    DEFAULT_BASE_URL = "https://app.trellus.ai/recordings"

    def __init__(self, base_url=None):
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")

    def resolve(self, call):
        if not isinstance(call, dict):
            return ""
        note = call.get("note")
        if not isinstance(note, str):
            return ""
        match = self.SESSION_RE.search(note)
        if not match:
            return ""
        return f"{self.base_url}/{match.group(0)}"


class ManualUrlRecordingSource(RecordingSource):
    """The operator has no dialer integration and attaches a recording URL to the call by
    hand. The adapter returns that URL when it is a valid http(s) link, else "".

    ``field`` (the call key the URL lives on) is overridable from config; it defaults to
    ``manual_recording_url``.
    """

    DEFAULT_FIELD = "manual_recording_url"

    def __init__(self, field=None):
        self.field = field or self.DEFAULT_FIELD

    def resolve(self, call):
        if not isinstance(call, dict):
            return ""
        return _clean_url(call.get(self.field))


def build_recording_source(config):
    """Build the RecordingSource named in ``config["recording_source"]``.

    Returns ``None`` when no source is configured (the caller leaves the column blank).
    Raises ``UnknownRecordingSource`` at build time for a type we have no adapter for, so a
    typo'd source fails fast at startup rather than silently blanking every recording.
    """
    cfg = config.get("recording_source")
    if not cfg:
        return None
    if isinstance(cfg, str):
        cfg = {"type": cfg}
    type_ = (cfg.get("type") or "").strip().lower()
    if not type_:
        return None
    if type_ == APOLLO:
        return ApolloRecordingSource()
    if type_ == TRELLUS:
        return TrellusRecordingSource(base_url=cfg.get("base_url"))
    if type_ in (MANUAL_URL, *MANUAL_URL_ALIASES):
        return ManualUrlRecordingSource(field=cfg.get("field"))
    raise UnknownRecordingSource(
        f"Unknown recording_source type {type_!r}. Valid types: {', '.join(VALID_TYPES)} "
        f"(aliases for {MANUAL_URL}: {', '.join(MANUAL_URL_ALIASES)})."
    )


def safe_resolve(source, call):
    """Resolve a recording link, degrading to "" rather than ever crashing the run.

    A missing source, an adapter that raises, or a ``None`` result all collapse to "" so the
    caller simply leaves the recording-link column blank.
    """
    if source is None:
        return ""
    try:
        result = source.resolve(call)
    except Exception:
        return ""
    # Adapters resolve to a str link (or "" when unresolvable). None or any non-str is an
    # adapter contract violation; degrade to "" instead of stringifying an arbitrary object
    # into the recording column.
    if not isinstance(result, str):
        return ""
    return result.strip()


def _clean_url(value):
    if not isinstance(value, str):
        return ""
    v = value.strip()
    if v.startswith("http://") or v.startswith("https://"):
        return v
    return ""
