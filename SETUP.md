# Setup Guide

Complete this once before running any SuperSDR skills. Three things to configure — takes about 10 minutes.

---

## 1. Google Drive connector

**Required by:** `list-building` (reads your SPOT doc), `client-proposal-doc-builder` (creates the proposal doc)

1. Open Claude Cowork on your desktop
2. Go to **Settings → Connectors**
3. Find **Google Drive** and click **Connect**
4. Sign in with the Google account that owns your SPOT docs
5. When prompted for permissions, make sure **edit access** is enabled — read-only is not enough for the proposal builder

To verify it's working: paste any Google Doc URL into a Cowork session and ask Claude to summarize it. If Claude reads the content, you're good.

---

## 2. Apollo API key

**Required by:** `list-building`

1. Log into your Apollo account at [app.apollo.io](https://app.apollo.io)
2. Go to **Settings → Integrations → API**
3. Copy your API key
4. Keep it somewhere accessible — the `list-building` skill will ask for it the first time you run it and offer to save it for future sessions

**Note:** You need an Apollo paid plan for API access. The free plan does not include it.

---

## 3. Browser automation (Claude in Chrome)

**Required by:** `apollo-campaign-builder`

This skill drives the Apollo UI directly — clicking buttons, creating sequences, setting up workflows — so Claude needs to be able to see and control your browser.

1. In Claude Cowork, go to **Settings → Computer Use** (or **Settings → Browser**)
2. Enable **Use your computer** / browser control
3. Open Chrome and log into your Apollo account at [app.apollo.io](https://app.apollo.io)
4. Keep that tab open when running `apollo-campaign-builder`

**Note:** This is a separate opt-in from the Google Drive connector. You need both if you're running the full flow.

---

## Which skills need what

| Skill | Google Drive | Apollo API key | Browser automation |
|---|---|---|---|
| client-spot | — | — | — |
| cold-calling-screenplay | — | — | — |
| list-building | required | required | — |
| apollo-campaign-builder | — | — | required |
| objection-drill | — | — | — |
| client-proposal-doc-builder | required (write) | — | — |

Skills with no requirements in this table run on built-in Cowork capabilities (web search, text generation) — no additional setup needed.

---

## Full flow setup checklist

If you're running the complete client onboarding flow (SPOT → list → sequences → proposal), do all three:

- [ ] Google Drive connector connected with edit access
- [ ] Apollo API key copied and ready
- [ ] Browser automation enabled in Cowork, Apollo open in Chrome
