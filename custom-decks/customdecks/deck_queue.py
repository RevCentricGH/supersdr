"""DeckQueue - build decks in bulk off the master-tracker sheet, write View links back.

This completes the master-tracker -> custom-decks pipeline. master-tracker fills a Google
Sheet with one tab per rep; each call row already carries a disposition and (when a
RecordingSource is configured) a recording link. The queue reads the activated leads from
those rep tabs, builds a deck for each, and writes the View link into a "Custom Decks" tab.

Design notes, all driven by config so nothing about a specific operator is baked in:

  - An "activated" lead is a rep-tab row whose disposition is in ``keep_dispositions`` - the
    same gate master-tracker uses on the way in.
  - The recording link is read straight from the rep tab's recording column (master-tracker's
    RecordingSource already resolved it on ingest), so the queue never re-implements dialer
    logic. A row with no recording link is skipped with a reason.
  - A deck needs a company and a website, which a call row does not have; the operator adds
    them as manual columns on the rep tab (master-tracker leaves manual columns untouched).
    A row missing either is skipped with a reason rather than guessed.
  - Idempotent: a lead whose Call ID already has a View Link in the Custom Decks tab is never
    rebuilt, so re-running only fills the gaps.

Every side effect is injected: ``sheet`` is the only thing that touches Google Sheets and
``build_deck`` is the only thing that builds a deck, so the orchestration is unit-tested with
fakes. ``run_queue`` wires the real collaborators (terminal only, not unit-tested).
"""
import os

from .errors import LockHeld

DEFAULT_DECKS_TAB = "Custom Decks"
DECKS_HEADER = ["Call ID", "Prospect", "Company", "View Link"]


class DeckQueue:
    def __init__(
        self,
        *,
        sheet,
        build_deck,
        rep_tabs,
        keep_dispositions,
        disposition_column="Disposition",
        decks_tab=DEFAULT_DECKS_TAB,
        id_column="Call ID",
        prospect_column="Prospect",
        company_column="Company",
        website_column="Website",
        recording_column="Recording URL",
    ):
        self.sheet = sheet
        self._build_deck = build_deck
        self.rep_tabs = list(rep_tabs)
        self._keep = {d.strip().lower() for d in keep_dispositions if d and d.strip()}
        self.disposition_column = disposition_column
        self.decks_tab = decks_tab
        self.id_column = id_column
        self.prospect_column = prospect_column
        self.company_column = company_column
        self.website_column = website_column
        self.recording_column = recording_column

    def _activated(self, row):
        return (row.get(self.disposition_column) or "").strip().lower() in self._keep

    def _already_linked(self):
        """Call IDs that already have a non-empty View Link in the Custom Decks tab."""
        linked = set()
        for r in self.sheet.read_rows(self.decks_tab):
            if (r.get("View Link") or "").strip():
                cid = (r.get(self.id_column) or "").strip()
                if cid:
                    linked.add(cid)
        return linked

    def run(self):
        """Build a deck for every activated, un-built lead and write its View link back.

        Returns a summary dict: ``built`` is a list of (call_id, view_url); ``skipped`` is a
        list of (call_id, reason). One lead's failure never aborts the batch.
        """
        self.sheet.ensure_header(self.decks_tab, DECKS_HEADER)
        linked = self._already_linked()
        built, skipped = [], []

        for tab in self.rep_tabs:
            for row in self.sheet.read_rows(tab):
                if not self._activated(row):
                    continue
                cid = (row.get(self.id_column) or "").strip()
                if not cid or cid in linked:
                    continue  # no id, or already has a deck (idempotent)

                recording = (row.get(self.recording_column) or "").strip()
                company = (row.get(self.company_column) or "").strip()
                website = (row.get(self.website_column) or "").strip()
                prospect_name = (row.get(self.prospect_column) or "").strip()

                if not recording:
                    skipped.append((cid, "no recording link"))
                    continue
                if not (company and website):
                    skipped.append((cid, "missing company or website"))
                    continue

                prospect = {"name": prospect_name, "company": company, "website": website}
                try:
                    view_url = self._build_deck(prospect, recording)
                except Exception as exc:  # gate failure or transient build error
                    skipped.append((cid, f"build failed: {exc}"))
                    continue

                self.sheet.append_row(self.decks_tab, [cid, prospect_name, company, view_url])
                linked.add(cid)
                built.append((cid, view_url))

        return {"built": built, "skipped": skipped}


class FileLock:
    """Exclusive on-disk lock so two queue runs never build the same sheet at once.

    Created with O_EXCL so a second run finds the file already there and raises ``LockHeld``
    instead of racing. Released on exit. A stale lock (from a crashed run) must be removed by
    hand - the message says so.
    """

    def __init__(self, path):
        self.path = path
        self._fd = None

    def __enter__(self):
        try:
            self._fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            raise LockHeld(
                f"another custom-decks queue run holds the lock at {self.path}; "
                f"remove it if you are sure no run is active"
            )
        os.write(self._fd, str(os.getpid()).encode())
        return self

    def __exit__(self, *exc):
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        try:
            os.remove(self.path)
        except FileNotFoundError:
            pass
        return False


# --- real wiring (terminal only; not unit-tested) -----------------------------------------


class GoogleSheet:
    """Minimal Google Sheets read/append adapter for the queue. Terminal-only."""

    def __init__(self, service, spreadsheet_id):
        self._svc = service
        self._id = spreadsheet_id

    def read_rows(self, tab):
        resp = (
            self._svc.values()
            .get(spreadsheetId=self._id, range=f"'{tab}'")
            .execute()
        )
        values = resp.get("values", [])
        if not values:
            return []
        header = values[0]
        return [dict(zip(header, row + [""] * (len(header) - len(row)))) for row in values[1:]]

    def ensure_header(self, tab, header):
        resp = (
            self._svc.values()
            .get(spreadsheetId=self._id, range=f"'{tab}'!1:1")
            .execute()
        )
        if not resp.get("values"):
            self._svc.values().update(
                spreadsheetId=self._id,
                range=f"'{tab}'!A1",
                valueInputOption="RAW",
                body={"values": [header]},
            ).execute()

    def append_row(self, tab, values_list):
        self._svc.values().append(
            spreadsheetId=self._id,
            range=f"'{tab}'!A1",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [values_list]},
        ).execute()


def run_queue(config, config_path):
    """Build the real collaborators and run the queue under a file lock. Terminal only."""
    from customdecks.branding import load_branding
    from customdecks.build_deck import _build_deps, build_deck

    queue_cfg = config["queue"]
    deps = _build_deps(config)
    branding = load_branding(config, config_path)

    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build as gbuild

    oauth = config.get("google_oauth", {})
    creds = Credentials.from_authorized_user_file(
        oauth.get("token_file", "token.json"),
        ["https://www.googleapis.com/auth/spreadsheets"],
    )
    sheets = gbuild("sheets", "v4", credentials=creds).spreadsheets()
    sheet = GoogleSheet(sheets, queue_cfg["google_sheet_id"])

    def build_one(prospect, recording_url):
        return build_deck(
            prospect,
            audio_url=recording_url,
            deps=deps,
            subpages=config.get("subpages", []),
            out_dir=config.get("out_dir", "out"),
            cta_text=config["cta_text"],
            cta_url=config["cta_url"],
            branding=branding,
        )

    queue = DeckQueue(
        sheet=sheet,
        build_deck=build_one,
        rep_tabs=queue_cfg["rep_tabs"],
        keep_dispositions=queue_cfg.get("keep_dispositions", []),
        decks_tab=queue_cfg.get("decks_tab", DEFAULT_DECKS_TAB),
    )

    lock_path = queue_cfg.get("lock_file", "custom-decks-queue.lock")
    with FileLock(lock_path):
        summary = queue.run()

    for cid, url in summary["built"]:
        print(f"  built {cid}: {url}")
    for cid, reason in summary["skipped"]:
        print(f"  skipped {cid}: {reason}")
    print(f"Done. {len(summary['built'])} deck(s) built, {len(summary['skipped'])} skipped.")
    return summary
