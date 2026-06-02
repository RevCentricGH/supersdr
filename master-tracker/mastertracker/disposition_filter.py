"""DispositionFilter - decide which calls reach the sheet, purely from the disposition.

Keeping is a set membership test plus a prefix test, both case-insensitive. A call that is
not kept is dropped before any per-call work (recording lookup, sheet write) happens, so a
skipped call never burns an API call. Skipped calls are also never recorded as ingested, so
a later run re-evaluates them once a rep tags them with a kept disposition.
"""


class DispositionFilter:
    def __init__(self, keep_dispositions, keep_prefixes=None):
        self._keep = {d.strip().lower() for d in keep_dispositions if d and d.strip()}
        self._prefixes = [
            p.strip().lower() for p in (keep_prefixes or []) if p and p.strip()
        ]

    def keep(self, disposition):
        if not disposition:
            return False
        d = disposition.strip().lower()
        if d in self._keep:
            return True
        return any(d.startswith(p) for p in self._prefixes)
