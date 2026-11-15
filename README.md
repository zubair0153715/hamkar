# Hamkar (ہمراہ کار) — AI Teammates

**Free, unlimited AI teammates that work while you're away. No account, no card, no paywall.**

Hamkar is an original clean-room build in the same category as xAI's **Grok Bot** (see "What Grok Bot is" below): named AI Bots with roles, persistent memory, reusable Skills, scheduled Routines, multi-Bot handoffs and an approval queue for sensitive actions. It is **not** affiliated with xAI / SpaceXSI / Grok. All code, name, branding and UI are original; the AI brain is Google Gemini on the owner's free quota.

Live route (after the next clinic-demo deploy): `https://clinic-demo.fastapicloud.dev/hamkar`

## What it does — v2 (15 Nov 2026, Grok Bot 1.0 parity, clean-room)

| Grok Bot feature (public) | Hamkar equivalent (this app) |
|---|---|
| Named Bots with roles, own cloud computer | Named Bots with roles + instructions, own chat + memory (browser storage) — **v2: each Bot also gets a local workspace (files + tools list) with export and "reset, keep files"** |
| Chat by text / voice note / call | Text chat + read-aloud via browser speech (free, client-side) |
| Persistent memory, learns from work | Visible, editable memory card + running summary + **v2: memory snippets (blurbs)** |
| Routines (schedule / Slack / GitHub events) | **v2: Routines are chat-defined** ("save this as a routine" from a reply, or typed) — run while the page is open; Run-now + run log |
| Automations (trigger catalog, run history, webhook) | **v2: Automations** — trigger time / manual / webhook, run history, pause/resume, run-now, webhook secret generate/rotate |
| Skills (teach a task, reuse it) | **v2: Skills as uploadable files** (.txt/.md → steps), toggle on/off, attach to Bots, invoke with @SkillName in chat — plus the v1 taught-steps form |
| Connectors (Gmail, Drive, Slack, Notion, GitHub, X) | Honest version: paste any text (email, article, notes) and the Bot works on it — no logins, no fake OAuth — **v2: plus a per-project inbox that routes messages to a Bot** |
| Approval rules / Auto Review before sensitive actions | **v2: Approvals are structured records** (tool, args, target, state pending/approved/denied) rendered as cards, with per-bot+tool "always allow" memory — nothing is ever sent, deleted or published by a Bot |
| Credentials vault ("password never enters the chat") | **v2: Credentials Vault** — values stored only in the browser, never shown, never logged; Bots request credentials through a dedicated field; messages containing a vault secret are refused in chat |
| Proactive teammates (offer work unasked) | "Suggest work" — the Bot proposes next tasks from your history |
| Multi-Bot handoffs, Bots message each other | `@BotName` routing in chat + Handoff button (sends a readable brief to another Bot) |
| Team Bots (share with Slack/Teams, Review learnings) | **v2: Team Bots** — share a Bot, one primary Bot, learning opt-in; learned items are reviewable (accept → memory / reject). Export a Bot as a full bundle (Bot + memory + Skills + Routines + workspace files) |
| Bot templates | **v2: the 4 starters are templates** — copy one into a new Bot |
| Meetings (join calls, take notes) | Not built — a Bot cannot join your calls; the Handoff + summary covers the note-taking part |
| Model routing (incl. third-party models) | No model picker — one brain (Gemini 2.5 Flash, free tier), stated plainly |

v1 (15 Nov 2026) had 4 starter Bots, Gemini chat, memory card, Skills (taught steps), Routines (conflated with automations), handoffs, approval queue (drafts only), Suggest work, read-aloud, paste-text connector, export/import single Bot. v2 keeps every v1 feature working and adds the rows marked **v2** above.

## Honest limits

- AI replies need `GEMINI_API_KEY` (owner's free quota). Without it, Bots, Skills, Routines, Automations, memory, Vault, workspaces and export/import still work; AI calls show an honest message.
- Routines and Automations run **while this page is open** (checked every 30 seconds). There is no server cron.
- No cloud computer per Bot — each Bot's workspace is local files in your browser (localStorage). No real web browsing, no real email sending, no real app logins, no meeting joins. The "paste text" box is the connector.
- Webhook triggers need a server endpoint (not in this build): the secret is generated/rotated here, and the Automation runs on its time trigger or Run now.
- Vault values live only in your browser and are never displayed, logged or pasted into chat; a message containing a vault secret is refused.
- Stateless server: everything lives in your browser (`localStorage`, key `hamkar-v2`; v1 data under `hamkar-v1` is migrated on first load). Clear it and your Bots go with it — export first.

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

The app is a route inside `clinic-demo` (`app/hamkar/`): `GET /hamkar`, plus `/hamkar/api/*` (`ai-status`, `starters`, `chat`, `summarize`, `suggest`, `routine`, `automation`, `action`, `handoff`, `skill-file`, `export-bot`, `credential-request`). Deploy is the standard clinic-demo deploy (blocked on the owner's FastAPI Cloud sign-in as of 15 Nov 2026 — the route goes live with the next deploy).

## Files

- `hamkar/engine.py` — pure logic: validation, routines, automations, approvals, vault, workspaces, file skills, team bots, templates, inbox, export bundles, prompts
- `hamkar/gemini.py` — Gemini calls (urllib, key from env at call time only)
- `hamkar/routes.py` — FastAPI router (`chat`, `summarize`, `suggest`, `routine`, `automation`, `action`, `handoff`, `skill-file`, `export-bot`, `credential-request`, `starters`, `ai-status`)
- `hamkar/pages.py` — single-page app (HTML + JS, localStorage `hamkar-v2`)
- `tests/verify.py` — 137 deterministic checks (63 v1 + 74 v2)
- `tests/live_check.py` — real Gemini calls (chat, suggest, routine)
