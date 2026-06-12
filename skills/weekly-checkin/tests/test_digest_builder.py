"""DigestBuilder: per-client join of sheet rows + SmartLead stats, with empty-week safety.

Fixture rows match the live master-tracker sheet column order (Date, Prospect, Disposition),
so this is the highest-signal test: it fails if the sheet column names drift out of lockstep.
"""
from weeklycheckin.digest_builder import DigestBuilder, render_digest

CLIENTS = [
    {"name": "Acme", "rep_tabs": ["Alice", "Bob"], "smartlead_campaign_ids": [11]},
    {"name": "Beta", "rep_tabs": ["Carol"], "smartlead_campaign_ids": [22, 33]},
]


def _row(date, prospect, disposition):
    return {"Date": date, "Prospect": prospect, "Disposition": disposition, "Phone": "x"}


def _stats(sent, opens, replies, bounces):
    return {
        "sent": sent,
        "opens": opens,
        "replies": replies,
        "bounces": bounces,
        "open_rate": opens / sent if sent else 0.0,
        "reply_rate": replies / sent if sent else 0.0,
    }


def test_per_client_sections_with_counts_and_dispositions():
    sheet_rows = {
        "Alice": [_row("2026-05-25", "J", "Interested"), _row("2026-05-26", "K", "Meeting Booked")],
        "Bob": [_row("2026-05-27", "L", "Interested")],
        "Carol": [_row("2026-05-28", "M", "Not Interested")],
    }
    smartlead = {11: _stats(100, 40, 10, 2), 22: _stats(50, 5, 1, 0), 33: _stats(0, 0, 0, 0)}
    sections = DigestBuilder().build(CLIENTS, sheet_rows, smartlead, "2026-W22")

    assert [s["client"] for s in sections] == ["Acme", "Beta"]
    acme = sections[0]
    assert acme["calls"] == 3
    assert acme["dispositions"] == {"Interested": 2, "Meeting Booked": 1}
    assert acme["campaigns"][0]["stats"]["reply_rate"] == 0.1

    beta = sections[1]
    assert beta["calls"] == 1
    assert beta["dispositions"] == {"Not Interested": 1}
    assert [c["campaign_id"] for c in beta["campaigns"]] == [22, 33]
    assert beta["week"] == "2026-W22"


def test_empty_week_yields_zeros_not_crash():
    sheet_rows = {"Alice": [], "Bob": [], "Carol": []}
    sections = DigestBuilder().build(CLIENTS, sheet_rows, {}, "2026-W22")
    assert sections[0]["calls"] == 0
    assert sections[0]["dispositions"] == {}
    # a campaign with no stats is carried as None, not silently zeroed
    assert sections[0]["campaigns"][0]["stats"] is None


def test_render_includes_client_titles_and_no_stats_marker():
    sheet_rows = {"Alice": [_row("2026-05-25", "J", "Interested")], "Bob": [], "Carol": []}
    smartlead = {11: _stats(100, 40, 10, 2)}
    sections = DigestBuilder().build(CLIENTS, sheet_rows, smartlead, "2026-W22")
    text = render_digest(sections)
    assert "Acme" in text
    assert "Beta" in text
    assert "2026-W22" in text
    assert "no stats" in text  # Beta's campaigns have no stats this week
