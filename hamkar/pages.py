# -*- coding: utf-8 -*-
"""Hamkar single-page app (HTML + JS, one string).

All state lives in the user's browser (localStorage, key hamkar-v1).
The server is stateless; AI calls go to /hamkar/api/*.
"""

HAMKAR_HTML = r'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hamkar — AI Teammates (ہمراہ کار)</title>
<style>
*{box-sizing:border-box} body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;margin:0;background:#0f172a;color:#e2e8f0}
header{background:#1e293b;padding:14px 18px;border-bottom:1px solid #334155}
header h1{margin:0;font-size:22px} header h1 span{color:#38bdf8}
header p{margin:4px 0 0;color:#94a3b8;font-size:13px}
.badge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:12px;background:#14532d;color:#bbf7d0}
.badge.off{background:#7f1d1d;color:#fecaca}
.wrap{display:grid;grid-template-columns:250px 1fr 300px;gap:12px;padding:12px;max-width:1400px;margin:0 auto}
@media(max-width:900px){.wrap{grid-template-columns:1fr}}
.card{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:12px;margin-bottom:12px}
.card h2{margin:0 0 8px;font-size:15px;color:#7dd3fc}
.card h3{margin:10px 0 6px;font-size:13px;color:#94a3b8}
button{background:#0284c7;color:#fff;border:0;border-radius:6px;padding:7px 12px;cursor:pointer;font-size:13px}
button.ghost{background:#334155} button.danger{background:#b91c1c} button.ok{background:#15803d}
button:disabled{opacity:.5;cursor:default}
input,select,textarea{width:100%;background:#0f172a;color:#e2e8f0;border:1px solid #475569;border-radius:6px;padding:7px;margin:4px 0;font-size:13px}
textarea{min-height:64px}
.botitem{padding:8px;border-radius:8px;cursor:pointer;margin-bottom:6px;border:1px solid transparent}
.botitem:hover{background:#273449}.botitem.on{background:#0c4a6e;border-color:#0284c7}
.botitem b{font-size:14px}.botitem small{display:block;color:#94a3b8}
#chat{height:52vh;overflow-y:auto;border:1px solid #334155;border-radius:8px;padding:10px;background:#0f172a}
.msg{margin:8px 0;padding:8px 10px;border-radius:8px;max-width:92%;white-space:pre-wrap;line-height:1.5;font-size:14px}
.msg.user{background:#0c4a6e;margin-left:auto}.msg.bot{background:#1e293b}
.msg .who{font-size:11px;color:#7dd3fc;display:block;margin-bottom:3px}
.msg .act{font-size:11px;color:#fbbf24;display:block;margin-top:5px}
.row{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.row>*{flex:1}.row button{flex:0 0 auto}
.note{font-size:12px;color:#94a3b8;line-height:1.5}
.pill{display:inline-block;background:#334155;border-radius:999px;padding:2px 8px;font-size:11px;margin:2px}
.appr{border:1px solid #475569;border-radius:8px;padding:8px;margin-bottom:8px}
.appr pre{white-space:pre-wrap;font-size:12px;background:#0f172a;padding:8px;border-radius:6px;max-height:180px;overflow:auto}
.log{font-size:12px;color:#cbd5e1}.log div{border-bottom:1px solid #273449;padding:5px 0}
.kbd{font-size:11px;color:#94a3b8}
details{margin:6px 0} summary{cursor:pointer;color:#7dd3fc;font-size:13px}
</style></head><body>
<header><h1>Hamkar <span>ہمراہ کار</span> — AI Teammates</h1>
<p>Named AI Bots with roles, memory, Skills, scheduled Routines, handoffs and an approval queue. Free, no account, no card. <span id="aistatus" class="badge off">AI: checking…</span></p>
<p class="note">Honest limits: AI replies need the owner's Gemini key (free quota). Without it, Bots, Skills, Routines, memory, chat history and export/import still work. Routines run while this page is open — there is no server cron. A Bot only <b>proposes</b> actions; nothing is ever sent, deleted or published without your approval.</p></header>
<div class="wrap">
<div>
  <div class="card"><h2>🤖 My Bots</h2><div id="botlist"></div>
    <h3>New Bot</h3>
    <input id="nb-name" placeholder="Name, e.g. Sehat">
    <input id="nb-role" placeholder="Role, e.g. Health Bot">
    <textarea id="nb-inst" placeholder="Instructions — what this Bot does, in 1–2 lines"></textarea>
    <div class="row"><select id="nb-lang"><option value="en">English</option><option value="roman">Roman Urdu</option><option value="ur">Urdu</option></select>
    <button onclick="addBot()">+ Add Bot</button></div>
    <h3>Team share</h3>
    <div class="row"><button class="ghost" onclick="exportBot()">Export active Bot</button>
    <button class="ghost" onclick="document.getElementById('impfile').click()">Import Bot</button></div>
    <input type="file" id="impfile" accept=".json" style="display:none" onchange="importBot(event)">
    <p class="note">Export a Bot as JSON and share it with your team — they import the same teammate. (Grok Bot's Team Bots, free version.)</p>
  </div>
  <div class="card"><h2>🧠 Memory card</h2>
    <p class="note">What <b id="memname">—</b> remembers. You can see and edit everything — nothing hidden.</p>
    <textarea id="memory" rows="4" placeholder="Facts the Bot should remember…"></textarea>
    <div class="row"><button class="ghost" onclick="saveMemory()">Save memory</button>
    <button class="ghost" onclick="summarizeChat()">✨ Summarise chat → memory</button></div>
  </div>
</div>
<div>
  <div class="card"><h2>💬 <span id="chattitle">Chat</span></h2>
    <div class="row" style="margin-bottom:6px">
      <select id="skillpick" title="Skill"><option value="">Skill: none</option></select>
      <label class="kbd"><input type="checkbox" id="voice" style="width:auto"> 🔊 Read replies aloud</label>
      <label class="kbd"><input type="checkbox" id="pastetoggle" style="width:auto" onchange="document.getElementById('pastebox').style.display=this.checked?'block':'none'"> 📋 Paste text for the Bot</label>
    </div>
    <div id="pastebox" style="display:none"><textarea id="pasted" placeholder="Paste an email, article or notes here — the Bot will work on this text. (This is the honest version of a connector: no logins, your text stays in your browser.)"></textarea></div>
    <div id="chat"></div>
    <div class="row" style="margin-top:8px">
      <input id="msg" placeholder="Message… (start with @BotName to hand it to another Bot)" onkeydown="if(event.key==='Enter')sendMsg()">
      <button onclick="sendMsg()">Send</button>
    </div>
    <div class="row" style="margin-top:6px">
      <button class="ghost" onclick="suggestWork()">💡 Suggest work</button>
      <button class="ghost" onclick="proposeAction()">✍️ Propose action…</button>
      <select id="handoffto" title="Hand off to…"></select>
      <button class="ghost" onclick="handoff()">↗️ Hand off</button>
    </div>
    <div id="suggest" style="margin-top:8px"></div>
  </div>
  <div class="card"><h2>✅ Approval queue</h2>
    <p class="note">Bots propose drafts and plans here. Nothing is sent or done until you approve it.</p>
    <div id="approvals"></div>
  </div>
</div>
<div>
  <div class="card"><h2>⏰ Routines</h2>
    <p class="note">Plain-language scheduled jobs, e.g. “weekdays 08:00 — news sweep”. They run while this page stays open (checked every 30 seconds).</p>
    <input id="rt-name" placeholder="Routine name, e.g. Morning sweep">
    <input id="rt-sched" placeholder="Schedule: daily 08:00 / weekdays 08:00 / monday 10:30 / manual">
    <textarea id="rt-task" placeholder="Task in plain words…"></textarea>
    <div class="row"><select id="rt-bot"></select><button onclick="addRoutine()">+ Add routine</button></div>
    <div id="routines"></div>
    <h3>Run log</h3><div id="runlog" class="log"></div>
  </div>
  <div class="card"><h2>🎓 Skills — teach a task</h2>
    <p class="note">A Skill is your preferred way of doing a task, saved as steps. Pick it in the chat bar and the Bot follows it.</p>
    <input id="sk-name" placeholder="Skill name, e.g. Morning news brief">
    <textarea id="sk-steps" placeholder="Steps, one per line"></textarea>
    <button onclick="addSkill()">+ Save skill</button>
    <div id="skills"></div>
  </div>
</div>
</div>
<script>
const KEY='hamkar-v1';
let S=null;
function blank(){return {bots:[],activeBot:null,chats:{},memory:{},summaries:{},skills:[],routines:[],approvals:[],runlog:[],lang:'en'};}
function save(){localStorage.setItem(KEY,JSON.stringify(S));}
function load(){try{S=JSON.parse(localStorage.getItem(KEY))||blank();}catch(e){S=blank();}
  if(!S.bots)S=blank();
  if(!S.bots.length){fetch('/hamkar/api/starters').then(r=>r.json()).then(d=>{S.bots=d.bots||[];S.activeBot=S.bots[0]?S.bots[0].id:null;save();renderAll();}).catch(()=>{});}
  renderAll();}
function bot(id){return S.bots.find(b=>b.id===id);}
function active(){return bot(S.activeBot)||S.bots[0];}
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
async function api(path,body){const r=await fetch('/hamkar/api/'+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body||{})});return r.json();}
function renderAll(){renderBots();renderChat();renderSkills();renderRoutines();renderApprovals();renderLog();
  document.getElementById('memory').value=S.memory[S.activeBot]||'';
  const a=active(); document.getElementById('memname').textContent=a?a.name:'—';
  document.getElementById('chattitle').textContent=a?('Chat — '+a.emoji+' '+a.name+' ('+a.role+')'):'Chat';}
function renderBots(){const el=document.getElementById('botlist');el.innerHTML='';
  S.bots.forEach(b=>{const d=document.createElement('div');d.className='botitem'+(b.id===S.activeBot?' on':'');
    d.innerHTML='<b>'+esc(b.emoji+' '+b.name)+'</b><small>'+esc(b.role)+' · '+esc(b.language)+'</small>';
    d.onclick=()=>{S.activeBot=b.id;save();renderAll();};el.appendChild(d);});
  const hb=document.getElementById('handoffto');hb.innerHTML='<option value="">Hand off to…</option>';
  S.bots.forEach(b=>{if(b.id!==S.activeBot)hb.innerHTML+='<option value="'+esc(b.id)+'">'+esc(b.name)+'</option>';});
  const rb=document.getElementById('rt-bot');rb.innerHTML='';S.bots.forEach(b=>{rb.innerHTML+='<option value="'+esc(b.id)+'">'+esc(b.name)+'</option>';});}
function renderChat(){const el=document.getElementById('chat');const a=active();el.innerHTML='';
  const turns=S.chats[S.activeBot]||[];
  if(!turns.length)el.innerHTML='<p class="note">No messages yet. Give '+esc(a?a.name:'this Bot')+' a job — or pick a Skill above.</p>';
  turns.forEach(t=>{const d=document.createElement('div');d.className='msg '+(t.role==='user'?'user':'bot');
    d.innerHTML='<span class="who">'+esc(t.role==='user'?'You':(a?a.name:'Bot'))+'</span>'+esc(t.text);
    if(t.action)d.innerHTML+='<span class="act">📋 Action proposed → see Approval queue</span>';
    el.appendChild(d);});
  el.scrollTop=el.scrollHeight;}
function addBot(){const name=document.getElementById('nb-name').value.trim();
  const role=document.getElementById('nb-role').value.trim();
  const inst=document.getElementById('nb-inst').value.trim();
  const lang=document.getElementById('nb-lang').value;
  if(name.length<2||inst.length<10){alert('Name (2+ chars) and instructions (10+ chars) needed.');return;}
  const id=name.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')||('bot-'+Date.now());
  if(bot(id)){alert('A Bot with that name already exists.');return;}
  if(S.bots.length>=20){alert('Max 20 Bots.');return;}
  S.bots.push({id,name,emoji:'🤖',role:role||'Teammate',instructions:inst,language:lang});
  S.activeBot=id;save();renderAll();
  document.getElementById('nb-name').value='';document.getElementById('nb-role').value='';document.getElementById('nb-inst').value='';}
function saveMemory(){S.memory[S.activeBot]=document.getElementById('memory').value.slice(0,1000);save();alert('Memory saved.');}
function pushTurn(bid,role,text,action){(S.chats[bid]=S.chats[bid]||[]).push({role,text,action:!!action});S.chats[bid]=S.chats[bid].slice(-40);save();}
function speak(t){if(!document.getElementById('voice').checked||!('speechSynthesis'in window))return;
  try{speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(t);u.lang='en-US';speechSynthesis.speak(u);}catch(e){}}
async function sendMsg(){const inp=document.getElementById('msg');let text=inp.value.trim();if(!text)return;
  let target=active();
  const m=text.match(/^\s*@(.+)/);
  if(m){const rest=m[1];let found=null;
    S.bots.forEach(b=>{if(rest.toLowerCase().startsWith(b.name.toLowerCase())&&(rest.length===b.name.length||/\s/.test(rest[b.name.length]))){if(!found||b.name.length>found.name.length)found=b;}});
    if(found){target=found;S.activeBot=found.id;text=rest.slice(found.name.length).trim();}}
  if(!text){inp.value='';return;}
  const skillId=document.getElementById('skillpick').value;
  const skill=skillId?(S.skills.find(s=>s.id===skillId)||null):null;
  const pasted=document.getElementById('pastetoggle').checked?document.getElementById('pasted').value.trim():null;
  pushTurn(target.id,'user',text);inp.value='';renderChat();
  const res=await api('chat',{bot:target,memory:S.memory[target.id]||'',summary:S.summaries[target.id]||'',history:S.chats[target.id]||[],message:text,skill,pasted_text:pasted||null,language:target.language||'en'});
  if(!res.ok){pushTurn(target.id,'bot','⚠️ '+res.error);renderChat();return;}
  pushTurn(target.id,'bot',res.reply,!!res.action);
  (res.remember||[]).forEach(f=>{const cur=S.memory[target.id]||'';if(cur.indexOf(f)<0)S.memory[target.id]=(cur?cur+'\n':'')+f;});
  if(res.action)addApproval(target,res.action);
  save();renderAll();speak(res.reply);}
async function summarizeChat(){const a=active();const turns=S.chats[a.id]||[];
  if(turns.length<2){alert('Summarise ke liye kam se kam 2 messages chahiye.');return;}
  const res=await api('summarize',{bot:a,turns,language:a.language||'en'});
  if(!res.ok){alert(res.error);return;}
  S.summaries[a.id]=res.summary;save();alert('Summary saved into memory notes.');}
async function suggestWork(){const a=active();
  const res=await api('suggest',{bot:a,summary:S.summaries[a.id]||'',history:S.chats[a.id]||[],language:a.language||'en'});
  const el=document.getElementById('suggest');
  if(!res.ok){el.innerHTML='<p class="note">⚠️ '+esc(res.error)+'</p>';return;}
  el.innerHTML='<h3>💡 Suggested work</h3>'+res.suggestions.map((s,i)=>'<div class="appr"><b>'+esc(s.title)+'</b><p class="note">'+esc(s.detail||'')+'</p><button onclick="doSuggestion('+i+')">Do it</button></div>').join('');
  window._sug=res.suggestions;}
function doSuggestion(i){const s=(window._sug||[])[i];if(!s)return;document.getElementById('msg').value=s.title+': '+s.detail;sendMsg();}
async function proposeAction(){const a=active();
  const inst=prompt('What should '+a.name+' draft? (e.g. "a follow-up email to the clinic about the demo")');
  if(!inst||inst.trim().length<5)return;
  const res=await api('action',{bot:a,memory:S.memory[a.id]||'',summary:S.summaries[a.id]||'',history:S.chats[a.id]||[],instruction:inst,language:a.language||'en'});
  if(!res.ok){alert(res.error);return;}
  addApproval(a,res.action);alert('Draft added to the Approval queue.');}
function addApproval(b,action){S.approvals.unshift({id:'ap'+Date.now()+Math.floor(Math.random()*999),bot:b.name,type:action.type,title:action.title,body:action.body,status:'pending',ts:new Date().toISOString()});save();renderApprovals();}
function renderApprovals(){const el=document.getElementById('approvals');el.innerHTML='';
  if(!S.approvals.length){el.innerHTML='<p class="note">No proposals yet.</p>';return;}
  S.approvals.slice(0,10).forEach(ap=>{const d=document.createElement('div');d.className='appr';
    d.innerHTML='<b>'+esc(ap.title)+'</b> <span class="pill">'+esc(ap.type)+'</span> <span class="pill">'+esc(ap.bot)+'</span> <span class="pill">'+esc(ap.status)+'</span><pre>'+esc(ap.body)+'</pre>';
    if(ap.status==='pending'){d.innerHTML+='<div class="row"><button class="ok" onclick="decideAppr(\''+ap.id+'\',\'approved\')">✓ Approve</button><button class="danger" onclick="decideAppr(\''+ap.id+'\',\'rejected\')">✕ Reject</button></div>';}
    else if(ap.status==='approved'){d.innerHTML+='<button class="ghost" onclick="copyAppr(\''+ap.id+'\')">📋 Copy text</button>';}
    el.appendChild(d);});}
function decideAppr(id,st){const ap=S.approvals.find(x=>x.id===id);if(ap){ap.status=st;save();renderApprovals();}}
function copyAppr(id){const ap=S.approvals.find(x=>x.id===id);if(ap&&navigator.clipboard)navigator.clipboard.writeText(ap.body).then(()=>alert('Copied.')); }
async function handoff(){const to=document.getElementById('handoffto').value;if(!to)return;
  const a=active();
  const res=await api('handoff',{source_bot:a,summary:S.summaries[a.id]||'',history:S.chats[a.id]||[]});
  if(!res.ok){alert(res.error);return;}
  const tb=bot(to);pushTurn(to,'bot','📥 Handoff from '+a.name+':\n'+res.brief);
  S.activeBot=to;save();renderAll();}
function renderSkills(){const el=document.getElementById('skills');el.innerHTML='';
  const sel=document.getElementById('skillpick');const cur=sel.value;sel.innerHTML='<option value="">Skill: none</option>';
  S.skills.forEach(s=>{sel.innerHTML+='<option value="'+esc(s.id)+'">'+esc(s.name)+'</option>';
    const d=document.createElement('div');d.className='appr';
    d.innerHTML='<b>'+esc(s.name)+'</b><p class="note">'+s.steps.map((st,i)=>esc((i+1)+'. '+st)).join('<br>')+'</p><button class="danger" onclick="delSkill(\''+s.id+'\')">Delete</button>';
    el.appendChild(d);});
  sel.value=cur;}
function addSkill(){const name=document.getElementById('sk-name').value.trim();
  const steps=document.getElementById('sk-steps').value.split('\n').map(s=>s.trim()).filter(Boolean);
  if(name.length<2||!steps.length){alert('Skill name + at least 1 step needed.');return;}
  if(S.skills.length>=50){alert('Max 50 Skills.');return;}
  const id=name.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')||('sk-'+Date.now());
  S.skills.push({id,name,steps:steps.slice(0,20)});save();renderSkills();
  document.getElementById('sk-name').value='';document.getElementById('sk-steps').value='';}
function delSkill(id){S.skills=S.skills.filter(s=>s.id!==id);save();renderSkills();}
function renderRoutines(){const el=document.getElementById('routines');el.innerHTML='';
  if(!S.routines.length){el.innerHTML='<p class="note">No routines yet.</p>';return;}
  S.routines.forEach(r=>{const b=bot(r.bot_id);const d=document.createElement('div');d.className='appr';
    d.innerHTML='<b>'+esc(r.name)+'</b> <span class="pill">'+esc(r.schedule)+'</span> <span class="pill">'+esc(b?b.name:r.bot_id)+'</span> <span class="pill">'+(r.enabled?'on':'off')+'</span><p class="note">'+esc(r.task)+'</p>';
    d.innerHTML+='<div class="row"><button onclick="runRoutineNow(\''+r.id+'\')">▶ Run now</button><button class="ghost" onclick="toggleRoutine(\''+r.id+'\')">'+(r.enabled?'Pause':'Resume')+'</button><button class="danger" onclick="delRoutine(\''+r.id+'\')">Delete</button></div>';
    el.appendChild(d);});}
function addRoutine(){const name=document.getElementById('rt-name').value.trim();
  const sched=document.getElementById('rt-sched').value.trim().toLowerCase();
  const task=document.getElementById('rt-task').value.trim();
  const bid=document.getElementById('rt-bot').value;
  if(name.length<2||task.length<5){alert('Routine name + task needed.');return;}
  if(!/^(manual|daily|weekdays|weekends|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+\d{1,2}:\d{2}$/.test(sched)&&sched!=='manual'){alert("Schedule like 'daily 08:00', 'weekdays 08:00', 'monday 10:30' or 'manual'.");return;}
  if(S.routines.length>=50){alert('Max 50 Routines.');return;}
  const id=name.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')||('rt-'+Date.now());
  const kind=sched==='manual'?'manual':sched.split(' ')[0];
  const time=sched==='manual'?'':sched.split(' ')[1];
  S.routines.push({id,name,bot_id:bid,task,schedule:sched,kind,time,enabled:true});
  save();renderRoutines();
  document.getElementById('rt-name').value='';document.getElementById('rt-sched').value='';document.getElementById('rt-task').value='';}
function toggleRoutine(id){const r=S.routines.find(x=>x.id===id);if(r){r.enabled=!r.enabled;save();renderRoutines();}}
function delRoutine(id){S.routines=S.routines.filter(x=>x.id!==id);save();renderRoutines();}
async function runRoutineNow(id){const r=S.routines.find(x=>x.id===id);if(!r)return;
  const b=bot(r.bot_id)||active();if(!b){alert('Bot not found.');return;}
  const res=await api('routine',{bot:b,routine:r,language:b.language||'en'});
  const line={ts:new Date().toISOString(),routine:r.name,ok:!!res.ok,result:res.ok?res.reply:res.error};
  S.runlog.unshift(line);S.runlog=S.runlog.slice(0,20);
  if(res.ok){pushTurn(b.id,'bot','⏰ Routine "'+r.name+'":\n'+res.reply,!!res.action);
    (res.remember||[]).forEach(f=>{const cur=S.memory[b.id]||'';if(cur.indexOf(f)<0)S.memory[b.id]=(cur?cur+'\n':'')+f;});
    if(res.action)addApproval(b,res.action);}
  save();renderAll();}
function renderLog(){const el=document.getElementById('runlog');el.innerHTML='';
  if(!S.runlog.length){el.innerHTML='<p class="note">No runs yet.</p>';return;}
  S.runlog.forEach(l=>{const d=document.createElement('div');
    d.innerHTML='<b>'+esc(l.routine)+'</b> · '+esc(new Date(l.ts).toLocaleString())+' · '+(l.ok?'✅':'⚠️')+'<br>'+esc(l.result).slice(0,200);
    el.appendChild(d);});}
function exportBot(){const a=active();if(!a)return;
  const blob=new Blob([JSON.stringify(a,null,2)],{type:'application/json'});
  const u=URL.createObjectURL(blob);const link=document.createElement('a');
  link.href=u;link.download=a.id+'.bot.json';link.click();URL.revokeObjectURL(u);}
function importBot(ev){const f=ev.target.files[0];if(!f)return;
  const rd=new FileReader();
  rd.onload=()=>{try{const b=JSON.parse(rd.result);
      if(!b.name||!b.instructions||b.instructions.length<10){alert('That file is not a valid Bot.');return;}
      if(bot(b.id)){b.id=b.id+'-'+Date.now();}
      S.bots.push({id:String(b.id).slice(0,40),name:String(b.name).slice(0,40),emoji:(b.emoji||'🤖').slice(0,4),role:String(b.role||'Teammate').slice(0,80),instructions:String(b.instructions).slice(0,1500),language:['en','roman','ur'].includes(b.language)?b.language:'en'});
      S.activeBot=S.bots[S.bots.length-1].id;save();renderAll();alert('Bot imported: '+b.name);
    }catch(e){alert('Could not read that file.');}};
  rd.readAsText(f);ev.target.value='';}
// Scheduler: routines fire while this page is open (checked every 30s).
const _fired={};
setInterval(()=>{const now=new Date();const hhmm=now.toTimeString().slice(0,5);const wd=now.getDay();
  S.routines.forEach(r=>{if(!r.enabled||r.kind==='manual'||!r.time)return;
    const days=r.kind==='daily'?[0,1,2,3,4,5,6]:r.kind==='weekdays'?[1,2,3,4,5]:r.kind==='weekends'?[0,6]:[['sunday','monday','tuesday','wednesday','thursday','friday','saturday'].indexOf(r.kind)];
    if(days.indexOf(wd)<0||r.time!==hhmm)return;
    const key=r.id+'-'+now.toDateString()+'-'+hhmm;
    if(_fired[key])return;_fired[key]=1;runRoutineNow(r.id);});
},30000);
fetch('/hamkar/api/ai-status').then(r=>r.json()).then(d=>{const el=document.getElementById('aistatus');
  el.textContent=d.ai_available?'AI: ready (Gemini)':'AI: key not set — Bots & tools still work';
  el.className='badge'+(d.ai_available?'':' off');}).catch(()=>{});
load();
</script></body></html>
'''
