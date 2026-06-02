"""master-tracker: pull a rep's Apollo calls into per-rep tabs of a Google Sheet.

Deep modules (pure, unit-tested):
  - DispositionFilter  - keep-set + prefix match
  - CallRowMapper      - normalized call record -> sheet row
  - Deduper            - dedup by (date, lowercased prospect)
  - IngestState        - ingested-call ledger; mark-only-after-write
  - pipeline           - per-rep ingest orchestration

Thin side-effecting wrappers (validated by manual run):
  - ApolloClient       - paged phone-call search with 429 backoff
  - SheetWriter        - append-only merge that preserves manual columns
"""
