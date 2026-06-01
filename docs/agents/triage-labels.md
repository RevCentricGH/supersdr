# Triage labels

| Role | Label | Meaning |
|------|-------|---------|
| Needs evaluation | `needs-triage` | Maintainer needs to assess; not yet ready for an agent |
| Waiting on reporter | `needs-info` | Blocked on more detail before it can be picked up |
| AFK-ready | `afk` | Fully specified; a coding agent can build it autonomously |
| Human-in-loop | `hitl` | Needs a human at a live connector mid-build (Apollo browser, Gmail send, end-to-end run) |
| Parent | `tracking` | Epic that lists its child slices; the `/ralph #N` target |
| Won't fix | `wontfix` | Will not be actioned |

`afk` vs `hitl` is about the build, not the skill's runtime. A skill can ask its end
user to confirm at runtime and still be `afk` to build. A slice is `hitl` only when
finishing it requires a human at a live external system (a real Apollo opportunity, a
real Gmail send, a cross-connector end-to-end run).

Swap, don't stack: when a slice becomes `afk` or `hitl`, drop `needs-triage`.
