#!/usr/bin/env python3
"""
list_builder.py — SuperSDR list-building engine.

Pipeline: Apollo pull → heuristic scoring → Tier filter
          → contact reveal (email + phone) → email validation → phone validation → CSV.

ICP qualification and signal enrichment are handled by Claude inline (web search / Perplexity MCP)
after the script runs — no Perplexity API key required.

Usage:
    python list_builder.py --client acme
    python list_builder.py --client acme --batch-size 200
    python list_builder.py --client acme --fresh
    python list_builder.py --client acme --skip-validation

Requirements: pip install -r requirements.txt
All API keys come from .env in this directory.
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("Missing pyyaml. Run: pip install pyyaml")

try:
    from dotenv import load_dotenv
except ImportError:
    sys.exit("Missing python-dotenv. Run: pip install python-dotenv")

_HERE = Path(__file__).parent
load_dotenv(_HERE / ".env")

sys.path.insert(0, str(_HERE))

from lib.apollo import pull_label_contacts, people_search_paged, people_match_batch
from lib.verify import EmailVerifier
from lib.phones import PhoneValidator
from lib.scoring import score_icp_heuristic


# ── Config ────────────────────────────────────────────────────────────────────

def load_config_from_yaml(client: str) -> dict:
    """Legacy path — loads from clients/{slug}.yaml. Used for cached/local configs."""
    path = _HERE / "clients" / f"{client}.yaml"
    if not path.exists():
        available = sorted(
            p.stem for p in (_HERE / "clients").glob("*.yaml")
            if not p.stem.startswith("_")
        )
        sys.exit(
            f"Client '{client}' not found.\n"
            f"Available: {', '.join(available) or 'none — pass --filters {path/to/filters.json} instead'}"
        )
    with open(path) as f:
        cfg = yaml.safe_load(f)
    cfg["_slug"] = client
    return cfg


def load_config_from_json(filters_path: str) -> dict:
    """Primary path — loads ICP filters from a JSON file.

    Claude extracts these from the client's SPOT doc (Tab 9 / Tab 5) and writes
    them to a temp file before invoking the script. The user never touches this file.

    Required fields:
      client_name, client_slug, icp_description, target_titles

    Optional fields:
      apollo_label_id, apollo_key_env, seniority, employee_range, locations,
      tech_signals, exclusions, github_queries, scoring, list_source_tier
    """
    path = Path(filters_path)
    if not path.exists():
        sys.exit(f"Filters file not found: {filters_path}")

    with open(path) as f:
        cfg = json.load(f)

    if not cfg.get("client_slug"):
        sys.exit("filters JSON missing required field: client_slug")
    if not cfg.get("client_name"):
        cfg["client_name"] = cfg["client_slug"].replace("_", " ").title()
    if not cfg.get("target_titles"):
        sys.exit("filters JSON missing required field: target_titles")

    cfg["_slug"] = cfg["client_slug"]
    return cfg


def get_apollo_key(config: dict) -> str:
    key_env = config.get("apollo_key_env", "APOLLO_API_KEY")
    key = os.getenv(key_env, "") or os.getenv("APOLLO_API_KEY", "")
    if not key:
        sys.exit(
            f"Apollo API key not set.\n"
            f"Add {key_env} (or APOLLO_API_KEY) to {_HERE / '.env'}"
        )
    return key


# ── Dedup ─────────────────────────────────────────────────────────────────────

def _dedup_path(client: str) -> Path:
    return _HERE / ".cache" / client / "seen_emails.txt"


def load_seen_emails(client: str) -> set[str]:
    p = _dedup_path(client)
    return set(p.read_text().splitlines()) if p.exists() else set()


def save_seen_emails(client: str, emails: list[str]):
    p = _dedup_path(client)
    p.parent.mkdir(parents=True, exist_ok=True)
    existing = load_seen_emails(client)
    p.write_text("\n".join(sorted(existing | set(e.lower() for e in emails if e))))


# ── Stage 1: Source ───────────────────────────────────────────────────────────

def stage_source(config: dict, batch_size: int, apollo_key: str, fresh: bool) -> list[dict]:
    label_id = config.get("apollo_label_id")

    if label_id and not fresh:
        print(f"\n[1/5] Pulling from Apollo label {label_id[:8]}...")
        contacts = pull_label_contacts(apollo_key, label_id)
        contacts = contacts[:batch_size]
        print(f"      {len(contacts)} contacts pulled")
    else:
        print("\n[1/5] Searching Apollo with ICP filters...")
        filters = {k: v for k, v in {
            "person_titles":                                      config.get("target_titles", []),
            "person_seniorities":                                 config.get("seniority", []),
            "organization_num_employees_ranges":                  config.get("employee_range", []),
            "person_locations":                                   config.get("locations", []),
            "currently_using_any_of_following_technologies":      config.get("tech_signals", []),
        }.items() if v}
        contacts = people_search_paged(apollo_key, filters, batch_size)
        print(f"      {len(contacts)} contacts found")

    return contacts


# ── Stage 2: Dedup ────────────────────────────────────────────────────────────

def stage_dedup(contacts: list[dict], client: str) -> list[dict]:
    seen = load_seen_emails(client)
    if not seen:
        return contacts
    before = len(contacts)
    contacts = [c for c in contacts if (c.get("email") or "").lower() not in seen]
    removed = before - len(contacts)
    if removed:
        print(f"\n[2/5] Dedup: removed {removed} already-seen contacts ({len(contacts)} remain)")
    return contacts


# ── Stage 3: Score + filter ───────────────────────────────────────────────────

def stage_score(contacts: list[dict], config: dict) -> list[dict]:
    scoring_cfg = config.get("scoring", {})
    weights  = scoring_cfg.get("weights")
    max_tier = scoring_cfg.get("max_tier", 2)

    print(f"\n[3/5] Scoring {len(contacts)} contacts...")

    for c in contacts:
        c["_icp_score"] = score_icp_heuristic(c, weights)

    contacts.sort(key=lambda c: c["_icp_score"], reverse=True)

    for c in contacts:
        s = c["_icp_score"]
        c["_tier"] = 1 if s >= 75 else 2 if s >= 50 else 3

    t1 = sum(1 for c in contacts if c["_tier"] == 1)
    t2 = sum(1 for c in contacts if c["_tier"] == 2)
    t3 = sum(1 for c in contacts if c["_tier"] == 3)
    filtered = [c for c in contacts if c["_tier"] <= max_tier]

    print(f"      T1={t1}  T2={t2}  T3={t3}  →  keeping Tier 1–{max_tier} ({len(filtered)} contacts)")
    return filtered


# ── Stage 4: Contact reveal (email + phone) ───────────────────────────────────

def stage_contact_reveal(contacts: list[dict], apollo_key: str) -> list[dict]:
    locked = [
        (i, c) for i, c in enumerate(contacts)
        if not c.get("email") or c.get("email_status", "").lower() in ("locked", "")
    ]
    if not locked:
        print("\n[4/6] Contact reveal: all contacts already have emails")
        return contacts

    print(f"\n[4/6] Revealing {len(locked)} locked contacts via Apollo (email + phone)...")
    revealed_data = people_match_batch([c for _, c in locked], apollo_key)

    emails_revealed = 0
    phones_revealed = 0
    for list_pos, (orig_idx, _) in enumerate(locked):
        if list_pos >= len(revealed_data):
            break
        r = revealed_data[list_pos]
        if r.get("_email"):
            contacts[orig_idx]["email"]        = r["_email"]
            contacts[orig_idx]["email_status"] = "verified"
            emails_revealed += 1
        if r.get("_phone"):
            contacts[orig_idx]["phone"] = r["_phone"]
            phones_revealed += 1
        if r.get("_last_name"):
            contacts[orig_idx]["last_name"] = r["_last_name"]

    print(f"      Emails revealed: {emails_revealed}/{len(locked)}  |  Phones revealed: {phones_revealed}/{len(locked)}")
    return contacts


# ── Stage 5: Email + phone validation ────────────────────────────────────────

def stage_validate(contacts: list[dict], skip_validation: bool) -> list[dict]:
    if skip_validation:
        print("\n[5/6] Validation skipped (--skip-validation)")
        for c in contacts:
            if c.get("email"):
                c["_email_status"] = "UNVERIFIED"
            if c.get("phone"):
                c["_phone_status"] = "UNVERIFIED"
                c["_phone_type"]   = ""
        return contacts

    # Email validation waterfall
    try:
        verifier  = EmailVerifier()
        has_email = [(i, c) for i, c in enumerate(contacts) if c.get("email")]
        print(f"\n[5/6] Validating {len(has_email)} emails ({verifier.provider_names})...")
        for i, c in has_email:
            result = verifier.verify_email(c["email"])
            c["_email_status"] = result["status"].upper()
            time.sleep(0.05)
        valid = sum(1 for c in contacts if c.get("_email_status") == "VALID")
        print(f"      Email: {valid}/{len(has_email)} valid")
    except ValueError as e:
        print(f"\n[5/6] Email validation skipped — {e}")
        for c in contacts:
            if c.get("email"):
                c["_email_status"] = "UNVERIFIED"

    # Phone validation (line type check)
    phone_validator = PhoneValidator()
    if phone_validator.available:
        print(f"      Phone line-type check via Twilio...")
        contacts = phone_validator.validate_batch(contacts)
    else:
        print(f"      Phone validation skipped (no TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN)")
        for c in contacts:
            c["_phone_status"] = "Not validated — dial and see" if c.get("phone") else "MISSING"
            c["_phone_type"]   = ""

    return contacts


# ── Stage 6: Output ───────────────────────────────────────────────────────────

def stage_output(contacts: list[dict], output_path: str) -> dict:
    stats = {"total": 0, "emails": 0, "valid_emails": 0,
             "phones": 0, "mobile": 0, "dropped": 0}
    rows  = []

    for c in contacts:
        email        = c.get("email", "")
        phone        = c.get("phone", "")
        email_status = c.get("_email_status", "UNVERIFIED" if email else "")
        phone_status = c.get("_phone_status", "UNVERIFIED" if phone else "MISSING")

        # Drop contacts with no reachable channel
        if not email and not phone:
            stats["dropped"] += 1
            continue
        if email_status == "INVALID" and phone_status in ("MISSING", "INVALID"):
            stats["dropped"] += 1
            continue

        # List Status — priority: best channel combination for SDR outreach
        has_good_email = email_status in ("VALID", "CATCH_ALL", "UNVERIFIED") and email
        has_good_phone = phone_status in ("MOBILE", "LANDLINE", "UNVERIFIED") and phone
        is_mobile      = phone_status == "MOBILE"

        if email_status == "VALID" and is_mobile:
            list_status = "READY"           # full channel coverage
        elif email_status == "VALID" and has_good_phone:
            list_status = "READY"
        elif email_status == "VALID":
            list_status = "EMAIL_ONLY"
        elif is_mobile and not email:
            list_status = "MOBILE_ONLY"
        elif has_good_phone and not email:
            list_status = "PHONE_ONLY"
        else:
            list_status = "UNVERIFIED"

        last_name = c.get("last_name", "")
        if "***" in last_name:
            last_name = ""

        # Channel-readiness booleans (per §1 output schema contract)
        email_ready    = email_status in ("VALID", "CATCH_ALL")
        phone_ready    = phone_status in ("MOBILE", "LANDLINE") or (
            phone and phone_status not in ("INVALID", "VOIP", "MISSING")
        )
        linkedin_ready = bool(c.get("linkedin_url"))

        rows.append({
            # Identity
            "First Name":             c.get("first_name", ""),
            "Last Name":              last_name,
            "Title":                  c.get("title", ""),
            "Company":                c.get("company_name", "") or c.get("company", ""),
            "Company Domain":         c.get("company_domain", ""),

            # Contact info
            "Email":                  email,
            "Email Status":           email_status,
            "Email Ready":            email_ready,
            "Phone":                  phone,
            "Phone Type":             c.get("_phone_type", ""),
            "Phone Status":           phone_status,
            "Phone Ready":            phone_ready,
            "LinkedIn URL":           c.get("linkedin_url", ""),
            "LinkedIn Ready":         linkedin_ready,

            # Scoring (Fit = channel-agnostic ICP fit, 0-100)
            "Fit Score":              c.get("_icp_score", ""),
            "Fit Tier":               c.get("_tier", ""),

            # Layer 4 — filled by Claude inline after the script runs
            "Intent Score":           "",       # 0-200+
            "Urgency Tier":           "",       # Red Hot / Hot / Warm / Cool / Cold
            "Top Signals":            "",       # 3-5 strongest signals with recency
            "Hook":                   "",       # 1-line personalization seed
            "Personalization Depth":  "lite",   # strong (Bucket 1-2) | lite — defaults to lite

            # Provenance + routing
            "List Source Tier":       c.get("_list_source_tier", "C"),  # A/B/C
            "List Status":            list_status,
        })

        stats["total"] += 1
        if email:                      stats["emails"] += 1
        if phone:                      stats["phones"] += 1
        if email_status == "VALID":    stats["valid_emails"] += 1
        if phone_status == "MOBILE":   stats["mobile"] += 1

    if not rows:
        print("\nNo contacts passed validation. Check enrichment results.")
        return stats

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    return stats


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SuperSDR List Builder")
    parser.add_argument("--filters",         help="Path to ICP filters JSON (extracted by Claude from the client's SPOT doc)")
    parser.add_argument("--client",          help="Client slug (legacy — loads clients/{slug}.yaml)")
    parser.add_argument("--batch-size",      type=int, default=100)
    parser.add_argument("--fresh",           action="store_true", help="Force live Apollo search (ignore apollo_label_id)")
    parser.add_argument("--skip-validation", action="store_true", help="Skip email validation waterfall")
    parser.add_argument("--output",          help="Output CSV path (default: ~/Desktop/{client}-list-{date}.csv)")
    args = parser.parse_args()

    if not args.filters and not args.client:
        parser.error("Must pass either --filters {json_path} (from SPOT doc) or --client {slug} (legacy YAML)")

    config = load_config_from_json(args.filters) if args.filters else load_config_from_yaml(args.client)
    slug   = config["_slug"]

    today       = date.today().isoformat()
    output_path = args.output or str(Path.home() / "Desktop" / f"{slug}-list-{today}.csv")

    print(f"\n=== List Builder: {config.get('client_name', slug)} — {today} ===")

    apollo_key = get_apollo_key(config)

    contacts = stage_source(config, args.batch_size, apollo_key, fresh=args.fresh)
    if not contacts:
        print("No contacts found. Check Apollo label ID or broaden ICP filters in the client config.")
        sys.exit(0)

    # Tag list source tier — defaults to C (3rd party / Apollo firmographic).
    # Override per-client via `list_source_tier: A|B|C` in clients/{slug}.yaml.
    list_tier = config.get("list_source_tier", "C")
    for c in contacts:
        c["_list_source_tier"] = list_tier

    contacts = stage_dedup(contacts, slug)
    contacts = stage_score(contacts, config)
    if not contacts:
        print("No contacts passed the scoring filter.")
        sys.exit(0)

    contacts = stage_contact_reveal(contacts, apollo_key)
    contacts = stage_validate(contacts, args.skip_validation)
    stats    = stage_output(contacts, output_path)

    save_seen_emails(slug, [c.get("email", "") for c in contacts if c.get("email")])

    total        = stats["total"]
    emails_found = stats["emails"]
    valid_emails = stats["valid_emails"]
    phones_found = stats["phones"]
    mobile       = stats["mobile"]
    email_pct    = round(emails_found / total * 100) if total else 0
    valid_pct    = round(valid_emails / emails_found * 100) if emails_found else 0
    phone_pct    = round(phones_found / total * 100) if total else 0
    mobile_pct   = round(mobile / phones_found * 100) if phones_found else 0

    print(f"""
Contacts ready:   {total}
Emails found:     {emails_found} ({email_pct}%)
Emails valid:     {valid_emails} ({valid_pct}% of found)
Phones found:     {phones_found} ({phone_pct}%)
Mobile numbers:   {mobile} ({mobile_pct}% of phones)
Dropped:          {stats['dropped']}

Output: {output_path}
""")


if __name__ == "__main__":
    main()
