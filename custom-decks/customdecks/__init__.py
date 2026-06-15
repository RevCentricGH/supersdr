"""custom-decks: generate a tailored prospect deck end-to-end from a single prospect
plus a transcript (or audio URL), rendered to Google Slides + PDF, returning a View link.

This is a Claude Code (terminal) skill. The deep modules here are pure or take their
side-effecting collaborators (HTTP, Claude, Marp, Google Drive) by injection so they can
be unit-tested without live credentials. ``build_deck`` wires them into the full pipeline.
"""
