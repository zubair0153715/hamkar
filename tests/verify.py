# -*- coding: utf-8 -*-
"""Hamkar deterministic checks — no key, no network.

Covers: starter Bots, Bot/Routine/Skill/Action/Reply/Suggestion
validation, routine due/next-run arithmetic, @mention routing,
prompt building (Bot only ever sees what the user can see), and
route smoke via TestClient on the router alone.

Run: ~/workspace/.venv-fc/bin/python tests/verify.py
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hamkar import engine  # noqa: E402

PASS = 0
FAIL = []


def check(name, ok, detail=""):
    global PASS
    if ok:
        PASS += 1
    else:
        FAIL.append(f"{name}: {detail}")


GOOD_BOT = {"id": "tehqeeq", "name": "Tehqeeq", "emoji": "🔍",
            "role": "Research Bot",
            "instructions": "Research a topic and return a short brief.",
            "language": "en"}

# --- starter bots -------------------------------------------------------------
check("4 starter bots", len(engine.STARTER_BOTS) == 4)
ids = [b["id"] for b in engine.STARTER_BOTS]
check("starter ids unique", len(ids) == len(set(ids)))
for b in engine.STARTER_BOTS:
    clean, err = engine.validate_bot(b)
    check(f"starter {b['id']} validates", err is None, str(err))
check("starter roles differ from Grok Bot examples",
      {b["role"] for b in engine.STARTER_BOTS} !=
      {"Talent Scout", "Expense Manager", "Bug Reproduction",
       "Chief of Staff"})

# --- bot validation -----------------------------------------------------------
clean, err = engine.validate_bot(GOOD_BOT)
check("good bot validates", err is None and clean["name"] == "Tehqeeq")
_, err = engine.validate_bot({"name": "X", "instructions": "short"})
check("short name rejected", err is not None)
_, err = engine.validate_bot({"name": "Test",
                              "instructions": "short"})
check("short instructions rejected", err is not None)
clean, _ = engine.validate_bot({**GOOD_BOT, "language": "xx"})
check("bad language defaults to en", clean["language"] == "en")

# --- @mention routing ---------------------------------------------------------
check("mention parses",
      engine.parse_mention("@Tehqeeq research this",
                           ["Tehqeeq", "Daftar"]) == "tehqeeq")
check("mention longest name wins",
      engine.parse_mention("@Research Bot do this",
                           ["Research", "Research Bot"]) == "research bot")
check("mention unknown name", engine.parse_mention(
    "@Nobody hello", ["Tehqeeq"]) is None)
check("no mention", engine.parse_mention("hello there") is None)
check("mention needs @ at start",
      engine.parse_mention("ask @Tehqeeq later") is None)

# --- routines -----------------------------------------------------------------
good_rt = {"name": "Morning sweep", "bot_id": "tehqeeq",
           "task": "Summarise overnight news.", "schedule": "weekdays 08:00"}
clean, err = engine.validate_routine(good_rt)
check("good routine validates", err is None, str(err))
check("routine kind parsed", clean["kind"] == "weekdays")
check("routine time parsed", clean["time"] == "08:00")
for bad_sched in ["every day", "daily 25:00", "daily 8:0", "never",
                  "daily", ""]:
    _, err = engine.validate_routine({**good_rt, "schedule": bad_sched})
    check(f"bad schedule rejected: {bad_sched!r}", err is not None)
clean, _ = engine.validate_routine({**good_rt, "schedule": "manual"})
check("manual routine validates", clean["kind"] == "manual")

mon_8 = datetime(2026, 11, 16, 8, 0)   # a Monday
sat_8 = datetime(2026, 11, 21, 8, 0)   # a Saturday
check("weekday routine due Mon 08:00",
      engine.routine_due(clean | {"kind": "weekdays", "time": "08:00",
                                  "enabled": True}, mon_8))
check("weekday routine not due Sat",
      not engine.routine_due(clean | {"kind": "weekdays", "time": "08:00",
                                      "enabled": True}, sat_8))
check("routine not due at 08:01",
      not engine.routine_due(clean | {"kind": "daily", "time": "08:00",
                                      "enabled": True},
                             datetime(2026, 11, 16, 8, 1)))
check("manual never due",
      not engine.routine_due(clean | {"kind": "manual", "time": "",
                                      "enabled": True}, mon_8))
check("disabled never due",
      not engine.routine_due(clean | {"kind": "daily", "time": "08:00",
                                      "enabled": False}, mon_8))
nxt = engine.next_run({"kind": "weekdays", "time": "08:00"},
                      datetime(2026, 11, 16, 9, 0))
check("next run skips to Tuesday",
      nxt is not None and nxt.weekday() == 1 and nxt.hour == 8,
      str(nxt))
check("manual has no next run",
      engine.next_run({"kind": "manual", "time": ""}, mon_8) is None)

# --- skills -------------------------------------------------------------------
clean, err = engine.validate_skill({"name": "News brief",
                                    "steps": ["Find top stories",
                                              "Summarise in 5 lines"]})
check("good skill validates", err is None and len(clean["steps"]) == 2)
clean, _ = engine.validate_skill({"name": "News",
                                  "steps": "line one\nline two"})
check("string steps split", clean is not None and len(clean["steps"]) == 2)
_, err = engine.validate_skill({"name": "S", "steps": []})
check("empty steps rejected", err is not None)

# --- reply / action / suggestion validation ------------------------------------
clean, err = engine.validate_reply(
    {"reply": "Here is the brief.",
     "remember": ["User likes short briefs"],
     "action": {"type": "draft_email", "title": "Follow-up",
                "body": "Hi, just following up."}})
check("good reply validates", err is None and clean["action"]["type"] == "draft_email")
_, err = engine.validate_reply({"reply": "  "})
check("empty reply rejected", err is not None)
_, err = engine.validate_reply({"reply": "x", "action": {"type": "send_email",
                                                         "title": "t",
                                                         "body": "b"}})
check("send_email action rejected (propose only)",
      err is not None)
_, err = engine.validate_action({"type": "plan", "title": "", "body": "x"})
check("action needs title", err is not None)
clean, err = engine.validate_suggestions(
    {"suggestions": [{"title": "Draft the reply", "detail": "It is due"}]})
check("good suggestions validate", err is None)
_, err = engine.validate_suggestions({"suggestions": []})
check("empty suggestions rejected", err is not None)
clean, err = engine.validate_summary("User asked for a news brief.")
check("good summary validates", err is None)

# --- prompts: the Bot only sees what the user can see -------------------------
prompt = engine.build_chat_prompt(
    GOOD_BOT, "User likes tea", "Earlier: news brief",
    [{"role": "user", "text": "hi"}], "research AI news",
    skill={"name": "News brief", "steps": ["Find stories", "Summarise"]},
    pasted_text="PASTED ARTICLE TEXT", language="en")
for needle in ["Tehqeeq", "Research a topic", "User likes tea",
               "Earlier: news brief", "News brief", "Find stories",
               "PASTED ARTICLE TEXT", "research AI news"]:
    check(f"prompt contains {needle[:20]!r}", needle in prompt)
check("prompt demands JSON only", '"reply"' in prompt)
check("prompt forbids sending", "never take" in prompt.lower()
      or "propose" in prompt.lower())

handoff = engine.build_handoff_brief(
    GOOD_BOT, "Working on news brief",
    [{"role": "user", "text": "hi"}, {"role": "bot", "text": "hello"}])
check("handoff names source bot", "Tehqeeq" in handoff)
check("handoff carries summary", "news brief" in handoff)

# --- routes (TestClient on the router alone) ----------------------------------
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from hamkar.routes import router  # noqa: E402

app = FastAPI()
app.include_router(router)
client = TestClient(app, raise_server_exceptions=False)

r = client.get("/hamkar")
check("GET /hamkar 200", r.status_code == 200, str(r.status_code))
check("page names Hamkar", "Hamkar" in r.text)
check("page states honest limits", "no server cron" in r.text)
r = client.get("/hamkar/api/ai-status")
check("ai-status 200", r.status_code == 200 and "ai_available" in r.json())
r = client.get("/hamkar/api/starters")
check("starters 4 bots", r.status_code == 200
      and len(r.json()["bots"]) == 4)
r = client.post("/hamkar/api/chat",
                json={"bot": GOOD_BOT, "message": "hello"})
check("chat without key fails honestly",
      r.status_code == 200 and r.json().get("ok") is False
      and "GEMINI_API_KEY" in r.json().get("error", ""))
r = client.post("/hamkar/api/handoff",
                json={"source_bot": GOOD_BOT, "summary": "s",
                      "history": []})
check("handoff returns brief",
      r.status_code == 200 and r.json().get("ok") is True
      and "Tehqeeq" in r.json().get("brief", ""))
r = client.post("/hamkar/api/chat",
                json={"bot": {"name": "X"}, "message": "hello"})
check("bad bot rejected", r.json().get("ok") is False)

print(f"\n{len(FAIL)} FAILURES, {PASS} checks passed")
for f in FAIL:
    print("FAIL:", f)
sys.exit(1 if FAIL else 0)
