#!/usr/bin/env python3
"""
list_builder.py — Apollo contact list builder for SuperSDR

Reads a client SPOT Google Doc, extracts ICP filters from Tab 5 + Tab 9,
searches Apollo for matching people, and creates a named contact list in
the user's Apollo workspace using append_label_names on bulk contact create.

Usage:
    python list_builder.py --spot-url <URL> [--list-name <NAME>] [--api-key <KEY>]

Requirements:
    pip install google-auth google-auth-oauthlib google-api-python-client requests
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import date
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

GOOGLE_CREDS_PATH = Path("~/.config/gmail/credentials.json").expanduser()
GOOGLE_TOKEN_PATH = Path("~/.config/gdocs/token.json").expanduser()
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]

APOLLO_BASE = "https://api.apollo.io/api/v1"
APOLLO_SEARCH_URL = f"{APOLLO_BASE}/mixed_people/api_search"
APOLLO_CONTACTS_URL = f"{APOLLO_BASE}/contacts/bulk_create"

ENV_FILE = Path(__file__).parent / ".env"

# ── Env helpers ───────────────────────────────────────────────────────────────

def load_env():
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())


def save_api_key(key: str):
    lines = ENV_FILE.read_text().splitlines() if ENV_FILE.exists() else []
    found = False
    for i, line in enumerate(lines):
        if line.startswith("APOLLO_API_KEY="):
            lines[i] = f"APOLLO_API_KEY={key}"
            found = True
            break
    if not found:
        lines.append(f"APOLLO_API_KEY={key}")
    ENV_FILE.write_text("\n".join(lines) + "\n")

# ── Google Docs auth ──────────────────────────────────────────────────────────

def get_docs_service():
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError:
        sys.exit(
            "Missing Google libraries. Run:\n"
            "  pip install google-auth google-auth-oauthlib google-api-python-client"
        )

    creds = None
    if GOOGLE_TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(GOOGLE_TOKEN_PATH), GOOGLE_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not GOOGLE_CREDS_PATH.exists():
                sys.exit(
                    f"Google credentials not found at {GOOGLE_CREDS_PATH}.\n"
                    "Run the gdocs auth flow first (python ~/.config/gdocs/gdocs.py auth)."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(GOOGLE_CREDS_PATH), GOOGLE_SCOPES)
            creds = flow.run_local_server(port=0)
        GOOGLE_TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        GOOGLE_TOKEN_PATH.write_text(creds.to_json())

    return build("docs", "v1", credentials=creds)

# ── SPOT reading ──────────────────────────────────────────────────────────────

def extract_doc_id(url_or_id: str) -> str:
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url_or_id)
    if match:
        return match.group(1)
    if re.match(r"^[a-zA-Z0-9_-]{25,}$", url_or_id):
        return url_or_id
    sys.exit(f"Could not extract doc ID from: {url_or_id}")


def _elements_to_text(elements: list) -> str:
    parts = []
    for elem in elements:
        if "paragraph" in elem:
            for pe in elem["paragraph"].get("elements", []):
                if "textRun" in pe:
                    parts.append(pe["textRun"].get("content", ""))
        elif "table" in elem:
            for row in elem["table"].get("tableRows", []):
                for cell in row.get("tableCells", []):
                    parts.append(_elements_to_text(cell.get("content", [])))
                    parts.append("\t")
                parts.append("\n")
    return "".join(parts)


def fetch_spot_tabs(doc_id: str) -> dict[str, str]:
    """Returns {tab_name: plain_text} for every tab in the doc."""
    service = get_docs_service()
    try:
        doc = service.documents().get(documentId=doc_id, includeTabsContent=True).execute()
    except Exception as e:
        sys.exit(f"Could not read SPOT doc: {e}\nCheck that the doc is shared with your Google account.")

    tabs: dict[str, str] = {}

    def process_tab(tab):
        name = tab.get("tabProperties", {}).get("title", "Untitled")
        body = tab.get("documentTab", {}).get("body", {})
        tabs[name] = _elements_to_text(body.get("content", []))
        for child in tab.get("childTabs", []):
            process_tab(child)

    for tab in doc.get("tabs", []):
        process_tab(tab)

    # Single-tab docs have no tabs array — fall back to root body
    if not tabs:
        body = doc.get("body", {})
        tabs["Main"] = _elements_to_text(body.get("content", []))

    return tabs


def find_tab(tabs: dict[str, str], *keywords: str) -> str:
    """Return text of first tab whose name contains any of the keywords."""
    for kw in keywords:
        for name, text in tabs.items():
            if kw.lower() in name.lower():
                return text
    return ""

# ── ICP extraction ────────────────────────────────────────────────────────────

def _extract_list(text: str, *section_names: str) -> list[str]:
    """Find a section header and collect bullet items below it."""
    for section in section_names:
        pattern = rf"(?i){re.escape(section)}[:\s]*\n(.*?)(?=\n[A-Z][^\n]{{3,}}[:\n]|\Z)"
        match = re.search(pattern, text, re.DOTALL)
        if not match:
            continue
        items = []
        for line in match.group(1).splitlines():
            line = line.strip().lstrip("-•*·▪").strip()
            if line and not line.upper().startswith("[TBD]") and len(line) > 1:
                items.append(line)
        if items:
            return items
    return []


def _extract_field(text: str, *labels: str) -> str:
    """Extract a single inline value following a label."""
    for label in labels:
        match = re.search(rf"(?i){re.escape(label)}[:\s]+([^\n]+)", text)
        if match:
            val = match.group(1).strip()
            if val and not val.upper().startswith("[TBD]"):
                return val
    return ""


def _parse_employee_range(raw: str) -> list[str]:
    match = re.search(r"(\d+)\s*[-–to]+\s*(\d+)", raw)
    if match:
        return [f"{match.group(1)},{match.group(2)}"]
    return []


def extract_icp(tabs: dict[str, str]) -> dict:
    tab9 = find_tab(tabs, "Tab 9", "Apollo Campaign", "Apollo Setup", "Campaign Setup")
    tab5 = find_tab(tabs, "Tab 5", "ICP", "Buyer Persona", "Ideal Customer")

    def get_list(*sections: str) -> list[str]:
        result = _extract_list(tab9, *sections)
        return result or _extract_list(tab5, *sections)

    def get_field(*labels: str) -> str:
        result = _extract_field(tab9, *labels)
        return result or _extract_field(tab5, *labels)

    emp_raw = get_field("Employee Range", "Company Size", "Employees")

    return {
        "client_name":    get_field("Client Name", "Company Name", "Client"),
        "client_domain":  get_field("Client Domain", "Domain", "Website"),
        "target_titles":  get_list("Target Titles", "Primary Titles", "Job Titles", "Titles"),
        "employee_range": _parse_employee_range(emp_raw) if emp_raw else [],
        "locations":      get_list("Locations", "Geography", "Target Locations", "Countries"),
        "industries":     get_list("Industries", "Target Industries", "Industry"),
        "keywords":       get_list("Keyword Passes", "Keywords", "Keyword Pass"),
        "tech_signals":   get_list("Tech Stack Signals", "Tech Signals", "Technology", "Tech Stack"),
        "exclusions":     get_list("Exclusions", "Exclude", "Competitor Domains", "Competitors"),
        "funding_stages": get_list("Funding Stages", "Funding Stage", "Funding"),
    }


def validate_icp(icp: dict) -> list[str]:
    missing = []
    if not icp["target_titles"]:
        missing.append("Target Titles")
    if not icp["employee_range"]:
        missing.append("Employee Range")
    if not icp["locations"]:
        missing.append("Locations")
    if not icp["keywords"] and not icp["industries"]:
        missing.append("Keyword Passes or Industries (at least one required)")
    return missing

# ── Apollo people search ──────────────────────────────────────────────────────

def apollo_search(icp: dict, api_key: str) -> list[dict]:
    try:
        import requests
    except ImportError:
        sys.exit("Missing requests library. Run: pip install requests")

    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }

    payload: dict = {
        "per_page": 100,
        "page": 1,
        "person_titles": icp["target_titles"],
        "person_locations": icp["locations"],
        "organization_num_employees_ranges": icp["employee_range"],
    }

    kw_tags = icp["keywords"] + icp["industries"]
    if kw_tags:
        payload["q_organization_keyword_tags"] = kw_tags

    if icp["funding_stages"]:
        payload["organization_latest_funding_stage_cd"] = icp["funding_stages"]

    if icp["tech_signals"]:
        payload["currently_using_any_of_following_technologies"] = icp["tech_signals"]

    all_people: list[dict] = []
    page = 1

    while True:
        payload["page"] = page
        resp = requests.post(APOLLO_SEARCH_URL, headers=headers, json=payload)

        if resp.status_code == 401:
            sys.exit("Apollo API error: invalid API key. Go to Settings → Integrations → API to get your key.")
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
        pagination = data.get("pagination", {})
        total = pagination.get("total_entries", 0) or data.get("total_entries", 0)

        all_people.extend(people)
        print(f"  Page {page}: {len(people)} results (total available: {total})")

        if not people or len(people) < 100 or len(all_people) >= total:
            break

        page += 1

    return all_people

# ── Apollo list creation ──────────────────────────────────────────────────────

def create_contact_list(people: list[dict], list_name: str, api_key: str) -> int:
    """
    Bulk-create contacts and assign them to a named Apollo list in one call
    using append_label_names. Returns the total number of contacts processed.
    """
    try:
        import requests
    except ImportError:
        sys.exit("Missing requests library. Run: pip install requests")

    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }

    total_processed = 0
    batch_size = 100

    for batch_num, i in enumerate(range(0, len(people), batch_size), start=1):
        batch = people[i : i + batch_size]

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
        # Response separates newly created vs pre-existing contacts
        batch_count = len(data.get("contacts", [])) + len(data.get("existing_contacts", []))
        total_processed += batch_count
        print(f"  Batch {batch_num}: {batch_count} contacts added to '{list_name}'")

    return total_processed

# ── CLI ───────────────────────────────────────────────────────────────────────

def prompt_input(label: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    val = input(f"{label}{hint}: ").strip()
    return val or default


def main():
    load_env()

    parser = argparse.ArgumentParser(description="Build an Apollo contact list from a client SPOT doc.")
    parser.add_argument("--spot-url",  help="Google Doc URL of the SPOT")
    parser.add_argument("--list-name", help="Name for the Apollo contact list")
    parser.add_argument("--api-key",   help="Apollo API key")
    args = parser.parse_args()

    print("\n=== Apollo List Builder ===\n")

    # Step 1 — SPOT URL
    spot_url = args.spot_url or prompt_input("SPOT doc URL")
    if not spot_url:
        sys.exit("SPOT URL is required. Run /client-spot first if you don't have one.")

    # Step 2 — Read SPOT
    print("\nReading SPOT doc...")
    doc_id = extract_doc_id(spot_url)
    tabs = fetch_spot_tabs(doc_id)
    print(f"  Tabs found: {', '.join(tabs.keys())}")

    # Step 3 — Extract ICP
    print("\nExtracting ICP filters...")
    icp = extract_icp(tabs)
    print(f"  Client:         {icp['client_name'] or '(not found)'}")
    print(f"  Titles:         {icp['target_titles']}")
    print(f"  Employee range: {icp['employee_range']}")
    print(f"  Locations:      {icp['locations']}")
    print(f"  Keywords:       {icp['keywords']}")
    print(f"  Industries:     {icp['industries']}")
    print(f"  Tech signals:   {icp['tech_signals']}")
    print(f"  Exclusions:     {icp['exclusions']}")
    print(f"  Funding stages: {icp['funding_stages']}")

    # Step 4 — Validate
    missing = validate_icp(icp)
    if missing:
        print(f"\nMissing critical fields: {', '.join(missing)}")
        print("Fill these in the SPOT doc (Tab 9 → Tab 5 fallback) and re-run.")
        sys.exit(1)

    # Step 5 — List name
    default_name = (
        f"{icp['client_name']} - Contacts - {date.today().isoformat()}"
        if icp["client_name"]
        else f"Contacts - {date.today().isoformat()}"
    )
    list_name = args.list_name or prompt_input("List name", default_name)

    print(f"\nFilters confirmed. List will be named: '{list_name}'")
    if not args.list_name and not args.spot_url:
        confirm = input("Run the Apollo search? (y/n): ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            sys.exit(0)

    # Step 6 — API key
    api_key = args.api_key or os.environ.get("APOLLO_API_KEY", "")
    if not api_key:
        api_key = prompt_input("Apollo API key")
        if not api_key:
            sys.exit("Apollo API key is required. Find it at: Apollo → Settings → Integrations → API")
        save = input("Save API key to .env for future runs? (y/n): ").strip().lower()
        if save == "y":
            save_api_key(api_key)
            print("  Saved to .env")

    # Step 7 — Search Apollo
    print("\nSearching Apollo...")
    people = apollo_search(icp, api_key)

    if not people:
        print("\nNo results found. The ICP filters may be too narrow.")
        print("Check Employee Range, Locations, and Keywords in Tab 9 of the SPOT and broaden at least one filter.")
        sys.exit(0)

    print(f"\n✓ Apollo people search: {len(people)} results")

    # Post-filter exclusions (no Apollo API param — drop matching domains client-side)
    if icp["exclusions"]:
        before = len(people)
        exclude_lower = [e.lower() for e in icp["exclusions"]]
        people = [
            p for p in people
            if not any(
                excl in ((p.get("organization") or {}).get("primary_domain", "") or "").lower()
                for excl in exclude_lower
            )
        ]
        dropped = before - len(people)
        if dropped:
            print(f"  Filtered out {dropped} contacts matching exclusion domains ({len(people)} remaining)")

    # Step 8 — Create contact list
    print(f"\nAdding {len(people)} contacts to '{list_name}'...")
    total = create_contact_list(people, list_name, api_key)

    print(f"""
✓ Read SPOT for {icp['client_name']}
✓ Extracted ICP filters
✓ Apollo people search: {len(people)} results
✓ Created list: {list_name}
✓ Added {total} contacts

View in Apollo: https://app.apollo.io/#/contacts

Next step: run /apollo-campaign-builder to set up sequences and workflows for this list.
""")


if __name__ == "__main__":
    main()
