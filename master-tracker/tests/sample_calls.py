"""Fixture builders for normalized Apollo call records.

A "normalized call record" is what ``ApolloClient`` yields and what every pure module
downstream consumes: raw Apollo JSON quirks are isolated in the client. Tests build these
records directly so they never touch a live API or sheet.
"""


def make_call(
    id="call_1",
    date="2026-05-20",
    prospect="Jane Doe",
    disposition="Interested",
    phone="+15551230001",
    duration_sec=142,
    recording_url="",
    timestamp=None,
):
    return {
        "id": id,
        "date": date,
        "timestamp": timestamp or (date + "T15:04:05Z"),
        "prospect": prospect,
        "disposition": disposition,
        "phone": phone,
        "duration_sec": duration_sec,
        "recording_url": recording_url,
    }
