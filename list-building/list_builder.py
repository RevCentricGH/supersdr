#!/usr/bin/env python3
"""
list_builder.py — Apollo contact list builder for SuperSDR

Claude reads the SPOT doc and extracts ICP filters, then calls this script
with those filters. This script only handles Apollo — no Google auth needed.

Usage:
    python list_builder.py --filters /tmp/icp_filters.json \
                           --list-name "Client - Contacts - 2026-05-21" \
                           --api-key "YOUR_APOLLO_API_KEY"

Requirements:
    pip install requests
"""

import argparse
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

APOLLO_SEARCH_URL = "https://api.apollo.io/api/v1/mixed_people/api_search"
APOLLO_CONTACTS_URL = "https://api.apollo.io/api/v1/contacts/bulk_create"

# ── Apollo people search ──────────────────────────────────────────────────────

def apollo_search(filters: dict, api_key: str) -> list[dict]:
    try:
        import requests
    except ImportError:
        sys.exit("Missing requests. Run: pip install requests")

    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }

    payload: dict = {"per_page": 100, "page": 1}

    if filters.get("target_titles"):
        payload["person_titles"] = filters["target_titles"]
    if filters.get("locations"):
        payload["person_locations"] = filters["locations"]
    if filters.get("employee_range"):
        payload["organization_num_employees_ranges"] = filters["employee_range"]
    if filters.get("funding_stages"):
        payload["organization_latest_funding_stage_cd"] = filters["funding_stages"]
    if filters.get("tech_signals"):
        payload["currently_using_any_of_following_technologies"] = filters["tech_signals"]

    kw_tags = filters.get("keywords", []) + filters.get("industries", [])
    if kw_tags:
        payload["q_organization_keyword_tags"] = kw_tags

    all_people: list[dict] = []
    page = 1

    while True:
        payload["page"] = page
        resp = requests.post(APOLLO_SEARCH_URL, headers=headers, json=payload)

        if resp.status_code == 401:
            sys.exit(
                "Apollo API error: invalid API key.\n"
                "Go to Apollo → Settings → Integrations → API and copy the key again."
            )
        if resp.status_code == 422:
            sys.exit(f"Apollo API error: invalid filter values.\n{resp.text[:400]}")
        if resp.status_code == 429:
            print("  Rate limited — waiting 5s...")
            time.sleep(5)
            continue
        if resp.status_code != 200:
            sys.exit(f"Apollo API error {resp.status_code}: {resp.text[:300]}")

        data = resp.json()
        people = data.get("people", [])
        total = (data.get("pagination") or {}).get("total_entries", 0) or data.get("total_entries", 0)

        all_people.extend(people)
        print(f"  Page {page}: {len(people)} results (total available: {total})")

        if not people or len(people) < 100 or len(all_people) >= total:
            break

        page += 1

    return all_people


# ── Exclusion filter (client-side — no Apollo API param) ──────────────────────

def apply_exclusions(people: list[dict], exclusions: list[str]) -> list[dict]:
    if not exclusions:
        return people
    exclude_lower = [e.lower() for e in exclusions]
    filtered = [
        p for p in people
        if not any(
            excl in ((p.get("organization") or {}).get("primary_domain") or "").lower()
            for excl in exclude_lower
        )
    ]
    dropped = len(people) - len(filtered)
    if dropped:
        print(f"  Filtered out {dropped} contacts matching exclusion domains ({len(filtered)} remaining)")
    return filtered


# ── Apollo contact list creation ──────────────────────────────────────────────

def create_contact_list(people: list[dict], list_name: str, api_key: str) -> int:
    """
    Bulk-create contacts in the user's Apollo workspace and assign them to
    a named list via append_label_names — one API call per batch of 100.
    Returns total contacts processed.
    """
    try:
        import requests
    except ImportError:
        sys.exit("Missing requests. Run: pip install requests")

    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }

    total = 0

    for batch_num, i in enumerate(range(0, len(people), 100), start=1):
        batch = people[i : i + 100]

        contacts = []
        for p in batch:
            org = p.get("organization") or {}
            contacts.append({
                "first_name":        p.get("first_name", ""),
                "last_name":         p.get("last_name") or p.get("last_name_obfuscated", ""),
                "title":             p.get("title", ""),
                "organization_name": org.get("name", ""),
                "website_url":       org.get("website_url") or org.get("primary_domain", ""),
                "linkedin_url":      p.get("linkedin_url", ""),
            })

        payload = {
            "contacts": contacts,
            "append_label_names": [list_name],
        }

        resp = requests.post(APOLLO_CONTACTS_URL, headers=headers, json=payload)

        if resp.status_code == 429:
            print(f"  Rate limited on batch {batch_num} — waiting 5s...")
            time.sleep(5)
            resp = requests.post(APOLLO_CONTACTS_URL, headers=headers, json=payload)

        if resp.status_code not in (200, 201):
            print(f"  Warning: batch {batch_num} returned {resp.status_code}: {resp.text[:200]}")
            continue

        data = resp.json()
        batch_count = len(data.get("contacts", [])) + len(data.get("existing_contacts", []))
        total += batch_count
        print(f"  Batch {batch_num}: {batch_count} contacts added to '{list_name}'")

    return total


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Build an Apollo contact list from extracted SPOT ICP filters."
    )
    parser.add_argument("--filters",   required=True, help="Path to JSON file with ICP filters")
    parser.add_argument("--list-name", required=True, help="Name for the Apollo contact list")
    parser.add_argument("--api-key",   help="Apollo API key (or set APOLLO_API_KEY env var)")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("APOLLO_API_KEY", "")
    if not api_key:
        sys.exit("Apollo API key required. Pass --api-key or set APOLLO_API_KEY env var.")

    filters_path = Path(args.filters)
    if not filters_path.exists():
        sys.exit(f"Filters file not found: {filters_path}")

    filters = json.loads(filters_path.read_text())

    print(f"\n=== Apollo List Builder ===")
    print(f"List name: {args.list_name}")
    print(f"Filters:   {json.dumps(filters, indent=2)}\n")

    # Search
    print("Searching Apollo...")
    people = apollo_search(filters, api_key)

    if not people:
        print(
            "\nNo results found. The ICP filters may be too narrow.\n"
            "Check Employee Range, Locations, and Keywords in Tab 9 of the SPOT "
            "and broaden at least one filter."
        )
        sys.exit(0)

    print(f"\n✓ Apollo search: {len(people)} results")

    # Exclusions
    people = apply_exclusions(people, filters.get("exclusions", []))

    # Create list
    print(f"\nAdding {len(people)} contacts to '{args.list_name}'...")
    total = create_contact_list(people, args.list_name, api_key)

    print(f"""
✓ Apollo search: {len(people)} results
✓ Created list: {args.list_name}
✓ Added {total} contacts

View in Apollo: https://app.apollo.io/#/contacts

Next step: run /apollo-campaign-builder to set up sequences and workflows for this list.
""")


if __name__ == "__main__":
    main()
