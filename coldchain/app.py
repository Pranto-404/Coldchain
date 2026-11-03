"""ColdChain API. Run: python run_demo.py. Production: use .env with DEMO_MODE=0."""
from pathlib import Path
import os,json,datetime,io,threading,csv,uuid,time,sqlite3
from contextlib import asynccontextmanager
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
except ImportError:pass
import jwt,qrcode
from fastapi import FastAPI,Depends,HTTPException,Header,Request,Response,Body
from fastapi.responses import HTMLResponse,FileResponse,StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from typing import Literal
from .db import connect,transaction,initialize,append_audit,now
from .security import check_password,hash_password
from .core import ingest,batch_view,batch_status,verified_integrity,predictions_for_all,relocation_suggestions,fridge_is_fresh,secret_for
from .security import signature

ROOT=Path(__file__).resolve().parents[1]
JWT_ALGO='HS256'
import secrets as _secrets
# Demo without a configured secret: random per process, so a token can't be forged from the public
# source. Sessions end when the server restarts, which on a free host also resets the demo data.
_EPHEMERAL_JWT=_secrets.token_urlsafe(48)
def jwt_secret():
    key=os.getenv('JWT_SECRET','')
    if len(key)<32:
        if os.getenv('DEMO_MODE')=='1': return _EPHEMERAL_JWT
        raise RuntimeError('JWT_SECRET needs at least 32 characters')
    return key

class Login(BaseModel):
    username:str
    password:str
class BatchCreate(BaseModel):
    name:str=Field(min_length=2,max_length=140)
    lot:str=Field(min_length=2,max_length=80)
    expires:datetime.date
    fridge_id:str
class Move(BaseModel):
    fridge_id:str
class BatchUpdate(BaseModel):
    name:str|None=Field(default=None,min_length=2,max_length=140)
    lot:str|None=Field(default=None,min_length=2,max_length=80)
    expires:datetime.date|None=None
class Dispose(BaseModel):
    reason:str=Field(min_length=3,max_length=200)
class UserUpdate(BaseModel):
    enabled:bool|None=None
    role:Literal['Admin','Pharmacist','Inspector']|None=None
class Attack(BaseModel):
    kind:Literal['forged','replay','stale','unknown_device']
    fridge_id:str='FRIDGE_A'
class Tamper(BaseModel):
    action:Literal['tamper','restore']
USERNAME_PATTERN=r'^[A-Za-z0-9._@+-]{3,60}$'
class Register(BaseModel):
    username:str=Field(pattern=USERNAME_PATTERN)
    password:str=Field(min_length=8,max_length=150)
    requested_role:Literal['Inspector','Pharmacist']='Inspector'
class Probe(BaseModel):
    temp_c:float=Field(ge=-2,le=24)
class UserCreate(BaseModel):
    username:str=Field(pattern=USERNAME_PATTERN)
    password:str=Field(min_length=8,max_length=150)
    role:str
class Relocation(BaseModel):
    batch_id:str
    target_fridge_id:str
class ExposureScene(BaseModel):
    scenario: Literal['safe','at_risk','discard']

class ForecastScene(BaseModel):
    scenario: Literal['rising_risk']

class SimControl(BaseModel):
    door_open:bool|None=None
    mains_ok:bool|None=None
    degraded:bool|None=None
    wifi_ok:bool|None=None
    heat_spike:bool|None=None

mqtt_service=None
simulator_service=None
@asynccontextmanager
async def lifespan(app):
    global mqtt_service,simulator_service
    jwt_secret()
    from .ml import load_model
    threading.Thread(target=load_model,name='model-warmup',daemon=True).start()
    if os.getenv('DEMO_MODE')!='1':
        for x in ('DEVICE_FRIDGE_A_SECRET','DEVICE_FRIDGE_B_SECRET'):
            if len(os.getenv(x,''))<32:raise RuntimeError(f'{x} must have 32+ characters')
    initialize()
    if os.getenv('MQTT_ENABLED','0')=='1':
        from .mqttbridge import MQTTBridge
        mqtt_service=MQTTBridge();mqtt_service.start()
    if os.getenv('DEMO_MODE')=='1':
        from .simulator import Simulator
        simulator_service=Simulator();simulator_service.start()
    yield
    if simulator_service:simulator_service.stop()
    if mqtt_service:mqtt_service.stop()

app=FastAPI(title='ColdChain — Vaccine Storage Monitor',version='1.0.0',lifespan=lifespan)
app.mount('/static', StaticFiles(directory=ROOT/'web'),name='static')

@app.middleware('http')
async def protective_headers(request,call_next):
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='same-origin'
    # Static files revalidate with ETag on every load, so a redeploy is picked up immediately.
    response.headers['Cache-Control']='no-store' if request.url.path.startswith('/api/') else 'no-cache'
    response.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; script-src 'self'; connect-src 'self'; font-src 'self' https://fonts.gstatic.com"
    return response

@app.get('/',response_class=HTMLResponse)
def index():return (ROOT/'web'/'index.html').read_text(encoding='utf-8')

@app.get('/health')
def health():return {'ok':True,'demo':os.getenv('DEMO_MODE')=='1','timestamp':now()}

def actor(authorization:str|None=Header(None)):
    if not authorization or not authorization.startswith('Bearer '):raise HTTPException(401,'Login required')
    try:
        claims=jwt.decode(authorization[7:],jwt_secret(),algorithms=[JWT_ALGO])
        c=connect(); u=c.execute('SELECT id,username,role,enabled FROM users WHERE id=?',(claims['sub'],)).fetchone();c.close()
        if not u or not u['enabled']: raise HTTPException(401,'Account disabled')
        return dict(u)
    except (jwt.InvalidTokenError,KeyError,ValueError) as e: raise HTTPException(401,'Invalid or expired token') from e

def require(*roles):
    def dep(a=Depends(actor)):
        if roles and a['role'] not in roles:raise HTTPException(403,'Insufficient permissions')
        return a
    return dep

failures={}
def client_ip(request):
    # Render/Vercel put the real client first in X-Forwarded-For; otherwise every user shares the proxy IP.
    fwd=request.headers.get('x-forwarded-for','').split(',')[0].strip()
    return (fwd or (request.client.host if request.client else ''))[:120]
@app.post('/api/auth/login')
def login(d:Login,request:Request):
    key=client_ip(request)+'|'+d.username.lower()[:60]
    hits=[x for x in failures.get(key,[]) if time.time()-x<600]
    if len(hits)>=10:raise HTTPException(429,'Too many attempts; try again in 10 minutes')
    if len(failures)>5000:failures.clear()
    c=connect(); u=c.execute('SELECT * FROM users WHERE lower(username)=lower(?) AND enabled=1',(d.username.strip(),)).fetchone(); c.close()
    if not u or not check_password(d.password,u['password_hash']):
        failures[key]=hits+[time.time()]
        raise HTTPException(401,'Invalid username or password')
    failures.pop(key,None)
    return issue_token(u)

def issue_token(u):
    token=jwt.encode({'sub':str(u['id']),'role':u['role'],'exp':datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=6)},jwt_secret(),algorithm=JWT_ALGO)
    return {'access_token':token,'token_type':'bearer','role':u['role'],'username':u['username']}

registrations={}
@app.post('/api/auth/register',status_code=201)
def register(d:Register,request:Request):
    """Self sign-up. New accounts are always read-only Inspectors; asking for Pharmacist only records a
    request that an Admin approves. Roles are never chosen by the person registering."""
    if os.getenv('ALLOW_REGISTRATION','1')!='1':raise HTTPException(403,'Self registration is disabled')
    ip=client_ip(request)
    recent=[x for x in registrations.get(ip,[]) if time.time()-x<3600]
    if len(recent)>=5:raise HTTPException(429,'Too many new accounts from this network; try again later')
    if len(registrations)>5000:registrations.clear()
    name=d.username.strip()
    try:
        with transaction() as c:
            if c.execute('SELECT 1 FROM users WHERE lower(username)=lower(?)',(name,)).fetchone():raise HTTPException(409,'That username is taken')
            requested='Pharmacist' if d.requested_role=='Pharmacist' else None
            c.execute('INSERT INTO users(username,password_hash,role,requested_role) VALUES(?,?,?,?)',(name,hash_password(d.password),'Inspector',requested))
            append_audit(c,name,'user_registered',{'username':name,'role':'Inspector','requested_role':requested})
            u=c.execute('SELECT * FROM users WHERE username=?',(name,)).fetchone()
    except sqlite3.IntegrityError as ex:raise HTTPException(409,'That username is taken') from ex
    registrations[ip]=recent+[time.time()]
    return issue_token(u)

@app.get('/api/me')
def me(a=Depends(actor)):return a

@app.get('/api/dashboard')
def dashboard(a=Depends(actor)):
    c=connect()
    fridges=[dict(r) for r in c.execute('SELECT * FROM fridges ORDER BY id')]
    batches=[batch_view(r) for r in c.execute('SELECT * FROM batches ORDER BY name')]
    forecasts=predictions_for_all(c)
    recommendations=relocation_suggestions(c,forecasts)
    # Per-sample 'reading' rows dominate the chain; the activity feed shows human and safety events.
    events=[dict(r) for r in c.execute("SELECT id,at,actor,action,details FROM audit WHERE action!='reading' ORDER BY id DESC LIMIT 16")]
    alerts=[dict(r) for r in c.execute('SELECT * FROM alert_outbox ORDER BY id DESC LIMIT 8')]
    since=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(hours=24)).replace(microsecond=0).isoformat()
    rejected=c.execute('SELECT COUNT(*) AS n FROM invalid_messages WHERE at>=?',(since,)).fetchone()['n']
    for f in fridges:
        f['red_latch']=any(b['fridge_id']==f['id'] and b['status']=='Discard' for b in batches)
        f['batch_count']=sum(1 for b in batches if b['fridge_id']==f['id'])
        f['online']=fridge_is_fresh(f,30)
        f['buffered']=len(simulator_service.states[f['id']]['queue']) if simulator_service and f['id'] in simulator_service.states else 0
    c.close()
    return {'fridges':fridges,'batches':batches,'predictions':forecasts,'recommendations':recommendations,'events':events,'alerts':alerts,'rejected_24h':rejected,'demo':os.getenv('DEMO_MODE')=='1','generated_at':now()}

@app.get('/api/fridges/{fridge_id}/history')
def history(fridge_id:str,limit:int=120,a=Depends(actor)):
    if fridge_id not in ('FRIDGE_A','FRIDGE_B'):raise HTTPException(404,'Fridge not found')
    c=connect();data=[dict(r) for r in c.execute('SELECT observed_at,temp_c,door_open,mains_ok,compressor_on,source FROM readings WHERE fridge_id=? ORDER BY seq DESC LIMIT ?', (fridge_id,max(1,min(1440,limit))))];c.close()
    return list(reversed(data))

@app.get('/api/batches')
def batches(a=Depends(actor)):
    c=connect();result=[batch_view(r) for r in c.execute('SELECT * FROM batches ORDER BY name')];c.close();return result

@app.post('/api/batches',status_code=201)
def create_batch(data:BatchCreate,a=Depends(require('Admin','Pharmacist'))):
    if data.fridge_id not in ('FRIDGE_A','FRIDGE_B'):raise HTTPException(422,'Invalid fridge')
    if data.expires<datetime.date.today():raise HTTPException(422,'Expiry already passed')
    bid=str(uuid.uuid4());token=uuid.uuid4().hex
    try:
        with transaction() as c:
            c.execute('INSERT INTO batches(id,name,lot,expires,fridge_id,public_token,created_at) VALUES(?,?,?,?,?,?,?)',(bid,data.name,data.lot,data.expires.isoformat(),data.fridge_id,token,now()))
            append_audit(c,a['username'],'batch_added',{'id':bid,'lot':data.lot,'fridge':data.fridge_id})
    except Exception as ex:
        if 'UNIQUE' in str(ex):raise HTTPException(409,'Batch lot already exists') from ex
        raise
    return {'id':bid,'public_token':token}

def move_batch(bid,target,username):
    if target not in ('FRIDGE_A','FRIDGE_B'): raise HTTPException(422,'Unknown target fridge')
    with transaction() as c:
        b=c.execute('SELECT * FROM batches WHERE id=?',(bid,)).fetchone()
        if not b:raise HTTPException(404,'Batch not found')
        if batch_status(b)=='Discard' or b['expires']<datetime.date.today().isoformat():raise HTTPException(409,'Discarded/expired batch cannot be relocated')
        if b['fridge_id']==target:raise HTTPException(409,'Batch already in destination fridge')
        f=c.execute('SELECT * FROM fridges WHERE id=?',(target,)).fetchone()
        if f['temp_c'] is None or not fridge_is_fresh(f) or not 2<=f['temp_c']<=8 or not f['mains_ok'] or f['door_open']:
            raise HTTPException(409,'Destination must be online, 2-8°C, on mains power and door closed')
        c.execute('UPDATE batches SET fridge_id=? WHERE id=?',(target,bid))
        append_audit(c,username,'batch_moved',{'batch_id':bid,'lot':b['lot'],'from':b['fridge_id'],'to':target,'exposure_preserved_seconds':b['exposure_seconds']})
        return {'ok':True,'batch_id':bid,'from':b['fridge_id'],'to':target,'exposure_seconds':b['exposure_seconds']}

@app.post('/api/batches/{batch_id}/move')
def move(batch_id:str,data:Move,a=Depends(require('Admin','Pharmacist'))):return move_batch(batch_id,data.fridge_id,a['username'])

@app.post('/api/relocations/confirm')
def confirm_relocation(data:Relocation,a=Depends(require('Admin','Pharmacist'))):
    c=connect(); rec=relocation_suggestions(c);c.close()
    if not any(r['batch_id']==data.batch_id and r['to_fridge']==data.target_fridge_id for r in rec):
        raise HTTPException(409,'Recommendation no longer valid; refresh dashboard')
    return move_batch(data.batch_id,data.target_fridge_id,a['username'])

@app.patch('/api/batches/{batch_id}')
def update_batch(batch_id:str,data:BatchUpdate,a=Depends(require('Admin','Pharmacist'))):
    changes=data.model_dump(exclude_none=True)
    if not changes:raise HTTPException(422,'Nothing to update')
    if 'expires' in changes:
        if changes['expires']<datetime.date.today():raise HTTPException(422,'Expiry already passed')
        changes['expires']=changes['expires'].isoformat()
    try:
        with transaction() as c:
            b=c.execute('SELECT * FROM batches WHERE id=?',(batch_id,)).fetchone()
            if not b:raise HTTPException(404,'Batch not found')
            for k,v in changes.items():c.execute(f'UPDATE batches SET {k}=? WHERE id=?',(v,batch_id))
            append_audit(c,a['username'],'batch_updated',{'batch_id':batch_id,'lot':b['lot'],'before':{k:b[k] for k in changes},'after':changes})
            result=batch_view(c.execute('SELECT * FROM batches WHERE id=?',(batch_id,)).fetchone())
    except sqlite3.IntegrityError as ex:raise HTTPException(409,'Batch lot already exists') from ex
    return result

@app.delete('/api/batches/{batch_id}')
def dispose_batch(batch_id:str,data:Dispose=Body(...),a=Depends(require('Admin','Pharmacist'))):
    with transaction() as c:
        b=c.execute('SELECT * FROM batches WHERE id=?',(batch_id,)).fetchone()
        if not b:raise HTTPException(404,'Batch not found')
        view=batch_view(b)
        c.execute('DELETE FROM batches WHERE id=?',(batch_id,))
        append_audit(c,a['username'],'batch_disposed',{'batch_id':batch_id,'lot':b['lot'],'name':b['name'],'fridge':b['fridge_id'],'status':view['status'],'exposure_seconds':b['exposure_seconds'],'reason':data.reason})
        fridge=b['fridge_id']
    publish_latch(fridge)
    return {'ok':True}

@app.post('/api/batches/{batch_id}/admin-reset')
def admin_reset(batch_id:str,a=Depends(require('Admin'))):
    with transaction() as c:
        b=c.execute('SELECT * FROM batches WHERE id=?',(batch_id,)).fetchone()
        if not b:raise HTTPException(404,'Batch not found')
        c.execute('UPDATE batches SET exposure_seconds=0,discard_latched=0 WHERE id=?',(batch_id,))
        append_audit(c,a['username'],'discard_latch_admin_reset',{'batch_id':batch_id,'lot':b['lot'],'previous_exposure_seconds':b['exposure_seconds'],'warning':'ADMIN ACTION: physical review and authorized disposition required; do not return compromised stock to service'})
        fridge=b['fridge_id']
    publish_latch(fridge)
    return {'ok':True,'warning':'An administrative software reset does not restore vaccine potency. Quarantine and follow local clinical quality procedures.'}

@app.get('/api/public/batch/{token}')
def public_batch(token:str):
    c=connect();b=c.execute('SELECT * FROM batches WHERE public_token=?',(token,)).fetchone();c.close()
    if not b:raise HTTPException(404,'Batch not found')
    x=batch_view(b)
    c=connect();f=c.execute('SELECT label FROM fridges WHERE id=?',(b['fridge_id'],)).fetchone();c.close()
    return {'name':x['name'],'lot':x['lot'],'expires':x['expires'],'status':x['status'],'expired':x['expired'],'remaining_pct':x['remaining_pct'],
            'exposure_minutes':round(float(x['exposure_seconds'])/60,1),'storage':f['label'] if f else None,'checked_at':now(),
            'note':'Demo/simulation results are not clinical release certification.' if os.getenv('DEMO_MODE')=='1' else 'Temperature history does not replace manufacturer stability policy.'}

PUBLIC_VERDICT={
    'Safe':('#059669','#ecfdf5','✓','Safe to use','Cold chain intact: this batch has used little or none of its 60-minute heat budget.'),
    'At Risk':('#b45309','#fffbeb','!','At risk','Less than 20% of the heat budget remains. Use soon and keep strictly at 2–8°C; ask the pharmacist.'),
    'Discard':('#b91c1c','#fef2f2','✕','Do not use','This batch spent too long above 8°C. It has been quarantined for disposal.'),
}

@app.get('/check/{token}',response_class=HTMLResponse)
def public_page(token:str):
    import html
    try: item=public_batch(token)
    except HTTPException:
        return HTMLResponse('<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Not found</title><body style="font-family:system-ui;display:grid;place-items:center;min-height:90vh;color:#334155"><div style="text-align:center"><h2>Batch not found</h2><p>This QR code is not registered. Do not use the product; ask the pharmacist.</p></div>',status_code=404)
    status=item['status'] if not item['expired'] else 'Discard'
    color,bg,icon,title,why=PUBLIC_VERDICT[status]
    if item['expired']:title,why='Expired',f"The expiry date {item['expires']} has passed. Do not use."
    days=(datetime.date.fromisoformat(item['expires'])-datetime.date.today()).days
    e=lambda v:html.escape(str(v))
    pct=max(0,min(100,float(item['remaining_pct'])))
    bar='#10b981' if item['status']=='Safe' else '#f59e0b' if item['status']=='At Risk' else '#ef4444'
    return HTMLResponse(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="60"><title>{e(title)} · {e(item['name'])} · ColdChain</title>
<style>*{{box-sizing:border-box}}body{{margin:0;font-family:system-ui,-apple-system,"Segoe UI",sans-serif;background:#eef3f9;color:#0f172a;display:grid;place-items:center;min-height:100vh;padding:16px}}
main{{background:#fff;border-radius:24px;max-width:440px;width:100%;box-shadow:0 20px 60px rgba(15,23,42,.12);overflow:hidden}}
.top{{padding:14px 22px;font-size:11px;letter-spacing:.16em;font-weight:800;color:#64748b;border-bottom:1px solid #e2e8f0}}
.verdict{{background:{bg};padding:26px 22px;display:flex;gap:16px;align-items:center}}
.icon{{width:58px;height:58px;border-radius:50%;background:{color};color:#fff;display:grid;place-items:center;font-size:30px;font-weight:900;flex:none}}
.verdict h1{{margin:0;font-size:28px;color:{color};letter-spacing:-.02em}}.verdict p{{margin:6px 0 0;color:#334155;line-height:1.5;font-size:14px}}
.body{{padding:20px 22px}}h2{{margin:0 0 2px;font-size:20px}}.lot{{color:#64748b;font-family:ui-monospace,Consolas,monospace;font-size:13px}}
dl{{display:grid;grid-template-columns:auto 1fr;gap:10px 16px;margin:18px 0}}dt{{color:#64748b;font-size:13px;font-weight:700}}dd{{margin:0;font-size:14px;font-weight:600}}
.bar{{height:10px;background:#e2e8f0;border-radius:99px;overflow:hidden;margin-top:6px}}.bar i{{display:block;height:100%;width:{pct}%;background:{bar}}}
footer{{padding:14px 22px;background:#f8fafc;border-top:1px solid #e2e8f0;font-size:12px;color:#64748b;line-height:1.5}}</style></head>
<body><main><div class="top">COLDCHAIN · PUBLIC BATCH CHECK</div>
<section class="verdict"><div class="icon">{icon}</div><div><h1>{e(title)}</h1><p>{e(why)}</p></div></section>
<section class="body"><h2>{e(item['name'])}</h2><div class="lot">Lot {e(item['lot'])}</div>
<dl><dt>Status</dt><dd>{e(item['status'])}</dd>
<dt>Expiry</dt><dd>{e(item['expires'])} · {'expired' if item['expired'] else f'{days} days left'}</dd>
<dt>Stored in</dt><dd>{e(item['storage'] or '—')}</dd>
<dt>Heat budget</dt><dd>{pct:.0f}% left ({e(item['exposure_minutes'])} of 60 weighted min used)<div class="bar"><i></i></div></dd></dl></section>
<footer>Live record checked {e(item['checked_at'][:19].replace('T',' '))} UTC · page refreshes every minute.<br>{e(item['note'])}</footer></main></body></html>''')

@app.get('/api/public/qr/{token}.png')
def qr_image(token:str,request:Request):
    c=connect();exists=c.execute('SELECT 1 FROM batches WHERE public_token=?',(token,)).fetchone();c.close()
    if not exists:raise HTTPException(404,'Unknown batch')
    base=(os.getenv('PUBLIC_BASE_URL') or str(request.base_url)).rstrip('/')
    img=qrcode.make(f'{base}/check/{token}')
    out=io.BytesIO();img.save(out,format='PNG');out.seek(0)
    return StreamingResponse(out,media_type='image/png')

@app.post('/api/device/ingest')
def device_ingest(payload:dict=Body(...)):
    try:
        result=ingest(payload,'device')
    except ValueError as e:raise HTTPException(401,str(e)) from e
    if not result.get('accepted'):raise HTTPException(409,result.get('reason','Rejected'))
    publish_latch(payload['device_id'])
    return result

def publish_latch(fid):
    global mqtt_service
    if not mqtt_service:return
    c=connect(); red=c.execute('SELECT COUNT(*) AS n FROM batches WHERE fridge_id=? AND discard_latched=1',(fid,)).fetchone()['n']>0;c.close()
    mqtt_service.publish_latch(fid,red)

@app.get('/api/integrity/verify')
def verify_log(a=Depends(actor)):
    result=verified_integrity()
    if not result['valid']:
        c=connect();r=c.execute('SELECT id,at,actor,action,details FROM audit WHERE id=?',(result['first_broken_id'],)).fetchone();c.close()
        result['broken_record']=dict(r) if r else None
    return result

@app.get('/api/audit')
def audit(limit:int=100,a=Depends(actor)):
    c=connect();x=[dict(r) for r in c.execute('SELECT * FROM audit ORDER BY id DESC LIMIT ?',(max(1,min(limit,500)),))];c.close();return x

@app.get('/api/security/rejections')
def security_rejections(a=Depends(require('Admin','Inspector'))):
    c=connect();data=[dict(r) for r in c.execute('SELECT * FROM invalid_messages ORDER BY id DESC LIMIT 200')];c.close();return data

@app.get('/api/readings/export.csv')
def export_csv(a=Depends(actor)):
    c=connect(); rows=c.execute('SELECT fridge_id,seq,observed_at,temp_c,door_open,mains_ok,compressor_on,battery_pct,source FROM readings ORDER BY fridge_id,seq').fetchall();c.close()
    out=io.StringIO();w=csv.writer(out);w.writerow(['fridge_id','seq','observed_at','temp_c','door_open','mains_ok','compressor_on','battery_pct','source'])
    for r in rows:w.writerow(list(r))
    return Response(out.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="coldchain_readings.csv"'})

@app.get('/api/admin/users')
def list_users(a=Depends(require('Admin'))):
    c=connect();rows=[dict(r) for r in c.execute('SELECT id,username,role,enabled,requested_role FROM users ORDER BY id')];c.close();return rows

@app.patch('/api/admin/users/{user_id}')
def update_user(user_id:int,data:UserUpdate,a=Depends(require('Admin'))):
    changes=data.model_dump(exclude_none=True)
    if not changes:raise HTTPException(422,'Nothing to update')
    if user_id==int(a['id']):raise HTTPException(409,'You cannot change your own account here')
    with transaction() as c:
        u=c.execute('SELECT * FROM users WHERE id=?',(user_id,)).fetchone()
        if not u:raise HTTPException(404,'User not found')
        for k,v in changes.items():c.execute(f'UPDATE users SET {k}=? WHERE id=?',(int(v) if isinstance(v,bool) else v,user_id))
        if 'role' in changes:c.execute('UPDATE users SET requested_role=NULL WHERE id=?',(user_id,))
        append_audit(c,a['username'],'user_updated',{'username':u['username'],'changes':changes,'request_was':u['requested_role']})
    return {'ok':True}

@app.post('/api/admin/users',status_code=201)
def create_user(data:UserCreate,a=Depends(require('Admin'))):
    if data.role not in ('Admin','Pharmacist','Inspector'):raise HTTPException(422,'Unsupported role')
    try:
        with transaction() as c:
            c.execute('INSERT INTO users(username,password_hash,role) VALUES(?,?,?)',(data.username,hash_password(data.password),data.role))
            append_audit(c,a['username'],'user_created',{'username':data.username,'role':data.role})
    except Exception as ex:
        if 'UNIQUE' in str(ex):raise HTTPException(409,'Username in use') from ex
        raise
    return {'ok':True,'username':data.username,'role':data.role}

@app.get('/api/simulator/controls')
def sim_controls(a=Depends(require('Admin','Pharmacist'))):
    if os.getenv('DEMO_MODE')!='1':raise HTTPException(404,'Not available in live mode')
    c=connect();rows=[dict(r) for r in c.execute('SELECT * FROM simulation_controls')];c.close()
    if simulator_service:
        for r in rows:r.update(simulator_service.runtime(r['fridge_id']))
    return rows

@app.post('/api/simulator/{fid}/control')
def sim_control(fid:str,data:SimControl,a=Depends(require('Admin','Pharmacist'))):
    if os.getenv('DEMO_MODE')!='1':raise HTTPException(404,'Not available in live mode')
    if fid not in ('FRIDGE_A','FRIDGE_B'):raise HTTPException(404,'Unknown fridge')
    changes={k:int(v) for k,v in data.model_dump(exclude_none=True).items()}
    if not changes:return {'ok':True}
    with transaction() as c:
        allowed={'door_open','mains_ok','degraded','wifi_ok','heat_spike'}
        if not set(changes)<=allowed:raise HTTPException(422,'Invalid field')
        for key,value in changes.items():c.execute(f'UPDATE simulation_controls SET {key}=? WHERE fridge_id=?',(value,fid))
        append_audit(c,a['username'],'simulation_control',{'fridge':fid,'controls':changes})
    if changes.get('degraded') and simulator_service:simulator_service.start_cooling_run(fid)
    if simulator_service:simulator_service.publish_now()
    return {'ok':True,'controls':changes}


# Round 1: explicitly synthetic historical scenarios used only for a 3-minute
# competition explanation. No fabricated sensor evidence is inserted.
ROUND1_EXPOSURE_LOT='SIM-R1-EXPOSURE'
EXPOSURE_SCENARIOS={
    'safe': {'weighted_seconds':0, 'above_8_minutes':0, 'above_12_minutes':0},
    'at_risk': {'weighted_seconds':3060, 'above_8_minutes':40, 'above_12_minutes':5.5},
    'discard': {'weighted_seconds':3600, 'above_8_minutes':40, 'above_12_minutes':10},
}

@app.post('/api/simulator/round1/exposure')
def round1_exposure(data:ExposureScene,a=Depends(require('Admin','Pharmacist'))):
    if os.getenv('DEMO_MODE')!='1':raise HTTPException(404,'Simulation only')
    scenario=EXPOSURE_SCENARIOS[data.scenario]
    with transaction() as c:
        row=c.execute('SELECT * FROM batches WHERE lot=?',(ROUND1_EXPOSURE_LOT,)).fetchone()
        if not row:
            bid=str(uuid.uuid4())
            c.execute('INSERT INTO batches(id,name,lot,expires,fridge_id,public_token,created_at) VALUES(?,?,?,?,?,?,?)',
                (bid,'Round 1 Synthetic Vaccine Sample',ROUND1_EXPOSURE_LOT,'2027-12-31','FRIDGE_A',uuid.uuid4().hex,now()))
        else:
            bid=row['id']
        c.execute('UPDATE batches SET exposure_seconds=?,discard_latched=? WHERE id=?',
            (scenario['weighted_seconds'],int(scenario['weighted_seconds']>=3600),bid))
        append_audit(c,a['username'],'round1_synthetic_exposure_staged',{
            'demo_only':True,'batch_id':bid,'lot':ROUND1_EXPOSURE_LOT,
            'scenario':data.scenario,'above_8_minutes':scenario['above_8_minutes'],
            'above_12_minutes':scenario['above_12_minutes'],
            'weighted_minutes':scenario['weighted_seconds']/60,
            'note':'Presentation example only. No real sensor readings or vaccine disposition.'})
        b=c.execute('SELECT * FROM batches WHERE id=?',(bid,)).fetchone()
        result=batch_view(b)
    result['demo_scenario']=data.scenario
    result['scenario_formula']=f"{scenario['above_8_minutes']} min at 9 C + {scenario['above_12_minutes']} min at 13 C x 2 = {scenario['weighted_seconds']/60:g} weighted minutes"
    return result

@app.post('/api/simulator/round1/forecast')
def round1_forecast(data:ForecastScene,a=Depends(require('Admin','Pharmacist'))):
    if os.getenv('DEMO_MODE')!='1':raise HTTPException(404,'Simulation only')
    if not simulator_service:raise HTTPException(503,'Simulator is not running')
    # Never inserts predicted results or invents recorded measurements.
    # It adjusts clearly synthetic simulator variables, which continue to
    # generate signed samples through the usual ingest path.
    simulator_service.stage_rising_risk()
    c=connect(); p=predictions_for_all(c); r=relocation_suggestions(c,p); c.close()
    return {'ok':True,'scenario':data.scenario,'predictions':p,
            'recommendations':r,'note':'Synthetic simulator scenario; forecast remains a model prediction, not measured clinical performance.'}


AI_DATASET={
    'source':'Synthetic fridge physics: 220 independent 145-minute trajectories (1 sample/min)',
    'disturbances':['Power cuts of 10-55 min','Door openings of 9-50 min','Compressor weakening to 40-82% strength','Ambient 18-32°C, random insulation and cooling capacity'],
    'target':'Fridge temperature exactly 30 minutes after the feature window',
    'split':'GroupShuffleSplit by trajectory (no leakage between train and test runs)',
    'model':'RandomForestRegressor (30 trees, depth 10)',
    'feature_help':{
        'temp_c':'Latest temperature','slope_c_per_min':'Warming/cooling speed over the last 5 minutes',
        'mean_c':'Average over 5 minutes','std_c':'Temperature variability','door_open':'Door currently open',
        'mains_ok':'Mains power present','compressor_on':'Compressor running now','compressor_duty':'Share of last 5 minutes compressor ran'},
    'health_method':'Compressor health = latest uninterrupted cooling run (°C/min) ÷ best recent run or reference rate, scaled 0-100. Below 70 = weakening.',
}

@app.get('/api/ai/report')
def ai_report(a=Depends(actor)):
    try:metrics=json.loads((ROOT/'report'/'model_metrics.json').read_text(encoding='utf-8'))
    except (OSError,ValueError):metrics=None
    c=connect();live=predictions_for_all(c);c.close()
    return {'metrics':metrics,'dataset':AI_DATASET,'live':live,'has_plot':(ROOT/'report'/'forecast_validation.png').exists()}

@app.get('/api/ai/validation.png')
def ai_plot():
    path=ROOT/'report'/'forecast_validation.png'
    if not path.exists():raise HTTPException(404,'Plot not generated; run train_model.py')
    return FileResponse(path,media_type='image/png')

# Demo-only security exercises: they push crafted packets through the real ingest path so the
# rejection log, HMAC check and nonce replay protection can be shown live without hardware.
def _demo_only():
    if os.getenv('DEMO_MODE')!='1':raise HTTPException(404,'Simulation only')

@app.post('/api/simulator/attack')
def simulate_attack(data:Attack,a=Depends(require('Admin','Pharmacist'))):
    _demo_only()
    if data.fridge_id not in ('FRIDGE_A','FRIDGE_B'):raise HTTPException(404,'Unknown fridge')
    c=connect();f=c.execute('SELECT * FROM fridges WHERE id=?',(data.fridge_id,)).fetchone();c.close()
    t=int(time.time())
    m={'device_id':data.fridge_id,'seq':int(f['last_seq'])+1,'observed_at':t,'temp_c_100':420,'door_open':False,'mains_ok':True,
       'compressor_on':False,'battery_pct':100,'sent_at':t,'nonce':uuid.uuid4().hex}
    if data.kind=='forged':
        m['signature']=signature('attacker-guessed-key',m)
    elif data.kind=='stale':
        m['sent_at']=t-900;m['observed_at']=t-900;m['signature']=signature(secret_for(data.fridge_id),m)
    elif data.kind=='unknown_device':
        m['device_id']='FRIDGE_X';m['signature']=signature('unknown',m)
    else:
        # Re-send the most recent genuine nonce, as an eavesdropper replaying a captured packet would.
        c=connect();n=c.execute('SELECT nonce FROM nonces WHERE fridge_id=? ORDER BY sent_at DESC LIMIT 1',(data.fridge_id,)).fetchone();c.close()
        if not n:raise HTTPException(409,'No genuine packet captured yet; wait a few seconds')
        m['nonce']=n['nonce'];m['signature']=signature(secret_for(data.fridge_id),m)
    try:
        result=ingest(m,'attack-demo')
        outcome='rejected' if not result.get('accepted') else 'accepted'
        reason=result.get('reason','')
    except ValueError as e:
        outcome='rejected';reason=str(e)
    return {'kind':data.kind,'outcome':outcome,'reason':reason}

@app.post('/api/simulator/{fid}/probe')
def sim_probe(fid:str,data:Probe,a=Depends(require('Admin','Pharmacist'))):
    """Manual operation: hold an ice pack or a warm hand to the simulated probe."""
    _demo_only()
    if fid not in ('FRIDGE_A','FRIDGE_B'):raise HTTPException(404,'Unknown fridge')
    if not simulator_service:raise HTTPException(503,'Simulator is not running')
    before=simulator_service.set_temperature(fid,data.temp_c)
    with transaction() as c:
        append_audit(c,a['username'],'simulation_probe_set',{'fridge':fid,'from_c':round(before,2),'to_c':data.temp_c,'demo_only':True})
    simulator_service.publish_now()
    return {'ok':True,'temp_c':data.temp_c}

@app.post('/api/simulator/reset')
def simulator_reset(a=Depends(require('Admin','Pharmacist'))):
    _demo_only()
    if not simulator_service:raise HTTPException(503,'Simulator is not running')
    simulator_service.reset()
    return {'ok':True}

_tamper_backup={}
@app.post('/api/simulator/tamper')
def simulate_tamper(data:Tamper,a=Depends(require('Admin'))):
    _demo_only()
    with transaction() as c:
        if data.action=='tamper':
            if _tamper_backup:raise HTTPException(409,'A record is already tampered; restore it first')
            # An older row, so live exposure maths (which reads the latest sample) is unaffected.
            r=c.execute("SELECT id,fridge_id,seq,temp_c FROM readings WHERE fridge_id='FRIDGE_A' ORDER BY seq DESC LIMIT 1 OFFSET 20").fetchone()
            if not r:raise HTTPException(409,'Not enough readings yet')
            _tamper_backup.update(dict(r))
            forged=round(float(r['temp_c'])-3.0,2)
            c.execute('UPDATE readings SET temp_c=? WHERE id=?',(forged,r['id']))
            return {'ok':True,'fridge':r['fridge_id'],'seq':r['seq'],'original':r['temp_c'],'forged':forged}
        if not _tamper_backup:raise HTTPException(409,'Nothing to restore')
        c.execute('UPDATE readings SET temp_c=? WHERE id=?',(_tamper_backup['temp_c'],_tamper_backup['id']))
        restored=dict(_tamper_backup);_tamper_backup.clear()
        append_audit(c,a['username'],'tamper_demo_restored',{'fridge':restored['fridge_id'],'seq':restored['seq'],'demo_only':True})
        return {'ok':True,'restored':restored}

