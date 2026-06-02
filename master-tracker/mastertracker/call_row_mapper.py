"""CallRowMapper - turn a normalized call record into a sheet row.

The mapper owns only the auto columns (the ones the tool writes). Manual columns the
operator adds are carried in the header so a fresh row reserves blank cells for them; they
are never populated by the tool and never overwritten on re-run.

Each row exposes ``key`` = (date, lowercased prospect), the identity the Deduper uses.
"""

AUTO_COLUMNS = [
    "Date",
    "Prospect",
    "Disposition",
    "Phone",
    "Duration (sec)",
    "Call ID",
    "Recording URL",
]


class MappedRow:
    def __init__(self, values, key):
        self.values = values
        self.key = key

    def as_list(self, header):
        return [self.values.get(col, "") for col in header]


class CallRowMapper:
    def __init__(self, manual_columns=None):
        self.manual_columns = list(manual_columns or [])

    def to_row(self, call):
        prospect = (call.get("prospect") or "").strip()
        date = call.get("date") or ""
        values = {
            "Date": date,
            "Prospect": prospect,
            "Disposition": call.get("disposition") or "",
            "Phone": call.get("phone") or "",
            "Duration (sec)": call.get("duration_sec"),
            "Call ID": call.get("id") or "",
            "Recording URL": call.get("recording_url") or "",
        }
        for col in self.manual_columns:
            values[col] = ""
        return MappedRow(values=values, key=(date, prospect.lower()))
