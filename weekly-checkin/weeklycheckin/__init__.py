"""weekly-checkin: read master-tracker call data + SmartLead stats into a weekly digest.

The pure logic (week bounds, sheet read, stats fetch, digest assembly) lives here and is
unit-tested. ``run.py`` is the only file that touches live credentials and the network.
"""
