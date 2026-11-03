'use strict';

const PAGES=['dashboard','hardware','inventory','ai','security','users','lab'];
const PAGE_META={
  dashboard:['Overview','Two fridges, live'],
  hardware:['Hardware','ESP32 node, wired up'],
  inventory:['Inventory','Batches and heat budget'],
  ai:['Forecast','30-minute breach forecast'],
  security:['Security','Signatures, replay protection, hash chain'],
  users:['Users','Accounts and roles'],
  lab:['Scenarios','Trigger faults on the simulated nodes'],
};

const state={
  token:sessionStorage.getItem('coldchain_token')||'',
  user:null,
  data:null,
  page:'dashboard',
  history:{},
  range:Number(localGet('cc_range'))||360,
  hover:{},
  inv:{q:'',status:'all',fridge:'all',sort:'name',dir:1},
  issues:new Map(),
  firstIssues:true,
  sound:localGet('cc_sound')==='1',
  aiReport:null,
  skew:0,
  refreshing:false,
};

// Stroke icons (24px grid, 1.6 stroke) used instead of emoji so they render the same on every OS.
const IC={
  grid:'<rect x="3.5" y="3.5" width="7" height="7" rx="1"/><rect x="13.5" y="3.5" width="7" height="7" rx="1"/><rect x="3.5" y="13.5" width="7" height="7" rx="1"/><rect x="13.5" y="13.5" width="7" height="7" rx="1"/>',
  chip:'<rect x="6" y="6" width="12" height="12" rx="1.5"/><rect x="9.5" y="9.5" width="5" height="5"/><path d="M9 2.5v3.5M15 2.5v3.5M9 18v3.5M15 18v3.5M2.5 9H6M2.5 15H6M18 9h3.5M18 15h3.5"/>',
  box:'<path d="M3.5 7.5 12 3l8.5 4.5v9L12 21l-8.5-4.5z"/><path d="M3.5 7.5 12 12l8.5-4.5M12 12v9"/>',
  spark:'<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6.3 6.3l2.4 2.4M15.3 15.3l2.4 2.4M6.3 17.7l2.4-2.4M15.3 8.7l2.4-2.4"/>',
  shield:'<path d="M12 3 4.5 6v5.5c0 4.6 3.2 8.1 7.5 9.5 4.3-1.4 7.5-4.9 7.5-9.5V6z"/><path d="m8.8 12 2.2 2.2 4.2-4.4"/>',
  users:'<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.6-3.6 3.2-5.5 6.5-5.5s5.9 1.9 6.5 5.5"/><path d="M15.5 4.8a3.3 3.3 0 0 1 0 6.4M18 14.8c2 .7 3.2 2.4 3.5 5.2"/>',
  flask:'<path d="M9 3h6M10 3v6L4.5 18.5A1.6 1.6 0 0 0 5.9 21h12.2a1.6 1.6 0 0 0 1.4-2.5L14 9V3"/><path d="M7.5 14h9"/>',
  bell:'<path d="M6 16.5V11a6 6 0 0 1 12 0v5.5l1.5 2h-15z"/><path d="M10 20.5a2.2 2.2 0 0 0 4 0"/>',
  logout:'<path d="M14 4h4.5A1.5 1.5 0 0 1 20 5.5v13a1.5 1.5 0 0 1-1.5 1.5H14"/><path d="M10 8l-4 4 4 4M6 12h10"/>',
  search:'<circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/>',
  thermo:'<path d="M10 14.5V5a2 2 0 0 1 4 0v9.5a4 4 0 1 1-4 0z"/><path d="M12 9v8"/>',
  door:'<path d="M5 21V3.5h11V21M3 21h18"/><circle cx="13" cy="12.5" r=".9" fill="currentColor"/>',
  plug:'<path d="M9 3v5M15 3v5M6.5 8h11v3a5.5 5.5 0 0 1-11 0zM12 16.5V21"/>',
  battery:'<rect x="2.5" y="7" width="17" height="10" rx="1.5"/><path d="M21.5 10.5v3"/>',
  fan:'<circle cx="12" cy="12" r="1.6"/><path d="M12 10.4C11 6.5 12 3.5 15 3.5c2.4 0 2.6 3.3-1.4 7.4M13.6 12c3.9-1 6.9 0 6.9 3 0 2.4-3.3 2.6-7.4-1.4M12 13.6c1 3.9 0 6.9-3 6.9-2.4 0-2.6-3.3 1.4-7.4M10.4 12c-3.9 1-6.9 0-6.9-3 0-2.4 3.3-2.6 7.4 1.4"/>',
  wifi:'<path d="M2.5 9a14 14 0 0 1 19 0M5.5 12.5a9.5 9.5 0 0 1 13 0M8.6 15.8a5 5 0 0 1 6.8 0"/><circle cx="12" cy="19" r="1" fill="currentColor"/>',
  wifioff:'<path d="M3 3l18 18M8.6 15.8a5 5 0 0 1 6.8 0M5.5 12.5a9.5 9.5 0 0 1 4-2.3M2.5 9a14 14 0 0 1 5.2-3.1M14.5 10.4a9.5 9.5 0 0 1 4 2.1M12.6 5.5A14 14 0 0 1 21.5 9"/><circle cx="12" cy="19" r="1" fill="currentColor"/>',
  alert:'<path d="M12 4 2.8 19.5h18.4z"/><path d="M12 10v4.5"/><circle cx="12" cy="17" r=".9" fill="currentColor"/>',
  check:'<path d="m5 12.5 4.5 4.5L19 7.5"/>',
  x:'<path d="M6 6l12 12M18 6 6 18"/>',
  chain:'<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1.2 1.2"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1.2-1.2"/>',
  key:'<circle cx="8" cy="15" r="4.5"/><path d="m11.2 11.8 8.3-8.3M16.5 6.5l2.5 2.5M14 9l2 2"/>',
  reset:'<path d="M4 12a8 8 0 1 0 2.4-5.7M4 4v4.5h4.5"/>',
  arrow:'<path d="M4 12h15M14 6.5l5.5 5.5-5.5 5.5"/>',
  print:'<path d="M7 9V3.5h10V9M7 17.5H4.5v-7A1.5 1.5 0 0 1 6 9h12a1.5 1.5 0 0 1 1.5 1.5v7H17"/><rect x="7" y="14" width="10" height="6.5"/>',
  copy:'<rect x="8.5" y="8.5" width="12" height="12" rx="1.5"/><path d="M15.5 8.5V5A1.5 1.5 0 0 0 14 3.5H5A1.5 1.5 0 0 0 3.5 5v9A1.5 1.5 0 0 0 5 15.5h3.5"/>',
  external:'<path d="M14 3.5h6.5V10M20.5 3.5 11 13M18 14v5a1.5 1.5 0 0 1-1.5 1.5H5A1.5 1.5 0 0 1 3.5 19V7.5A1.5 1.5 0 0 1 5 6h5"/>',
  snow:'<path d="M12 2.5v19M3.8 7.3l16.4 9.4M3.8 16.7l16.4-9.4M9.5 4.5 12 7l2.5-2.5M9.5 19.5 12 17l2.5 2.5"/>',
  gauge:'<path d="M3.5 17a8.5 8.5 0 1 1 17 0"/><path d="m12 17 4-5.5"/>',
  sound:'<path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path d="M15.5 9a4.2 4.2 0 0 1 0 6M18.3 6.5a8 8 0 0 1 0 11"/>',
  cross:'<path d="M12 4v16M4 12h16"/>',
  plus:'<path d="M12 5v14M5 12h14"/>',
  power:'<path d="M12 3v8"/><path d="M6.6 6.6a7.5 7.5 0 1 0 10.8 0"/>',
  sun:'<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M4.6 4.6 6 6M18 18l1.4 1.4M2.5 12h2M19.5 12h2M4.6 19.4 6 18M18 6l1.4-1.4"/>',
  moon:'<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/>',
  user:'<circle cx="12" cy="8" r="4"/><path d="M4 20.5c.8-4 4-6 8-6s7.2 2 8 6"/>',
  lock:'<rect x="5" y="10.5" width="14" height="10" rx="2"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3"/>',
  heat:'<path d="M8 20c-1.5-2 1.5-4 0-6s1.5-4 0-6M12 20c-1.5-2 1.5-4 0-6s1.5-4 0-6M16 20c-1.5-2 1.5-4 0-6s1.5-4 0-6"/>',
};
const icon=(name,cls='')=>`<svg class="ic ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${IC[name]||''}</svg>`;
function hydrateIcons(root=document){root.querySelectorAll('[data-ic]').forEach(el=>{if(!el.__ic){el.innerHTML=icon(el.dataset.ic);el.__ic=1;}});}

function localGet(k){try{return localStorage.getItem(k);}catch{return null;}}
function localSet(k,v){try{localStorage.setItem(k,v);}catch{}}

const $=id=>document.getElementById(id);
const $$=sel=>Array.from(document.querySelectorAll(sel));
const esc=v=>String(v??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const roleLabel=role=>({Admin:'Administrator',Pharmacist:'Pharmacist',Inspector:'Inspector'})[role]||role||'User';
const fridgeLabel=id=>id==='FRIDGE_A'?'Fridge Alpha':id==='FRIDGE_B'?'Fridge Beta':id;
const fmtTemp=v=>v==null?'—':`${Number(v).toFixed(1)}°C`;
const fmtPct=v=>v==null?'—':`${Number(v).toFixed(0)}%`;
const fmtTime=v=>!v?'—':new Date(v).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'});
const fmtDateTime=v=>!v?'—':new Date(v).toLocaleString([], {month:'short',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit'});
const fmtDate=v=>!v?'—':new Date(v+'T00:00:00').toLocaleDateString([], {year:'numeric',month:'short',day:'2-digit'});
const statusClass=s=>s==='Discard'?'danger':s==='At Risk'?'warning':'safe';
const serverNow=()=>Date.now()-state.skew;
const isRole=(...roles)=>state.user && roles.includes(state.user.role);
const canEdit=()=>isRole('Admin','Pharmacist');

function ago(iso){
  if(!iso) return 'never';
  const s=Math.max(0,Math.round((serverNow()-new Date(iso).getTime())/1000));
  if(s<60) return `${s}s ago`;
  if(s<3600) return `${Math.floor(s/60)}m ago`;
  return `${Math.floor(s/3600)}h ago`;
}
function fmtDur(sec){if(sec<60) return `${sec}s`;if(sec<3600) return `${Math.floor(sec/60)}m ${String(sec%60).padStart(2,'0')}s`;return `${Math.floor(sec/3600)}h ${String(Math.floor(sec%3600/60)).padStart(2,'0')}m`;}
function daysUntil(dateStr){return Math.round((new Date(dateStr+'T00:00:00')-new Date(new Date().toDateString()))/86400000);}

// Only touch the DOM when content actually changed, which avoids flicker and keeps focus/hover.
function setHTML(el,html){
  if(!el || el.__html===html) return;
  // Entry animations only on a container's first fill; later refreshes swap content without replaying them.
  const first=el.__html===undefined;
  el.innerHTML=html;el.__html=html;
  if(first){el.classList.add('enter');setTimeout(()=>el.classList.remove('enter'),900);}
}
// For lists with buttons: hold live updates while the pointer or focus is inside, so a click is
// never lost to a re-render. The next refresh after the pointer leaves applies the update.
function setLiveHTML(el,html){
  if(!el) return;
  if(!state.force && el.__html!==undefined && (el.matches(':hover')||el.contains(document.activeElement)&&document.activeElement!==document.body)) return;
  setHTML(el,html);
}

async function api(path,options={}){
  const headers={...(options.body?{'Content-Type':'application/json'}:{}),...(state.token?{Authorization:'Bearer '+state.token}:{}),...(options.headers||{})};
  let response;
  try{response=await fetch(path,{...options,headers});}
  catch{throw new Error('Cannot reach the ColdChain server. Check that it is running.');}
  if(!response.ok){
    let detail=`Request failed (${response.status})`;
    try{
      const body=await response.json();
      if(typeof body.detail==='string') detail=body.detail;
      else if(Array.isArray(body.detail)) detail=body.detail.map(d=>`${(d.loc||[]).slice(-1)[0]}: ${d.msg}`).join('; ');
    }catch{}
    if(response.status===401 && path!=='/api/auth/login'){
      logout();
      throw new Error('Your session has expired. Please sign in again.');
    }
    throw new Error(detail);
  }
  const ctype=response.headers.get('content-type')||'';
  return ctype.includes('application/json')?response.json():response;
}

/* ---------- toasts ---------- */
function toast(message,kind='info'){
  const el=document.createElement('div');
  el.className=`toast ${kind}`;
  el.setAttribute('role',kind==='error'||kind==='danger'?'alert':'status');
  const ms=kind==='danger'?7000:4200;
  el.innerHTML=`<span class="toast-ico">${icon(kind==='error'||kind==='danger'?'alert':kind==='success'?'check':'bell')}</span><span>${esc(message)}</span><i class="toast-bar" style="animation-duration:${ms}ms"></i>`;
  el.addEventListener('click',()=>{el.classList.remove('show');setTimeout(()=>el.remove(),300);});
  $('toasts').appendChild(el);
  requestAnimationFrame(()=>el.classList.add('show'));
  setTimeout(()=>{el.classList.remove('show');setTimeout(()=>el.remove(),300);},ms);
}

function beep(){
  if(!state.sound) return;
  try{
    const ctx=new (window.AudioContext||window.webkitAudioContext)();
    [0,0.22].forEach(t=>{
      const o=ctx.createOscillator(),g=ctx.createGain();
      o.type='square';o.frequency.value=880;g.gain.value=0.05;
      o.connect(g);g.connect(ctx.destination);o.start(ctx.currentTime+t);o.stop(ctx.currentTime+t+0.14);
    });
    setTimeout(()=>ctx.close(),800);
  }catch{}
}

/* ---------- theme ---------- */
function setTheme(t){
  document.documentElement.classList.add('theme-anim');
  document.documentElement.dataset.theme=t;
  localSet('cc_theme',t);
  setTimeout(()=>document.documentElement.classList.remove('theme-anim'),450);
  if(window.HW && state.page==='hardware') HW.update();
}
const toggleTheme=()=>setTheme(document.documentElement.dataset.theme==='dark'?'light':'dark');
$$('[data-theme-toggle]').forEach(b=>b.addEventListener('click',toggleTheme));

/* ---------- sign in / create account ---------- */
async function enterWith(result,message){
  $('login-error').textContent='';
  state.token=result.access_token;
  sessionStorage.setItem('coldchain_token',state.token);
  state.user=await api('/api/me');
  revealApp();
  await refresh();
  toast(message||`Signed in as ${state.user.username} (${roleLabel(state.user.role)}).`,'success');
}
async function attemptLogin(username,password){
  $('login-error').textContent='';
  const result=await api('/api/auth/login',{method:'POST',body:JSON.stringify({username,password})});
  await enterWith(result);
}
function showAuth(which){
  $$('.auth-tab').forEach(t=>{const on=t.dataset.auth===which;t.classList.toggle('active',on);t.setAttribute('aria-selected',String(on));});
  $$('.auth-pane').forEach(p=>p.classList.toggle('hidden',p.dataset.pane!==which));
  document.querySelector('.auth-tabs').dataset.active=which;
  $('login-error').textContent='';
  setTimeout(()=>document.querySelector(`.auth-pane[data-pane="${which}"] input`)?.focus(),60);
}
$$('.auth-tab').forEach(t=>t.addEventListener('click',()=>showAuth(t.dataset.auth)));
$$('[data-auth-go]').forEach(b=>b.addEventListener('click',()=>showAuth(b.dataset.authGo)));

function busy(btn,label){
  const lab=btn.querySelector('.btn-label');const prev=lab?lab.textContent:'';
  btn.disabled=true;btn.classList.add('is-busy');if(lab) lab.textContent=label;
  return ()=>{btn.disabled=false;btn.classList.remove('is-busy');if(lab) lab.textContent=prev;};
}
function shake(el){el.classList.remove('shake');void el.offsetWidth;el.classList.add('shake');}

$$('.cred-card').forEach(card=>card.addEventListener('click',async()=>{
  $$('.cred-card').forEach(c=>c.classList.toggle('selected',c===card));
  card.classList.add('loading');card.disabled=true;
  try{await attemptLogin(card.dataset.user,card.dataset.pass);}
  catch(err){$('login-error').textContent=err.message;shake(document.querySelector('.auth-card'));}
  finally{card.classList.remove('loading');card.disabled=false;}
}));

$('login-form').addEventListener('submit',async e=>{
  e.preventDefault();
  const u=$('login-username').value.trim(),pw=$('login-password').value;
  if(!u||!pw){$('login-error').textContent='Enter your username and password.';shake(e.target);return;}
  const done=busy(e.target.querySelector('button[type=submit]'),'Signing in…');
  try{await attemptLogin(u,pw);}
  catch(err){$('login-error').textContent=err.message;shake(e.target);}
  finally{done();}
});
$('pw-toggle').addEventListener('click',()=>{
  const input=$('login-password');const show=input.type==='password';
  input.type=show?'text':'password';$('pw-toggle').textContent=show?'Hide':'Show';
  $('pw-toggle').setAttribute('aria-label',show?'Hide password':'Show password');
});

function pwScore(pw){
  let s=0;if(pw.length>=8)s++;if(pw.length>=12)s++;if(/[a-z]/.test(pw)&&/[A-Z]/.test(pw))s++;if(/\d/.test(pw))s++;if(/[^A-Za-z0-9]/.test(pw))s++;
  return Math.min(4,s);
}
$('reg-password').addEventListener('input',e=>{
  const pw=e.target.value,sc=pw?pwScore(pw):0;
  const bar=$('pw-meter-bar');bar.style.width=`${pw?Math.max(10,sc*25):0}%`;bar.dataset.level=sc;
  $('pw-meter-text').textContent=!pw?'At least 8 characters':pw.length<8?`${8-pw.length} more character${8-pw.length>1?'s':''}`:['Weak','Weak','Fair','Good','Strong'][sc]+' password';
});
$('register-form').addEventListener('submit',async e=>{
  e.preventDefault();
  const u=$('reg-username').value.trim(),pw=$('reg-password').value,pw2=$('reg-password2').value;
  const role=document.querySelector('input[name=reqrole]:checked')?.value||'Inspector';
  const err=m=>{$('login-error').textContent=m;shake(e.target);};
  if(!/^[A-Za-z0-9._@+-]{3,60}$/.test(u)) return err('Username: 3–60 letters, numbers or . _ - @ +');
  if(pw.length<8) return err('Password needs at least 8 characters.');
  if(pw!==pw2) return err('The two passwords do not match.');
  const done=busy(e.target.querySelector('button[type=submit]'),'Creating…');
  try{
    const result=await api('/api/auth/register',{method:'POST',body:JSON.stringify({username:u,password:pw,requested_role:role})});
    e.target.reset();$('pw-meter-bar').style.width='0';$('pw-meter-text').textContent='At least 8 characters';
    await enterWith(result,role==='Pharmacist'?'Account created with read-only access. Your Pharmacist request is waiting for an admin.':'Account created. You have read-only Inspector access.');
  }catch(ex){err(ex.message);}
  finally{done();}
});

/* ---------- front page motion ---------- */
(function frontPage(){
  const field=$('frost-field');
  if(field && !REDUCED_FRONT()){
    for(let i=0;i<26;i++){
      const d=document.createElement('i');
      d.style.left=`${Math.random()*100}%`;d.style.animationDelay=`${-Math.random()*18}s`;
      d.style.animationDuration=`${12+Math.random()*14}s`;d.style.setProperty('--s',`${1+Math.random()*2.6}px`);d.style.setProperty('--dx',`${(Math.random()*60-30).toFixed(0)}px`);
      field.appendChild(d);
    }
  }
  // count-up stats once visible
  $$('[data-count]').forEach(el=>{
    const to=Number(el.dataset.count),suf=el.dataset.suffix||'';let t0=null;
    const step=t=>{t0??=t;const p=Math.min(1,(t-t0)/1200),v=Math.round(to*(1-Math.pow(1-p,3)));el.textContent=v+suf;if(p<1) requestAnimationFrame(step);};
    setTimeout(()=>requestAnimationFrame(step),500);
  });
  // live preview card: a small local thermostat loop, clearly labelled "simulated preview"
  let temp=4.8,comp=false,door=false,tick=0;const hist=[];
  for(let i=0;i<80;i++) hist.push(4.8+Math.sin(i/9)*1.1);
  const y=v=>88-(v-2)/6*66;
  function frame(){
    if(!$('login-screen') || $('login-screen').classList.contains('hidden')) return;
    tick++;door=(tick%140)>118;
    if(temp>=7) comp=true; if(temp<=3) comp=false;
    temp+= (door?0.06:0.018) - (comp?0.07:0);
    hist.push(temp);if(hist.length>80) hist.shift();
    const pts=hist.map((v,i)=>`${(i*400/79).toFixed(1)},${y(v).toFixed(1)}`);
    $('lc-line').setAttribute('d','M'+pts.join(' L'));
    $('lc-dot').setAttribute('cy',y(temp).toFixed(1));
    $('lc-temp').textContent=temp.toFixed(1);
    const warn=temp>=7||door;$('lc-state').textContent=temp>8?'BREACH':warn?'WARNING':'SAFE';
    $('lc-state').className='lc-state '+(temp>8?'danger':warn?'warning':'safe');
    $('lc-door').textContent=door?'open':'closed';$('lc-comp').textContent=comp?'cooling':'idle';
    $('lc-fc').textContent=door&&temp>6?'may pass 8 °C':'no breach';
  }
  frame();setInterval(frame,700);
  // server status (Render's free plan sleeps; tell visitors it is waking up)
  async function ping(n=0){
    try{const r=await fetch('/health',{cache:'no-store'});if(!r.ok) throw 0;$('server-state').textContent='server online';$('server-state').parentElement.classList.add('ok');}
    catch{$('server-state').textContent='server waking up…';if(n<20) setTimeout(()=>ping(n+1),3000);}
  }
  ping();
})();
function REDUCED_FRONT(){return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;}

/* ---------- micro-interactions ---------- */
// Ripple from the pointer on buttons; purely visual, no effect on behaviour.
document.addEventListener('pointerdown',e=>{
  const b=e.target.closest('.btn,.mini-btn,.cred-card,.nav-link,.seg-btn,.fchip,.attack-btn,.ctl-btn,.auth-tab,.icon-btn');
  if(!b || b.disabled || REDUCED_FRONT()) return;
  const r=b.getBoundingClientRect(),d=Math.max(r.width,r.height)*1.4;
  const s=document.createElement('span');s.className='ripple';
  s.style.width=s.style.height=`${d}px`;s.style.left=`${e.clientX-r.left-d/2}px`;s.style.top=`${e.clientY-r.top-d/2}px`;
  b.appendChild(s);setTimeout(()=>s.remove(),650);
});
function moveNavIndicator(){
  const ind=$('nav-indicator'),act=document.querySelector('.nav-link.active');
  if(!ind||!act||act.offsetParent===null){if(ind) ind.style.opacity=0;return;}
  ind.style.opacity=1;
  ind.style.transform=`translate(${act.offsetLeft}px,${act.offsetTop}px)`;
  ind.style.width=`${act.offsetWidth}px`;ind.style.height=`${act.offsetHeight}px`;
}
window.addEventListener('resize',()=>requestAnimationFrame(moveNavIndicator));

function applyRoleVisibility(){
  const demo=!!state.data?.demo;
  $$('.edit-only,.admin-only,.demo-only,.demo-nav').forEach(el=>{
    const has=c=>el.classList.contains(c);
    let show=true;
    if(has('edit-only') && !canEdit()) show=false;
    if(has('admin-only') && !isRole('Admin')) show=false;
    if((has('demo-only')||has('demo-nav')) && !demo) show=false;
    if(has('demo-nav') && !canEdit()) show=false;
    if(el.id==='restore-btn') show=show&&_tamperActive;
    if(el.id==='tamper-btn') show=show&&!_tamperActive;
    el.classList.toggle('hidden',!show);
  });
}

function revealApp(){
  $('login-screen').classList.add('hidden');
  $('app-shell').classList.remove('hidden');
  $('logged-user').textContent=state.user.username;
  $('logged-role').textContent=roleLabel(state.user.role);
  $('avatar').textContent=state.user.username.slice(0,2).toUpperCase();
  applyRoleVisibility();
  const wanted=location.hash.replace('#','');
  // Lab visibility depends on demo mode, known only after the first dashboard load.
  state.pendingPage=PAGES.includes(wanted)?wanted:null;
  setPage(state.pendingPage||'dashboard',false);
}

function logout(){
  state.token='';state.user=null;state.data=null;state.issues.clear();state.firstIssues=true;
  sessionStorage.removeItem('coldchain_token');
  $('app-shell').classList.add('hidden');
  $('login-screen').classList.remove('hidden');
  $('login-password').value='';
  showAuth('signin');$('login-error').textContent='';
}
$('logout-btn').addEventListener('click',()=>{logout();toast('Signed out.');});

async function restore(){
  if(!state.token) return;
  try{state.user=await api('/api/me');revealApp();await refresh();}
  catch{logout();}
}

/* ---------- navigation ---------- */
function pageAllowed(page){
  if(page==='lab') return !!state.data?.demo && canEdit();
  if(page==='users') return isRole('Admin');
  return PAGES.includes(page);
}
function setPage(page,push=true){
  if(!pageAllowed(page)) page='dashboard';
  state.page=page;
  $$('.page-view').forEach(view=>view.classList.toggle('hidden',view.id!==`page-${page}`));
  $$('[data-page]').forEach(btn=>{const on=btn.dataset.page===page;btn.classList.toggle('active',on);btn.setAttribute('aria-current',on?'page':'false');});
  const [crumb,title]=PAGE_META[page];
  $('page-title').textContent=crumb;$('current-breadcrumb').textContent=title;
  requestAnimationFrame(moveNavIndicator);
  document.querySelector('.nav-link.active')?.scrollIntoView?.({block:'nearest',inline:'nearest',behavior:'smooth'});
  document.title=`${crumb} · ColdChain`;
  if(page==='hardware' && window.HW) HW.show();
  if(push && location.hash!=='#'+page) history.replaceState(null,'','#'+page);
  window.scrollTo({top:0,behavior:'smooth'});
  if(page==='security'){loadAudit();loadRejections();}
  if(page==='lab') loadControls();
  if(page==='users') loadUsers();
  if(page==='ai') loadAiReport();
}
$$('[data-page]').forEach(btn=>btn.addEventListener('click',()=>setPage(btn.dataset.page)));
document.addEventListener('click',e=>{
  const open=e.target.closest('[data-open]');
  if(open){e.preventDefault();setPage(open.dataset.open);closeBell();}
  const link=e.target.closest('[data-page-link]');
  if(link){e.preventDefault();setPage(link.dataset.pageLink);}
});
window.addEventListener('hashchange',()=>{const p=location.hash.replace('#','');if(state.user && p!==state.page && PAGES.includes(p)) setPage(p,false);});

document.addEventListener('keydown',e=>{
  if(e.key==='Escape'){closeModal();closeBell();return;}
  if(!state.user || !$('modal-backdrop').classList.contains('hidden')) return;
  const typing=/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName||'');
  if(typing || e.ctrlKey || e.metaKey || e.altKey) return;
  const idx=Number(e.key);
  const visible=PAGES.filter(pageAllowed);
  if(idx>=1 && idx<=visible.length){setPage(visible[idx-1]);e.preventDefault();}
  else if(e.key==='/'){setPage('inventory');setTimeout(()=>$('inv-search').focus(),50);e.preventDefault();}
  else if(e.key==='r'||e.key==='R'){refresh(true);}
  else if(e.key==='t'||e.key==='T'){toggleTheme();}
  else if(state.page==='hardware' && window.HW) HW.key(e);
});

setInterval(()=>{$('clock').textContent=new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'});},1000);

/* ---------- fridge status (mirrors the ESP32 OLED / LED logic) ---------- */
function fridgeState(f,pred){
  const reasons=[];
  if(!f.online) return {label:'Offline',cls:'danger',oled:'OFFLINE',reasons:[`No data for ${ago(f.last_seen)}`]};
  const t=f.temp_c;
  let cls='safe',label='Safe';
  if(t>8){reasons.push(`${fmtTemp(t)} is above 8°C`);}
  if(t<2){reasons.push(`${fmtTemp(t)} is below 2°C (freezing risk)`);}
  if(f.red_latch){reasons.push('A batch reached 0% heat budget (discard latch)');}
  if(reasons.length) return {label:'Breach',cls:'danger',oled:'BREACH',reasons};
  if(t>=7) reasons.push('Approaching 8°C limit');
  if(f.door_open) reasons.push('Door is open');
  if(!f.mains_ok) reasons.push('On battery power');
  if(pred?.forecast?.warning) reasons.push(`Forecast ${fmtTemp(pred.forecast.predicted_c)} in 30 min`);
  if(reasons.length){cls='warning';label='Warning';}
  return {label,cls,oled:cls==='warning'?'WARNING':'SAFE',reasons};
}
function doorOpenSeconds(f){
  if(!f.door_open || !f.door_open_since) return 0;
  return Math.max(0,Math.round((serverNow()-new Date(f.door_open_since).getTime())/1000));
}

/* ---------- metrics ---------- */
function metricCard(label,value,suffix,detail,cls='',ic='',page='',key=''){
  const num=Number.isFinite(value);
  return `<button class="metric-card ${cls}" ${page?`data-open="${page}"`:''}>
    <span class="metric-label">${icon(ic)}${esc(label)}</span>
    <strong class="metric-value mono"><span ${num?`data-k="m-${key}" data-v="${value}" data-d="0"`:''}>${num?value:'—'}</span><span class="metric-sub">${suffix}</span></strong>
    <small class="metric-detail">${esc(detail)}</small></button>`;
}
function renderMetrics(data){
  const online=data.fridges.filter(f=>f.online).length;
  const risk=data.batches.filter(b=>b.status==='At Risk').length;
  const discard=data.batches.filter(b=>b.status==='Discard'||b.expired).length;
  const states=data.fridges.map(f=>fridgeState(f,data.predictions[f.id]));
  const breaches=states.filter(s=>s.cls==='danger').length;
  const warnings=states.filter(s=>s.cls==='warning').length;
  const healths=data.fridges.map(f=>data.predictions[f.id]?.health?.score).filter(v=>v!=null);
  const minHealth=healths.length?Math.min(...healths):null;
  setHTML($('metrics'),[
    metricCard('Fridges online',online,`/${data.fridges.length}`,breaches?`${breaches} in breach · ${warnings} warning`:warnings?`${warnings} with a warning`:'both inside 2–8 °C',breaches?'danger':warnings?'warn':'ok','snow','dashboard','on'),
    metricCard('Batches',data.batches.length,'',`${data.batches.filter(b=>b.status==='Safe'&&!b.expired).length} safe to use`,'','box','inventory','b'),
    metricCard('Need attention',risk+discard,'',risk+discard?`${risk} at risk · ${discard} discard/expired`:'nothing to act on',discard?'danger':risk?'warn':'ok','alert','inventory','att'),
    metricCard('Weakest compressor',minHealth??NaN,minHealth==null?'':'/100',minHealth==null?'learning from cooling runs':minHealth<70?'cooling slower than baseline':'cooling normally',minHealth!=null&&minHealth<70?'warn':'ok','gauge','ai','h'),
    metricCard('Rejected packets',data.rejected_24h||0,'',data.rejected_24h?'last 24 h · forged or replayed':'none in the last 24 h',data.rejected_24h?'warn':'ok','shield','security','r'),
  ].join(''));
  animateIn($('metrics'));
}

/* ---------- motion helpers ----------
   Cards are re-rendered from data every 5 s, so values remember their previous reading (by key)
   and animate from it. That keeps a temperature visibly sliding instead of jumping. */
const REDUCED=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
state.prev={};
function animateIn(root){
  if(!root) return;
  root.querySelectorAll('[data-k]').forEach(el=>{
    const k=el.dataset.k,v=Number(el.dataset.v),from=state.prev[k];
    state.prev[k]=v;
    if(el.dataset.arc){
      const len=Number(el.dataset.arc),max=Number(el.dataset.max)||100;
      const dash=x=>`${(Math.max(0,Math.min(max,x))/max*len).toFixed(1)} 999`;
      if(from==null||REDUCED){el.style.strokeDasharray=dash(v);return;}
      el.style.transition='none';el.style.strokeDasharray=dash(from);
      el.getBoundingClientRect();
      el.style.transition='';requestAnimationFrame(()=>{el.style.strokeDasharray=dash(v);});
      return;
    }
    if(from==null||from===v||REDUCED) return;
    const d=Number(el.dataset.d||0),t0=performance.now(),dur=700;
    const step=t=>{const p=Math.min(1,(t-t0)/dur),e=1-Math.pow(1-p,3);el.textContent=(from+(v-from)*e).toFixed(d);if(p<1) requestAnimationFrame(step);};
    el.textContent=from.toFixed(d);requestAnimationFrame(step);
  });
}

/* ---------- chart ---------- */
const CH={w:640,h:200,l:34,r:10,t:12,b:24,split:0.8};
function chartSvg(fid,rows,cls,forecast){
  const pts=rows.filter(r=>Number.isFinite(Number(r.temp_c)));
  if(pts.length<2) return `<div class="empty-box small">Waiting for temperature samples…</div>`;
  const step=Math.ceil(pts.length/240);
  const sampled=pts.filter((_,i)=>i%step===0||i===pts.length-1);
  const temps=sampled.map(r=>Number(r.temp_c));
  const fc=forecast?.predicted_c;
  const hi=Math.max(12,Math.ceil(Math.max(...temps,fc??0)+1));
  const lo=Math.min(0,Math.floor(Math.min(...temps)-1));
  const plotW=CH.w-CH.l-CH.r, histW=plotW*(fc==null?1:CH.split);
  const t0=new Date(sampled[0].observed_at).getTime(), t1=new Date(sampled.at(-1).observed_at).getTime();
  const x=t=>CH.l+((t-t0)/Math.max(t1-t0,1))*histW;
  const y=v=>CH.t+(1-(v-lo)/(hi-lo))*(CH.h-CH.t-CH.b);
  const color=cls==='danger'?'var(--bad)':cls==='warning'?'var(--warn)':'var(--accent)';
  // Split at telemetry gaps (> 60 s) so missing data is shown as missing, not as a straight line.
  const segs=[];let cur=[];
  sampled.forEach((r,i)=>{if(i&&new Date(r.observed_at)-new Date(sampled[i-1].observed_at)>60000){segs.push(cur);cur=[];}cur.push(r);});
  segs.push(cur);
  const ptsOf=seg=>seg.map(r=>`${x(new Date(r.observed_at).getTime()).toFixed(1)},${y(Number(r.temp_c)).toFixed(1)}`).join(' ');
  const gaps=segs.slice(1).map((seg,i)=>[segs[i].at(-1),seg[0]]);
  const ticks=[];for(let v=lo;v<=hi;v+=hi-lo>14?4:2) ticks.push(v);
  const lastX=x(t1),lastY=y(temps.at(-1));
  const doorBands=[];let start=null;
  sampled.forEach((r,i)=>{
    const gapNext=i<sampled.length-1&&new Date(sampled[i+1].observed_at)-new Date(r.observed_at)>60000;
    if(r.door_open && start==null) start=i;
    if((!r.door_open||gapNext||i===sampled.length-1) && start!=null){doorBands.push([start,i]);start=null;}
  });
  const fmtAxis=t=>new Date(t).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
  let fcSvg='';
  if(fc!=null){
    const fx=CH.l+plotW, fy=y(fc), warn=fc>8;
    fcSvg=`<rect x="${lastX.toFixed(1)}" y="${CH.t}" width="${(fx-lastX).toFixed(1)}" height="${CH.h-CH.t-CH.b}" class="fc-zone"/>
      <line x1="${lastX.toFixed(1)}" y1="${lastY.toFixed(1)}" x2="${fx.toFixed(1)}" y2="${fy.toFixed(1)}" class="fc-line ${warn?'warn':''}"/>
      <circle cx="${fx.toFixed(1)}" cy="${fy.toFixed(1)}" r="5" class="fc-dot ${warn?'warn':''}"/>
      <text x="${(fx-6).toFixed(1)}" y="${(fy+(fy<CH.t+20?18:-10)).toFixed(1)}" text-anchor="end" class="fc-label ${warn?'warn':''}">AI +30m ${fc.toFixed(1)}°</text>
      <text x="${fx.toFixed(1)}" y="${CH.h-6}" text-anchor="end" class="axis">+30 min</text>`;
  }
  return `<svg class="temp-chart" viewBox="0 0 ${CH.w} ${CH.h}" role="img" aria-label="Temperature history${fc!=null?' with 30-minute forecast':''}">
    <rect x="${CH.l}" y="${y(8).toFixed(1)}" width="${plotW}" height="${(y(2)-y(8)).toFixed(1)}" class="safe-band"/>
    ${ticks.map(v=>`<line x1="${CH.l}" x2="${CH.w-CH.r}" y1="${y(v).toFixed(1)}" y2="${y(v).toFixed(1)}" class="grid"/><text x="${CH.l-6}" y="${(y(v)+4).toFixed(1)}" text-anchor="end" class="axis">${v}°</text>`).join('')}
    ${doorBands.map(([a,b])=>`<rect x="${x(new Date(sampled[a].observed_at).getTime()).toFixed(1)}" y="${CH.t}" width="${Math.max(2,x(new Date(sampled[b].observed_at).getTime())-x(new Date(sampled[a].observed_at).getTime())).toFixed(1)}" height="${CH.h-CH.t-CH.b}" class="door-band"/>`).join('')}
    <line x1="${CH.l}" x2="${CH.w-CH.r}" y1="${y(8).toFixed(1)}" y2="${y(8).toFixed(1)}" class="limit hi"/>
    <line x1="${CH.l}" x2="${CH.w-CH.r}" y1="${y(2).toFixed(1)}" y2="${y(2).toFixed(1)}" class="limit lo"/>
    ${gaps.map(([a,b])=>{const xa=x(new Date(a.observed_at).getTime()),xb=x(new Date(b.observed_at).getTime());return `<rect x="${xa.toFixed(1)}" y="${CH.t}" width="${Math.max(1,xb-xa).toFixed(1)}" height="${CH.h-CH.t-CH.b}" class="gap-band"/>${xb-xa>46?`<text x="${((xa+xb)/2).toFixed(1)}" y="${CH.t+14}" text-anchor="middle" class="axis">no data</text>`:''}`;}).join('')}
    ${segs.map(seg=>{const l=ptsOf(seg);return `<polygon points="${x(new Date(seg[0].observed_at).getTime()).toFixed(1)},${y(lo)} ${l} ${x(new Date(seg.at(-1).observed_at).getTime()).toFixed(1)},${y(lo)}" style="fill:${color}" opacity=".13"/><polyline points="${l}" class="ln" style="stroke:${color}"/>`;}).join('')}
    ${fcSvg}
    <line x1="${lastX.toFixed(1)}" x2="${lastX.toFixed(1)}" y1="${CH.t}" y2="${CH.h-CH.b}" class="now-line"/>
    <circle cx="${lastX.toFixed(1)}" cy="${lastY.toFixed(1)}" r="5" style="fill:${color}" class="pulse-dot"/>
    <text x="${CH.l}" y="${CH.h-6}" class="axis">${fmtAxis(t0)}</text>
    <text x="${lastX.toFixed(1)}" y="${CH.h-6}" text-anchor="${fc==null?'end':'middle'}" class="axis">now</text>
    <line class="hover-line hidden" x1="0" x2="0" y1="${CH.t}" y2="${CH.h-CH.b}"/>
    <circle class="hover-dot hidden" r="4.5"/>
  </svg>`;
}

function chartHover(box,clientX){
  const fid=box.dataset.fridge;
  const rows=(state.history[fid]||[]).filter(r=>Number.isFinite(Number(r.temp_c)));
  const svg=box.querySelector('svg');const tip=box.querySelector('.chart-tip');
  if(!svg||rows.length<2||!tip) return;
  const rect=svg.getBoundingClientRect();
  const vx=((clientX-rect.left)/rect.width)*CH.w;
  const fc=state.data?.predictions?.[fid]?.forecast?.predicted_c;
  const histW=(CH.w-CH.l-CH.r)*(fc==null?1:CH.split);
  const frac=(vx-CH.l)/histW;
  const line=svg.querySelector('.hover-line'),dot=svg.querySelector('.hover-dot');
  if(frac<0||frac>1.0001){line.classList.add('hidden');dot.classList.add('hidden');
    if(fc!=null && frac>1){tip.innerHTML=`<b>AI forecast</b><span>${fmtTemp(fc)} in 30 min</span>`;tip.style.left=`${Math.min(rect.width-140,clientX-rect.left)}px`;tip.classList.remove('hidden');}
    else tip.classList.add('hidden');
    return;}
  const t0=new Date(rows[0].observed_at).getTime(),t1=new Date(rows.at(-1).observed_at).getTime();
  const target=t0+frac*(t1-t0);
  let best=rows[0];for(const r of rows){if(Math.abs(new Date(r.observed_at).getTime()-target)<Math.abs(new Date(best.observed_at).getTime()-target)) best=r;}
  const pts=[...svg.querySelectorAll('polyline')].flatMap(pl=>pl.getAttribute('points').split(' ').map(p=>p.split(',').map(Number)));
  const bx=CH.l+((new Date(best.observed_at).getTime()-t0)/Math.max(t1-t0,1))*histW;
  const near=pts.reduce((a,p)=>Math.abs(p[0]-bx)<Math.abs(a[0]-bx)?p:a,pts[0]);
  line.setAttribute('x1',bx);line.setAttribute('x2',bx);line.classList.remove('hidden');
  dot.setAttribute('cx',near[0]);dot.setAttribute('cy',near[1]);dot.classList.remove('hidden');
  tip.innerHTML=`<b>${fmtTemp(best.temp_c)}</b><span>${fmtTime(best.observed_at)}</span><span>${best.door_open?'Door open':'Door closed'} · ${best.compressor_on?'Comp. on':'Comp. off'}${best.mains_ok?'':' · Battery'}</span>`;
  tip.style.left=`${Math.max(0,Math.min(rect.width-150,(bx/CH.w)*rect.width-70))}px`;
  tip.classList.remove('hidden');
  state.hover[fid]=clientX-rect.left;
}
document.addEventListener('pointermove',e=>{
  const box=e.target.closest?.('.chart-box');
  $$('.chart-box').forEach(b=>{if(b!==box){b.querySelector('.chart-tip')?.classList.add('hidden');b.querySelectorAll('.hover-line,.hover-dot').forEach(n=>n.classList.add('hidden'));delete state.hover[b.dataset.fridge];}});
  if(box) chartHover(box,e.clientX);
});

$$('.seg-btn[data-range]').forEach(btn=>btn.addEventListener('click',()=>{
  state.range=Number(btn.dataset.range);localSet('cc_range',String(state.range));
  $$('.seg-btn[data-range]').forEach(b=>b.classList.toggle('active',b===btn));
  loadHistory();
}));
$$('.seg-btn[data-range]').forEach(b=>b.classList.toggle('active',Number(b.dataset.range)===state.range));

/* ---------- fridge cards ---------- */
function healthRing(score,size=64,key=''){
  const cls=score==null?'muted':score<40?'danger':score<70?'warning':'safe';
  const r=20,len=2*Math.PI*r;
  return `<svg class="ring ${cls}" viewBox="0 0 48 48" width="${size}" height="${size}" role="img" aria-label="Health ${score??'unknown'} of 100">
    <circle cx="24" cy="24" r="${r}" class="ring-track"/>
    <circle cx="24" cy="24" r="${r}" class="ring-val" transform="rotate(-90 24 24)" ${key?`data-k="ring-${key}" data-v="${score??0}" data-arc="${len.toFixed(1)}" data-max="100"`:`style="stroke-dasharray:${((score??0)/100*len).toFixed(1)} 999"`}/>
    <text x="24" y="28.5" text-anchor="middle">${score==null?'–':score}</text></svg>`;
}
// 270° dial from 0 to 12 °C with the 2–8 °C band marked, like an analogue fridge gauge.
function tempDial(f,st){
  const R=54,C=2*Math.PI*R,arc=C*0.75,MAX=12;
  const ang=v=>135+Math.max(0,Math.min(MAX,v))/MAX*270;
  const pt=(a,r)=>[70+r*Math.cos(a*Math.PI/180),70+r*Math.sin(a*Math.PI/180)];
  const band=(lo,hi)=>{const [x1,y1]=pt(ang(lo),R+9),[x2,y2]=pt(ang(hi),R+9);return `M${x1.toFixed(1)} ${y1.toFixed(1)} A${R+9} ${R+9} 0 ${ang(hi)-ang(lo)>180?1:0} 1 ${x2.toFixed(1)} ${y2.toFixed(1)}`;};
  const ticks=[0,1,2,3,4,5,6,7,8,9,10,11,12].map(v=>{const [a,b]=pt(ang(v),R-10),[c,d]=pt(ang(v),R-(v%2?7:4));
    return `<line x1="${a.toFixed(1)}" y1="${b.toFixed(1)}" x2="${c.toFixed(1)}" y2="${d.toFixed(1)}"/>`;}).join('');
  const lbl=v=>{const [x,y]=pt(ang(v),R+19);return `<text x="${x.toFixed(1)}" y="${(y+3).toFixed(1)}">${v}</text>`;};
  const t=f.temp_c??0;
  return `<svg class="dial ${st.cls}" viewBox="-14 -14 168 168" role="img" aria-label="Temperature ${fmtTemp(f.temp_c)}">
    <circle cx="70" cy="70" r="${R}" class="dial-track" transform="rotate(135 70 70)" style="stroke-dasharray:${arc.toFixed(1)} 999"/>
    <path d="${band(2,8)}" class="dial-band"/>
    <g class="dial-ticks">${ticks}${lbl(2)}${lbl(8)}</g>
    <circle cx="70" cy="70" r="${R}" class="dial-val" transform="rotate(135 70 70)" data-k="dial-${f.id}" data-v="${t}" data-arc="${arc.toFixed(1)}" data-max="${MAX}"/>
    <text x="70" y="78" class="dial-num" text-anchor="middle" data-k="t-${f.id}" data-v="${t}" data-d="1">${f.temp_c==null?'--.-':t.toFixed(1)}</text>
    <text x="70" y="95" class="dial-cap" text-anchor="middle">°C</text>
  </svg>`;
}
function renderFridges(data){
  setHTML($('fridge-grid'),data.fridges.map(f=>{
    const pred=data.predictions[f.id]||{};const fc=pred.forecast||{};const health=pred.health||{};
    const st=fridgeState(f,pred);
    const doorS=doorOpenSeconds(f);
    const buzzer=doorS>60;
    const redLed=st.cls==='danger'||!f.mains_ok||f.red_latch;
    const greenLed=!redLed && f.online && f.temp_c<7;
    const batches=data.batches.filter(b=>b.fridge_id===f.id).sort((a,b)=>a.remaining_pct-b.remaining_pct);
    const drawn=state.drawn?.[f.id];
    return `<article class="fridge-card st-${st.cls}">
      <header class="fc-head">
        <div>
          <span class="fc-id mono">${esc(f.id)}</span>
          <h4>${esc(f.label)}</h4>
          <small>${f.simulated?'software twin':'ESP32 node'} · updated ${esc(ago(f.last_seen))}</small>
        </div>
        <div class="fc-status">
          <span class="status-pill ${st.cls}"><i></i>${st.label}</span>
          <span class="leds" title="Node LEDs and buzzer">
            <span class="led red ${redLed?'on':''}"></span><span class="led green ${greenLed?'on':''}"></span>
            <span class="buzzer ${buzzer?'on':''}">${icon('sound')}</span>
          </span>
        </div>
      </header>
      ${st.reasons.length?`<ul class="reason-list ${st.cls}">${st.reasons.map(r=>`<li>${esc(r)}</li>`).join('')}</ul>`:''}
      <div class="fc-body">
        ${tempDial(f,st)}
        <div class="oled" aria-label="OLED display">
          <div class="oled-row"><span>COLDCHAIN</span><span>${esc(f.id.replace('FRIDGE_',''))}</span></div>
          <div class="oled-temp">${f.temp_c==null?'--.-':Number(f.temp_c).toFixed(1)} C</div>
          <div class="oled-row"><span class="oled-state ${st.cls}">${st.oled}</span><span>${f.online?'MQTT':'OFFLINE'}</span></div>
          <div class="oled-row small"><span>${f.mains_ok?'MAINS':'BATTERY'}</span><span>Q:${f.buffered||0}</span></div>
        </div>
      </div>
      <div class="fc-stats">
        <div class="kv ${f.door_open?'warn':''}"><span>Door</span><b>${icon('door')}${f.door_open?`open <em class="mono">${fmtDur(doorS)}</em>`:'closed'}</b></div>
        <div class="kv ${f.mains_ok?'':'warn'}"><span>Power</span><b>${icon(f.mains_ok?'plug':'battery')}${f.mains_ok?'mains':'battery'}</b></div>
        <div class="kv"><span>Battery</span><b><span class="batt"><span style="width:${f.battery_pct??0}%" class="${(f.battery_pct??100)<30?'low':''}"></span></span><em class="mono">${f.battery_pct??'—'}%</em></b></div>
        <div class="kv"><span>Compressor</span><b>${icon('fan',f.compressor_on?'spin':'')}${f.compressor_on?'running':'idle'}</b></div>
      </div>
      ${f.buffered?`<div class="buffer-note">${icon('wifioff')}Wi-Fi down — ${f.buffered} readings held on the node, will sync in order</div>`:''}
      <div class="chart-shell">
        <div class="mini-head"><span>last ${state.range===120?'10 min':state.range===360?'30 min':'2 h'}</span><span class="legend"><i class="key band"></i>2–8 °C <i class="key fc"></i>forecast <i class="key door"></i>door open</span></div>
        <div class="chart-box ${drawn?'':'first'}" data-fridge="${esc(f.id)}" id="chart-${esc(f.id)}">${chartSvg(f.id,state.history[f.id]||[],st.cls,fc)}<div class="chart-tip hidden"></div></div>
      </div>
      <div class="forecast-row">
        <button class="forecast-box ${fc.warning?'warning':''}" data-open="ai">
          <span>+30 min forecast</span>
          <strong class="mono">${fc.predicted_c==null?'—':fmtTemp(fc.predicted_c)}</strong>
          <small>${fc.warning?`may pass 8 °C${fc.minutes_to_8c!=null?` · ~${Math.round(fc.minutes_to_8c)} min on current trend`:''}`:'no breach expected'}</small>
        </button>
        <button class="forecast-box health ${health.score!=null&&health.score<70?'warning':''}" data-open="ai">
          ${healthRing(health.score,50,f.id)}
          <div><span>Compressor</span><small>${health.score==null?esc(health.note||'learning…'):health.score<70?'weakening — cools slower than baseline':'cooling normally'}</small></div>
        </button>
      </div>
      <div class="fridge-batches">
        <div class="mini-head"><span>Stock (${batches.length})</span><button class="link-btn" data-open="inventory">manage</button></div>
        ${batches.length?batches.slice(0,4).map(b=>`<div class="fb-row"><span class="fb-name">${esc(b.name)} <small class="mono">${esc(b.lot)}</small></span><span class="budget-bar"><span class="${statusClass(b.status)}" style="width:${Math.max(0,Math.min(100,b.remaining_pct))}%"></span></span><span class="fb-pct mono ${statusClass(b.status)}">${Math.round(b.remaining_pct)}%</span></div>`).join(''):'<div class="muted-note">Empty.</div>'}
        ${batches.length>4?`<div class="muted-note">+${batches.length-4} more</div>`:''}
      </div>
    </article>`;
  }).join(''));
  animateIn($('fridge-grid'));
  state.drawn=state.drawn||{};
  data.fridges.forEach(f=>{if((state.history[f.id]||[]).length>1) state.drawn[f.id]=true;});
  Object.entries(state.hover).forEach(([fid,px])=>{const box=$(`chart-${fid}`);if(box){const r=box.querySelector('svg')?.getBoundingClientRect();if(r) chartHover(box,r.left+px);}});
}

/* ---------- activity ---------- */
const EVENT_TITLES={
  database_initialized:'Database initialized',batch_added:'Batch registered',batch_moved:'Batch relocated',batch_updated:'Batch edited',batch_disposed:'Batch disposed',
  discard_latch_admin_reset:'Discard latch reset by admin',door_alert:'Door open > 60 s alert',batch_status_change:'Batch status changed',telemetry_rejected:'Telemetry rejected',
  telemetry_gap:'Telemetry gap detected',simulation_control:'Simulation control changed',user_created:'User created',user_updated:'User updated',reading:'Sensor reading',
  synthetic_baseline_seeded:'Synthetic history seeded',round1_rising_risk_staged:'Rising-risk scenario staged',round1_synthetic_exposure_staged:'Exposure scenario staged',
  simulation_reset:'Simulation reset',tamper_demo_restored:'Tamper demo restored',nonmonotonic_observation:'Out-of-order timestamp',
};
function readableEvent(event){
  let parsed={};
  try{parsed=typeof event.details==='string'?JSON.parse(event.details):event.details||{};}catch{}
  const action=event.action||'';
  let detail='';
  if(action==='batch_status_change') detail=`${parsed.lot}: ${parsed.from} → ${parsed.to}`;
  else if(action==='batch_moved') detail=`${parsed.lot}: ${fridgeLabel(parsed.from)} → ${fridgeLabel(parsed.to)}`;
  else if(action==='telemetry_rejected') detail=`${parsed.device}: ${String(parsed.reason||'').replace(/_/g,' ')}`;
  else if(action==='door_alert') detail=`${fridgeLabel(parsed.fridge)} · delivery: ${parsed.delivery}`;
  else if(action==='simulation_control') detail=`${fridgeLabel(parsed.fridge)} · ${Object.entries(parsed.controls||{}).map(([k,v])=>`${k.replace(/_/g,' ')}=${v?'on':'off'}`).join(', ')}`;
  else if(action==='reading') detail=`${parsed.device} #${parsed.seq} · ${(parsed.temp_c_100/100).toFixed(2)}°C`;
  else detail=Object.entries(parsed).filter(([k])=>!['note','id','batch_id','demo_only'].includes(k)).slice(0,3).map(([k,v])=>`${k.replace(/_/g,' ')}: ${typeof v==='object'?JSON.stringify(v):v}`).join(' · ');
  const title=EVENT_TITLES[action]||action.replace(/_/g,' ');
  const level=/rejected|nonmonotonic|disposed|reset|tamper/.test(action)?'warn':/door_alert/.test(action)||(action==='batch_status_change'&&parsed.to==='Discard')?'danger':action==='batch_status_change'?'warn':'';
  return {title,detail:detail||'—',level};
}
function eventItem(event,withId=false){
  const item=readableEvent(event);
  return `<article class="list-item">
    <div class="item-icon ${item.level}"></div>
    <div class="item-copy"><strong>${withId?`#${event.id} · `:''}${esc(item.title)}</strong><span>${esc(event.actor||'system')} · ${esc(item.detail)}</span></div>
    <time title="${esc(fmtDateTime(event.at))}">${esc(ago(event.at))}</time>
  </article>`;
}
function renderEvents(data){
  const events=(data.events||[]).slice(0,7);
  setHTML($('event-list'),events.length?events.map(e=>eventItem(e)).join(''):`<div class="empty-box">No events yet.</div>`);
}

/* ---------- relocation ---------- */
function relocationHtml(recs,data){
  if(!recs.length){
    const atRisk=data.fridges.filter(f=>{const s=fridgeState(f,data.predictions[f.id]);return s.cls!=='safe';});
    if(atRisk.length){
      const names=atRisk.map(f=>f.label).join(' and ');
      const empty=atRisk.every(f=>!data.batches.some(b=>b.fridge_id===f.id&&b.status!=='Discard'&&!b.expired));
      return `<div class="empty-box">${esc(names)} ${atRisk.length>1?'need':'needs'} attention, but ${empty?'holds no movable batches':'no other fridge is currently safe enough to receive stock (online, 2.5–6.5°C, mains on, no forecast risk)'}.</div>`;
    }
    return `<div class="empty-box"><b>No relocation needed.</b><br>When a fridge is breaching or forecast to pass 8°C within 30 minutes, the AI lists which batches to move and where.</div>`;
  }
  const groups={};
  recs.forEach(r=>{(groups[`${r.from_fridge}>${r.to_fridge}`]??=[]).push(r);});
  return Object.values(groups).map(list=>{
    const r0=list[0];
    return `<article class="rec-group">
      <div class="rec-route">
        <div><span class="route-from">${esc(fridgeLabel(r0.from_fridge))}</span><span class="route-arrow">→</span><span class="route-to">${esc(fridgeLabel(r0.to_fridge))}</span></div>
        <small>Why: ${esc(r0.reason)} · destination now ${fmtTemp(r0.target_temp_c)}${r0.target_forecast_c!=null?`, forecast ${fmtTemp(r0.target_forecast_c)}`:''}</small>
      </div>
      ${list.map(r=>`<div class="rec-card">
        <div class="rec-copy"><strong>${esc(r.name)} ${r.priority==='high'?'<span class="prio">urgent</span>':''}</strong><p>Lot ${esc(r.lot)} · ${esc(String(r.remaining_pct))}% heat budget left</p></div>
        <button class="btn btn-primary btn-sm rec-btn" data-batch="${esc(r.batch_id)}" data-target="${esc(r.to_fridge)}" ${canEdit()?'':'disabled title="Pharmacist or Admin only"'}>Move</button>
      </div>`).join('')}
      ${list.length>1&&canEdit()?`<button class="btn btn-primary btn-block rec-all" data-items='${esc(JSON.stringify(list.map(r=>[r.batch_id,r.to_fridge])))}'>${icon('check')}Confirm all ${list.length} moves to ${esc(fridgeLabel(r0.to_fridge))}</button>`:''}
    </article>`;
  }).join('');
}
function renderRecommendations(data){
  setLiveHTML($('relocation-list'),relocationHtml(data.recommendations,data));
  setLiveHTML($('ai-relocation'),relocationHtml(data.recommendations,data));
}
document.addEventListener('click',async e=>{
  const btn=e.target.closest('.rec-btn');
  if(btn){
    btn.disabled=true;btn.textContent='Moving…';
    await runAction(()=>api('/api/relocations/confirm',{method:'POST',body:JSON.stringify({batch_id:btn.dataset.batch,target_fridge_id:btn.dataset.target})}),`Relocation recorded to ${fridgeLabel(btn.dataset.target)}. Move the stock physically too.`);
    return;
  }
  const all=e.target.closest('.rec-all');
  if(all){
    all.disabled=true;all.textContent='Moving…';
    const items=JSON.parse(all.dataset.items);let ok=0;const errors=[];
    for(const [batch_id,target] of items){
      try{await api('/api/relocations/confirm',{method:'POST',body:JSON.stringify({batch_id,target_fridge_id:target})});ok++;}
      catch(err){errors.push(err.message);}
    }
    toast(errors.length?`${ok} moved, ${errors.length} failed: ${errors[0]}`:`${ok} batches relocated. Move the stock physically too.`,errors.length?'error':'success');
    await refresh(false,true);
  }
});

/* ---------- notifications ---------- */
function computeIssues(data){
  const list=[];
  data.fridges.forEach(f=>{
    const pred=data.predictions[f.id]||{};const st=fridgeState(f,pred);
    if(!f.online) list.push({key:`off-${f.id}`,level:'danger',title:`${f.label} offline`,detail:`Last data ${ago(f.last_seen)}`,page:'dashboard'});
    else{
      if(f.temp_c>8) list.push({key:`hot-${f.id}`,level:'danger',title:`${f.label} breach: ${fmtTemp(f.temp_c)}`,detail:'Above 8°C — heat budget is being used',page:'dashboard'});
      if(f.temp_c<2) list.push({key:`cold-${f.id}`,level:'danger',title:`${f.label} too cold: ${fmtTemp(f.temp_c)}`,detail:'Below 2°C — freezing can destroy vaccines',page:'dashboard'});
      const ds=doorOpenSeconds(f);
      if(f.door_open) list.push({key:`door-${f.id}${ds>60?'-alarm':''}`,level:ds>60?'danger':'warning',title:`${f.label} door open ${fmtDur(ds)}`,detail:ds>60?'Over 60 s: buzzer on, alert sent':'Alarm after 60 seconds',page:'dashboard'});
      if(!f.mains_ok) list.push({key:`pwr-${f.id}`,level:'warning',title:`${f.label} on battery (${f.battery_pct}%)`,detail:'Mains power failure, compressor stopped',page:'dashboard'});
      if(pred.forecast?.warning && f.temp_c<=8) list.push({key:`fc-${f.id}`,level:'warning',title:`${f.label} forecast ${fmtTemp(pred.forecast.predicted_c)}`,detail:'AI predicts a breach within 30 min',page:'ai'});
      if(pred.health?.score!=null && pred.health.score<70) list.push({key:`hl-${f.id}`,level:'warning',title:`${f.label} compressor weakening (${pred.health.score}/100)`,detail:'Cooling slower than its baseline',page:'ai'});
      if(f.buffered) list.push({key:`buf-${f.id}`,level:'info',title:`${f.label} offline buffer: ${f.buffered}`,detail:'Wi-Fi down, readings held on the node',page:'dashboard'});
    }
    void st;
  });
  data.batches.forEach(b=>{
    if(b.status==='Discard') list.push({key:`dis-${b.id}`,level:'danger',title:`Discard: ${b.name}`,detail:`Lot ${b.lot} used its full heat budget`,page:'inventory'});
    else if(b.status==='At Risk') list.push({key:`risk-${b.id}`,level:'warning',title:`At risk: ${b.name}`,detail:`Lot ${b.lot} · ${b.remaining_pct}% budget left`,page:'inventory'});
    if(b.expired) list.push({key:`exp-${b.id}`,level:'danger',title:`Expired: ${b.name}`,detail:`Lot ${b.lot} expired ${b.expires}`,page:'inventory'});
  });
  if(data.recommendations.length) list.push({key:'reloc',level:'warning',title:`${data.recommendations.length} relocation${data.recommendations.length>1?'s':''} suggested`,detail:'One click to confirm',page:'dashboard'});
  const order={danger:0,warning:1,info:2};
  return list.sort((a,b)=>order[a.level]-order[b.level]);
}
function renderIssues(data){
  const issues=computeIssues(data);
  const fresh=issues.filter(i=>i.level==='danger' && !state.issues.has(i.key));
  if(!state.firstIssues && fresh.length){fresh.forEach(i=>toast(`${i.title} — ${i.detail}`,'danger'));beep();}
  state.firstIssues=false;
  state.issues=new Map(issues.map(i=>[i.key,i]));
  const urgent=issues.filter(i=>i.level!=='info').length;
  $('bell-count').textContent=urgent;$('bell-count').classList.toggle('hidden',!urgent);
  $('bell-btn').classList.toggle('ringing',issues.some(i=>i.level==='danger'));
  setLiveHTML($('bell-list'),issues.length?issues.map(i=>`<button class="bell-item ${i.level}" data-open="${i.page}"><b>${esc(i.title)}</b><span>${esc(i.detail)}</span></button>`).join(''):'<div class="bell-empty">All clear. Nothing needs attention.</div>');
  const danger=issues.filter(i=>i.level==='danger');
  const banner=$('critical-banner');
  banner.classList.toggle('hidden',!danger.length);
  setHTML(banner,danger.length?`<span class="cb-ico">!</span><div><b>${esc(danger[0].title)}</b> · ${esc(danger[0].detail)}${danger.length>1?` <em>+${danger.length-1} more</em>`:''}</div><button class="btn btn-sm btn-light" data-open="${danger[0].page}">View</button>`:'');
  const fac=$('facility-status');
  fac.className='facility-status '+(danger.length?'danger':urgent?'warning':'');
  $('facility-summary').textContent=danger.length?`${danger.length} critical issue${danger.length>1?'s':''}`:urgent?`${urgent} warning${urgent>1?'s':''}`:'All systems normal';
  const aiWarn=data.fridges.some(f=>data.predictions[f.id]?.forecast?.warning||((data.predictions[f.id]?.health?.score??100)<70));
  $('ai-pill').classList.toggle('hidden',!aiWarn);
  $('sec-pill').textContent=data.rejected_24h||0;$('sec-pill').classList.toggle('hidden',!data.rejected_24h);
}
function closeBell(){$('bell-panel').classList.add('hidden');$('bell-btn').setAttribute('aria-expanded','false');}
$('bell-btn').addEventListener('click',e=>{e.stopPropagation();const p=$('bell-panel');const open=p.classList.toggle('hidden');$('bell-btn').setAttribute('aria-expanded',String(!open));});
document.addEventListener('click',e=>{if(!e.target.closest('.bell-wrap')) closeBell();});
$('sound-toggle').checked=state.sound;
$('sound-toggle').addEventListener('change',e=>{state.sound=e.target.checked;localSet('cc_sound',state.sound?'1':'0');if(state.sound) beep();});

/* ---------- inventory ---------- */
function filteredBatches(data){
  const {q,status,fridge,sort,dir}=state.inv;
  const query=q.toLowerCase();
  return data.batches.filter(b=>{
    if(query && !(`${b.name} ${b.lot}`.toLowerCase().includes(query))) return false;
    if(fridge!=='all' && b.fridge_id!==fridge) return false;
    if(status==='expired') return b.expired;
    if(status!=='all' && b.status!==status) return false;
    return true;
  }).sort((a,b)=>{const x=a[sort],y=b[sort];return (x>y?1:x<y?-1:0)*dir;});
}
function renderInventory(data){
  $('inventory-count').textContent=data.batches.length;
  $('cnt-all').textContent=data.batches.length;
  $('cnt-safe').textContent=data.batches.filter(b=>b.status==='Safe').length;
  $('cnt-risk').textContent=data.batches.filter(b=>b.status==='At Risk').length;
  $('cnt-discard').textContent=data.batches.filter(b=>b.status==='Discard').length;
  $('cnt-expired').textContent=data.batches.filter(b=>b.expired).length;
  $$('.sort-btn').forEach(b=>{b.classList.toggle('active',b.dataset.sort===state.inv.sort);b.dataset.dir=b.dataset.sort===state.inv.sort?(state.inv.dir>0?'▲':'▼'):'';});
  const rows=filteredBatches(data);
  setLiveHTML($('inventory-tbody'),rows.length?rows.map(b=>{
    const cls=statusClass(b.status);const pct=Math.max(0,Math.min(100,Number(b.remaining_pct)||0));
    const days=daysUntil(b.expires);
    const fridge=data.fridges.find(f=>f.id===b.fridge_id);
    return `<tr class="${b.status==='Discard'||b.expired?'row-danger':b.status==='At Risk'?'row-warn':''}">
      <td><button class="product-cell" data-detail="${esc(b.id)}"><strong>${esc(b.name)}</strong><small>Lot ${esc(b.lot)}</small></button></td>
      <td><span class="fridge-tag">${esc(fridgeLabel(b.fridge_id))}</span><small class="sub">${fridge?fmtTemp(fridge.temp_c):''}</small></td>
      <td><div class="budget-line"><strong>${fmtPct(b.remaining_pct)}</strong><span class="budget-bar wide"><span class="${cls}" style="width:${pct}%"></span></span></div>
        <span class="weighted-label">${(Number(b.exposure_seconds||0)/60).toFixed(1)} of 60 weighted min used</span></td>
      <td>${esc(fmtDate(b.expires))}<small class="sub ${b.expired?'bad':days<=30?'warnc':''}">${b.expired?'Expired':days===0?'Expires today':`${days} days left`}</small></td>
      <td><span class="status-pill ${cls}">${esc(b.status)}</span>${b.expired?'<span class="status-pill sm danger">Expired</span>':''}</td>
      <td>${inventoryActions(b)}</td>
    </tr>`;
  }).join(''):`<tr><td colspan="6"><div class="empty-box">${data.batches.length?'No batch matches these filters.':'No batches yet. Add one with “+ Add batch”.'}</div></td></tr>`);
}
function inventoryActions(b){
  const editor=canEdit();
  const moveDisabled=!editor||b.status==='Discard'||b.expired;
  return `<div class="action-row">
    <button class="mini-btn" data-detail="${esc(b.id)}" title="Details and public QR">QR</button>
    ${editor?`<button class="mini-btn" data-move="${esc(b.id)}" ${moveDisabled?'disabled title="Discarded or expired stock cannot be moved"':''}>Move</button>
    <button class="mini-btn" data-edit="${esc(b.id)}">Edit</button>
    <button class="mini-btn danger" data-dispose="${esc(b.id)}">Dispose</button>`:''}
    ${b.status==='Discard'&&isRole('Admin')?`<button class="mini-btn warn" data-reset="${esc(b.id)}">Reset latch</button>`:''}
  </div>`;
}
$('inv-search').addEventListener('input',e=>{state.inv.q=e.target.value;state.data&&renderInventory(state.data);});
$$('#inv-status .fchip').forEach(btn=>btn.addEventListener('click',()=>{state.inv.status=btn.dataset.status;$$('#inv-status .fchip').forEach(b=>b.classList.toggle('active',b===btn));state.data&&renderInventory(state.data);}));
$('inv-fridge').addEventListener('change',e=>{state.inv.fridge=e.target.value;state.data&&renderInventory(state.data);});
$$('.sort-btn').forEach(btn=>btn.addEventListener('click',()=>{
  if(state.inv.sort===btn.dataset.sort) state.inv.dir*=-1; else {state.inv.sort=btn.dataset.sort;state.inv.dir=1;}
  state.data&&renderInventory(state.data);
}));
document.addEventListener('click',e=>{
  const t=e.target.closest('[data-detail],[data-move],[data-edit],[data-dispose],[data-reset]');
  if(!t) return;
  if(t.dataset.detail) openDetail(t.dataset.detail);
  else if(t.dataset.move) openMove(t.dataset.move);
  else if(t.dataset.edit) openEdit(t.dataset.edit);
  else if(t.dataset.dispose) openDispose(t.dataset.dispose);
  else if(t.dataset.reset) openReset(t.dataset.reset);
});

/* ---------- modals ---------- */
let lastFocus=null;
function modal(title,html){
  lastFocus=document.activeElement;
  $('modal-title').textContent=title;
  $('modal-body').innerHTML=html;
  $('modal-backdrop').classList.remove('hidden');
  setTimeout(()=>($('modal-body').querySelector('input,select,textarea,button')||$('modal-close')).focus(),30);
}
function closeModal(){
  if($('modal-backdrop').classList.contains('hidden')) return;
  $('modal-backdrop').classList.add('hidden');$('modal-body').innerHTML='';
  lastFocus?.focus?.();
}
$('modal-close').addEventListener('click',closeModal);
$('modal-backdrop').addEventListener('click',e=>{if(e.target===$('modal-backdrop')) closeModal();});

const findBatch=id=>state.data?.batches.find(b=>b.id===id);

function openDetail(id){
  const b=findBatch(id);if(!b) return;
  const url=`${location.origin}/check/${b.public_token}`;
  const cls=statusClass(b.status);
  modal(b.name,`
    <div class="detail-grid">
      <img class="qr-image" src="/api/public/qr/${encodeURIComponent(b.public_token)}.png" alt="QR code for lot ${esc(b.lot)}">
      <div class="detail-facts">
        <span class="status-pill ${cls}">${esc(b.status)}</span>${b.expired?' <span class="status-pill danger">Expired</span>':''}
        <dl>
          <dt>Lot</dt><dd>${esc(b.lot)}</dd>
          <dt>Fridge</dt><dd>${esc(fridgeLabel(b.fridge_id))}</dd>
          <dt>Expiry</dt><dd>${esc(fmtDate(b.expires))}</dd>
          <dt>Heat budget</dt><dd>${fmtPct(b.remaining_pct)} left · ${(b.exposure_seconds/60).toFixed(1)} weighted min used</dd>
        </dl>
      </div>
    </div>
    <p class="modal-copy">Anyone can scan this QR to see the batch's live Safe / At Risk / Discard status and expiry — no login needed.</p>
    <div class="btn-row">
      <a class="btn btn-secondary" href="${esc(url)}" target="_blank" rel="noopener">Open public page ↗</a>
      <button class="btn btn-secondary" id="copy-public-url">Copy link</button>
      <button class="btn btn-primary" id="print-qr">Print label</button>
    </div>`);
  $('copy-public-url').onclick=()=>navigator.clipboard.writeText(url).then(()=>toast('Verification link copied.','success')).catch(()=>toast('Copy failed — use the link above.','error'));
  $('print-qr').onclick=()=>{
    const w=window.open('','_blank','width=420,height=560');
    if(!w){toast('Allow pop-ups to print the label.','error');return;}
    w.document.write(`<title>${esc(b.lot)}</title><body style="font-family:system-ui;text-align:center;padding:24px"><h2 style="margin:0">${esc(b.name)}</h2><p>Lot ${esc(b.lot)} · Exp ${esc(b.expires)}</p><img src="${location.origin}/api/public/qr/${encodeURIComponent(b.public_token)}.png" style="width:260px"><p style="font-size:12px">Scan to verify cold-chain status</p></body>`);
    w.document.close();
    // Inline onload would be blocked by the CSP, so trigger printing from this page instead.
    const img=w.document.querySelector('img');
    const go=()=>setTimeout(()=>w.print(),150);
    if(img.complete) go(); else img.onload=go;
  };
}

function openMove(id){
  const b=findBatch(id);if(!b) return;
  const options=state.data.fridges.filter(f=>f.id!==b.fridge_id).map(f=>{
    const st=fridgeState(f,state.data.predictions[f.id]);
    const ok=f.online && f.temp_c>=2 && f.temp_c<=8 && f.mains_ok && !f.door_open;
    return `<label class="radio-card ${ok?'':'disabled'}"><input type="radio" name="dest" value="${esc(f.id)}" ${ok?'':'disabled'}>
      <span><b>${esc(f.label)}</b><small>${fmtTemp(f.temp_c)} · ${st.label}${ok?'':' · not eligible'}</small></span></label>`;
  }).join('');
  modal('Move batch',`
    <div class="note-box"><strong>${esc(b.name)}</strong> · Lot ${esc(b.lot)}<br>Now in ${esc(fridgeLabel(b.fridge_id))}. Its exposure history (${(b.exposure_seconds/60).toFixed(1)} min) moves with it.</div>
    <fieldset class="radio-list"><legend>Destination</legend>${options}</fieldset>
    <p class="hint">Destination must be online, 2–8°C, on mains power, door closed.</p>
    <button class="btn btn-primary btn-block" id="submit-move">Confirm move</button>`);
  const first=$('modal-body').querySelector('input[name=dest]:not([disabled])');if(first) first.checked=true;
  $('submit-move').onclick=()=>{
    const dest=$('modal-body').querySelector('input[name=dest]:checked');
    if(!dest){toast('No eligible destination fridge right now.','error');return;}
    runAction(()=>api(`/api/batches/${id}/move`,{method:'POST',body:JSON.stringify({fridge_id:dest.value})}),`Moved to ${fridgeLabel(dest.value)}. Move the stock physically too.`);
  };
}

function batchForm(b){
  const min=new Date().toISOString().slice(0,10);
  return `<form id="batch-form" class="stack-form">
    <label for="batch-name">Product / vaccine name</label>
    <input id="batch-name" required minlength="2" maxlength="140" placeholder="e.g. Insulin glargine" value="${esc(b?.name||'')}">
    <label for="batch-lot">Lot number</label>
    <input id="batch-lot" required minlength="2" maxlength="80" placeholder="e.g. LOT-2026-001" value="${esc(b?.lot||'')}">
    <label for="batch-exp">Expiry date</label>
    <input id="batch-exp" type="date" required min="${min}" value="${esc(b?.expires||'')}">
    ${b?'':`<label for="batch-fridge">Storage fridge</label>
    <select id="batch-fridge">${state.data.fridges.map(f=>`<option value="${f.id}">${esc(f.label)} · ${fmtTemp(f.temp_c)}</option>`).join('')}</select>`}
    <div class="form-error error" id="form-error"></div>
    <button class="btn btn-primary btn-block" type="submit">${b?'Save changes':'Register batch'}</button>
  </form>`;
}
$('new-batch-btn').addEventListener('click',()=>{
  modal('Register a batch',batchForm(null));
  $('batch-form').addEventListener('submit',async e=>{
    e.preventDefault();
    await runAction(()=>api('/api/batches',{method:'POST',body:JSON.stringify({name:$('batch-name').value.trim(),lot:$('batch-lot').value.trim(),expires:$('batch-exp').value,fridge_id:$('batch-fridge').value})}),'Batch registered. A public QR code is ready.',true);
  });
});
function openEdit(id){
  const b=findBatch(id);if(!b) return;
  modal('Edit batch',batchForm(b));
  $('batch-form').addEventListener('submit',async e=>{
    e.preventDefault();
    const body={};const name=$('batch-name').value.trim(),lot=$('batch-lot').value.trim(),exp=$('batch-exp').value;
    if(name!==b.name) body.name=name; if(lot!==b.lot) body.lot=lot; if(exp!==b.expires) body.expires=exp;
    if(!Object.keys(body).length){closeModal();return;}
    await runAction(()=>api(`/api/batches/${id}`,{method:'PATCH',body:JSON.stringify(body)}),'Batch updated and recorded in the audit log.',true);
  });
}
function openDispose(id){
  const b=findBatch(id);if(!b) return;
  modal('Dispose batch',`
    <div class="warning-box">This removes <b>${esc(b.name)}</b> (lot ${esc(b.lot)}) from inventory. The disposal and reason are kept in the tamper-evident audit log.</div>
    <form id="dispose-form" class="stack-form">
      <label for="dispose-reason">Reason</label>
      <select id="dispose-reason"><option>Heat budget exhausted (discard)</option><option>Expired</option><option>Damaged packaging</option><option>Administered / used</option><option>Data entry error</option></select>
      <div class="form-error error" id="form-error"></div>
      <button class="btn btn-danger btn-block" type="submit">Dispose batch</button>
    </form>`);
  if(b.expired) $('dispose-reason').value='Expired';
  else if(b.status!=='Discard') $('dispose-reason').value='Administered / used';
  $('dispose-form').addEventListener('submit',async e=>{
    e.preventDefault();
    await runAction(()=>api(`/api/batches/${id}`,{method:'DELETE',body:JSON.stringify({reason:$('dispose-reason').value})}),'Batch disposed and logged.',true);
  });
}
function openReset(id){
  const b=findBatch(id);if(!b) return;
  modal('Admin latch reset',`
    <div class="warning-box"><strong>Safety warning:</strong> resetting the software discard latch turns the red LED off. It does <b>not</b> restore potency. Quarantine and a professional review are still required.</div>
    <div class="note-box">Lot <strong>${esc(b.lot)}</strong> — ${esc(b.name)}</div>
    <label class="check-inline"><input type="checkbox" id="reset-ack"> I have quarantined this stock and understand the risk</label>
    <button class="btn btn-danger btn-block" id="submit-reset" disabled>Reset latch</button>`);
  $('reset-ack').onchange=e=>{$('submit-reset').disabled=!e.target.checked;};
  $('submit-reset').onclick=()=>runAction(()=>api(`/api/batches/${id}/admin-reset`,{method:'POST'}),'Latch reset recorded. Clinical review still required.');
}

async function runAction(fn,successMessage,inForm=false){
  try{await fn();closeModal();toast(successMessage,'success');await refresh(false,true);}
  catch(err){
    if(inForm && $('form-error')) $('form-error').textContent=err.message;
    else toast(err.message,'error');
    $$('.rec-btn').forEach(b=>{b.disabled=!canEdit();b.textContent='Move';});
  }
}

/* ---------- AI page ---------- */
function renderAiLive(data){
  setHTML($('ai-live'),data.fridges.map(f=>{
    const p=data.predictions[f.id]||{};const fc=p.forecast||{};const h=p.health||{};
    const warn=fc.warning;const delta=fc.predicted_c!=null&&f.temp_c!=null?fc.predicted_c-f.temp_c:null;
    return `<article class="surface ai-card ${warn?'warning':''}">
      <div class="block-head compact"><div><span class="section-label">${esc(f.id)}</span><h3>${esc(f.label)}</h3></div><span class="status-pill ${warn?'warning':'safe'}">${warn?'Breach risk':'No risk'}</span></div>
      <div class="fc-flow">
        <div><span>Now</span><b>${fmtTemp(f.temp_c)}</b></div>
        <div class="fc-arrow ${warn?'warn':''}">${delta==null?'→':`${delta>=0?'+':''}${delta.toFixed(1)}°`}<i>30 min</i></div>
        <div class="${warn?'bad':''}"><span>Predicted</span><b>${fmtTemp(fc.predicted_c)}</b></div>
      </div>
      <div class="fc-facts">
        <span>Trend <b>${fc.slope_c_per_min==null?'—':`${fc.slope_c_per_min>0?'+':''}${fc.slope_c_per_min.toFixed(2)}°C/min`}</b></span>
        <span>Straight-line trend hits 8°C <b>${f.temp_c>8?'already above':fc.minutes_to_8c!=null?`~${Math.round(fc.minutes_to_8c)} min`:'never'}</b></span>
        <span>Model <b>${esc(fc.method||'—')}</b></span>
      </div>
      <div class="health-row">
        ${healthRing(h.score,76,'ai'+f.id)}
        <div><b>Compressor health ${h.score==null?'':`· ${h.trend==='weakening'?'weakening':'normal'}`}</b>
          <small>${esc(h.note||'')}</small>
          ${h.recent_rate!=null?`<div class="rate-bars"><span>Latest run</span><i style="width:${Math.max(2,Math.min(100,100*h.recent_rate/Math.max(h.baseline_rate||1,0.01)))}%"></i><span>Baseline</span><i class="base" style="width:100%"></i></div>`:''}
        </div>
      </div>
    </article>`;
  }).join(''));
  animateIn($('ai-live'));
}
async function loadAiReport(){
  if(state.aiReport){renderAiReport(state.aiReport);return;}
  try{state.aiReport=await api('/api/ai/report');renderAiReport(state.aiReport);}
  catch(err){setHTML($('ai-report'),`<div class="empty-box">${esc(err.message)}</div>`);}
}
function renderAiReport(r){
  const m=r.metrics,d=r.dataset;
  if(!m){setHTML($('ai-report'),'<div class="empty-box">Model metrics not found. Run train_model.py.</div>');return;}
  const imp=Object.entries(m.feature_importances).sort((a,b)=>b[1]-a[1]);
  const [tn,fp,fn,tp]=m.breach_confusion_matrix_tn_fp_fn_tp;
  setHTML($('ai-report'),`
    <div class="block-head compact"><div><span class="section-label">Model report</span><h3>Dataset, features and results</h3></div><span class="ai-chip">${esc(d.model)}</span></div>
    <div class="metric-strip">
      <div><b>${m.mean_absolute_error_c}°C</b><span>Mean abs. error</span></div>
      <div><b>${m.root_mean_squared_error_c}°C</b><span>RMSE</span></div>
      <div><b>${Math.round(m.breach_precision*100)}%</b><span>Breach precision</span></div>
      <div><b>${Math.round(m.breach_recall*100)}%</b><span>Breach recall</span></div>
      <div><b>${m.breach_f1}</b><span>F1 score</span></div>
    </div>
    <div class="report-grid">
      <div>
        <h4>Dataset</h4>
        <ul class="facts">
          <li>${esc(d.source)}</li>
          <li>${m.train_rows.toLocaleString()} training rows / ${m.test_rows.toLocaleString()} test rows (${m.distinct_test_trajectories} unseen runs)</li>
          <li>${esc(d.split)}</li>
          <li>Target: ${esc(d.target)}</li>
          ${d.disturbances.map(x=>`<li>${esc(x)}</li>`).join('')}
        </ul>
        <h4>Breach detection (test set)</h4>
        <div class="confusion">
          <span></span><span class="ch">Pred. safe</span><span class="ch">Pred. breach</span>
          <span class="rh">Actual safe</span><b class="good">${tn}</b><b class="bad">${fp}</b>
          <span class="rh">Actual breach</span><b class="bad">${fn}</b><b class="good">${tp}</b>
        </div>
      </div>
      <div>
        <h4>Features (importance)</h4>
        <div class="imp-list">${imp.map(([k,v])=>`<div class="imp-row" title="${esc(d.feature_help[k]||'')}"><span>${esc(k)}<small>${esc(d.feature_help[k]||'')}</small></span><i style="width:${Math.max(2,v*100)}%"></i><b>${(v*100).toFixed(1)}%</b></div>`).join('')}</div>
        <h4>Compressor health method</h4><p class="muted-p">${esc(d.health_method)}</p>
      </div>
      ${r.has_plot?`<figure class="plot"><img src="/api/ai/validation.png" alt="Predicted vs actual temperature 30 minutes ahead on the test set" loading="lazy"><figcaption>Predicted vs actual temperature 30 min ahead, unseen test runs. Dotted lines mark 8°C.</figcaption></figure>`:''}
    </div>
    <details class="limits"><summary>Limitations (${m.limitations.length})</summary><ul>${m.limitations.map(x=>`<li>${esc(x)}</li>`).join('')}</ul><p class="muted-p">${esc(m.data_provenance)}</p></details>`);
}

/* ---------- security ---------- */
let _tamperActive=false;
function chainViz(records,brokenId){
  return records.slice(0,6).reverse().map((r,i,arr)=>`
    <div class="block ${brokenId&&r.id>=brokenId?'broken':''}">
      <span>#${r.id}</span><b>${esc((EVENT_TITLES[r.action]||r.action).slice(0,18))}</b>
      <code>prev ${esc((r.prev_hash||'').slice(0,8))}…</code><code>hash ${esc((r.digest||'').slice(0,8))}…</code>
    </div>${i<arr.length-1?'<i class="link">⟶</i>':''}`).join('');
}
$('verify-btn').addEventListener('click',async()=>{
  const btn=$('verify-btn');btn.disabled=true;btn.textContent='Verifying…';
  try{
    const result=await api('/api/integrity/verify');
    const box=$('integrity-result');
    box.className='integrity-box '+(result.valid?'ok':'fail');
    if(result.valid){
      box.innerHTML=`<b>Verified.</b> All ${result.checked.toLocaleString()} chained records match. Latest hash <code>${esc(result.latest_hash.slice(0,16))}…</code>`;
      toast('Hash chain verified — no edits detected.','success');
    }else{
      const br=result.broken_record?readableEvent(result.broken_record):null;
      box.innerHTML=`<b>Tampering detected at record #${result.first_broken_id}.</b> ${result.reason==='reading_record_differs_from_audit'?'A stored sensor reading no longer matches its signed, chained copy.':'The hash chain is broken (a record was edited or removed).'}${br?`<br><small>${esc(br.title)} · ${esc(br.detail)}</small>`:''}`;
      toast('Integrity check FAILED — an edited record was detected.','danger');
    }
    await loadAudit(result.valid?null:result.first_broken_id);
  }catch(err){toast(err.message,'error');}
  finally{btn.disabled=false;btn.textContent='Verify integrity';}
});
$('tamper-btn').addEventListener('click',async()=>{
  try{
    const r=await api('/api/simulator/tamper',{method:'POST',body:JSON.stringify({action:'tamper'})});
    _tamperActive=true;$('restore-btn').classList.remove('hidden');$('tamper-btn').classList.add('hidden');
    $('integrity-result').className='integrity-box warnbox';
    $('integrity-result').innerHTML=`<b>Simulated attacker</b> changed ${esc(fridgeLabel(r.fridge))} reading #${r.seq} from ${fmtTemp(r.original)} to ${fmtTemp(r.forged)} directly in the database. Now press <b>Verify integrity</b>.`;
    toast('A past reading was edited in the database. Run Verify integrity.','info');
  }catch(err){toast(err.message,'error');}
});
$('restore-btn').addEventListener('click',async()=>{
  try{
    await api('/api/simulator/tamper',{method:'POST',body:JSON.stringify({action:'restore'})});
    _tamperActive=false;$('restore-btn').classList.add('hidden');$('tamper-btn').classList.remove('hidden');
    $('integrity-result').className='integrity-box';$('integrity-result').innerHTML='Original value restored. Verify again to confirm the chain is valid.';
    toast('Tampered reading restored.','success');
  }catch(err){toast(err.message,'error');}
});
$$('.attack-btn').forEach(btn=>btn.addEventListener('click',async()=>{
  btn.disabled=true;
  try{
    const r=await api('/api/simulator/attack',{method:'POST',body:JSON.stringify({kind:btn.dataset.attack})});
    const box=$('attack-result');box.classList.remove('hidden');
    box.className='attack-result '+(r.outcome==='rejected'?'ok':'fail');
    box.innerHTML=r.outcome==='rejected'?`${icon('shield')}<span><b>Blocked.</b> ${esc(btn.querySelector('b').textContent)} → <code>${esc(r.reason)}</code>, logged below.</span>`:`<b>Accepted?!</b> ${esc(r.reason)}`;
    await loadRejections();await refresh();
  }catch(err){toast(err.message,'error');}
  finally{btn.disabled=false;}
}));
async function loadRejections(){
  try{
    const rows=await api('/api/security/rejections');
    $('rej-count').textContent=rows.length;
    setHTML($('rejection-list'),rows.length?`<table class="mini-table"><thead><tr><th>Time</th><th>Device</th><th>Reason</th></tr></thead><tbody>${rows.slice(0,30).map(r=>`<tr><td>${esc(fmtDateTime(r.at))}</td><td><code>${esc(r.device_id)}</code></td><td><span class="reason-tag">${esc(String(r.reason).replace(/_/g,' '))}</span></td></tr>`).join('')}</tbody></table>`:'<div class="empty-box">No rejected packets. Try an attack above.</div>');
  }catch(err){
    setHTML($('rejection-list'),`<div class="empty-box">${esc(err.message)}</div>`);
  }
}
async function loadAudit(brokenId=null){
  try{
    const events=await api('/api/audit?limit=200');
    $('chain-viz').innerHTML=chainViz(events,brokenId);
    const showReadings=$('show-readings').checked;
    const list=events.filter(e=>showReadings||e.action!=='reading').slice(0,60);
    setHTML($('audit-list'),list.length?list.map(e=>eventItem(e,true)).join(''):`<div class="empty-box">No audit records.</div>`);
  }catch(err){toast(err.message,'error');}
}
$('show-readings').addEventListener('change',()=>loadAudit());
$('csv-link').addEventListener('click',async e=>{
  e.preventDefault();
  try{
    const response=await fetch('/api/readings/export.csv',{headers:{Authorization:'Bearer '+state.token}});
    if(!response.ok) throw new Error('CSV export failed.');
    const url=URL.createObjectURL(await response.blob());
    const link=document.createElement('a');link.href=url;link.download='coldchain_readings.csv';link.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
    toast('Readings CSV downloaded.','success');
  }catch(err){toast(err.message,'error');}
});

/* ---------- users ---------- */
async function loadUsers(){
  if(!isRole('Admin')) return;
  try{
    const users=await api('/api/admin/users');
    const pending=users.filter(u=>u.requested_role);
    $('req-tag').textContent=pending.length?`${pending.length} pending request${pending.length>1?'s':''}`:'no pending requests';
    $('req-tag').classList.toggle('warn',!!pending.length);
    setHTML($('user-list'),`<table class="mini-table users"><thead><tr><th>User</th><th>Role</th><th>Status</th></tr></thead><tbody>${users.sort((a,b)=>(b.requested_role?1:0)-(a.requested_role?1:0)).map(u=>{
      const self=u.username===state.user.username;
      const req=u.requested_role?`<div class="req-row"><span class="req-badge">requests ${esc(u.requested_role)}</span><button class="mini-btn ok" data-approve="${u.id}" data-role="${esc(u.requested_role)}">${icon('check')}Approve</button></div>`:'';
      return `<tr class="${u.requested_role?'row-req':''}"><td><span class="avatar sm">${esc(u.username.slice(0,2).toUpperCase())}</span> <b>${esc(u.username)}</b>${self?' <small>(you)</small>':''}${req}</td>
      <td><select class="role-select" data-user="${u.id}" ${self?'disabled':''} aria-label="Role for ${esc(u.username)}">${['Admin','Pharmacist','Inspector'].map(r=>`<option ${r===u.role?'selected':''}>${r}</option>`).join('')}</select></td>
      <td><button class="toggle ${u.enabled?'on':''}" data-user-toggle="${u.id}" data-enabled="${u.enabled?1:0}" ${self?'disabled':''} role="switch" aria-checked="${!!u.enabled}" aria-label="Enable ${esc(u.username)}"></button> <small>${u.enabled?'Active':'Disabled'}</small></td></tr>`;}).join('')}</tbody></table>`);
  }catch(err){toast(err.message,'error');}
}
document.addEventListener('change',async e=>{
  const sel=e.target.closest('.role-select');if(!sel) return;
  try{await api(`/api/admin/users/${sel.dataset.user}`,{method:'PATCH',body:JSON.stringify({role:sel.value})});toast('Role updated.','success');}
  catch(err){toast(err.message,'error');}
  loadUsers();
});
document.addEventListener('click',async e=>{
  const ap=e.target.closest('[data-approve]');if(!ap) return;
  ap.disabled=true;
  try{await api(`/api/admin/users/${ap.dataset.approve}`,{method:'PATCH',body:JSON.stringify({role:ap.dataset.role})});toast(`Approved as ${ap.dataset.role}.`,'success');}
  catch(err){toast(err.message,'error');}
  loadUsers();refreshRequests();
});
async function refreshRequests(){
  if(!isRole('Admin')) return;
  try{const n=(await api('/api/admin/users')).filter(u=>u.requested_role).length;$('req-pill').textContent=n;$('req-pill').classList.toggle('hidden',!n);}catch{}
}
document.addEventListener('click',async e=>{
  const t=e.target.closest('[data-user-toggle]');if(!t) return;
  try{await api(`/api/admin/users/${t.dataset.userToggle}`,{method:'PATCH',body:JSON.stringify({enabled:t.dataset.enabled!=='1'})});toast('Account updated.','success');}
  catch(err){toast(err.message,'error');}
  loadUsers();
});
$('user-form').addEventListener('submit',async e=>{
  e.preventDefault();
  try{
    await api('/api/admin/users',{method:'POST',body:JSON.stringify({username:$('nu-name').value.trim(),password:$('nu-pass').value,role:$('nu-role').value})});
    toast(`User ${$('nu-name').value.trim()} created.`,'success');e.target.reset();loadUsers();
  }catch(err){toast(err.message,'error');}
});

/* ---------- simulation lab ---------- */
const QUICK={
  door:['FRIDGE_A',{door_open:true},'Door opened on Fridge Alpha. Watch the door timer; at 60 s the buzzer icon sounds and an alert is logged.'],
  power:['FRIDGE_A',{mains_ok:false},'Mains cut on Fridge Alpha: compressor stops, battery % starts falling, card shows Battery.'],
  wifi:['FRIDGE_A',{wifi_ok:false},'Wi-Fi dropped on Fridge Alpha: readings now queue on the node (see Q: on the OLED). Restore Wi-Fi to sync them in order.'],
  weak:['FRIDGE_A',{degraded:true},'Fridge Alpha compressor weakened. Health drops after its next cooling run (starts at 7°C).'],
};
$$('.quick').forEach(btn=>btn.addEventListener('click',async()=>{
  const [fid,body,msg]=QUICK[btn.dataset.quick];
  btn.disabled=true;
  try{
    await api(`/api/simulator/${fid}/control`,{method:'POST',body:JSON.stringify(body)});
    feedback(`${msg} <button class="link-btn" data-open="dashboard">Watch on Overview →</button>`);
    toast('Scenario started.','success');await loadControls(true);await refresh(false,true);
  }catch(err){feedback(esc(err.message),true);}
  finally{btn.disabled=false;}
}));
function feedback(html,error=false){$('scenario-feedback').className='scenario-feedback'+(error?' error':'');$('scenario-feedback').innerHTML=html;}
$('sim-reset-btn').addEventListener('click',async()=>{
  try{await api('/api/simulator/reset',{method:'POST'});feedback('Both nodes back to normal: door closed, mains on, Wi-Fi on, healthy compressor, no thermal load.');toast('Simulation reset.','success');await loadControls(true);await refresh(false,true);}
  catch(err){feedback(esc(err.message),true);}
});
$$('.scenario-exposure').forEach(btn=>btn.addEventListener('click',async()=>{
  $$('.scenario-exposure').forEach(b=>b.disabled=true);
  try{
    const r=await api('/api/simulator/round1/exposure',{method:'POST',body:JSON.stringify({scenario:btn.dataset.scenario})});
    feedback(`<b>${esc(r.status)}</b> — ${esc(String(r.remaining_pct))}% budget left. ${esc(r.scenario_formula)}. <button class="link-btn" data-open="inventory">See lot ${esc(r.lot)} in Inventory →</button>`);
    await refresh();
  }catch(err){feedback(esc(err.message),true);}
  finally{$$('.scenario-exposure').forEach(b=>b.disabled=false);}
}));
$('round1-forecast-btn').addEventListener('click',async e=>{
  const btn=e.currentTarget;btn.disabled=true;
  try{
    const r=await api('/api/simulator/round1/forecast',{method:'POST',body:JSON.stringify({scenario:'rising_risk'})});
    const ahead=r.predictions.FRIDGE_A?.forecast?.predicted_c;
    feedback(`Fridge Alpha is warming under load with a weak compressor. 30-min forecast: <b>${ahead==null?'pending':fmtTemp(ahead)}</b>. Relocation advice appears within ~10 s. <button class="link-btn" data-open="ai">Open AI insights →</button>`);
    await refresh();
  }catch(err){feedback(esc(err.message),true);}
  finally{btn.disabled=false;}
});

const LAB_SWITCHES=[
  ['door_open','Door open','Alarm + alert after 60 s'],
  ['mains_ok','Mains power','Off = battery mode, compressor stops'],
  ['wifi_ok','Wi-Fi','Off = buffer readings, replay in order'],
  ['degraded','Weak compressor','Cools ~60% slower'],
  ['heat_spike','Thermal load','Warm item / hot room'],
];
async function loadControls(force=false){
  if(!state.data?.demo || !canEdit()) return;
  const prev=state.force;if(force) state.force=true;
  try{
    const controls=await api('/api/simulator/controls');
    setLiveHTML($('lab-controls'),controls.map(c=>`
      <article class="surface lab-card">
        <div class="block-head compact"><div><span class="section-label">Simulated ESP32</span><h3>${esc(fridgeLabel(c.fridge_id))}</h3></div>
          <span class="status-pill ${c.sim_temp>8||c.sim_temp<2?'danger':c.sim_temp>=7?'warning':'safe'}">${c.sim_temp==null?'—':fmtTemp(c.sim_temp)}</span></div>
        <div class="lab-state">
          <span>${icon('fan',c.sim_compressor?'spin':'')} compressor ${c.sim_compressor?'on':'off'}</span>
          <span>Min off-time ${c.min_off_remaining?`${c.min_off_remaining}s left`:'satisfied'}</span>
          <span>Battery ${c.battery??'—'}%</span>
          <span class="${c.buffered?'warnc':''}">Buffered ${c.buffered??0}</span>
        </div>
        <p class="hint">Thermostat: ON at 7°C, OFF at 3°C, 60 s minimum off-time.</p>
        ${LAB_SWITCHES.map(([key,label,desc])=>`
          <div class="toggle-row"><div><strong>${esc(label)}</strong><small>${esc(desc)}</small></div>
            <button class="toggle ${c[key]?'on':''}" role="switch" aria-checked="${!!c[key]}" aria-label="${esc(label)} on ${esc(fridgeLabel(c.fridge_id))}" data-fridge="${esc(c.fridge_id)}" data-key="${esc(key)}" data-value="${c[key]?1:0}"></button></div>`).join('')}
      </article>`).join(''));
  }catch(err){toast(err.message,'error');}
  finally{state.force=prev;}
}
document.addEventListener('click',async e=>{
  const t=e.target.closest('#lab-controls .toggle');if(!t) return;
  t.disabled=true;
  try{
    await api(`/api/simulator/${t.dataset.fridge}/control`,{method:'POST',body:JSON.stringify({[t.dataset.key]:t.dataset.value!=='1'})});
    await loadControls(true);await refresh(false,true);
  }catch(err){toast(err.message,'error');t.disabled=false;}
});

/* ---------- data refresh ---------- */
async function loadHistory(){
  if(!state.data) return;
  const ids=state.data.fridges.map(f=>f.id);
  try{
    const rows=await Promise.all(ids.map(id=>api(`/api/fridges/${id}/history?limit=${state.range}`)));
    ids.forEach((id,i)=>{state.history[id]=rows[i];});
  }catch{}
  renderFridges(state.data);
}

async function refresh(manual=false,force=false){
  if(!state.token || state.refreshing) return;
  state.refreshing=true;state.force=force||manual;
  try{
    const data=await api('/api/dashboard');
    state.data=data;
    state.skew=Date.now()-new Date(data.generated_at).getTime();
    $('connection-status').textContent='Live';
    $('sync-pill').classList.remove('offline');
    $('demo-notice').classList.toggle('hidden',!data.demo);
    applyRoleVisibility();
    if(state.pendingPage){const p=state.pendingPage;state.pendingPage=null;if(p!==state.page && pageAllowed(p)) setPage(p,false);}
    renderMetrics(data);
    renderIssues(data);
    renderRecommendations(data);
    renderEvents(data);
    renderInventory(data);
    renderAiLive(data);
    await loadHistory();
    if(window.HW) HW.update(data);
    if(state.page==='lab') loadControls();
    if(state.page==='security') loadRejections();
    refreshRequests();
    if(manual) toast('Dashboard refreshed.','success');
  }catch(err){
    $('connection-status').textContent='Connection lost';
    $('sync-pill').classList.add('offline');
    if(manual) toast(err.message,'error');
  }finally{state.refreshing=false;state.force=false;}
}

async function markOperationMode(){
  try{
    const response=await fetch('/health',{cache:'no-store'});
    if(!response.ok) return;
    const details=await response.json();
    if(details.demo===false){
      $('demo-cred-list').classList.add('hidden');
      $('login-title').textContent='On-site hardware sign in';
      $('login-subtitle').textContent='Use your Admin, Pharmacist or Inspector credentials.';
      $('login-mode-notice').innerHTML='<strong>Live hardware mode:</strong> simulation controls are disabled. Read private passwords from ONSITE_PRIVATE_CREDENTIALS.txt on this PC. Hackathon prototype, not certified medical monitoring.';
      $('facility-name').textContent='On-site facility';
    }
  }catch{ /* the login error explains a stopped backend */ }
}

setInterval(()=>{if(state.token && !document.hidden) refresh();},5000);
document.addEventListener('visibilitychange',()=>{if(!document.hidden && state.token) refresh();});
hydrateIcons();
markOperationMode();
restore();
