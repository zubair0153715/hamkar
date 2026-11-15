# -*- coding: utf-8 -*-
"""Hamkar routes — AI teammates studio (Grok Bot category, clean-room).

Original build. Not affiliated with xAI / SpaceXSI / Grok. Stateless:
Bots, chats, routines, skills and approvals live in the user's own
browser (localStorage). No account, no card, no paywall. AI replies
need GEMINI_API_KEY (owner's free quota); without it, everything
except AI calls still works.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

from . import engine, gemini
from .pages import HAMKAR_HTML

router = APIRouter(prefix="/hamkar")


def _bad(msg):
    return JSONResponse({"ok": False, "error": msg}, status_code=200)


@router.get("", response_class=HTMLResponse)
def index():
    return HAMKAR_HTML


@router.get("/api/ai-status")
def ai_status():
    return {"ai_available": gemini.key_available()}


@router.get("/api/starters")
def starters():
    return {"ok": True, "bots": engine.STARTER_BOTS}


@router.post("/api/chat")
def api_chat(body: dict):
    result, err = gemini.chat(
        body.get("bot") or {}, body.get("memory") or "",
        body.get("summary") or "", body.get("history") or [],
        body.get("message") or "", skill=body.get("skill"),
        pasted_text=body.get("pasted_text") or None,
        language=body.get("language") or "en")
    if err:
        return _bad(err)
    return {"ok": True, **result}


@router.post("/api/summarize")
def api_summarize(body: dict):
    summary, err = gemini.summarize(
        body.get("bot") or {}, body.get("turns") or [],
        language=body.get("language") or "en")
    if err:
        return _bad(err)
    return {"ok": True, "summary": summary}


@router.post("/api/suggest")
def api_suggest(body: dict):
    result, err = gemini.suggest(
        body.get("bot") or {}, body.get("summary") or "",
        body.get("history") or [], language=body.get("language") or "en")
    if err:
        return _bad(err)
    return {"ok": True, **result}


@router.post("/api/routine")
def api_routine(body: dict):
    result, err = gemini.run_routine(
        body.get("bot") or {}, body.get("routine") or {},
        language=body.get("language") or "en")
    if err:
        return _bad(err)
    return {"ok": True, **result}


@router.post("/api/action")
def api_action(body: dict):
    action, err = gemini.propose_action(
        body.get("bot") or {}, body.get("memory") or "",
        body.get("summary") or "", body.get("history") or [],
        body.get("instruction") or "",
        language=body.get("language") or "en")
    if err:
        return _bad(err)
    return {"ok": True, "action": action}


@router.post("/api/handoff")
def api_handoff(body: dict):
    source, err = engine.validate_bot(body.get("source_bot") or {})
    if err:
        return _bad(err)
    brief = engine.build_handoff_brief(
        source, body.get("summary") or "",
        engine.validate_history(body.get("history") or []))
    return {"ok": True, "brief": brief}
