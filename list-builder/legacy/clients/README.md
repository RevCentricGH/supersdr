# Client configs (legacy / cache only)

The primary input for list-builder is the client's SPOT doc — not local files. Claude reads Tab 9 of the SPOT doc and writes a temp filters JSON each run.

This directory is only used for:
- Legacy YAML configs from earlier versions of the skill
- Optional local caching for stable / heavily-used clients
- The `_template.yaml` reference for what fields the script accepts

You should NOT need to write or edit files here for normal use.

See `SKILL.md` for the SPOT doc → filters JSON flow.
