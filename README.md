# SuperSDR Skills

Claude Cowork skills for the SuperSDR community.

## Skills

| Skill | What it does |
|-------|-------------|
| [rc-client-spot](rc-client-spot/) | Generate a complete multi-tab Single Point of Truth (SPOT) Google Doc for a new client — campaign status, company overview, problem/solution, ICP, competitive landscape, objections, screenplay, and Apollo campaign setup |
| [revcentric-cold-calling-screenplay](revcentric-cold-calling-screenplay/) | Generate a verbatim cold call screenplay (Short or Full version) for any B2B company — pulls live case studies from the client's website automatically |
| [rc-apollo-campaign-builder](rc-apollo-campaign-builder/) | Build the initial Apollo lead list from SPOT ICP criteria and set up all 7 outreach sequences + 3 workflow plays for a new client using browser automation |
| [rc-objection-drill](rc-objection-drill/) | Cold call objection handling trainer — Quick Drill or Live Roleplay modes across the 5 core objection families |
| [revcentric-proposal-builder](revcentric-proposal-builder/) | Build a send-ready RevCentric.ai client proposal (DFY Calling, cold email, or combined outbound) as a Word doc from a discovery-call transcript — includes pricing tiers, completed-conversations model, T&Cs, and signature block |

## How to use

1. Open the skill folder you want (e.g. `rc-client-spot`)
2. Click `SKILL.md` → click **Raw** → save the file to your computer
3. In Claude Cowork, upload the file or paste the contents at the start of your session
4. Follow the instructions in the skill

## Data flow

```
SPOT (rc-client-spot)
  ├── Tab 3 + Tab 4 → revcentric-cold-calling-screenplay
  ├── Tab 9         → rc-apollo-campaign-builder
  └── discovery call transcript → revcentric-proposal-builder
```

Run `rc-client-spot` first. Everything else builds off it.
