#!/usr/bin/env python3
"""
list_builder.py — Enriched, validated, signal-enriched list builder for SuperSDR

Reads contacts from an Apollo TAM export (TAM mode) or searches Apollo directly
(direct mode), enriches with emails/phones, validates, and adds signal context.

Usage (TAM mode):
    python list_builder.py \
      --mode tam \
      --client "Cekura" \
      --batch-size 100 \
      --raw-csv /tmp/cekura_raw.csv \
      --api-key "YOUR_APOLLO_KEY" \
      --output /tmp/cekura_list_2026-05-21.csv

Usage (direct mode):
    python list_builder.py \
      --mode direct \
      --client "Cekura" \
      --batch-size 100 \
      --filters /tmp/cekura_filters.json \
      --api-key "YOUR_APOLLO_KEY" \
      --output /tmp/cekura_list_2026-05-21.csv

Optional flags:
    --email-validation-key   BounceBan or NeverBounce API key
    --skip-signals           Skip signal enrichment (faster run)
    --enrichment-tool        apollo (default) | bettercontact | fullenrich

Requirements:
    pip install requests
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

APOLLO_SEARCH_URL  = "https://api.apollo.io/api/v1/mixed_people/api_search"
APOLLO_ENRICH_URL  = "https://api.apollo.io/api/v1/people/bulk_match"
BOUNCEBAN_URL      = "https://api.bounceban.com/v1/verify/bulk"


# ── Apollo search (direct mode) ───────────────────────────────────────────────

def apollo_search(filters: dict, batch_size: int, api_key: str) -> list[dict]:
    try:
        import requests
    except ImportError:
        sys.exit("Missing requests. Run: pip install requests")

    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }

    payload: dict = {"per_page": min(100, batch_size), "page": 1}

    if filters.get("target_titles"):
        payload["person_titles"] = filters["target_titles"]
    if filters.get("seniority"):
        payload["person_seniorities"] = filters["seniority"]
    if filters.get("locations"):
        payload["organization_locations"] = filters["locations"]
    if filters.get("employee_range"):
        payload["organization_num_employees_ranges"] = filters["employee_range"]
    if filters.get("funding_stages"):
        payload["organization_latest_funding_stage_cd"] = filters["funding_stages"]
    if filters.get("tech_signals"):
        payload["currently_using_any_of_following_technologies"] = filters["tech_signals"]

    # Industries and keywords go to separate params (not merged)
    if filters.get("industries"):
        payload["organization_industry_tag_ids"] = filters["industries"]
    if filters.get("keywords"):
        payload["q_keywords"] = " ".join(filters["keywords"])

    all_people: list[dict] = []
    page = 1

    while len(all_people) < batch_size:
        payload["page"] = page
        resp = requests.post(APOLLO_SEARCH_URL, headers=headers, json=payload)

        if resp.status_code == 401:
            sys.exit("Apollo API error: invalid API key.")
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
        total = (data.get("pagination") or {}).get("total_entries", 0)

        all_people.extend(people)
        print(f"  Page {page}: {len(people)} results (total available: {total})")

        if not people or len(people) < 100:
            break
        page += 1

    return all_people[:batch_size]


# ── Load contacts from TAM CSV export ─────────────────────────────────────────

def load_from_csv(csv_path: str) -> list[dict]:
    path = Path(csv_path)
    if not path.exists():
        sys.exit(f"TAM CSV not found: {csv_path}")
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ── Apollo enrichment (reveal emails + phones) ────────────────────────────────

def enrich_contacts(people: list[dict], api_key: str) -> list[dict]:
    try:
        import requests
    except ImportError:
        sys.exit("Missing requests. Run: pip install requests")

    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }

    enriched = []

    for i in range(0, len(people), 10):
        batch = people[i : i + 10]
        details = []
        for p in batch:
            entry = {}
            if p.get("linkedin_url") or p.get("LinkedIn URL"):
                entry["linkedin_url"] = p.get("linkedin_url") or p.get("LinkedIn URL")
            if p.get("first_name") or p.get("First Name"):
                entry["first_name"] = p.get("first_name") or p.get("First Name")
            if p.get("last_name") or p.get("Last Name"):
                entry["last_name"] = p.get("last_name") or p.get("Last Name")
            org = p.get("organization") or {}
            if org.get("name") or p.get("Company"):
                entry["organization_name"] = org.get("name") or p.get("Company")
            details.append(entry)

        resp = requests.post(
            APOLLO_ENRICH_URL,
            headers=headers,
            json={"details": details, "reveal_personal_emails": False},
        )

        if resp.status_code == 429:
            print(f"  Rate limited on enrichment batch {i // 10 + 1} — waiting 5s...")
            time.sleep(5)
            resp = requests.post(
                APOLLO_ENRICH_URL,
                headers=headers,
                json={"details": details, "reveal_personal_emails": False},
            )

        if resp.status_code not in (200, 201):
            print(f"  Enrichment batch {i // 10 + 1} failed ({resp.status_code}) — skipping")
            enriched.extend(batch)
            continue

        data = resp.json()
        matches = data.get("matches", [])

        for original, match in zip(batch, matches):
            if match:
                original["_enriched_email"] = match.get("email", "")
                original["_enriched_phone"] = (
                    (match.get("phone_numbers") or [{}])[0].get("sanitized_number", "")
                )
                original["_enriched_phone_type"] = (
                    (match.get("phone_numbers") or [{}])[0].get("type", "")
                )
            enriched.append(original)

        print(f"  Enrichment batch {i // 10 + 1}: {len(matches)} matched")

    return enriched


# ── Email validation (BounceBan) ──────────────────────────────────────────────

def validate_emails(people: list[dict], api_key: str) -> list[dict]:
    try:
        import requests
    except ImportError:
        sys.exit("Missing requests. Run: pip install requests")

    emails = [p.get("_enriched_email", "") for p in people]
    emails_to_check = [e for e in emails if e]

    if not emails_to_check:
        print("  No emails to validate.")
        return people

    resp = requests.post(
        BOUNCEBAN_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"emails": emails_to_check},
    )

    if resp.status_code != 200:
        print(f"  Email validation failed ({resp.status_code}) — marking all as UNVERIFIED")
        for p in people:
            p["_email_status"] = "UNVERIFIED"
        return people

    results = {r["email"]: r["status"] for r in resp.json().get("results", [])}

    for p in people:
        email = p.get("_enriched_email", "")
        if not email:
            p["_email_status"] = "MISSING"
        else:
            raw_status = results.get(email, "UNVERIFIED")
            # Normalise to VALID / INVALID / UNVERIFIED
            p["_email_status"] = (
                "VALID" if raw_status in ("valid", "deliverable")
                else "INVALID" if raw_status in ("invalid", "undeliverable", "bounce")
                else "UNVERIFIED"
            )

    valid = sum(1 for p in people if p.get("_email_status") == "VALID")
    print(f"  Email validation: {valid}/{len(emails_to_check)} valid")
    return people


# ── Signal enrichment (per company, via web search) ───────────────────────────

def enrich_signals(people: list[dict]) -> list[dict]:
    try:
        import subprocess
    except ImportError:
        pass

    companies = {}
    for p in people:
        org = p.get("organization") or {}
        name = org.get("name") or p.get("Company", "")
        domain = org.get("primary_domain") or p.get("Website", "")
        if name and name not in companies:
            companies[name] = domain

    print(f"  Running signal enrichment for {len(companies)} unique companies...")

    signal_notes = {}
    for company, domain in companies.items():
        query = f"{company} hiring OR funding OR news 2026"
        # Claude handles the actual web search when running in Cowork
        # This is a placeholder that Claude will execute inline
        signal_notes[company] = f"[Signal: search '{query}']"

    for p in people:
        org = p.get("organization") or {}
        name = org.get("name") or p.get("Company", "")
        p["_signal_notes"] = signal_notes.get(name, "")

    return people


# ── Output CSV ────────────────────────────────────────────────────────────────

def write_output(people: list[dict], output_path: str) -> dict:
    stats = {"total": 0, "emails_found": 0, "phones_found": 0, "emails_valid": 0, "dropped": 0}

    rows = []
    for p in people:
        org = p.get("organization") or {}
        email = p.get("_enriched_email", "")
        phone = p.get("_enriched_phone", "")
        email_status = p.get("_email_status", "UNVERIFIED")

        # Apply validation matrix
        if email_status == "INVALID" and not phone:
            stats["dropped"] += 1
            continue
        if not email and not phone:
            stats["dropped"] += 1
            continue

        status = (
            "READY"       if email_status == "VALID" and phone
            else "EMAIL_ONLY"   if email_status == "VALID" and not phone
            else "PHONE_ONLY"   if phone and not email
            else "UNVERIFIED"
        )

        last_name = p.get("last_name") or p.get("Last Name") or ""
        # Drop obfuscated last names
        if "***" in last_name:
            last_name = ""

        rows.append({
            "First Name":    p.get("first_name") or p.get("First Name", ""),
            "Last Name":     last_name,
            "Title":         p.get("title") or p.get("Title", ""),
            "Company":       org.get("name") or p.get("Company", ""),
            "Email":         email,
            "Email Status":  email_status,
            "Phone":         phone,
            "Phone Type":    p.get("_enriched_phone_type", ""),
            "LinkedIn URL":  p.get("linkedin_url") or p.get("LinkedIn URL", ""),
            "Signal Notes":  p.get("_signal_notes", ""),
            "List Status":   status,
        })

        stats["total"] += 1
        if email:
            stats["emails_found"] += 1
        if phone:
            stats["phones_found"] += 1
        if email_status == "VALID":
            stats["emails_valid"] += 1

    if not rows:
        print("\nNo contacts passed validation — check enrichment results and try broadening filters.")
        sys.exit(0)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    return stats


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Build an enriched, validated dial-ready list.")
    parser.add_argument("--mode",                  required=True, choices=["tam", "direct"])
    parser.add_argument("--client",                required=True)
    parser.add_argument("--batch-size",            type=int, default=100)
    parser.add_argument("--filters",               help="Path to ICP filters JSON (direct mode)")
    parser.add_argument("--raw-csv",               help="Path to TAM export CSV (tam mode)")
    parser.add_argument("--api-key",               help="Apollo API key")
    parser.add_argument("--email-validation-key",  help="BounceBan API key (optional)")
    parser.add_argument("--skip-signals",          action="store_true")
    parser.add_argument("--output",                required=True)
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("APOLLO_API_KEY", "")
    if not api_key:
        sys.exit("Apollo API key required. Pass --api-key or set APOLLO_API_KEY.")

    today = date.today().isoformat()
    print(f"\n=== List Builder — {args.client} — {today} ===\n")

    # 1. Source contacts
    if args.mode == "tam":
        if not args.raw_csv:
            sys.exit("--raw-csv required for TAM mode.")
        print("Loading contacts from TAM export...")
        people = load_from_csv(args.raw_csv)
        people = people[:args.batch_size]
        print(f"  Loaded {len(people)} contacts from TAM")
    else:
        if not args.filters:
            sys.exit("--filters required for direct mode.")
        filters = json.loads(Path(args.filters).read_text())
        print("Searching Apollo...")
        people = apollo_search(filters, args.batch_size, api_key)
        print(f"  Found {len(people)} contacts")

    if not people:
        print("No contacts to process.")
        sys.exit(0)

    # 2. Enrich
    print(f"\nEnriching {len(people)} contacts via Apollo...")
    people = enrich_contacts(people, api_key)

    # 3. Validate emails
    if args.email_validation_key:
        print("\nValidating emails...")
        people = validate_emails(people, args.email_validation_key)
    else:
        print("\nNo email validation key — marking emails as UNVERIFIED")
        for p in people:
            p["_email_status"] = "UNVERIFIED" if p.get("_enriched_email") else "MISSING"

    # 4. Signal enrichment
    if not args.skip_signals:
        print("\nRunning signal enrichment...")
        people = enrich_signals(people)

    # 5. Write output
    print(f"\nWriting output to {args.output}...")
    stats = write_output(people, args.output)

    email_pct = round(stats["emails_found"] / stats["total"] * 100) if stats["total"] else 0
    phone_pct = round(stats["phones_found"] / stats["total"] * 100) if stats["total"] else 0

    print(f"""
Contacts processed: {stats['total']}
Emails found:       {stats['emails_found']} ({email_pct}%)
Phones found:       {stats['phones_found']} ({phone_pct}%)
Emails valid:       {stats['emails_valid']}
Dropped:            {stats['dropped']}

Output: {args.output}

Next steps:
- Spot-check 5-10 rows in the CSV
- Upload to Smartlead or Apollo sequence
- Run /apollo-campaign-builder if sequences aren't set up yet
""")


if __name__ == "__main__":
    main()
