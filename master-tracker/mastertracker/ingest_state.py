"""IngestState - the ledger of call IDs that have been written to the sheet.

The pipeline marks a call ingested only after its row write succeeds, then persists. This
is the v2 fix: a call a rep dispositions *after* the dialer first logs it is left out of
the ledger until the run that actually writes its row, so it is never silently dropped.

The ledger is a fast-path skip (do not re-map a call we already wrote); dedup correctness
itself rests on the sheet, not on this file. A missing or empty state file therefore loads
clean and causes no duplicates.
"""
import json
import os


class IngestState:
    def __init__(self, path):
        self.path = path
        self._ids = self._load(path)

    @staticmethod
    def _load(path):
        if not path or not os.path.exists(path):
            return set()
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError):
            return set()
        return set(data.get("ingested_ids", []))

    def is_ingested(self, call_id):
        return bool(call_id) and call_id in self._ids

    def mark_ingested(self, call_id):
        if call_id:
            self._ids.add(call_id)

    def save(self):
        payload = {"ingested_ids": sorted(self._ids)}
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        os.replace(tmp, self.path)
