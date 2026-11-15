# -*- coding: utf-8 -*-
"""Hamkar AI layer — Bot replies, summaries, proactive suggestions,
routine runs and action drafts via Gemini.

Same call pattern as the other gap builds (Kirdar/Daftar/Poda):
urllib, key read from the environment AT CALL TIME only, never
stored or logged. Every AI JSON is validated by engine before it
reaches the page.

Without a key, AI chat, summaries, suggestions, routine runs and
action drafts are unavailable; creating/editing Bots, Skills,
Routines, memory, chat history, export/import and the approval
queue still work fully.
"""

import json
import os
import urllib.error
import urllib.request

from . import engine

MODEL = "gemini-2.5-flash"
TIMEOUT = 120


def _get_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_APIkey")


def key_available():
    return bool(_get_key())


def _call_text(prompt, max_tokens=3000, temperature=0.7):
    """One Gemini generateContent call with text only.
    Returns (text, error)."""
    key = _get_key()
    if not key:
        return None, ("AI ke liye GEMINI_API_KEY set nahi hai. Bots, "
                      "Skills, Routines, memory aur export/import phir "
                      "bhi poore kaam karte hain.")
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODEL}:generateContent?key={key}")
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature,
                             "maxOutputTokens": max_tokens},
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return None, "AI quota khatam (429). Thodi der baad dobara try karein."
        return None, f"AI error (HTTP {e.code}). Dobara try karein."
    except Exception as exc:  # network, timeout, bad JSON
        return None, f"AI se rabta nahi hua ({exc}). Dobara try karein."
    try:
        return body["candidates"][0]["content"]["parts"][0]["text"].strip(), None
    except (KeyError, IndexError, TypeError):
        return None, "AI ne khaali jawab diya. Dobara try karein."


def _parse_json(raw):
    """Parse the model's JSON, tolerating ```json fences."""
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1] if "\n" in text else ""
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    try:
        data = json.loads(text.strip())
    except (json.JSONDecodeError, ValueError):
        return None, "AI ka jawab JSON nahi tha. Dobara try karein."
    if not isinstance(data, dict):
        return None, "AI ka jawab samajh nahi aaya."
    return data, None


def chat(bot, memory, summary, history, message, skill=None,
         pasted_text=None, language="en"):
    """One Bot reply. Returns (result, error) where result is
    {"reply": str, "remember": [facts], "action": dict|None}."""
    bot, err = engine.validate_bot(bot)
    if err:
        return None, err
    if language not in engine.LANGUAGES:
        return None, "Language ghalat hai — English, Roman-Urdu ya Urdu chunein."
    message = (message or "").strip()
    if not message:
        return None, "Message khaali hai."
    if len(message) > engine.MAX_MESSAGE:
        return None, "Message 2000 harf se chhota rakhein."
    if skill is not None:
        skill, err = engine.validate_skill(skill)
        if err:
            return None, err
    prompt = engine.build_chat_prompt(
        bot, engine.validate_memory(memory), summary,
        engine.validate_history(history), message, skill=skill,
        pasted_text=pasted_text, language=language)
    raw, err = _call_text(prompt, max_tokens=2500, temperature=0.7)
    if err:
        return None, err
    data, err = _parse_json(raw)
    if err:
        return None, err
    clean, err = engine.validate_reply(data)
    if err:
        return None, err
    clean["language"] = language
    return clean, None


def summarize(bot, turns, language="en"):
    """Summarise turns into a running memory note. Returns
    (summary_text, error)."""
    bot, err = engine.validate_bot(bot)
    if err:
        return None, err
    if language not in engine.LANGUAGES:
        return None, "Language ghalat hai."
    turns = engine.validate_history(turns)
    if not turns:
        return None, "Summarise karne ke liye koi baat-cheet nahi."
    lines = []
    for turn in turns:
        who = "User" if turn["role"] == "user" else bot["name"]
        lines.append(f"{who}: {turn['text']}")
    lang_word = engine.LANG_WORD[language]
    prompt = (
        f"Summarise this chat with {bot['name']} ({bot['role']}) into a "
        f"short memory note, so the Bot can keep the work straight in "
        f"future replies. Write in {lang_word}. Keep it under 800 "
        "characters. Keep: the user's name if given, open tasks, "
        "decisions made, and anything promised. Drop: greetings and "
        "small talk.\n\nReply with ONLY a JSON object, no markdown, "
        'no extra text:\n{"summary": "The summary text."}\n\nCHAT:\n'
        + "\n".join(lines))
    raw, err = _call_text(prompt, max_tokens=1500, temperature=0.3)
    if err:
        return None, err
    data, err = _parse_json(raw)
    if err:
        return None, err
    return engine.validate_summary(data.get("summary"))


def suggest(bot, summary, history, language="en"):
    """Proactive next-work suggestions. Returns (result, error)."""
    bot, err = engine.validate_bot(bot)
    if err:
        return None, err
    if language not in engine.LANGUAGES:
        return None, "Language ghalat hai."
    prompt = engine.build_suggest_prompt(
        bot, summary, engine.validate_history(history), language)
    raw, err = _call_text(prompt, max_tokens=1500, temperature=0.7)
    if err:
        return None, err
    data, err = _parse_json(raw)
    if err:
        return None, err
    return engine.validate_suggestions(data)


def run_routine(bot, routine, language="en"):
    """Run one scheduled Routine now. Returns (result, error) in the
    same shape as chat()."""
    bot, err = engine.validate_bot(bot)
    if err:
        return None, err
    routine, err = engine.validate_routine(routine)
    if err:
        return None, err
    if language not in engine.LANGUAGES:
        return None, "Language ghalat hai."
    prompt = engine.build_routine_prompt(bot, routine, language)
    raw, err = _call_text(prompt, max_tokens=2500, temperature=0.7)
    if err:
        return None, err
    data, err = _parse_json(raw)
    if err:
        return None, err
    clean, err = engine.validate_reply(data)
    if err:
        return None, err
    clean["language"] = language
    return clean, None


def propose_action(bot, memory, summary, history, instruction,
                   language="en"):
    """Draft one action (email/message/plan/note) for the approval
    queue. Returns (action_dict, error)."""
    bot, err = engine.validate_bot(bot)
    if err:
        return None, err
    instruction = (instruction or "").strip()
    if len(instruction) < 5:
        return None, "Kya draft karna hai, wo likhein."
    if len(instruction) > engine.MAX_MESSAGE:
        return None, "Instruction 2000 harf se chhoti rakhein."
    if language not in engine.LANGUAGES:
        return None, "Language ghalat hai."
    prompt = engine.build_action_prompt(
        bot, engine.validate_memory(memory), summary,
        engine.validate_history(history), instruction, language)
    raw, err = _call_text(prompt, max_tokens=3000, temperature=0.7)
    if err:
        return None, err
    data, err = _parse_json(raw)
    if err:
        return None, err
    return engine.validate_action(data)
