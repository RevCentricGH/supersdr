# SuperSDR Skills

Claude Code skills for the SuperSDR community.

## Skills

| Skill | What it does |
|-------|-------------|
| [rc-client-spot](rc-client-spot/) | Generate a complete 9-tab Single Point of Truth (SPOT) doc for a new client — company overview, ICP, problem/solution, objections, screenplay placeholder, and Apollo campaign setup |
| [revcentric-cold-calling-screenplay](revcentric-cold-calling-screenplay/) | Generate a verbatim cold call screenplay (Short or Full version) for any B2B company — pulls live case studies from the client's website automatically |
| [rc-apollo-campaign-builder](rc-apollo-campaign-builder/) | Build the initial Apollo lead list from SPOT ICP criteria and set up all 7 outreach sequences + 3 workflow plays for a new client |
| [rc-objection-drill](rc-objection-drill/) | Cold call objection handling trainer — Quick Drill or Live Roleplay modes across the 5 core objection families |

## How to use

1. Install [Claude Code](https://claude.ai/code)
2. Clone this repo into your Claude skills directory:
   ```bash
   git clone https://github.com/RevCentricGH/supersdr.git ~/.claude/skills/supersdr
   ```
3. The skills will be available in your Claude Code sessions automatically

## Data flow

```
SPOT (rc-client-spot)
  ├── Tab 3 + Tab 4 → revcentric-cold-calling-screenplay
  └── Tab 9         → rc-apollo-campaign-builder
```

Run `rc-client-spot` first. Everything else builds off it.
