# -*- coding: utf-8 -*-
"""Hamkar live check — real Gemini calls. Skips cleanly when no
GEMINI_API_KEY is set (the deployed key lives in the FastAPI Cloud
env, not on this VM).

Run: ~/workspace/.venv-fc/bin/python tests/live_check.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hamkar import engine, gemini  # noqa: E402

if not gemini.key_available():
    print("SKIP: no GEMINI_API_KEY in this shell (live check only).")
    sys.exit(0)

BOT = engine.STARTER_BOTS[0]
ok = True

res, err = gemini.chat(BOT, "", "", [], "Say hello in one short line.",
                       language="en")
print("chat:", "OK" if res else f"FAIL {err}")
if res:
    print("  reply:", res["reply"][:160])
ok = ok and res is not None

res, err = gemini.suggest(BOT, "", [{"role": "user", "text": "I need a morning news brief every day."}], language="en")
print("suggest:", "OK" if res else f"FAIL {err}")
if res:
    print("  suggestions:", [s["title"] for s in res["suggestions"]])
ok = ok and res is not None

res, err = gemini.run_routine(
    BOT, {"name": "Test routine", "bot_id": "tehqeeq",
          "task": "Write a one-line test report.", "schedule": "manual",
          "kind": "manual", "time": "", "enabled": True}, language="en")
print("routine:", "OK" if res else f"FAIL {err}")
if res:
    print("  reply:", res["reply"][:160])
ok = ok and res is not None

sys.exit(0 if ok else 1)
