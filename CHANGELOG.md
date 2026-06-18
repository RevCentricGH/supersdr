# Changelog

Notable changes to the SuperSDR skills. Skills ship as per-skill release ZIPs auto-built from `main`, so entries are grouped by date rather than version. Format follows [Keep a Changelog](https://keepachangelog.com).

## 2026-06-17

### Changed
- **pre-brief**: the meeting brief is now a styled Word document (`.docx`, opens in Google Docs), rendered by a bundled deterministic builder (`assets/build_brief_docx.py`) instead of a plain Google Doc. The builder fixes the styling (navy headings, `[Kind, anchor]` labels, bold-labeled Transcript anchors) and rejects point/anchor numbering mismatches. The Google Doc link is now optional, so Google Drive is no longer required to produce the brief. ([#152])

### Documentation
- README: corrected the `client-proposal-doc-builder` entry to describe its styled `.docx` output (Google Doc link optional) and changed its Google Drive connector from required to optional. ([#151])
- README: the Google Drive connector note now names pre-brief alongside the proposal builder as Drive-optional. ([#153])

[#151]: https://github.com/RevCentricGH/supersdr/pull/151
[#152]: https://github.com/RevCentricGH/supersdr/pull/152
[#153]: https://github.com/RevCentricGH/supersdr/pull/153
