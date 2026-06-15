# Heuristic ICP Scoring (Stage 2)

Score each contact 0-100. Baseline 50, then add/subtract. Clamp to 0-100 and assign tiers.

**Domain signals**
- `.ai` TLD → +15
- `.io` / `.dev` / `.xyz` / `.app` → +5

**Company name**
- Contains "AI" as word → +10
- Contains "labs" / "intelligence" / "cognition" / "llm" → +5
- Contains "copilot" / "agent" / "gpt" → +8

**Industry**
- AI / ML → +15
- Software / IT → +5

**Employee count**
- <50 → +10
- 50-199 → +5
- 500-1999 → -5
- 2000+ → -15

**Funding stage**
- Seed / Series A → +5
- Series D+ / IPO / Public → -5

**Title seniority**
- C-suite (CTO, CEO, Chief X) → +10
- VP / Head of → +7
- Director → +4
- ML / AI / LLM / Prompt in title → +3

**Tiers**
- ≥75 → Tier 1
- 50-74 → Tier 2
- <50 → Tier 3 (drop)
