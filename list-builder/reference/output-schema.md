# Output Schema

The Google Sheet column contract. Every downstream channel tool reads this schema - don't change column names.

| Column | Filled by | Notes |
|---|---|---|
| First Name, Last Name, Title, Company, Company Domain | Apollo MCP | Identity |
| Email, Email Status, **Email Ready** (bool) | Apollo + ZeroBounce if connected | Email Ready = ZeroBounce `valid` / `catch-all`, or Apollo `verified` as fallback |
| Phone, Phone Type, **Phone Ready** (bool) | Apollo + Twilio if connected | Phone Ready = MOBILE or LANDLINE; Phone Type from Twilio Lookup |
| LinkedIn URL, **LinkedIn Ready** (bool) | Apollo MCP | LinkedIn Ready = URL present |
| **Fit Score** (0-100) | Claude inline | Heuristic ICP score from Stage 2 |
| Fit Tier (1-3) | Claude inline | Tier 1 = ≥75, Tier 2 = 50-74, Tier 3 = dropped |
| **Intent Score** (0-200+) | Claude inline (Tier 1 only) | Compound signal × recency from Stage 6 |
| **Urgency Tier** | Claude inline | Red Hot / Hot / Warm / Cool / Cold |
| **Top Signals** | Claude inline | 3-5 strongest signals with recency, semicolon-separated |
| **Hook** | Claude inline | 1-line opener using 7-bucket framework |
| **Personalization Depth** | Claude inline | strong (Bucket 1-2) / lite (Bucket 3+) |
| List Source Tier | SPOT doc | A / B / C (defaults to C - Apollo firmographic) |
| List Status | Derived | READY / EMAIL_ONLY / MOBILE_ONLY / etc. |

---

## Urgency Tiers

| Score | Tier | SLA |
|---|---|---|
| 150+ | Red Hot | <1hr - escalate to AE |
| 100-149 | Hot | <24hr - personalized sequence |
| 50-99 | Warm | Standard sequence |
| 20-49 | Cool | Nurture |
| <20 | Cold | Low-touch |

---

## Intent Score Formula

```
INTENT_SCORE = Σ (trigger_points × recency_multiplier)
```

Trigger points:
- Job change in window: 40
- Funding round: 35
- Hiring signal: 20
- Tech stack change: 15
- Content engagement: 10

Recency multipliers:
- Yesterday: 1.5×
- This week: 1.2×
- This month: 1.0×
- 30+ days: 0.3×

---

## Hook Bucket Framework (ranked by value)

1. Self-authored content (posts, articles, podcasts) → Personalization Depth: **strong**
2. Engaged content (likes, shares) → **strong**
3. Self-identified traits (LinkedIn headline) → **lite**
4. Junk drawer (interests, schools) → **lite**
5. Background (tenure, awards) → **lite**
6. Company-level (funding, news) → **lite**
7. Technographics (tools, stack) → **lite**

Try in order, stop at first hit. Red Hot contacts require a strong hook (Bucket 1-2). If not found, try a different contact at the same company before falling back.
