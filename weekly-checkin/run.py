#!/usr/bin/env python3
"""weekly-checkin CLI - build a weekly per-client delivery digest and deliver it.

Runs in a terminal (NOT Cowork). It reads call/disposition rows from the master-tracker Google
Sheet for the requested ISO week and pulls each client's SmartLead campaign stats, builds a
per-client digest, then delivers it to the destination configured in config.json (a Google Doc,
a Slack webhook, or email). Schedule it on a weekly cron, or run it on demand.

    python3 run.py --week 2026-W22                        # deliver per config.json
    python3 run.py --week 2026-W22 --config /path/cfg.json
    python3 run.py --week 2026-W22 --dry-run              # print the digest, deliver nothing

The schedule lives in config (`schedule.cron`) as a reference value you paste into your crontab;
run.py does not evaluate it and runs unconditionally when invoked. This file is the only place
that touches live credentials and the network. All the logic it calls (week bounds, sheet read,
stats fetch, digest assembly, delivery routing, locking) lives in the unit-tested weeklycheckin
package.
"""
import argparse
import os
import secrets
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from weeklycheckin import deliver, lockfile
from weeklycheckin.config import load_config
from weeklycheckin.digest_builder import DigestBuilder, digest_has_activity, render_digest
from weeklycheckin.sheet_reader import SheetReader
from weeklycheckin.smartlead_client import SmartLeadClient
from weeklycheckin.week_filter import week_bounds

# Read-only on the sheet. google_doc delivery additionally needs documents write access; that
# scope is added only when the configured delivery type is google_doc (see _scopes_for).
SHEETS_READONLY = "https://www.googleapis.com/auth/spreadsheets.readonly"
DOCS_SCOPE = "https://www.googleapis.com/auth/documents"


def _scopes_for(delivery_cfg):
    scopes = [SHEETS_READONLY]
    if isinstance(delivery_cfg, dict) and delivery_cfg.get("type") == "google_doc":
        scopes.append(DOCS_SCOPE)
    return scopes


def _build_credentials(oauth_cfg, scopes):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    token_file = oauth_cfg.get("token_file", "token.json")
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(oauth_cfg["credentials_file"], scopes)
            creds = flow.run_local_server(port=0)
        fd = os.open(token_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(creds.to_json())
    return creds


def _sheets_service(creds):
    from googleapiclient.discovery import build

    return build("sheets", "v4", credentials=creds).spreadsheets()


def _doc_appender(creds):
    """Return append(document_id, text): insert `text` at the end of the Doc's body in one
    batchUpdate. Thin live-API wiring, validated by the end-to-end run (not unit-tested)."""
    from googleapiclient.discovery import build

    docs = build("docs", "v1", credentials=creds).documents()

    def append(document_id, text):
        doc = docs.get(documentId=document_id).execute()
        end_index = doc["body"]["content"][-1]["endIndex"]
        docs.batchUpdate(
            documentId=document_id,
            body={"requests": [{"insertText": {"location": {"index": end_index - 1}, "text": text}}]},
        ).execute()

    return append


def _build_digest(config, week):
    start, end = week_bounds(week)
    clients = config["clients"]
    creds = _build_credentials(config.get("google_oauth", {}), _scopes_for(config.get("delivery")))
    reader = SheetReader(_sheets_service(creds), config["google_sheet_id"])
    tabs = [tab for client in clients for tab in client.get("rep_tabs", [])]
    sheet_rows = reader.read_weeks(tabs, start, end)

    smartlead = SmartLeadClient(config["smartlead_api_key"])
    smartlead_stats = {}
    for client in clients:
        smartlead_stats.update(
            smartlead.fetch_campaign_stats(
                client.get("smartlead_campaign_ids", []), start.isoformat(), end.isoformat()
            )
        )
    sections = DigestBuilder().build(clients, sheet_rows, smartlead_stats, week)
    return sections, creds


def _new_run_id():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "-" + secrets.token_hex(2)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build and deliver a weekly per-client digest.")
    parser.add_argument("--week", required=True, help="YYYY-WNN (ISO 8601 week, Monday-anchored)")
    parser.add_argument("--config", default="config.json", help="path to config.json")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the digest to stdout and deliver nothing (run before the first live send)",
    )
    args = parser.parse_args(argv)

    config = load_config(args.config)
    delivery_cfg = config.get("delivery")

    if args.dry_run:
        sections, _ = _build_digest(config, args.week)
        print(render_digest(sections))
        print("\n[dry-run] delivery skipped.", file=sys.stderr)
        return

    # Fail fast on a misconfigured destination before doing any network work.
    deliver.validate_delivery_config(delivery_cfg)

    lock_path = lockfile.lock_path_for(args.config)
    pid = os.getpid()
    try:
        lockfile.acquire(lock_path, pid=pid, now=time.time())
    except lockfile.LockHeld as exc:
        raise SystemExit(f"weekly-checkin: {exc}")

    try:
        sections, creds = _build_digest(config, args.week)
        digest = render_digest(sections)

        if not digest_has_activity(sections):
            print(
                f"warning: no call or campaign activity for {args.week}; "
                "delivering no-activity notice",
                file=sys.stderr,
            )
            digest = (
                f"weekly-checkin {args.week}: no call or campaign activity this week.\n\n"
                + digest
            )

        run_id = _new_run_id()
        doc_appender = _doc_appender(creds) if delivery_cfg.get("type") == "google_doc" else None
        deliver.deliver(digest, delivery_cfg, run_id=run_id, doc_appender=doc_appender)
        print(
            f"delivered {args.week} digest via {delivery_cfg['type']} (run_id {run_id})",
            file=sys.stderr,
        )
    finally:
        lockfile.release(lock_path, pid=pid)


if __name__ == "__main__":
    main()
