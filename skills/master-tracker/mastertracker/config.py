"""Config loading and the backfill-window start date.

The backfill window is expressed as a day count in config; ``compute_backfill_start`` turns
it into the ISO start date the pipeline and ApolloClient bound their searches to. ``today``
is injectable so the computation is testable.
"""
import datetime
import json


def load_config(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def compute_backfill_start(config, today=None):
    days = config.get("backfill_days")
    if not days:
        return None
    today = today or datetime.date.today()
    start = today - datetime.timedelta(days=int(days))
    return start.isoformat()
