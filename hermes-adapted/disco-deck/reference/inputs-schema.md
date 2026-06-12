# disco-deck inputs schema

The JSON the generator (`disco-deck-template/generate.py`) consumes. Write these fields, run the generator, and it back-solves the funnel and fills the slides. Funnel counts, SDR count, and monthly price are **derived by the generator** - do not put them in the inputs.

## Fields

| Field | Type | Source | Notes |
|---|---|---|---|
| `prospect` | string | Transcript, verified against Apollo `account.name` | Appears on the cover and as "Built for <prospect>." |
| `goal_arr` | number (dollars) | Transcript (the goal moment), else Hunter | The funnel anchor. Never invent it. e.g. `1000000`. |
| `acv` | number (dollars) | Transcript (pricing/deal size); Apollo `amount` only as a cross-check; else ask | Average contract value. e.g. `30000`. At the disco stage Apollo usually has no amount. |
| `set_rate` | number 0-1 | RevCentric benchmark default | Conversations -> meetings booked. |
| `show_rate` | number 0-1 | RevCentric benchmark default | Booked -> held. |
| `stage2_rate` | number 0-1 | RevCentric benchmark default | Held -> qualified opp. |
| `close_rate` | number 0-1 | RevCentric benchmark default | Opp -> won (win rate). |
| `convos_per_sdr_yr` | number | RevCentric benchmark default | Conversation capacity per SDR per year. |
| `followup_date` | string | `google-calendar` booked follow-up, else Hunter | Free text, e.g. `"Thursday, June 18"`. Optional: if empty or omitted, slide 10 degrades to a graceful default ("a time that works for you"). |

Override a benchmark rate only when the prospect surfaced their own conversion number in the transcript; anchor any override to the transcript moment in the Step 4 confirm.

## RevCentric benchmark defaults

These reproduce the reference deck and are the defaults unless the transcript says otherwise:

```json
{
  "set_rate": 0.08,
  "show_rate": 0.80,
  "stage2_rate": 0.40,
  "close_rate": 0.25,
  "convos_per_sdr_yr": 1800
}
```

## Example inputs

```json
{
  "prospect": "Acme Robotics",
  "goal_arr": 1000000,
  "acv": 30000,
  "set_rate": 0.08,
  "show_rate": 0.80,
  "stage2_rate": 0.40,
  "close_rate": 0.25,
  "convos_per_sdr_yr": 1800,
  "followup_date": "Thursday, June 18"
}
```

## Back-solve fill-math (what the generator runs)

Work backward from the goal to the funnel and the SDR count:

```
clients = ceil(goal_arr / acv)
opps    = ceil(clients / close_rate)
held    = ceil(opps / stage2_rate)
booked  = ceil(held / show_rate)        # "Meetings booked" bar (annual)
convos  = ceil(booked / set_rate)       # "Conversations / yr" bar (display rounds to nearest 100)
sdrs    = ceil(convos / convos_per_sdr_yr)
monthly = sdrs * $10K                   # fixed RevCentric FTE price
```

The slide-3 funnel shows `convos -> booked -> held -> opps -> clients -> goal_arr`; slide 8 shows `<sdrs> SDRs = <monthly>/mo`. With the example above this solves to 34 clients, 136 opps, 340 held, 425 booked, ~5,300 conversations, and 3 SDRs.

## Preview without rendering

```bash
~/rc-meetings-automation/workflows/phase-2-pre-call/disco-deck-template/render.sh inputs.json --no-render
```

Prints the back-solved token values (SDR count, conversation count, etc.) so the math can be confirmed before the deck is rendered.

## Not in scope (current template)

- `case_study` / slide 6 is static (Crux / WhoisXML / Paperless Parts). Industry-matched selection is a later build.
- Slide 3-alt (KPI/benchmark framing for quality-led calls) is not built; this schema drives the goal-driven funnel only.
