# Optional Capabilities (integrations)

Each optional capability adds a pipeline stage when your harness has it, and is skipped or downgraded when it doesn't. Bind each to whatever your harness provides - a connector, an MCP server, or an API client. Tool names below (Apollo, ZeroBounce, Twilio, and so on) are examples that cover the capability, not requirements.

| Capability | What it adds |
|---|---|
| Read a Google Doc + write a Google Sheet | Reading the client SPOT doc and writing the output sheet (e.g. a Google Drive/Sheets tool) |
| Email validation | A real deliverability check instead of trusting Apollo's verified status (e.g. ZeroBounce) |
| Phone line-type lookup | Mobile / landline / VoIP detection on each phone (e.g. Twilio Lookup) |
| Deeper signal research | Richer Layer 4 per-company research (e.g. Perplexity) |
| Extra enrichment | Additional enrichment passes when Apollo's hit rate is low (e.g. Clay) |
| Intent signals | Website visitors / community engagement for Layer 4 (e.g. Common Room) |
| Push to a cold-email campaign | Upload the final list straight into a campaign, started paused (e.g. Smartlead, Instantly) |
| Push to a LinkedIn outreach sequence | Push LinkedIn-ready contacts into a sequence (e.g. HeyReach) |
| Sync to a CRM | Create the contacts as leads, tagged to the client list (e.g. HubSpot) |

The required capability (Apollo sourcing + enrichment) is not in this table - without it the skill stops. See the Prerequisites section in `SKILL.md`.
