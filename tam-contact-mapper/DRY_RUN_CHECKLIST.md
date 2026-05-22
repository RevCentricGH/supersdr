# TAM Contact Mapper — Remaining Verification Checklist

Live Playwright probe on **2026-05-22** confirmed the major UI structure (sidebar layout, filter labels, Location tabs, # Employees presets, "Save as new search" button location, exclusion model). The items below are the few things the probe did **not** cover and still need a live click-through inside Cowork.

Stamp date: __________  Tester: __________  Client used: __________

---

## End-to-end click-through (the probe only inspected — did not save)

- [ ] Run the full skill in Cowork: read SPOT → extract filters → apply each filter → click Apply Filters → click "Save as new search" → confirm the saved view appears in the view-name dropdown
- [ ] Confirm the saved view also appears under the Saved Searches tab in the top-left nav

## Save dialog contents (probe didn't open it)

- [ ] Exact label of every field shown when "Save as new search" is clicked: __________
- [ ] Are visibility / permission options on the same dialog or a separate step? __________
- [ ] Is the subscription-alert toggle in the dialog or post-save? __________
- [ ] Default visibility: __________

## Filter mechanics not exercised by the probe

- [ ] Confirm Management Levels appears INSIDE the Job Titles section when expanded (probe found neither at top level — predict it's nested). Exact location and label: __________
- [ ] Confirm "Show advanced" inside Technologies exposes the match-mode selector (any of / all of / has used). Exact label of mode options: __________
- [ ] Confirm "Exclude locations" inside the Location section is a link or a tab. Exact behavior: __________
- [ ] Confirm Company section exposes an inline Exclude path for domain lists. Exact label and behavior: __________
- [ ] Apply Filters behavior: do filters auto-apply on selection, or only after clicking Apply Filters? (Probe found the button but didn't test auto-apply.) __________

## Plan-gated filters (probe didn't enumerate locked sections)

- [ ] Note any filter that showed an upgrade prompt instead of inputs: __________

---

## After the run

1. Open `tam_filter_builder.py` — patch any nested label / mechanic that differed from prediction
2. Bump the date in both `tam_filter_builder.py` and `SKILL.md` banners
3. Move this file to `archive/DRY_RUN_CHECKLIST_YYYY-MM-DD.md` or delete it
