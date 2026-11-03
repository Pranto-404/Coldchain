'use strict';
/* Hardware view: an interactive drawing of one ESP32 fridge node.
   The scene is built once per node and then only its attributes/classes change, so the
   CSS transitions (door swing, relay, LEDs, fan) actually play instead of being re-created
   every 5 s. Uses globals from app.js (state, api, esc, icon, fridgeState, ...). */
(function(){
  const NS='http://www.w3.org/2000/svg';
  const PINS=[
    ['GPIO4','DS18B20 probe','temp'],['GPIO18','Door reed switch','door'],['GPIO19','Compressor relay','relay'],
    ['GPIO21/22','OLED (I²C SDA/SCL)','oled'],['GPIO25','Red LED','red'],['GPIO26','Green LED','green'],
    ['GPIO27','Buzzer','buzz'],['GPIO32','Mains-fail button','btn'],['GPIO34','Battery (ADC)','batt'],
  ];
  const hw={fid:'FRIDGE_A',built:null,prev:{},controls:{},serial:[],sceneEl:null,visible:false};

  function interior(t){
    // cold blue -> neutral -> warm as the cabinet heats up
    if(t==null) return '#e7eaee';
    const stops=[[0,[198,222,255]],[4,[226,238,252]],[8,[246,240,226]],[12,[250,214,204]],[20,[246,190,180]]];
    for(let i=1;i<stops.length;i++){
      const [a,ca]=stops[i-1],[b,cb]=stops[i];
      if(t<=b){const k=Math.max(0,(t-a)/(b-a));return `rgb(${ca.map((c,j)=>Math.round(c+(cb[j]-c)*k)).join(',')})`;}
    }
    return 'rgb(246,190,180)';
  }

  function sceneSvg(f,batches){
    const vials=batches.slice(0,15).map((b,i)=>{
      const row=Math.floor(i/5),col=i%5,x=60+col*40,y=[128,208,288][row];
      return `<g class="vial ${statusClass(b.status)}" transform="translate(${x} ${y})"><title>${esc(b.name)} · ${esc(b.lot)} · ${esc(b.status)} · ${Math.round(b.remaining_pct)}% budget</title>
        <rect x="0" y="0" width="16" height="6" rx="1.5" class="cap"/><rect x="1" y="5" width="14" height="25" rx="3" class="glass"/><rect x="2.5" y="${5+25*(1-Math.max(.15,b.remaining_pct/100))}" width="11" height="${25*Math.max(.15,b.remaining_pct/100)-1.5}" rx="2" class="liquid"/></g>`;
    }).join('');
    const pinL=[['GPIO4',252],['GPIO18',278],['GPIO19',304],['GPIO21',330],['GPIO22',343]];
    const pinR=[['GPIO25',252],['GPIO26',278],['GPIO27',304],['GPIO32',330],['GPIO34',356]];
    const header=x=>Array.from({length:15},(_,i)=>`<rect x="${x}" y="${239+i*13}" width="7" height="7" class="pin"/>`).join('');
    return `<svg viewBox="0 0 1000 560" class="hw-svg" role="img" aria-label="ESP32 node ${esc(f.id)} wired to ${esc(f.label)}">
  <defs>
    <filter id="glow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <pattern id="vent" width="8" height="8" patternUnits="userSpaceOnUse"><path d="M0 4h8" class="vent-line"/></pattern>
  </defs>

  <!-- wires (drawn first so parts sit on top) -->
  <path id="w-temp" class="wire w-temp" d="M246 196 C300 196 300 150 330 150 S400 252 438 252"/>
  <path id="w-door" class="wire w-door" d="M292 112 C350 112 380 278 438 278"/>
  <path id="w-relay" class="wire w-relay" d="M438 304 C400 304 400 470 375 482"/>
  <path id="w-comp" class="wire w-comp thick" d="M330 505 C290 505 270 455 240 446"/>
  <path id="w-i2c" class="wire w-i2c" d="M438 330 C410 330 410 160 470 150"/>
  <path class="wire w-i2c" d="M438 343 C404 343 404 160 490 150"/>
  <path id="w-red" class="wire w-red" d="M580 252 L652 252"/>
  <path id="w-green" class="wire w-green" d="M580 278 C610 278 620 292 652 292"/>
  <path id="w-buzz" class="wire w-buzz" d="M580 304 C610 304 620 340 640 340"/>
  <path id="w-btn" class="wire w-btn" d="M580 330 C610 330 615 398 640 398"/>
  <path id="w-batt" class="wire w-batt" d="M580 356 C600 356 600 456 620 456"/>

  <!-- network paths -->
  <path id="p-up" class="net" d="M505 196 C560 110 700 100 820 118"/>
  <path id="p-down" class="net" d="M900 146 L900 230"/>
  <path id="p-db" class="net" d="M900 286 L900 372"/>
  <path id="p-ack" class="net ack" d="M820 262 C720 262 640 226 578 226"/>
  <path id="p-q" class="net q" d="M560 430 C640 520 740 520 820 506"/>
  <path id="p-qout" class="net q-out" d="M900 478 C990 420 990 160 980 132"/>

  <!-- FRIDGE -->
  <g class="fridge">
    <rect x="30" y="30" width="250" height="440" rx="9" class="cab"/>
    <rect x="46" y="80" width="218" height="292" rx="3" class="interior" id="hw-interior"/>
    <g class="shelves"><path d="M50 158H260M50 238H260M50 318H260"/></g>
    <g id="hw-vials">${vials||'<text x="155" y="230" text-anchor="middle" class="empty-txt">no stock</text>'}</g>
    <g id="hw-frost" class="frost">${Array.from({length:10},(_,i)=>`<circle cx="${62+i*20}" cy="${92+(i%3)*8}" r="1.6" style="animation-delay:${(i*0.37).toFixed(2)}s"/>`).join('')}</g>
    <g class="probe"><rect x="234" y="182" width="12" height="28" rx="5"/><text x="240" y="224" text-anchor="middle">DS18B20</text></g>
    <rect x="110" y="40" width="90" height="28" rx="3" class="cab-disp"/>
    <text x="155" y="60" text-anchor="middle" class="cab-disp-txt mono" id="hw-cab-temp">--.-°C</text>
    <g class="comp-bay">
      <rect x="30" y="380" width="250" height="90" rx="0" class="bay"/>
      <rect x="30" y="380" width="250" height="90" fill="url(#vent)" opacity=".5"/>
      <rect x="58" y="398" width="76" height="56" rx="12" class="comp-drum"/>
      <text x="96" y="430" text-anchor="middle" class="part-txt">COMPRESSOR</text>
      <circle cx="210" cy="426" r="32" class="fan-ring"/>
      <g id="hw-fan" class="fan-blades"><path d="M210 426 C200 404 216 398 222 404 C226 410 218 420 210 426 Z"/><path d="M210 426 C232 416 238 432 232 438 C226 442 216 434 210 426 Z"/><path d="M210 426 C220 448 204 454 198 448 C194 442 202 432 210 426 Z"/><path d="M210 426 C188 436 182 420 188 414 C194 410 204 418 210 426 Z"/><circle cx="210" cy="426" r="4"/></g>
    </g>
    <g id="hw-heat" class="heat"><path d="M292 450 q8 -10 0 -20 q-8 -10 0 -20"/><path d="M306 456 q8 -10 0 -20 q-8 -10 0 -20 q8 -10 0 -20"/><path d="M320 450 q8 -10 0 -20 q-8 -10 0 -20"/></g>
    <g class="reed"><rect x="282" y="98" width="10" height="26" rx="2"/><text x="300" y="94" class="part-txt">REED</text></g>
    <g id="hw-door" class="door" tabindex="0" role="button" aria-label="Fridge door">
      <rect x="30" y="72" width="250" height="306" rx="6" class="glass-door"/>
      <path d="M70 92 L120 92 L60 220 L46 220 Z M140 92 L160 92 L80 260 L66 260 Z" class="glint"/>
      <rect x="258" y="170" width="8" height="70" rx="3" class="handle"/>
      <rect x="268" y="100" width="9" height="22" rx="2" class="magnet"/>
    </g>
    <text x="155" y="492" text-anchor="middle" class="caption" id="hw-fridge-cap">${esc(f.label)}</text>
  </g>

  <!-- RELAY -->
  <g class="relay" id="hw-relay">
    <rect x="330" y="470" width="96" height="62" rx="4" class="pcb-blue"/>
    <rect x="342" y="480" width="34" height="34" rx="2" class="relay-cube"/>
    <circle cx="398" cy="484" r="3" id="hw-relay-led" class="relay-led"/>
    <circle cx="390" cy="514" r="3" class="term"/><circle cx="414" cy="514" r="3" class="term"/>
    <line x1="390" y1="514" x2="413" y2="506" id="hw-relay-lever" class="lever"/>
    <text x="378" y="547" text-anchor="middle" class="part-txt">RELAY · GPIO19</text>
  </g>

  <!-- OLED -->
  <g class="oled-mod">
    <rect x="432" y="40" width="146" height="112" rx="4" class="pcb-blue"/>
    <rect x="442" y="52" width="126" height="74" rx="2" class="oled-screen"/>
    <text x="448" y="66" class="oled-t" id="hw-o1">COLDCHAIN</text>
    <text x="448" y="90" class="oled-t big" id="hw-o2">--.- C</text>
    <text x="448" y="106" class="oled-t" id="hw-o3">—</text>
    <text x="448" y="120" class="oled-t" id="hw-o4">—</text>
    <text x="505" y="144" text-anchor="middle" class="part-txt light">SSD1306 · I²C 0x3C</text>
  </g>

  <!-- ESP32 -->
  <g class="esp">
    <g id="hw-wifi" class="wifi" tabindex="0" role="button" aria-label="Wi-Fi antenna">
      <rect x="470" y="150" width="70" height="52" fill="transparent"/>
      <path d="M484 182 a30 30 0 0 1 42 0" class="wave w3"/><path d="M490 189 a20 20 0 0 1 30 0" class="wave w2"/><path d="M496 196 a10 10 0 0 1 18 0" class="wave w1"/>
      <path d="M486 160 L524 198 M524 160 L486 198" class="wifi-x"/>
    </g>
    <rect x="430" y="200" width="150" height="236" rx="6" class="pcb-black"/>
    <rect x="455" y="214" width="100" height="112" rx="3" class="shield"/>
    <path d="M462 206 h8 v-6 h8 v6 h8 v-6 h8 v6 h8 v-6 h8 v6 h8" class="antenna"/>
    <text x="505" y="262" text-anchor="middle" class="shield-txt">ESP32</text>
    <text x="505" y="278" text-anchor="middle" class="shield-txt sm">WROOM-32</text>
    <text x="505" y="312" text-anchor="middle" class="shield-txt sm mono" id="hw-node-id">${esc(f.id)}</text>
    ${header(436)}${header(567)}
    ${pinL.map(([n,y])=>`<text x="${434}" y="${y+5}" text-anchor="end" class="pin-txt">${n.replace('GPIO','')}</text>`).join('')}
    ${pinR.map(([n,y])=>`<text x="${578}" y="${y+5}" class="pin-txt">${n.replace('GPIO','')}</text>`).join('')}
    <rect x="492" y="428" width="26" height="12" rx="2" class="usb"/>
    <circle cx="470" cy="420" r="3" class="pwr-led"/>
    <text x="505" y="458" text-anchor="middle" class="caption">ESP32 DevKit</text>
  </g>

  <!-- indicators -->
  <g class="ind">
    <g id="hw-red" class="ledpart red"><circle cx="664" cy="252" r="10"/><text x="682" y="256" class="part-txt">RED · 25</text></g>
    <g id="hw-green" class="ledpart green"><circle cx="664" cy="292" r="10"/><text x="682" y="296" class="part-txt">GREEN · 26</text></g>
    <g id="hw-buzz" class="buzzpart"><circle cx="656" cy="340" r="15" class="buzz-body"/><circle cx="656" cy="340" r="4" class="buzz-hole"/>
      <path d="M676 330 a14 14 0 0 1 0 20 M684 324 a24 24 0 0 1 0 32" class="buzz-wave"/><text x="694" y="344" class="part-txt">BUZZER · 27</text></g>
    <g id="hw-btn" class="btnpart" tabindex="0" role="button" aria-label="Mains-fail button">
      <rect x="640" y="382" width="32" height="32" rx="4" class="btn-base"/><rect x="646" y="388" width="20" height="20" rx="10" class="btn-cap"/>
      <text x="682" y="396" class="part-txt">MAINS FAIL · 32</text><text x="682" y="409" class="part-txt dim" id="hw-btn-txt">press to cut</text></g>
    <g class="battpart"><rect x="620" y="440" width="78" height="32" rx="4" class="batt-body"/><rect x="698" y="450" width="5" height="12" rx="1" class="batt-tip"/>
      <rect x="624" y="444" width="70" height="24" rx="2" id="hw-batt-fill" class="batt-fill"/>
      <text x="659" y="461" text-anchor="middle" class="batt-txt mono" id="hw-batt-txt">100%</text><text x="712" y="461" class="part-txt">18650 · ADC 34</text></g>
  </g>

  <!-- network -->
  <g class="netbox"><rect x="820" y="90" width="160" height="56" rx="6"/><text x="836" y="114" class="nb-t">MQTT broker</text><text x="836" y="132" class="nb-s mono" id="hw-topic">coldchain/telemetry/${esc(f.id.slice(-1))}</text></g>
  <g class="netbox"><rect x="820" y="230" width="160" height="56" rx="6"/><text x="836" y="254" class="nb-t">ColdChain API</text><text x="836" y="272" class="nb-s mono">HMAC · nonce · seq</text></g>
  <g class="netbox"><rect x="820" y="372" width="160" height="50" rx="6"/><text x="836" y="395" class="nb-t">SQLite + hash chain</text><text x="836" y="411" class="nb-s mono" id="hw-seq">seq —</text></g>
  <g class="netbox q" id="hw-qbox"><rect x="820" y="478" width="160" height="56" rx="6"/><text x="836" y="500" class="nb-t">Flash queue</text><text x="836" y="518" class="nb-s mono" id="hw-q">0 / 900 samples</text>
    <rect x="910" y="490" width="60" height="8" rx="2" class="qbar-bg"/><rect x="910" y="490" width="0" height="8" rx="2" class="qbar" id="hw-qbar"/></g>
  <g id="hw-packets"></g>
</svg>`;
  }

  function build(){
    const data=state.data;if(!data) return;
    const f=data.fridges.find(x=>x.id===hw.fid);if(!f) return;
    const batches=data.batches.filter(b=>b.fridge_id===f.id).sort((a,b)=>a.remaining_pct-b.remaining_pct);
    const host=$('hw-scene');
    host.innerHTML=sceneSvg(f,batches);
    hw.built=hw.fid;hw.batchKey=batches.map(b=>b.id+b.status+Math.round(b.remaining_pct)).join('|');
    hw.prev={seq:f.last_seq,door:f.door_open,mains:f.mains_ok,comp:f.compressor_on,buffered:f.buffered};
    const bind=(id,fn)=>{const el=document.getElementById(id);el.addEventListener('click',fn);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();fn();}});};
    bind('hw-door',()=>toggle('door_open',!f_now().door_open,'Door'));
    bind('hw-btn',()=>toggle('mains_ok',!f_now().mains_ok,'Mains'));
    bind('hw-wifi',()=>toggle('wifi_ok',!(hw.controls.wifi_ok??1),'Wi-Fi'));
    hw.sceneEl=host.querySelector('svg');
  }
  const f_now=()=>state.data.fridges.find(x=>x.id===hw.fid);

  async function toggle(key,value,label){
    if(!state.data?.demo){toast('Live hardware: use the physical switch on the node.','info');return;}
    if(!canEdit()){toast('Inspectors have read-only access.','info');return;}
    try{
      await api(`/api/simulator/${hw.fid}/control`,{method:'POST',body:JSON.stringify({[key]:!!value})});
      serial(`# operator: ${label} → ${key==='mains_ok'?(value?'mains restored':'mains FAILED'):key==='wifi_ok'?(value?'wifi up':'wifi DOWN'):(value?'door OPEN':'door closed')}`,'op');
      await loadControls();await refresh(false,true);
    }catch(err){toast(err.message,'error');}
  }

  async function loadControls(){
    if(!state.data?.demo || !canEdit()){hw.controls={};return;}
    try{const rows=await api('/api/simulator/controls');hw.controls=rows.find(r=>r.fridge_id===hw.fid)||{};}catch{hw.controls={};}
  }

  function setText(id,t){const el=document.getElementById(id);if(el&&el.textContent!==t) el.textContent=t;}
  function cls(id,c,on){document.getElementById(id)?.classList.toggle(c,!!on);}

  function packet(pathId,label,kind,delay=0,then){
    const g=document.getElementById('hw-packets');if(!g||REDUCED){then&&then();return;}
    setTimeout(()=>{
      const p=document.createElementNS(NS,'g');p.setAttribute('class',`pkt ${kind}`);
      p.innerHTML=`<circle r="5"/>${label?`<text x="8" y="-7">${esc(label)}</text>`:''}<animateMotion dur="${kind==='ack'?'0.8s':'1.1s'}" fill="freeze" begin="indefinite" calcMode="spline" keyTimes="0;1" keySplines="0.4 0 0.2 1"><mpath href="#${pathId}"/></animateMotion>`;
      g.appendChild(p);
      try{p.querySelector('animateMotion').beginElement();}catch{}
      setTimeout(()=>{p.remove();then&&then();},kind==='ack'?850:1150);
    },delay);
  }
  function sendChain(seq,i){
    packet('p-up',`#${seq}`,'data',i*160,()=>packet('p-down','','data',0,()=>{packet('p-db','','data');packet('p-ack','ACK','ack');}));
  }

  function serial(line,kind=''){
    hw.serial.push({line,kind});if(hw.serial.length>80) hw.serial.shift();
    const out=$('hw-serial');if(!out||!hw.visible) return;
    out.innerHTML=hw.serial.map(x=>`<span class="${x.kind}">${esc(x.line)}</span>`).join('\n');
    out.scrollTop=out.scrollHeight;
  }

  function fsm(f){
    const c=hw.controls;let st='idle';
    if(f.compressor_on) st='cool'; else if((c.min_off_remaining||0)>0) st='lock';
    if(!f.mains_ok) st='nopower';
    const t=f.temp_c??0,pos=v=>Math.max(0,Math.min(100,(v-1)/(9-1)*100));
    const node=(id,title,sub)=>`<div class="fsm-node ${st===id?'on':''}"><b>${title}</b><small>${sub}</small></div>`;
    setText('hw-state-tag',{idle:'IDLE',cool:'COOLING',lock:'MIN-OFF',nopower:'NO MAINS'}[st]);
    setHTML($('hw-fsm'),`
      <div class="fsm">
        ${node('idle','Idle','relay off, warming')}
        <span class="fsm-arrow">≥ 7 °C<br>and 60 s off</span>
        ${node('cool','Cooling','relay on')}
        <span class="fsm-arrow">≤ 3 °C</span>
        ${node('lock','Min-off',(c.min_off_remaining?`${c.min_off_remaining}s left`:'60 s lockout'))}
      </div>
      ${st==='nopower'?'<p class="fsm-note">Mains failed — the relay is forced off until power returns.</p>':''}
      <div class="hyst">
        <div class="hyst-bar"><span class="hb-band" style="left:${pos(3)}%;width:${pos(7)-pos(3)}%"></span>
          <span class="hb-mark" style="left:${pos(3)}%"><i>3</i></span><span class="hb-mark" style="left:${pos(7)}%"><i>7</i></span>
          <span class="hb-mark lim" style="left:${pos(2)}%"><i>2</i></span><span class="hb-mark lim" style="left:${pos(8)}%"><i>8</i></span>
          <span class="hb-now ${f.compressor_on?'down':'up'}" style="left:${pos(t)}%"><i class="mono">${fmtTemp(f.temp_c)}</i></span></div>
        <small class="muted">Hysteresis: the compressor starts at 7 °C and stops at 3 °C, so it doesn't chatter around one set-point.</small>
      </div>`);
  }

  function pins(f,st,redLed,greenLed,buzzer){
    const val={temp:fmtTemp(f.temp_c),door:f.door_open?'OPEN':'closed',relay:f.compressor_on?'ON':'off',oled:st.oled,
      red:redLed?'ON':'off',green:greenLed?'ON':'off',buzz:buzzer?'ON':'off',btn:f.mains_ok?'released':'mains fail',batt:`${f.battery_pct??'—'}%`};
    const hot={door:f.door_open,relay:f.compressor_on,red:redLed,green:greenLed,buzz:buzzer,btn:!f.mains_ok};
    setHTML($('hw-pins'),`<table class="pin-table">${PINS.map(([g,n,k])=>`<tr class="${hot[k]?'hot':''}"><td class="mono">${g}</td><td>${n}</td><td class="mono r">${esc(val[k])}</td></tr>`).join('')}</table>`);
  }

  function update(){
    const data=state.data;if(!data||!hw.visible) return;
    const f=f_now();if(!f) return;
    const batches=data.batches.filter(b=>b.fridge_id===f.id).sort((a,b)=>a.remaining_pct-b.remaining_pct);
    const key=batches.map(b=>b.id+b.status+Math.round(b.remaining_pct)).join('|');
    if(hw.built!==hw.fid || key!==hw.batchKey) build();
    const pred=data.predictions[f.id]||{};const st=fridgeState(f,pred);
    const doorS=doorOpenSeconds(f),buzzer=doorS>60;
    const redLed=st.cls==='danger'||!f.mains_ok||f.red_latch;
    const greenLed=!redLed&&f.online&&f.temp_c<7;
    const wifiOk=hw.controls.wifi_ok!=null?!!hw.controls.wifi_ok:!f.buffered;

    document.getElementById('hw-interior').style.fill=interior(f.temp_c);
    setText('hw-cab-temp',`${f.temp_c==null?'--.-':Number(f.temp_c).toFixed(1)}°C`);
    cls('hw-door','open',f.door_open);
    cls('hw-frost','on',f.compressor_on);
    cls('hw-fan','spin',f.compressor_on);
    cls('hw-heat','on',f.compressor_on);
    cls('hw-relay','on',f.compressor_on);
    ['w-relay','w-comp'].forEach(id=>cls(id,'live',f.compressor_on));
    cls('w-door','live',f.door_open);
    cls('hw-red','on',redLed);cls('w-red','live',redLed);
    cls('hw-green','on',greenLed);cls('w-green','live',greenLed);
    cls('hw-buzz','on',buzzer);cls('w-buzz','live',buzzer);
    cls('hw-btn','pressed',!f.mains_ok);cls('w-btn','live',!f.mains_ok);
    setText('hw-btn-txt',f.mains_ok?'press to cut':'pressed · on battery');
    cls('hw-wifi','off',!wifiOk);
    const sceneSvgEl=hw.sceneEl;if(sceneSvgEl){sceneSvgEl.classList.toggle('offline',!wifiOk);sceneSvgEl.classList.toggle('st-'+st.cls,true);['safe','warning','danger'].forEach(c=>{if(c!==st.cls) sceneSvgEl.classList.remove('st-'+c);});}
    const bat=Math.max(0,Math.min(100,f.battery_pct??100));
    const bf=document.getElementById('hw-batt-fill');if(bf){bf.setAttribute('width',(70*bat/100).toFixed(1));bf.classList.toggle('low',bat<30);bf.classList.toggle('charging',!!f.mains_ok&&bat<100);}
    setText('hw-batt-txt',`${bat}%`);
    setText('hw-o1',`COLDCHAIN ${f.id.slice(-1)}`);
    setText('hw-o2',`${f.temp_c==null?'--.-':Number(f.temp_c).toFixed(1)} C`);
    setText('hw-o3',`${st.oled}  ${wifiOk?'MQTT':'OFFLINE'}`);
    setText('hw-o4',`${f.mains_ok?'MAINS':'BATTERY'}  Q:${f.buffered||0}`);
    cls('hw-o3','blink',st.cls==='danger');
    setText('hw-seq',`seq ${f.last_seq}`);
    const q=f.buffered||0;setText('hw-q',`${q} / 900 samples`);
    const qb=document.getElementById('hw-qbar');if(qb) qb.setAttribute('width',(60*Math.min(1,q/900)+ (q?4:0)).toFixed(1));
    cls('hw-qbox','active',q>0);

    // events since the previous refresh
    const p=hw.prev;
    const newSeq=f.last_seq-(p.seq??f.last_seq);
    if(p.door!==undefined && p.door!==f.door_open) serial(`DOOR ${f.door_open?'OPEN':'CLOSED'} → immediate sample (door-change publish)`,'ev');
    if(p.mains!==undefined && p.mains!==f.mains_ok) serial(f.mains_ok?'POWER restored → mains':'POWER FAIL → battery, relay forced off','warn');
    if(p.comp!==undefined && p.comp!==f.compressor_on) serial(`RELAY ${f.compressor_on?'ON  (temp ≥ 7.0)':'OFF (temp ≤ 3.0 or no mains) → min-off 60 s'}`,'ev');
    if(buzzer && !p.buzz) serial('BUZZER ON — door open > 60 s, alert queued (Telegram/email)','bad');
    if(!wifiOk && q>(p.buffered||0)) {serial(`WIFI DOWN — appended to /queue.jsonl (Q=${q})`,'warn');packet('p-q','','queued');}
    if(newSeq>0){
      const burst=(p.buffered||0)>0 && q===0;
      if(burst) serial(`WIFI UP — replaying ${newSeq} queued samples in order`,'ev');
      const n=Math.min(newSeq,burst?10:3);
      for(let i=0;i<n;i++) sendChain(f.last_seq-n+1+i,i);
      serial(`PUB coldchain/telemetry/${f.id} seq=${f.last_seq} t=${Number(f.temp_c).toFixed(2)} door=${+f.door_open} mains=${+f.mains_ok} comp=${+f.compressor_on} sig=hmac-sha256`,'');
      serial(`ACK seq=${f.last_seq} (signature + nonce verified)`,'ok');
    }
    hw.prev={seq:f.last_seq,door:f.door_open,mains:f.mains_ok,comp:f.compressor_on,buffered:q,buzz:buzzer};
    if(newSeq>0||!hw.serial.length) serial(`NODE=${f.id} TEMP=${Number(f.temp_c??0).toFixed(2)} DOOR=${+f.door_open} POWER=${+f.mains_ok} COMP=${+f.compressor_on} BAT=${f.battery_pct} REDLATCH=${+!!f.red_latch} QUEUE=${q} MQTT=${+wifiOk}`,'dim');

    fsm(f);pins(f,st,redLed,greenLed,buzzer);
    $('hw-hint').innerHTML=!state.data.demo?'Live node: the drawing mirrors the physical ESP32.':canEdit()?'Click the <b>door</b>, the <b>mains-fail button</b> or the <b>antenna</b> to change the node.':'Read-only view. Pharmacists and admins can operate the simulated node.';
  }

  $$('#hw-tabs .seg-btn').forEach(b=>b.addEventListener('click',async()=>{
    hw.fid=b.dataset.hw;$$('#hw-tabs .seg-btn').forEach(x=>x.classList.toggle('active',x===b));
    hw.serial=[];hw.built=null;await loadControls();update();
  }));
  $('serial-clear').addEventListener('click',()=>{hw.serial=[];$('hw-serial').innerHTML='';});

  window.HW={
    async show(){hw.visible=true;await loadControls();update();},
    async update(){
      hw.visible=state.page==='hardware';
      if(!hw.visible) return;
      await loadControls();update();
    },
  };
})();
