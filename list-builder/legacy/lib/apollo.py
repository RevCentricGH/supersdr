"""Apollo API helpers for contact sourcing and email reveal.

Endpoints used:
  - /api/v1/contacts/search         — pull from saved label (TAM mode)
  - /api/v1/mixed_people/api_search — live search with ICP filters (fresh mode)
  - /api/v1/people/match            — credit-based email + phone reveal
  - /api/v1/organizations/enrich    — org-level data by domain

All 429s are retried with backoff.
"""
from __future__ import annotations

import re
import time
from urllib.parse import urlparse

import requests

CONTACTS_URL = "https://api.apollo.io/api/v1/contacts/search"
PEOPLE_URL   = "https://api.apollo.io/api/v1/mixed_people/api_search"
MATCH_URL    = "https://api.apollo.io/api/v1/people/match"
ENRICH_URL   = "https://api.apollo.io/api/v1/organizations/enrich"

_DOMAIN_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$")


def _clean_domain(raw: str) -> str:
    if not raw:
        return ""
    raw = raw.strip().lower()
    if raw.startswith("http"):
        raw = urlparse(raw).netloc or raw
    return raw.replace("www.", "").strip("/").split("/")[0]


def _post(url: str, payload: dict, api_key: str, retries: int = 3) -> dict:
    for attempt in range(retries):
        try:
            r = requests.post(
                url, json=payload,
                headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
                timeout=30,
            )
            if r.status_code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            if r.status_code == 200:
                return r.json()
        except Exception:
            time.sleep(2)
    return {}


def _normalize(p: dict, org: dict | None = None) -> dict:
    """Normalize a raw Apollo person dict to a flat contact row."""
    if org is None:
        org = p.get("organization") or p.get("account") or {}
    domain = _clean_domain(org.get("primary_domain") or org.get("website_url") or "")
    return {
        "first_name":     p.get("first_name") or "",
        "last_name":      p.get("last_name") or "",
        "title":          p.get("title") or "",
        "email":          p.get("email") or "",
        "email_status":   (p.get("email_status") or "").lower(),
        "apollo_id":      p.get("id") or p.get("person_id") or "",
        "linkedin_url":   p.get("linkedin_url") or "",
        "company_name":   org.get("name") or p.get("organization_name") or "",
        "company_domain": domain,
        "employees":      str(org.get("estimated_num_employees") or ""),
        "industry":       org.get("industry") or "",
        "funding_stage":  org.get("latest_funding_stage") or org.get("last_funding_round_type") or "",
        "country":        p.get("country") or org.get("country") or "",
    }


def pull_label_contacts(api_key: str, label_id: str, max_pages: int = 50) -> list[dict]:
    """Pull all contacts from an Apollo saved label via /contacts/search."""
    contacts: list[dict] = []
    for page in range(1, max_pages + 1):
        data = _post(CONTACTS_URL, {
            "contact_label_ids": [label_id],
            "page": page,
            "per_page": 100,
        }, api_key)
        batch = data.get("contacts") or []
        if not batch:
            break
        for p in batch:
            contacts.append(_normalize(p))
        pagination = data.get("pagination") or {}
        total = pagination.get("total_entries") or 0
        if total and len(contacts) >= total:
            break
        if len(batch) < 100:
            break
        time.sleep(0.5)
    return contacts


def people_search_paged(api_key: str, filters: dict, batch_size: int) -> list[dict]:
    """Search Apollo with ICP filters, page through until batch_size reached."""
    contacts: list[dict] = []
    page = 1

    while len(contacts) < batch_size:
        payload: dict = {"page": page, "per_page": min(100, batch_size - len(contacts))}
        payload.update({k: v for k, v in filters.items() if v})

        data = _post(PEOPLE_URL, payload, api_key)
        people = data.get("people") or []
        if not people:
            break

        for p in people:
            contacts.append(_normalize(p))

        total = (data.get("pagination") or {}).get("total_entries", 0)
        if total and len(contacts) >= min(total, batch_size):
            break
        if len(people) < 100:
            break

        page += 1
        time.sleep(0.3)

    return contacts[:batch_size]


def people_match_batch(contacts: list[dict], api_key: str) -> list[dict]:
    """Run /people/match on each contact to reveal locked emails + phones.

    Burns Apollo credits. Uses apollo_id > linkedin_url > name+domain priority.
    Returns list of dicts with _email, _phone, _last_name fields merged in.
    """
    results = []
    for i, c in enumerate(contacts):
        payload: dict = {"reveal_personal_emails": True}

        apollo_id = (c.get("apollo_id") or "").strip()
        linkedin  = (c.get("linkedin_url") or "").strip()
        first     = (c.get("first_name") or "").strip()
        last      = (c.get("last_name") or "").strip()
        domain    = (c.get("company_domain") or "").strip()

        if apollo_id:
            payload["id"] = apollo_id
        elif linkedin:
            payload["linkedin_url"] = linkedin
        elif first and domain:
            payload["first_name"] = first
            if last and "***" not in last:
                payload["last_name"] = last
            payload["email_from_domain"] = domain
            if c.get("company_name"):
                payload["organization_name"] = c["company_name"]
        else:
            results.append({})
            continue

        data = _post(MATCH_URL, payload, api_key)
        person = data.get("person") or {}

        results.append({
            "_email":     (person.get("email") or "").strip(),
            "_phone":     ((person.get("phone_numbers") or [{}])[0].get("sanitized_number") or ""),
            "_last_name": (person.get("last_name") or "").strip(),
        })

        if (i + 1) % 50 == 0:
            print(f"    Reveal progress: {i + 1}/{len(contacts)}")
        time.sleep(0.3)

    return results


def org_enrich(domain: str, api_key: str) -> dict:
    """Enrich organization data by domain. Returns partial dict — no error on failure."""
    try:
        r = requests.get(
            ENRICH_URL,
            headers={"X-Api-Key": api_key},
            params={"domain": domain},
            timeout=30,
        )
        if r.status_code != 200:
            return {}
        org = r.json().get("organization") or {}
        return {
            "employees":      org.get("estimated_num_employees"),
            "annual_revenue": org.get("annual_revenue"),
            "industry":       org.get("industry"),
            "funding_stage":  org.get("latest_funding_stage") or org.get("last_funding_round_type"),
            "total_funding":  org.get("total_funding_printed"),
            "country":        org.get("country"),
        }
    except Exception:
        return {}
