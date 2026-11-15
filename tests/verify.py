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

# --- v2: approvals as a data object -----------------------------------------
good_appr = {"bot_id": "tehqeeq", "bot": "Tehqeeq", "tool": "send_email",
             "args": {"to": "clinic@example.com"}, "target": "Gmail",
             "state": "pending"}
clean, err = engine.validate_approval(good_appr)
check("good approval validates",
      err is None and clean["state"] == "pending", str(err))
_, err = engine.validate_approval({**good_appr, "tool": "launch_missiles"})
check("unknown approval tool rejected", err is not None)
_, err = engine.validate_approval({**good_appr, "state": "maybe"})
check("bad approval state rejected", err is not None)
clean, err = engine.approval_from_action(
    GOOD_BOT, {"type": "draft_email", "title": "Follow-up", "body": "Hi."})
check("approval from action",
      err is None and clean["tool"] == "draft_email"
      and clean["state"] == "pending", str(err))
decided, err = engine.decide_approval(clean, "approved", always_allow=True)
check("decide approval",
      err is None and decided["state"] == "approved"
      and decided["always_allow"] is True, str(err))
_, err = engine.decide_approval(decided, "denied")
check("decided approval is terminal", err is not None)
_, err = engine.decide_approval(clean, "maybe")
check("bad decision rejected", err is not None)
check("always-allow key",
      engine.always_allow_key("tehqeeq", "send_email", "Gmail")
      == "tehqeeq|send_email|Gmail")
check("approval matches allow", engine.approval_matches_allow(
    {"bot_id": "tehqeeq", "tool": "send_email", "target": "Gmail"},
    ["tehqeeq|send_email|Gmail"]))
check("approval mismatch no allow", not engine.approval_matches_allow(
    {"bot_id": "tehqeeq", "tool": "send_email", "target": "Slack"},
    ["tehqeeq|send_email|Gmail"]))
check("approval summary names bot+tool",
      "Tehqeeq" in engine.approval_summary(good_appr)
      and "send email" in engine.approval_summary(good_appr))

# --- v2: automations (split from routines) ----------------------------------
good_auto = {"name": "Daily brief", "bot_id": "tehqeeq",
             "task": "Write the morning brief.",
             "trigger": "time", "schedule": "daily 08:00"}
clean, err = engine.validate_automation(good_auto)
check("good time automation validates",
      err is None and clean["kind"] == "daily" and clean["time"] == "08:00",
      str(err))
clean, err = engine.validate_automation(
    {**good_auto, "trigger": "manual", "schedule": "manual"})
check("manual automation validates",
      err is None and clean["trigger"] == "manual", str(err))
clean, err = engine.validate_automation({**good_auto, "trigger": "webhook"})
check("webhook automation gets a secret",
      err is None and len(clean["webhook_secret"]) == 32, str(err))
_, err = engine.validate_automation({**good_auto, "trigger": "smoke-signal"})
check("bad trigger rejected", err is not None)
_, err = engine.validate_automation({**good_auto, "schedule": "daily 25:00"})
check("bad automation schedule rejected", err is not None)
clean2, err = engine.rotate_webhook_secret(
    {**good_auto, "trigger": "webhook", "webhook_secret": "a" * 32})
check("webhook secret rotates",
      err is None and clean2["webhook_secret"] != "a" * 32
      and len(clean2["webhook_secret"]) == 32, str(err))
_, err = engine.rotate_webhook_secret(good_auto)
check("non-webhook rotate rejected", err is not None)
check("time automation due Mon 08:00", engine.automation_due(
    {"trigger": "time", "kind": "daily", "time": "08:00", "enabled": True},
    mon_8))
check("manual automation never due", not engine.automation_due(
    {"trigger": "manual", "kind": "manual", "time": "", "enabled": True},
    mon_8))
check("webhook automation never due", not engine.automation_due(
    {"trigger": "webhook", "kind": "manual", "time": "", "enabled": True},
    mon_8))
clean, err = engine.validate_run_entry(
    {"name": "Daily brief", "ok": True, "result": "done"})
check("run entry validates",
      err is None and clean["name"] == "Daily brief", str(err))
clean, err = engine.validate_run_entry(
    {"routine": "Morning sweep", "ok": False, "result": "AI error"})
check("run entry accepts routine key",
      err is None and clean["name"] == "Morning sweep", str(err))
clean, err = engine.validate_routine({**good_rt, "origin": "chat"})
check("routine origin chat",
      err is None and clean["origin"] == "chat", str(err))
clean, _ = engine.validate_routine(good_rt)
check("routine origin defaults to form", clean["origin"] == "form")
aprompt = engine.build_automation_prompt(
    GOOD_BOT, {"name": "Daily brief", "trigger": "time",
               "task": "Write it."}, language="en")
check("automation prompt names automation",
      "Daily brief" in aprompt and "time" in aprompt)

# --- v2: credentials vault ----------------------------------------------------
good_cred = {"name": "Clinic Gmail", "type": "password",
             "value": "s3cr3t-value"}
clean, err = engine.validate_credential(good_cred)
check("good credential validates",
      err is None and clean["value"] == "s3cr3t-value", str(err))
_, err = engine.validate_credential({"name": "Cred", "value": ""})
check("empty credential value rejected", err is not None)
_, err = engine.validate_credential(
    {"name": "Cred", "type": "dna", "value": "v"})
check("bad credential type rejected", err is not None)
pub = engine.credential_public(clean)
check("credential public hides value",
      "value" not in pub and pub["name"] == "Clinic Gmail")
check("redact scrubs secrets",
      engine.redact_secrets("my key is s3cr3t-value ok", ["s3cr3t-value"])
      == "my key is [redacted] ok")
check("redact ignores short values",
      engine.redact_secrets("abc def", ["ab"]) == "abc def")
check("redact leaves clean text",
      engine.redact_secrets("hello world", ["s3cr3t-value"]) == "hello world")
clean, err = engine.validate_credential_request(
    {"bot_id": "daftar", "bot": "Daftar", "credential_name": "Clinic Gmail",
     "reason": "to check the inbox"})
check("credential request validates",
      err is None and clean["state"] == "pending", str(err))
_, err = engine.validate_credential_request(
    {"credential_name": "X", "reason": "y"})
check("credential request needs reason", err is not None)

# --- v2: per-bot workspace -----------------------------------------------------
good_file = {"bot_id": "tehqeeq", "name": "notes.md",
             "content": "# Notes\nhello"}
clean, err = engine.validate_workspace_file(good_file)
check("workspace file validates",
      err is None and clean["kind"] == "markdown" and clean["size"] > 0,
      str(err))
check("file kind by extension",
      engine.workspace_file_kind("data.json") == "json"
      and engine.workspace_file_kind("a.txt") == "text"
      and engine.workspace_file_kind("x.bin") == "other")
_, err = engine.validate_workspace_file({"name": "x.txt", "content": 42})
check("non-text file content rejected", err is not None)
reset = engine.reset_workspace([good_file], ["calendar", "contacts"],
                               keep_files=True)
check("reset keeps files, clears tools",
      len(reset["files"]) == 1 and reset["tools"] == [])
reset = engine.reset_workspace([good_file], ["calendar"], keep_files=False)
check("reset can drop files too",
      reset["files"] == [] and reset["tools"] == [])
summ = engine.workspace_summary(
    [good_file, {"bot_id": "t", "name": "a.json", "content": "{}"}])
check("workspace summary counts",
      summ["count"] == 2 and summ["kinds"].get("markdown") == 1
      and summ["kinds"].get("json") == 1, str(summ))

# --- v2: skills as files --------------------------------------------------------
clean, err = engine.parse_skill_file(
    "news-brief.md",
    "# Morning news brief\n- Find top stories\n- Summarise in 5 lines\n")
check("skill file parses",
      err is None and clean["name"] == "Morning news brief"
      and len(clean["steps"]) == 2 and clean["source"] == "file", str(err))
clean, err = engine.parse_skill_file(
    "my-skill.txt", "1. Open the inbox\n2. Reply to urgent mail\n")
check("skill file name from filename",
      err is None and clean["name"] == "My Skill", str(err))
_, err = engine.parse_skill_file("empty.md", "   \n")
check("empty skill file rejected", err is not None)
clean, err = engine.validate_skill(
    {"name": "News", "steps": ["a"], "enabled": False,
     "bots": ["tehqeeq"]})
check("skill toggle + attach",
      err is None and clean["enabled"] is False
      and clean["bots"] == ["tehqeeq"], str(err))
check("skill mention parses", engine.parse_skill_mention(
    "@News brief do it",
    [{"name": "News brief", "steps": ["a"], "enabled": True}]) is not None)
check("disabled skill mention ignored", engine.parse_skill_mention(
    "@News brief do it",
    [{"name": "News brief", "steps": ["a"], "enabled": False}]) is None)
check("skill mention needs @", engine.parse_skill_mention(
    "News brief do it", [{"name": "News brief", "steps": ["a"]}]) is None)

# --- v2: team bots ---------------------------------------------------------------
clean, err = engine.validate_bot(
    {**GOOD_BOT, "shared": True, "primary": True,
     "learning_opt_in": True})
check("team bot fields validate",
      err is None and clean["shared"] is True and clean["primary"] is True
      and clean["learning_opt_in"] is True, str(err))
clean, err = engine.validate_learned_item(
    {"bot_id": "tehqeeq", "text": "User likes short briefs"})
check("learned item validates",
      err is None and clean["state"] == "pending", str(err))
_, err = engine.validate_learned_item({"text": "x"})
check("short learned item rejected", err is not None)
_, err = engine.validate_learned_item(
    {"text": "valid text", "state": "absorbed"})
check("bad learned state rejected", err is not None)
primary = engine.team_primary(
    [{"id": "a", "shared": True},
     {"id": "b", "shared": True, "primary": True}])
check("team primary picked", primary is not None and primary["id"] == "b")
check("no shared bots, no primary",
      engine.team_primary([{"id": "a"}]) is None)

# --- v2: templates, memory blurbs, inbox, export --------------------------------
clean, err = engine.bot_from_template("tehqeeq", "Tehqeeq 2")
check("bot from template",
      err is None and clean["role"] == "Research Bot"
      and clean["name"] == "Tehqeeq 2", str(err))
_, err = engine.bot_from_template("nope")
check("bad template rejected", err is not None)
clean, err = engine.validate_memory_blurb({"text": "User likes tea"})
check("memory blurb validates",
      err is None and clean["text"] == "User likes tea", str(err))
blurbs = engine.memory_blurbs("likes tea\n\nprefers mornings\n")
check("memory blurbs split lines", len(blurbs) == 2, str(blurbs))
clean, err = engine.validate_inbox_message(
    {"project": "PharmaReg", "sender": "a@b.com", "subject": "Hi",
     "body": "Please review."})
check("inbox message validates",
      err is None and clean["status"] == "new", str(err))
_, err = engine.validate_inbox_message({"project": "P", "body": "x"})
check("inbox needs project + body", err is not None)
assigned, err = engine.assign_inbox(
    {"project": "PharmaReg", "body": "Please review."}, "daftar")
check("inbox assign triages",
      err is None and assigned["bot_id"] == "daftar"
      and assigned["status"] == "triaged", str(err))
bundle, err = engine.export_bot_bundle(
    GOOD_BOT, "likes tea", [{"name": "News", "steps": ["a"]}],
    [good_rt], [good_file])
check("export bundle v2",
      err is None and bundle["version"] == 2
      and bundle["bot"]["name"] == "Tehqeeq"
      and len(bundle["skills"]) == 1 and len(bundle["routines"]) == 1
      and len(bundle["workspace_files"]) == 1, str(err))

# --- v2: routes -------------------------------------------------------------------
r = client.post("/hamkar/api/skill-file",
                json={"filename": "news.md",
                      "content": "# News\n- Find stories\n"})
check("skill-file route",
      r.status_code == 200 and r.json().get("ok") is True
      and r.json()["skill"]["name"] == "News", str(r.json()))
r = client.post("/hamkar/api/skill-file",
                json={"filename": "e.md", "content": "  "})
check("skill-file route rejects empty", r.json().get("ok") is False)
r = client.post("/hamkar/api/export-bot",
                json={"bot": GOOD_BOT, "memory": "likes tea", "skills": [],
                      "routines": [], "workspace_files": []})
check("export-bot route",
      r.status_code == 200 and r.json().get("ok") is True
      and r.json()["bundle"]["version"] == 2, str(r.json()))
r = client.post("/hamkar/api/credential-request",
                json={"request": {"bot_id": "daftar", "bot": "Daftar",
                                 "credential_name": "Gmail",
                                 "reason": "check inbox"}})
check("credential-request route",
      r.status_code == 200 and r.json().get("ok") is True, str(r.json()))
r = client.post("/hamkar/api/automation",
                json={"bot": GOOD_BOT,
                      "automation": {"name": "Auto", "task": "Do it",
                                     "trigger": "manual"}})
check("automation without key fails honestly",
      r.status_code == 200 and r.json().get("ok") is False
      and "GEMINI_API_KEY" in r.json().get("error", ""))

# --- v2: page markers ---------------------------------------------------------------
r = client.get("/hamkar")
check("page has Vault", "Credentials Vault" in r.text)
check("page has Automations", "Automations" in r.text)
check("page has Workspace", "Workspace" in r.text)
check("page has Inbox", "Project inbox" in r.text)
check("page has Team Bots", "Team Bots" in r.text)
check("page uses hamkar-v2 key", "hamkar-v2" in r.text)
check("page states webhook limit",
      "Webhook triggers need a server endpoint" in r.text)

print(f"\n{len(FAIL)} FAILURES, {PASS} checks passed")
for f in FAIL:
    print("FAIL:", f)
sys.exit(1 if FAIL else 0)
