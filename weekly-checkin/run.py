#!/usr/bin/env python3
"""weekly-checkin CLI - build a weekly per-client delivery digest.

Runs in a terminal (NOT Cowork). It reads call/disposition rows from the master-tracker Google
Sheet for the requested ISO week and pulls each client's SmartLead campaign stats, then prints a
per-client digest. It only reads the sheet; it never writes to it.

    python3 run.py --week 2026-W22
    python3 run.py --week 2026-W22 --config /path/to/config.json

This file is the only place that touches live credentials and the network. All the logic it
calls (week bounds, sheet read, stats fetch, digest assembly) lives in the unit-tested
weeklycheckin package.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from weeklycheckin.config import load_config
from weeklycheckin.digest_builder import DigestBuilder, render_digest
from weeklycheckin.sheet_reader import SheetReader
from weeklycheckin.smartlead_client import SmartLeadClient
from weeklycheckin.week_filter import week_bounds

# Read-only: this skill never writes to the sheet.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def _build_sheets_service(oauth_cfg):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    token_file = oauth_cfg.get("token_file", "token.json")
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                oauth_cfg["credentials_file"], SCOPES
            )
            creds = flow.run_local_server(port=0)
        fd = os.open(token_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(creds.to_json())
    return build("sheets", "v4", credentials=creds).spreadsheets()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build a weekly per-client delivery digest.")
    parser.add_argument(
        "--week", required=True, help="YYYY-WNN (ISO 8601 week, Monday-anchored)"
    )
    parser.add_argument("--config", default="config.json", help="path to config.json")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    start, end = week_bounds(args.week)
    clients = config["clients"]

    service = _build_sheets_service(config.get("google_oauth", {}))
    reader = SheetReader(service, config["google_sheet_id"])
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

    sections = DigestBuilder().build(clients, sheet_rows, smartlead_stats, args.week)
    print(render_digest(sections))


if __name__ == "__main__":
    main()
