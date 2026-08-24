"""Pipeline - wire the pure modules and the thin wrappers into one idempotent ingest.

``ingest_rep_calls`` handles a single rep's calls; ``run`` loops the reps map and routes
each rep's calls to its own tab. The ordering that matters:

  1. skip calls already in the ledger (fast path; the sheet is still the dedup authority)
  2. drop calls whose disposition is not kept - never recorded, so a later run re-evaluates
  3. drop calls before the backfill window
  4. map to rows (resolving the recording link first, so dedup can prefer the recorded
     copy of a double-logged call), then dedup against the sheet's existing keys and
     within the batch
  5. append each new row, and only on a successful append mark the call ingested
  6. after all appends succeed, also mark the dropped duplicates whose (date, prospect)
     row is already settled in the sheet - append-only means they can never be written,
     and without the mark they would be re-fetched and re-mapped on every future run

Step 5 is the v2 fix: marking after the write means a failed write leaves the call out of
the ledger, so the next run retries it.
"""
from .call_row_mapper import AUTO_COLUMNS, RECORDING_COLUMN, CallRowMapper
from .deduper import Deduper
from .disposition_filter import DispositionFilter
from .recording_source import build_recording_source, safe_resolve


def ingest_rep_calls(
    *,
    calls,
    tab,
    sheet,
    disposition_filter,
    mapper,
    deduper,
    ingest_state,
    backfill_start=None,
    recording_source=None,
):
    header = AUTO_COLUMNS + list(mapper.manual_columns)
    sheet.ensure_header(tab, header)

    kept = []
    for call in calls:
        if ingest_state.is_ingested(call.get("id")):
            continue
        if not disposition_filter.keep(call.get("disposition")):
            continue
        if backfill_start and (call.get("date") or "") < backfill_start:
            continue
        kept.append(call)

    rows = []
    for call in kept:
        row = mapper.to_row(call)
        # The recording source is the sole authority for the recording-link column. With no
        # source, a non-resolving source, or one that raises, safe_resolve yields "" so the
        # column is left blank rather than crashing the run. Resolved before dedup so a
        # same-day duplicate pair collapses onto the row that actually has a recording.
        row.values[RECORDING_COLUMN] = safe_resolve(recording_source, call)
        rows.append(row)
    existing_keys = sheet.existing_keys(tab)
    new_rows = deduper.new_rows(rows, existing_keys)

    written = 0
    settled_keys = set(existing_keys)
    for row in new_rows:
        sheet.append_row(tab, row.as_list(header))  # may raise; mark only if it does not
        ingest_state.mark_ingested(row.call_id)
        settled_keys.add(row.key)
        written += 1
    # A dropped row whose key is settled (already in the sheet, or written by this run)
    # can never be written on any future run - the sheet is append-only - so mark it
    # ingested too, or every double-logged call is re-fetched and re-mapped forever. On a
    # mid-loop write failure this never runs, so nothing unwritten gets marked.
    for row in rows:
        if row.key in settled_keys:
            ingest_state.mark_ingested(row.call_id)
    return written


def run(config, *, apollo, sheet, ingest_state, backfill_start=None):
    """Loop the reps map. Each rep gets its own Apollo search and its own tab."""
    disposition_filter = DispositionFilter(
        config.get("keep_dispositions", []), config.get("keep_prefixes", [])
    )
    mapper = CallRowMapper(manual_columns=config.get("manual_columns", []))
    deduper = Deduper()
    # Built once at startup so an unknown source name fails fast here, before any rep is
    # searched or any row is written, rather than silently blanking recordings at run time.
    recording_source = build_recording_source(config)

    results = {}
    try:
        for rep_name, rep_cfg in config["reps"].items():
            calls = apollo.search_calls(rep_cfg, since=backfill_start)
            results[rep_name] = ingest_rep_calls(
                calls=calls,
                tab=rep_name,
                sheet=sheet,
                disposition_filter=disposition_filter,
                mapper=mapper,
                deduper=deduper,
                ingest_state=ingest_state,
                backfill_start=backfill_start,
                recording_source=recording_source,
            )
    finally:
        # Persist the ledger even when a mid-rep write raises: rows written before the
        # failure stay marked, so the next run does not re-fetch and re-map them.
        ingest_state.save()
    return results
