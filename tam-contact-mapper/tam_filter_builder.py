"""
TAM Filter Builder
------------------
Data model for Apollo People-search filters used by the tam-contact-mapper skill.

This file is NOT run directly. It is read by the tam-contact-mapper skill,
which uses Claude in Chrome MCP tools to apply each filter in the Apollo People UI
and save the resulting search as a named TAM view.

Usage (via skill):
  The skill reads FILTER_SCHEMA and EXECUTION_GUIDE, then drives the browser
  through filter application using vision + DOM interaction tools.

Direct reference:
  python3 tam_filter_builder.py --schema   # print the filter schema
  python3 tam_filter_builder.py --guide    # print the execution guide
"""

# ------------------------------------------------------------------
# Filter schema — fields the SPOT extractor produces and how each
# maps onto an Apollo People-search filter section.
#
# Section names below match Apollo's UI labels validated via live
# Playwright probe on 2026-05-22.
# ------------------------------------------------------------------

FILTER_SCHEMA = {
    "target_titles":  {"apollo_section": "Job Titles",          "ui_type": "multi_token_autocomplete", "supports_exclude": True,  "exclude_via": "Show advanced inside Job Titles section"},
    "seniority":      {"apollo_section": "Job Titles",          "ui_type": "checkbox_list",            "supports_exclude": False, "notes": "Management Levels is NESTED inside the Job Titles section — not a top-level filter"},
    "employee_range": {"apollo_section": "# Employees",         "ui_type": "preset_ranges_plus_custom","supports_exclude": False, "notes": "Presets + custom range + 'Unknown' option"},
    "locations":      {"apollo_section": "Location",            "ui_type": "multi_token_autocomplete", "supports_exclude": True,  "tab_toggle": "Contact / Account HQ", "exclude_via": "'Exclude locations' link inside Location section"},
    "industries":     {"apollo_section": "Industry & Keywords", "ui_type": "multi_token_autocomplete", "supports_exclude": True,  "notes": "Combined section — Industry sub-field"},
    "keywords":       {"apollo_section": "Industry & Keywords", "ui_type": "free_text",                "supports_exclude": False, "notes": "Combined section — Keywords sub-field"},
    "tech_signals":   {"apollo_section": "Technologies",        "ui_type": "multi_token_autocomplete", "supports_exclude": False, "match_mode": "Set under 'Show advanced' inside Technologies section"},
    "funding_stages": {"apollo_section": "Funding",             "ui_type": "checkbox_list",            "supports_exclude": False, "notes": "Visible by default in sidebar (NOT behind More Filters)"},
    "exclusions":     {"apollo_section": "Company",             "ui_type": "domain_or_company_list",   "supports_exclude": True,  "exclude_via": "Inline 'Exclude' option inside Company section (per-section, not global)"},
}

REQUIRED_FIELDS = ["target_titles", "employee_range", "locations"]
REQUIRED_ANY_OF = ["keywords", "industries"]


# ------------------------------------------------------------------
# Execution guide (read by the skill agent)
# ------------------------------------------------------------------

EXECUTION_GUIDE = """
APOLLO PEOPLE SEARCH — BROWSER EXECUTION STEPS
==================================================

Live-confirmed sidebar sections (in default top-to-bottom order):
  Lists, Persona, Email Status, Job Titles, People Lookalikes, Company,
  Company Lookalikes, Education, Location, Enrichment Type, # Employees,
  Industry & Keywords, Market Segments, SIC and NAICS, AI Filters,
  Buying Intent, Scores, Owner, Technologies, Revenue, Funding,
  Job Postings, Signals, Sequence, Website Visitors, Email Opened,
  Person Deleted

  Plus a "More Filters" button at the bottom that expands additional
  sections: Person Info (Name, Awards, Work URLs, Time Zone, Total Years
  of Experience, Job Change, Time in Current Role, Territories), Company
  Info (# Employees by Dept., Headcount Growth, Founded Year, Languages,
  Retail Locations, News), Engagement Activity (Last Activity, Email
  Sent/Clicked/Replied/Bounced/Unsubscribed/etc., Call Restrictions,
  Conversation), Created Source, Misc (Phone Status/Confidence, Parent
  Accounts, Stage, Custom Fields).

Top of filter panel header controls (live-confirmed):
  - "Hide Filters" — collapses the sidebar
  - "Apply Filters" — applies pending filter changes
  - "Clear all" — resets all filters
  - Result count (e.g. "243,106,472 records found")

Above the results table (live-confirmed):
  - "Save as new search" button — THIS is the save entry point, not
    a button inside the filter sidebar
  - "Research with AI" / "Create workflow" — adjacent buttons; do not confuse
  - The current view name (e.g. "Default view") with a "Search settings" link

HOW TO VERIFY A FILTER TOOK (run after EVERY step B–I):
  1. Click "Apply Filters" at the top of the sidebar — do this after every
     filter, not just at the end. Apollo does not always auto-apply.
  2. Wait for the result count to update.
  3. Confirm the result count changed from the previous step's count.
     If the count did not change at all, the filter did not take.
  4. Confirm the active-filter pill for that section appears above the
     results table.
  If verification fails: retry the filter once. If it fails again,
  screenshot and report before continuing — do not silently skip.

Before starting:
  1. Confirm Chrome is open and logged in at app.apollo.io
  2. Confirm extracted filters from SPOT Tab 9 (fall back to Tab 5)
  3. Confirm the search name with the user
  4. Confirm Apollo plan supports the filters in use — some advanced filters
     (Buying Intent, AI Filters, certain Technologies tiers) gate on plan

STEP A — Navigate to the People search
  - Go to: https://app.apollo.io/#/people
  - Wait for the left Filters sidebar AND the results table to load
  - Verify the header shows "Find people" + a result count + "Apply Filters"
  - Note the starting result count before any filters are applied

STEP B — Job Titles (target_titles)
  - In the left sidebar, expand the "Job Titles" section
  - For each title in target_titles:
      - Type the title into the input
      - Wait for the autocomplete dropdown
      - Click the matching suggestion (do not press Enter — Enter can
        commit raw text instead of the canonical Apollo value, except
        for intentional Boolean operator strings like "VP OR Director")
      - If autocomplete returns no match: the value is not in Apollo's
        controlled vocabulary — try a common variant (e.g. "VP of Sales"
        vs "Vice President of Sales"), then report to user if still no match
  - Verify: input chips show each selected title
  - Apply and verify (see HOW TO VERIFY above)

STEP C — Management Levels (seniority) [if provided]
  - Management Levels is NESTED INSIDE the Job Titles section — it is
    NOT a top-level sidebar filter. Look for the Management Levels
    checkbox list below the title input within the same Job Titles panel.
  - Check each level present in seniority (C-Suite, VP, Director, Head,
    Manager, Owner, Partner, Senior, Entry, Intern)
  - If the panel is collapsed, click into Job Titles first to expand
  - Apply and verify (see HOW TO VERIFY above)

STEP D — # Employees (employee_range)
  - Find the "# Employees" section in left sidebar
  - Three modes are available (live-confirmed):
      (a) Preset checkboxes — ranges including 1-10, 11-20, 21-50,
          51-100, 101-200, 201-500, 501-1000, 1001-5000, 5001-10000, 10001+
      (b) Custom range — enter min and max
      (c) "Unknown" — companies whose headcount Apollo does not have
  - For preset matches, check matching range(s). For custom needs, enter
    custom min/max.
  - Apply and verify (see HOW TO VERIFY above)

STEP E — Location (locations)
  - Find the "Location" section in left sidebar
  - Two tabs (live-confirmed verbatim):
      - "Contact" — person's own location (default tab)
      - "Account HQ" — company's headquarters location
  - For a TAM that targets company-HQ geography (most B2B outbound),
    SWITCH TO "Account HQ" tab before entering values
  - For each location: type → click matching autocomplete suggestion
  - For excluded geos: click "Exclude locations" (in-section link,
    confirmed live)
  - Apply and verify (see HOW TO VERIFY above)

STEP F — Industry & Keywords (industries, keywords)
  - "Industry & Keywords" is ONE COMBINED section
  - Industry sub-field: type → click matching autocomplete suggestion
    (Apollo uses controlled vocabulary; try variants before reporting
    a no-match to the user)
  - Keywords sub-field: free-text input. Multiple terms are OR by default;
    use quotes for phrase matches
  - Apply and verify (see HOW TO VERIFY above)

STEP G — Technologies (if tech_signals provided)
  - Find the "Technologies" section in left sidebar (visible by default)
  - Default placeholder is "Include technologies..."
  - For each technology: type → click matching autocomplete suggestion
  - For match-mode changes (any vs all of, currently uses vs has used):
    click "Show advanced" inside the Technologies section to expose
    the mode selector
  - Apply and verify (see HOW TO VERIFY above)

STEP H — Funding (if funding_stages provided)
  - "Funding" is VISIBLE BY DEFAULT in the sidebar (not behind
    More Filters — earlier guidance was wrong; confirmed live)
  - Check each matching stage (Seed, Series A, Series B, …)
  - Note: Funding filter may still gate on plan tier (locked sections
    will show an upgrade prompt instead of inputs — skip and report)
  - Apply and verify (see HOW TO VERIFY above)

STEP I — Exclusions (if provided)
  - Apollo uses INLINE, PER-SECTION exclusion (NOT a global "Is not any
    of" tab). Each filter section that supports exclusion exposes its
    own exclude path. Live-confirmed examples:
      - Location section → "Exclude locations" link
      - Technologies section → "Show advanced" → exclude mode
      - Company / Company Lookalikes → in-section Exclude option
  - Domain exclusions:
      - Open the "Company" section
      - Use its in-section Exclude option
      - Paste the list of competitor domains (Apollo accepts list paste)
  - Competitor company-name exclusions: same path
  - Apply and verify (see HOW TO VERIFY above)

STEP J — Review final result count
  - All filters should already be applied and verified from steps B–I
  - Click "Apply Filters" one final time to ensure all changes are committed
  - Confirm the result count is stable (not loading)
  - If 0 results: STOP. Suggest broadening filters in this order:
    # Employees → Location → Industry → Keywords
  - If results look reasonable, proceed to save

STEP K — Save the search
  NOTE: This step has not been run end-to-end inside Claude Cowork.
  Follow carefully and use fallbacks if the UI differs from what's described.

  - Scroll to the top of the page — "Save as new search" sits ABOVE the
    results table, near the view-name dropdown and "Search settings" link.
    It is NOT inside the filter sidebar.
  - If "Save as new search" is not visible:
      - Check the URL — if it contains /lists/ you are in a list view,
        not the People search. Navigate back to app.apollo.io/#/people
        and re-apply filters.
      - If the URL is correct but the button is missing, the user's plan
        may not support saved searches — report this and stop.
  - Click "Save as new search"
  - A save dialog should appear. The exact fields may vary by plan tier.
    At minimum you will see a Name input:
      - Enter: "{client_name} - TAM - {YYYY-MM-DD}"
      - If a Visibility selector is present, set it appropriately
      - If other fields appear (permissions, alert toggle), leave defaults
    If the dialog looks different from this description, screenshot it,
    adapt as best you can, and note what you saw in the final report.
  - Confirm / click Save
  - VERIFY the save succeeded using TWO checks:
      1. The view-name dropdown at the top of the results table now shows
         the new search name (not "Default view")
      2. Navigate to the Saved Searches tab in the top-left nav and confirm
         the search name appears there (the tab shows "No saved searches yet"
         when empty — confirmed live; if it still shows that, the save failed)
  - If either check fails: do not report success. Screenshot, report the
    failure, and tell the user they can save manually via the same button.

KNOWN UI DETAILS (live-confirmed 2026-05-22):
  - Filters live in the LEFT SIDEBAR (top-to-bottom flow, not chips)
  - "More Filters" button (NOT "Show More Filters") expands deep filters
  - "Hide Filters" toggle collapses the sidebar
  - "Apply Filters" sits at top of the filter sidebar
  - "Clear all" sits adjacent to Apply Filters
  - "Save as new search" is ABOVE the results table, NOT in the filter sidebar
  - "Pinned Filters" exists as a concept — users can pin filters they
    use often; do not rely on a section being at a stable position if the
    user has customized
  - Location filter uses "Contact" / "Account HQ" tabs verbatim
  - Management Levels is nested INSIDE Job Titles, not a top-level filter
  - Funding is visible by default — not behind More Filters
  - Exclusion is INLINE per section (e.g., "Exclude locations"), NOT a
    global toggle; each section that supports exclusion exposes its own
    path, often under "Show advanced"

FALLBACKS:
  - Filter section not visible → click "More Filters" at the bottom of
    the sidebar to expand the full filter list
  - Autocomplete returns no match → try common variants first; if still
    no match, report the value to the user and ask for a substitute
  - Result count not updating after a filter → click "Apply Filters";
    if still unchanged after two attempts, the filter did not take — report
  - "Save as new search" button missing → user may be in a list view
    (check URL) or on a plan without saved views
  - Save dialog looks different from description → screenshot, adapt,
    note the discrepancy in the final report
  - Advanced filter locked / shows upgrade prompt → skip and note for user
"""


# ------------------------------------------------------------------
# CLI for local reference
# ------------------------------------------------------------------

def print_schema():
    for field, meta in FILTER_SCHEMA.items():
        print(f"{field:<18} -> Apollo section: {meta['apollo_section']}")
        for k, v in meta.items():
            if k != "apollo_section":
                print(f"  {k}: {v}")
    print(f"\nRequired: {REQUIRED_FIELDS}")
    print(f"Required (any of): {REQUIRED_ANY_OF}")


def print_guide():
    print(EXECUTION_GUIDE)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--schema":
        print_schema()
    elif len(sys.argv) > 1 and sys.argv[1] == "--guide":
        print_guide()
    else:
        print("Usage: python3 tam_filter_builder.py [--schema | --guide]")
