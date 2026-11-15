# Hamkar (ہمراہ کار) — AI Teammates

**Free, unlimited AI teammates that work while you're away. No account, no card, no paywall.**

Hamkar is an original clean-room build in the same category as xAI's **Grok Bot** (see "What Grok Bot is" below): named AI Bots with roles, persistent memory, reusable Skills, scheduled Routines, multi-Bot handoffs and an approval queue for sensitive actions. It is **not** affiliated with xAI / SpaceXSI / Grok. All code, name, branding and UI are original; the AI brain is Google Gemini on the owner's free quota.

Live route (after the next clinic-demo deploy): `https://clinic-demo.fastapicloud.dev/hamkar`

## What it does

| Grok Bot feature (public) | Hamkar equivalent (this app) |
|---|---|
| Named Bots with roles, own cloud computer | Named Bots with roles + instructions, own chat + memory (browser storage) |
| Chat by text / voice note / call | Text chat + read-aloud via browser speech (free, client-side) |
| Persistent memory, learns from work | Visible, editable memory card + running summary |
| Routines (schedule / Slack / GitHub events) | Routines in plain language (`daily 08:00`, `weekdays 08:00`, `monday 10:30`, `manual`) — run while the page is open; Run-now + run log |
| Skills (teach a task, reuse it) | Skills: name + ordered steps; pick one in the chat bar and the Bot follows it |
| Connectors (Gmail, Drive, Slack, Notion, GitHub, X) | Honest version: paste any text (email, article, notes) and the Bot works on it — no logins, no fake OAuth |
| Approval rules / Auto Review before sensitive actions | Approval queue: Bots only *propose* drafts/plans; you approve, reject or copy — nothing is ever sent, deleted or published by a Bot |
| Proactive teammates (offer work unasked) | "Suggest work" — the Bot proposes next tasks from your history |
| Multi-Bot handoffs, Bots message each other | `@BotName` routing in chat + Handoff button (sends a readable brief to another Bot) |
| Team Bots (share with Slack/Teams, Review learnings) | Export a Bot as JSON, share it, teammates import the same Bot |
| Meetings (join calls, take notes) | Not built — a Bot cannot join your calls; the Handoff + summary covers the note-taking part |
| Model routing (incl. third-party models) | No model picker — one brain (Gemini 2.5 Flash, free tier), stated plainly |

## Honest limits

- AI replies need `GEMINI_API_KEY` (owner's free quota). Without it, Bots, Skills, Routines, memory, chat history, export/import and approvals still work; AI calls show an honest message.
- Routines run **while this page is open** (checked every 30 seconds). There is no server cron.
- No real web browsing, no real email sending, no real app logins. The "paste text" box is the connector.
- Stateless server: everything lives in your browser (`localStorage`, key `hamkar-v1`). Clear it and your Bots go with it — export first.

## What Grok Bot is (research, 15 Nov 2026)

- **Grok Bot** (xAI writes it as two words; "Grokbot" is the common informal spelling) is xAI's always-on AI-agent product, distinct from the Grok chatbot. It launched in **early beta on 11 August 2026**; **Grok Bot 1.0** left beta on **11 November 2026** (launch post dated 2 November 2026).
- Each user gets **one persistent Linux cloud computer** (browser, files, terminal, memory); named Bots share it, each with its own screen. Bots sign in to connected apps (Gmail, Calendar, Drive, Slack, Notion, GitHub, X), run **Routines** on a schedule or on events, and ask for approval before sensitive actions.
- 1.0 adds **Team Bots** (shared with a team, in Slack / Microsoft Teams / video calls), **proactive teammates** (Bots offer work unasked, follow up on unfinished work), and more capable browser/document work. Meetings need Team/Enterprise/Ultra plans.
- xAI routes each task to what it calls the best model — in October 2026 Musk named Claude Opus 5.5 among them; there is **no model picker**. Grok 4.8 was in soft rollout to Grok Bot users (Nov 2026).
- Pricing: bundled in **The X Subscription** — Premium $30/mo, Super $100, Ultra $200 (team seats $30/$100/$200); Free and Plus ($8) do not include it. Built with **Cursor** (acquired by SpaceX); xAI rebranded as **SpaceXSI** (SpaceX Super Intelligence) in October 2026 after SpaceX acquired xAI in February 2026.
- Sources: [xAI — Introducing Grok Bot 1.0](https://x.ai/news/grok-bot-1-0) · [Grokati — Grok Bot 1.0 launches](https://www.grokati.com/articles/2026-11-11-grok-bot-1-0-launches) · [Crosswalk — Grok Bot agent card](https://crosswalk.to/agents/grok-bot) · [GeekExtreme — GrokBot as an autonomous agent platform](https://www.geekextreme.com/what-is-elon-musk-s-ai-thing/)

## Run

```bash
# tests (no key, no network)
~/workspace/.venv-fc/bin/python tests/verify.py
# live Gemini check (needs GEMINI_API_KEY in the shell; skips otherwise)
~/workspace/.venv-fc/bin/python tests/live_check.py
```

The app is a route inside `clinic-demo` (`app/hamkar/`): `GET /hamkar`, plus `/hamkar/api/*` (`ai-status`, `starters`, `chat`, `summarize`, `suggest`, `routine`, `action`, `handoff`). Deploy is the standard clinic-demo deploy (blocked on the owner's FastAPI Cloud sign-in as of 15 Nov 2026 — the route goes live with the next deploy).

## Files

- `hamkar/engine.py` — pure logic: validation, routines, skills, prompts
- `hamkar/gemini.py` — Gemini calls (urllib, key from env at call time only)
- `hamkar/routes.py` — FastAPI router
- `hamkar/pages.py` — single-page app (HTML + JS)
- `tests/verify.py` — 63 deterministic checks
- `tests/live_check.py` — real Gemini calls (chat, suggest, routine)
