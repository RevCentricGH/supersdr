"""Deduper - keep only rows the sheet does not already have.

The dialer's call ID is the primary identity: copies of the same call in one batch
collapse to one row first, keeping the copy with a recording, so a copy re-returned by
paging after its recording attached still contributes the link. (date, lowercased
prospect) is the secondary identity, decided from the sheet's existing keys, never from
local state, so an empty or wiped state file never causes a duplicate (contract 18).

When two distinct calls in one batch collide on (date, prospect) with the SAME
disposition - some accounts log one conversation twice, one entry with a recording and
one without - the entry WITH a recording wins, whichever arrived first. Calls whose
dispositions differ are genuinely different conversations, so the first one keeps the
row: a recorded afternoon follow-up can never replace a booked meeting in the sheet.
"""


class Deduper:
    def new_rows(self, rows, existing_keys):
        # Stage 1: collapse copies of the same call ID, preferring the recorded copy.
        # Rows without an ID get a per-row sentinel so they never collapse here.
        by_call = {}
        for index, row in enumerate(rows):
            ident = row.call_id or ("", index)
            current = by_call.get(ident)
            if current is None:
                by_call[ident] = row
            elif row.has_recording and not current.has_recording:
                by_call[ident] = row
        # Stage 2: drop rows the sheet already has, then collapse same-day duplicates.
        # dicts are insertion-ordered and replacement keeps position, so the dict itself
        # is the single source of output order.
        best = {}
        for row in by_call.values():
            if row.key in existing_keys:
                continue
            current = best.get(row.key)
            if current is None:
                best[row.key] = row
            elif (
                row.has_recording
                and not current.has_recording
                and row.disposition == current.disposition
            ):
                best[row.key] = row
        return list(best.values())
