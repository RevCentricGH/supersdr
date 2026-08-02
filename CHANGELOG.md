# Changelog

Notable changes to the SuperSDR skills. Skills ship as per-skill release ZIPs auto-built from `main`, so entries are grouped by date rather than version. Format follows [Keep a Changelog](https://keepachangelog.com).

## 2026-08-01

### Fixed
- **apollo-campaign-builder**: the 4 workflow plays were built against the wrong Apollo trigger. The guide told the agent to use "Contact updated" and pick the disposition out of a **contact stage** picker. "Meeting Scheduled" and "Connect Incomplete" are dispositions, not stages, so the picker came up empty and workflows 1 and 3 could never leave Draft. Verified against a live Apollo workspace: the correct event is **"Call logged"**, filtered by source sequence plus disposition. All four workflows now use it.
- **apollo-campaign-builder**: removed the `Update Contact Stage` action from all 4 workflows. Contact stages are owned by the disposition-to-stage triggers in `apollo-account-setup`. Workflows 2 and 4 had been setting the same stage value they triggered on, which re-fires the workflow against its own output.
- **apollo-campaign-builder**: workflow triggers now scope to the client's Call Only sequence. Without that filter a workflow fires on every logged call in the workspace, including other clients'.
- **apollo-campaign-builder**: `SKILL.md` and `workflow_builder.py` gave the agent two different trigger instructions. They now agree.

### Added
- **apollo-account-setup**: the disposition step now checks for existing workflows first and refuses to run destructively on a live account. Apollo workflows store a reference to a disposition rather than its name, so deleting and re-creating dispositions orphans every workflow that filtered on one; the workflow stays Active, matches nobody, and its trigger reads "the disposition undefined".
- **apollo-campaign-builder**: troubleshooting rows for the dangling-disposition failure, the missing "Disposition changed" dropdown option, and `Contact owner does not have email account` enrollment failures.
- **CI**: the campaign-builder guard now fails the build if a workflow trigger filters on anything that is not a real disposition (naming it explicitly when the value is a contact stage), if a trigger is missing its source sequence, if a workflow writes a contact stage, or if the disposition-to-stage trigger map references an unknown disposition or stage or leaves one unmapped.

## 2026-06-17

### Changed
- **pre-brief**: the meeting brief is now a styled Word document (`.docx`, opens in Google Docs), rendered by a bundled deterministic builder (`assets/build_brief_docx.py`) instead of a plain Google Doc. The builder fixes the styling (navy headings, `[Kind, anchor]` labels, bold-labeled Transcript anchors) and rejects point/anchor numbering mismatches. The Google Doc link is now optional, so Google Drive is no longer required to produce the brief. ([#152])

### Documentation
- README: corrected the `client-proposal-doc-builder` entry to describe its styled `.docx` output (Google Doc link optional) and changed its Google Drive connector from required to optional. ([#151])
- README: the Google Drive connector note now names pre-brief alongside the proposal builder as Drive-optional. ([#153])

[#151]: https://github.com/RevCentricGH/supersdr/pull/151
[#152]: https://github.com/RevCentricGH/supersdr/pull/152
[#153]: https://github.com/RevCentricGH/supersdr/pull/153
