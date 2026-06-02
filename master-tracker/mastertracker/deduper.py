"""Deduper - keep only rows the sheet does not already have.

Identity is (date, lowercased prospect). A row is new when its key is absent from the
existing sheet keys and has not already appeared earlier in the same batch. The existing
keys come straight from the sheet, not from local state, so an empty or wiped state file
never causes a duplicate (contract 18).
"""


class Deduper:
    def new_rows(self, rows, existing_keys):
        seen = set(existing_keys)
        out = []
        for row in rows:
            if row.key in seen:
                continue
            seen.add(row.key)
            out.append(row)
        return out
