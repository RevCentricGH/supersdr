# Issue tracker

Issues live in GitHub Issues. Use the `gh` CLI for all operations.

- List: `gh issue list --state open --limit 50 --json number,title,labels,body`
- Create: `gh issue create --title "..." --body "..." --label "..."`
- View: `gh issue view <N> --json number,title,body,labels,comments`
- Comment: `gh issue comment <N> --body "..."`

Slices carry a `## Parent` reference to their tracking issue and a `## Blocked by`
section naming the slices that must merge first. Respect that order.
