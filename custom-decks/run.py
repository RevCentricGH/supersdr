#!/usr/bin/env python3
"""custom-decks CLI shim - generate tailored prospect decks.

Runs in a terminal (NOT Cowork). Two modes, chosen by config:

  - Queue mode (config has a ``queue`` block with a ``google_sheet_id``): build decks in bulk
    off the master-tracker sheet and write View links back. Takes no prospect flags.

        python3 run.py --config config.json

  - Ad-hoc mode (no queue configured): one prospect in, one View link out.

        python3 run.py --name "Jane Doe" --company "Acme" --website https://acme.com \\
            --transcript call.txt
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _config_path(argv):
    """Peek the --config value (default config.json) so the mode can be chosen before the
    per-mode argument parser runs."""
    for i, arg in enumerate(argv):
        if arg == "--config" and i + 1 < len(argv):
            return argv[i + 1]
        if arg.startswith("--config="):
            return arg.split("=", 1)[1]
    return "config.json"


def main():
    path = _config_path(sys.argv[1:])
    config = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            config = json.load(fh)

    if config.get("queue", {}).get("google_sheet_id"):
        from customdecks.deck_queue import run_queue

        run_queue(config, path)
    else:
        from customdecks.build_deck import main as build_main

        build_main()


if __name__ == "__main__":
    main()
