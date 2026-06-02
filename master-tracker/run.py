#!/usr/bin/env python3
"""master-tracker CLI - pull each rep's Apollo calls into per-rep tabs of a Google Sheet.

Runs in a terminal (NOT Cowork). Wire up real credentials in config.json, then:

    python3 run.py                # uses ./config.json
    python3 run.py --config path/to/config.json

This file is the only place that touches live credentials and the network. All the logic it
calls (filter, dedup, mark-after-write) lives in the unit-tested mastertracker package.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mastertracker.apollo_client import ApolloClient
from mastertracker.config import compute_backfill_start, load_config
from mastertracker.ingest_state import IngestState
from mastertracker.pipeline import run
from mastertracker.sheet_writer import SheetWriter

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


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
        with open(token_file, "w", encoding="utf-8") as fh:
            fh.write(creds.to_json())
    return build("sheets", "v4", credentials=creds).spreadsheets()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Pull Apollo calls into a Google Sheet.")
    parser.add_argument("--config", default="config.json", help="path to config.json")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    backfill_start = compute_backfill_start(config)

    apollo = ApolloClient(config["apollo_api_key"])
    service = _build_sheets_service(config.get("google_oauth", {}))
    sheet = SheetWriter(service, config["google_sheet_id"])
    state = IngestState(config.get("state_file", "state.json"))

    results = run(config, apollo=apollo, sheet=sheet, ingest_state=state, backfill_start=backfill_start)

    total = sum(results.values())
    for rep, n in results.items():
        print(f"  {rep}: {n} new row(s)")
    print(f"Done. {total} new row(s) across {len(results)} rep tab(s).")


if __name__ == "__main__":
    main()
