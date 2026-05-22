# Channels — async notifications for SuperSDR skills

Channels let external services (Telegram, Discord, iMessage, webhooks) push events into a running Claude Cowork session. Two-way: you send a message from your phone, Claude reacts to it live, the reply pushes back through the same channel.

This unlocks async, event-driven workflows that the SuperSDR skills alone don't cover.

---

## When you'd want this

You probably don't need channels to use any of the SuperSDR skills. The skills work fine in normal back-and-forth Claude sessions. Channels are for when you want:

- **Async status checks from your phone** — "check campaign stats for [client]" from Telegram → Claude pulls SmartLead numbers → replies back
- **Webhook-driven reactions** — SmartLead webhook fires when bounce rate spikes → Claude auto-investigates the bounce list and flags invalid emails
- **Team coordination** — teammates can ping Claude from Discord/Telegram without opening Cowork
- **Off-session triggers** — something fires while you're away, Claude handles it and you see the summary when you come back

Skip this entirely if you're a solo operator who only uses Claude from the desktop. The skills already cover that case.

---

## Channel types

| Channel | Status | Best for |
|---|---|---|
| Telegram | Official plugin | Personal async checks ("how's [client] looking?") |
| Discord | Official plugin | Team coordination, shared workflows |
| iMessage | Official plugin | Mac-only, lower friction for solo use |
| Webhook | Custom MCP | Production triggers (SmartLead bounce alerts, Apollo signal events) |

---

## One-time setup — Telegram (easiest)

1. **Create a Telegram bot:**
   - Open Telegram, message `@BotFather`
   - Send `/newbot`, follow the prompts
   - Save the bot token it gives you (looks like `1234567890:ABC...`)

2. **Install the Telegram channels plugin in Cowork:**
   - Open Claude Settings → Plugins
   - Search for "Telegram" (official plugin from `claude-plugins-official`)
   - Install and provide the bot token

3. **Pair the bot:**
   - Start a chat with your bot in Telegram
   - Send `/pair` — it returns a code
   - Paste the code in the plugin settings

4. **Start your Cowork session with channels enabled:**
   - `claude --channels plugin:telegram@claude-plugins-official`
   - Or set this as default in your Cowork settings

That's it. Now any message you send to the bot lands in your active Claude session as an event, and Claude's replies push back to Telegram.

Discord and iMessage follow the same pattern with their respective bot/auth setup.

---

## Use cases by skill

### list-builder

- "Build a list for [client]" from Telegram → Claude runs the skill end-to-end → Telegram gets the final summary with the Google Sheet link
- SmartLead webhook on a campaign bounce spike → Claude opens the bounce list, identifies the bad rows, pushes a "validation needed" alert back to Telegram with the count

### apollo-campaign-builder

- Long-running browser automation can take 30+ minutes for all 7 sequences and 3 workflows. Set up a Telegram channel so Claude pushes a notification when each sequence completes ("✓ [Client] - Call Only created, 10 steps, active") instead of you watching the screen

### client-proposal-doc-builder

- On a call: "I need the [client] proposal in 10 min" → Telegram → Claude generates the proposal + drafts the follow-up email → Telegram gets the doc URL + email body to copy
- Useful when you're not at your desk during a discovery call

### Generic — cross-skill

- Discord channel for campaign alerts where the team gets pinged on high-intent contacts (intent score ≥150 from the list-builder)
- Telegram alerts when scheduled tasks (nightly list refresh, weekly campaign health check) finish

---

## Custom webhook channels

For production triggers (SmartLead bounce events, Apollo signal events, calendar booking confirmations), you'll want a webhook channel rather than a person-driven channel. Pattern:

1. Build a small webhook receiver (any framework — Fly.io, Railway, Cloudflare Worker)
2. Register it as a custom MCP channel in your Cowork settings
3. The external service hits your webhook → it pushes into the Cowork session

This is more dev work than the official plugins. Worth it if you have real event volume to react to.

---

## Caveats

- **Sessions don't run forever.** Channels push into an *active* session. If your Cowork session is closed, the message goes to a queue but Claude isn't reacting in real time. For always-on async, use Routines (cloud-based polling) instead of channels.
- **Rate limits apply.** Telegram has its own limits; respect them on burst events.
- **Auth lives in your account.** Don't share bot tokens. Treat them like API keys.
- **Channels ≠ a permanent bot.** This is convenience tooling for your own Cowork sessions, not a replacement for building a proper customer-facing bot.

---

## When NOT to use channels

- If you're new to Cowork and just trying to run the skills — skip this entirely
- If you only operate from desktop and never need async — overkill
- If you need an always-on system that runs without you (e.g., 24/7 webhook handler) — use Routines or a dedicated backend, not channels
