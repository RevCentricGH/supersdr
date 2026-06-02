#!/usr/bin/env python3
"""custom-decks CLI shim - generate a tailored prospect deck (ad-hoc mode).

Runs in a terminal (NOT Cowork). All wiring lives in customdecks.build_deck.main; this is
just the entry point so you can run:

    python3 run.py --name "Jane Doe" --company "Acme" --website https://acme.com \\
        --transcript call.txt
    python3 run.py --name "Jane Doe" --company "Acme" --website https://acme.com \\
        --audio-url https://.../call.mp3
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from customdecks.build_deck import main

if __name__ == "__main__":
    main()
