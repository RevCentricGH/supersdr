"""Put the skill directory on sys.path so tests can import the customdecks package.

The skill folder is named ``custom-decks`` (a hyphen, not a valid Python identifier),
so the importable package lives one level down as ``customdecks``. pytest imports this
conftest during collection, which is enough to make ``from customdecks.x import y`` work
from anywhere the suite runs (repo root or the skill folder).
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
