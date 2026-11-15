# -*- coding: utf-8 -*-
"""Build the static (GitHub Pages) version of Hamkar from hamkar/pages.py.

The app is a single self-contained HTML+JS page; the FastAPI server only
serves it and proxies Gemini. This build makes the page honest on a host
with no server, without touching the repo source:

1. api() can no longer throw on a dead /hamkar/api/* call — it returns
   {ok:false, error: ...} so the UI shows the honest message instead of
   silently doing nothing (chat/summarize/suggest/routine/automation/action
   need the server key; skill-file/export-bot/handoff/credential-request
   need the server's pure helpers).
2. The AI badge says plainly the static build has no server key.
3. The 4 starter Bots are inlined (window.HAMKAR_STARTERS) and used as
   fallback when the /hamkar/api/starters fetch fails, so first-run
   templates still work.

No API key is embedded anywhere. Run: python3 build_static.py
Output: static-build/index.html
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from hamkar.engine import STARTER_BOTS  # noqa: E402
from hamkar.pages import HAMKAR_HTML  # noqa: E402

AI_MSG = ("AI is not available in this static build — AI replies need the "
          "owner's Gemini key on a server. Bots, memory, Skills, Vault "
          "and workspaces still work.")
SERVER_MSG = ("This needs the Hamkar server and is not available "
              "in this static build.")

API_OLD = ("async function api(path,body){const r=await fetch('/hamkar/api/'+path,"
           "{method:'POST',headers:{'Content-Type':'application/json'},"
           "body:JSON.stringify(body||{})});return r.json();}")
API_NEW = ("async function api(path,body){try{const r=await fetch('/hamkar/api/'+path,"
           "{method:'POST',headers:{'Content-Type':'application/json'},"
           "body:JSON.stringify(body||{})});return await r.json();}"
           "catch(e){const ai=['chat','summarize','suggest','routine','automation','action'];"
           "return {ok:false,error:ai.indexOf(path)>=0?'"
           + AI_MSG.replace("'", "\\'") + "':'" + SERVER_MSG + "'};}}")


def replace_once(html, old, new, label):
    n = html.count(old)
    assert n == 1, f"{label}: expected 1 occurrence, found {n}"
    return html.replace(old, new)


def main():
    html = HAMKAR_HTML

    # 1. Guarded api().
    html = replace_once(html, API_OLD, API_NEW, "api()")

    # 2. AI badge: the 3-line ai-status fetch block -> honest static text.
    lines = html.split("\n")
    idx = next(i for i, ln in enumerate(lines)
               if ln.startswith("fetch('/hamkar/api/ai-status')"))
    block = "\n".join(lines[idx:idx + 3])
    assert "ai_available" in block and block.rstrip().endswith(".catch(()=>{});"), \
        "ai-status block shape changed"
    badge = ("(function(){var el=document.getElementById('aistatus');"
             "el.textContent='AI: off on static hosting — needs server key';"
             "el.className='badge off';})();")
    lines[idx:idx + 3] = [badge]
    html = "\n".join(lines)

    # 3. Starters fallback in load(): line starting with the bots fetch.
    lines = html.split("\n")
    idx = next(i for i, ln in enumerate(lines)
               if ln.strip().startswith("if(!S.bots.length){fetch('/hamkar/api/starters')"))
    assert lines[idx].rstrip().endswith(".catch(()=>{});}")
    lines[idx] = lines[idx].replace(
        ".catch(()=>{});}",
        ".catch(()=>{if(window.HAMKAR_STARTERS){S.bots=JSON.parse(JSON.stringify(window.HAMKAR_STARTERS));"
        "S.activeBot=S.bots[0]?S.bots[0].id:null;save();renderAll();}});}")
    html = "\n".join(lines)

    # 4. Templates fallback: the starters fetch at the end of the script.
    old_tpl = ("fetch('/hamkar/api/starters').then(r=>r.json())"
               ".then(d=>{window._templates=d.bots||[];renderTemplates();}).catch(()=>{});")
    new_tpl = ("fetch('/hamkar/api/starters').then(r=>r.json())"
               ".then(d=>{window._templates=d.bots||[];renderTemplates();})"
               ".catch(()=>{window._templates=window.HAMKAR_STARTERS||[];renderTemplates();});")
    html = replace_once(html, old_tpl, new_tpl, "templates fetch")

    # 5. Inline the starter data before the app script (exactly one <script>).
    assert html.count("<script>") == 1, "unexpected <script> count"
    starters_js = ("<script>window.HAMKAR_STARTERS="
                   + json.dumps(STARTER_BOTS, ensure_ascii=False) + ";</script>")
    html = html.replace("<script>", starters_js + "<script>", 1)

    # Markers that must survive.
    for m in ["hamkar-v2", "Tehqeeq", "HAMKAR_STARTERS",
              "AI: off on static hosting", "aistatus", "localStorage"]:
        assert m in html, f"marker missing: {m}"

    outdir = os.path.join(HERE, "static-build")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {out} ({len(html)} bytes, {len(STARTER_BOTS)} starters inlined)")


if __name__ == "__main__":
    main()
