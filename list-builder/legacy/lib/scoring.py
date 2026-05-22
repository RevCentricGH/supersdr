"""ICP scoring — heuristic 0-100 model.

No API calls. Runs on all rows using deterministic rules:
domain TLD, company name signals, industry, employee count, funding stage, title seniority.

ICP qualification (filtering out non-fits) is handled by Claude inline after the script runs.

Tier assignment:
  Tier 1 (>=75): high priority
  Tier 2 (50-74): standard
  Tier 3 (<50): filtered out by default
"""
from __future__ import annotations

import re

DEFAULT_WEIGHTS: dict[str, int] = {
    "tld_ai":                  15,
    "tld_io_dev_xyz_app":       5,
    "name_ai_word":            10,
    "name_labs_intelligence":   5,
    "name_copilot_agent_gpt":   8,
    "industry_ai_ml":          15,
    "industry_software_it":     5,
    "emp_under_50":            10,
    "emp_50_200":               5,
    "emp_500_plus":            -5,
    "emp_2000_plus":          -15,
    "funding_seed_a":           5,
    "funding_d_plus":          -5,
    "title_c_suite":           10,
    "title_vp_head":            7,
    "title_director":           4,
    "title_ml_ai_infra":        3,
    "confirmed_signal_bonus":  20,
}


def score_icp_heuristic(row: dict, weights: dict[str, int] | None = None) -> int:
    """Return 0-100 heuristic ICP score for a contact row."""
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    score = 50  # baseline

    domain   = (row.get("company_domain") or "").lower()
    name     = (row.get("company_name")   or row.get("company") or "").lower()
    industry = (row.get("industry")       or "").lower()
    title    = (row.get("title")          or "").lower()
    funding  = (row.get("funding_stage")  or "").lower()

    try:
        emp = int(row.get("employees") or row.get("num_employees") or 0)
    except (ValueError, TypeError):
        emp = 0

    # Domain TLD
    if domain.endswith(".ai"):
        score += w["tld_ai"]
    elif any(domain.endswith(t) for t in (".io", ".dev", ".xyz", ".app")):
        score += w["tld_io_dev_xyz_app"]

    # Company name signals
    if re.search(r"\bai\b", name):
        score += w["name_ai_word"]
    if re.search(r"\b(labs|intelligence|cognition|llm)\b", name):
        score += w["name_labs_intelligence"]
    if re.search(r"\b(copilot|agent|gpt)\b", name):
        score += w["name_copilot_agent_gpt"]

    # Industry
    if "artificial intelligence" in industry or "machine learning" in industry:
        score += w["industry_ai_ml"]
    elif "software" in industry or "information technology" in industry:
        score += w["industry_software_it"]

    # Employee count
    if emp and emp < 50:
        score += w["emp_under_50"]
    elif emp and emp < 200:
        score += w["emp_50_200"]
    elif emp >= 2000:
        score += w["emp_2000_plus"]
    elif emp >= 500:
        score += w["emp_500_plus"]

    # Funding
    if any(s in funding for s in ("seed", "series_a", "series a")):
        score += w["funding_seed_a"]
    elif any(s in funding for s in ("series_d", "series e", "ipo", "public")):
        score += w["funding_d_plus"]

    # Title seniority
    if any(k in title for k in ("cto", "cpo", "ceo", "chief", "vp ", "vice president")):
        score += w["title_c_suite"]
    elif any(k in title for k in ("head of", "vp of")):
        score += w["title_vp_head"]
    elif "director" in title:
        score += w["title_director"]
    if any(k in title for k in ("ml ", "machine learning", "ai ", "artificial intelligence", "llm", "prompt")):
        score += w["title_ml_ai_infra"]

    # Client-confirmed signal (set upstream by signal enrichment)
    if row.get("_confirmed_signal"):
        score += w["confirmed_signal_bonus"]

    return max(0, min(100, score))
