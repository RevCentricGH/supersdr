"""DeckQueue: build decks in bulk off the master-tracker sheet, write View links back.

Covers issue #12: disposition gating, recording/company/website preconditions, idempotency,
build-failure resilience, and the overlapping-run lock.
"""
import pytest

from customdecks.deck_queue import DECKS_HEADER, DeckQueue, FileLock
from customdecks.errors import LockHeld

REP_HEADER = ["Date", "Prospect", "Disposition", "Call ID", "Recording URL", "Company", "Website"]


class FakeSheet:
    def __init__(self):
        self.tabs = {}

    def seed(self, tab, rows, header=REP_HEADER):
        self.tabs[tab] = {"header": list(header), "rows": [dict(r) for r in rows]}

    def read_rows(self, tab):
        return [dict(r) for r in self.tabs.get(tab, {}).get("rows", [])]

    def ensure_header(self, tab, header):
        self.tabs.setdefault(tab, {"header": list(header), "rows": []})

    def append_row(self, tab, values_list):
        t = self.tabs[tab]
        t["rows"].append(dict(zip(t["header"], values_list)))

    def decks(self):
        return self.read_rows("Custom Decks")


def _lead(cid, disp="Meeting Booked", prospect="Jane Doe", company="Acme Corp",
          website="https://acme.test", recording="https://rec.test/" + "x"):
    return {
        "Date": "2026-05-20",
        "Prospect": prospect,
        "Disposition": disp,
        "Call ID": cid,
        "Recording URL": recording,
        "Company": company,
        "Website": website,
    }


class SpyBuilder:
    """Records (prospect, recording) calls and returns a deterministic view url per call id."""

    def __init__(self, fail_for=None):
        self.calls = []
        self.fail_for = fail_for or set()

    def __call__(self, prospect, recording):
        self.calls.append((prospect, recording))
        if prospect["company"] in self.fail_for:
            raise RuntimeError("gate failed")
        return f"https://slides.test/{prospect['company'].replace(' ', '_')}/view"


def _queue(sheet, builder, **overrides):
    kw = dict(
        sheet=sheet,
        build_deck=builder,
        rep_tabs=["Rep A"],
        keep_dispositions=["Meeting Booked", "Interested"],
    )
    kw.update(overrides)
    return DeckQueue(**kw)


def test_builds_a_deck_for_each_activated_lead_and_writes_the_view_link():
    sheet = FakeSheet()
    sheet.seed("Rep A", [_lead("c1", prospect="Jane", company="Acme")])
    builder = SpyBuilder()

    summary = _queue(sheet, builder).run()

    assert len(builder.calls) == 1
    assert summary["built"] == [("c1", "https://slides.test/Acme/view")]
    decks = sheet.decks()
    assert decks == [{"Call ID": "c1", "Prospect": "Jane", "Company": "Acme",
                      "View Link": "https://slides.test/Acme/view"}]
    assert DECKS_HEADER == ["Call ID", "Prospect", "Company", "View Link"]


def test_skips_leads_whose_disposition_is_not_activated():
    sheet = FakeSheet()
    sheet.seed("Rep A", [_lead("c1", disp="No Answer")])
    builder = SpyBuilder()

    summary = _queue(sheet, builder).run()
    assert builder.calls == []
    assert summary["built"] == []
    assert sheet.decks() == []


def test_skips_a_lead_with_no_recording_link():
    sheet = FakeSheet()
    sheet.seed("Rep A", [_lead("c1", recording="")])
    builder = SpyBuilder()

    summary = _queue(sheet, builder).run()
    assert builder.calls == []
    assert summary["built"] == []
    assert summary["skipped"] == [("c1", "no recording link")]


def test_skips_a_lead_missing_company_or_website():
    sheet = FakeSheet()
    sheet.seed("Rep A", [_lead("c1", company=""), _lead("c2", website="")])
    builder = SpyBuilder()

    summary = _queue(sheet, builder).run()
    assert builder.calls == []
    assert {cid for cid, _ in summary["skipped"]} == {"c1", "c2"}
    assert all(reason == "missing company or website" for _, reason in summary["skipped"])


def test_is_idempotent_skipping_leads_already_linked():
    sheet = FakeSheet()
    sheet.seed("Rep A", [_lead("c1", company="Acme")])
    # a prior run already wrote a View Link for c1
    sheet.seed("Custom Decks", [
        {"Call ID": "c1", "Prospect": "Jane", "Company": "Acme", "View Link": "https://old/view"},
    ], header=DECKS_HEADER)
    builder = SpyBuilder()

    summary = _queue(sheet, builder).run()
    assert builder.calls == []        # not rebuilt
    assert summary["built"] == []
    assert len(sheet.decks()) == 1    # no duplicate row appended


def test_a_build_failure_skips_that_lead_without_aborting_the_batch():
    sheet = FakeSheet()
    sheet.seed("Rep A", [
        _lead("c1", company="Boilerplate Co"),  # builder will raise for this one
        _lead("c2", company="Acme"),
    ])
    builder = SpyBuilder(fail_for={"Boilerplate Co"})

    summary = _queue(sheet, builder).run()
    assert summary["built"] == [("c2", "https://slides.test/Acme/view")]
    assert summary["skipped"] and summary["skipped"][0][0] == "c1"
    assert "build failed" in summary["skipped"][0][1]
    # only the successful lead is written back
    assert [r["Call ID"] for r in sheet.decks()] == ["c2"]


def test_reads_activated_leads_across_multiple_rep_tabs():
    sheet = FakeSheet()
    sheet.seed("Rep A", [_lead("a1", company="Acme")])
    sheet.seed("Rep B", [_lead("b1", company="Beta")])
    builder = SpyBuilder()

    summary = _queue(sheet, builder, rep_tabs=["Rep A", "Rep B"]).run()
    assert {cid for cid, _ in summary["built"]} == {"a1", "b1"}


# --- FileLock (overlapping-run guard) -----------------------------------------------

def test_file_lock_blocks_a_second_concurrent_run(tmp_path):
    path = str(tmp_path / "queue.lock")
    with FileLock(path):
        with pytest.raises(LockHeld):
            with FileLock(path):
                pass


def test_file_lock_is_released_on_exit_so_a_later_run_can_acquire(tmp_path):
    path = str(tmp_path / "queue.lock")
    with FileLock(path):
        pass
    # released - a subsequent run acquires cleanly
    with FileLock(path):
        pass
