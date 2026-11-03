"""V10: security demos, batch management, user admin, AI report and compressor-health behaviour."""
import datetime
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from coldchain.app import app
from coldchain.db import connect,transaction
from coldchain.ml import compressor_health
from coldchain.simulator import Simulator
from .conftest import reading


@pytest.fixture
def demo(tmp_path,monkeypatch):
    monkeypatch.setenv('DB_PATH',str(tmp_path/'v10.sqlite'))
    monkeypatch.setenv('DEMO_MODE','1')
    monkeypatch.setenv('MQTT_ENABLED','0')
    from coldchain import app as appmod
    appmod.failures.clear()  # login throttle is process-wide; isolate each test
    with patch('coldchain.simulator.Simulator.start',lambda self:self.seed_synthetic_baseline()):
        with TestClient(app) as client:
            yield client


def login(client,username,password=None):
    password=password or f'ColdChainDemo_{username.capitalize()}2026!'
    r=client.post('/api/auth/login',json={'username':username,'password':password})
    assert r.status_code==200,r.text
    return {'Authorization':'Bearer '+r.json()['access_token']}


def test_attack_demos_are_all_rejected_and_logged(demo):
    admin=login(demo,'admin');inspector=login(demo,'inspector')
    assert demo.post('/api/simulator/attack',json={'kind':'forged'},headers=inspector).status_code==403
    for kind,reason in [('forged','Invalid HMAC'),('replay','replayed_nonce'),('stale','Malformed or outdated telemetry'),('unknown_device','Unknown device')]:
        r=demo.post('/api/simulator/attack',json={'kind':kind},headers=admin)
        assert r.status_code==200,r.text
        assert r.json()['outcome']=='rejected' and r.json()['reason']==reason
    reasons={x['reason'] for x in demo.get('/api/security/rejections',headers=inspector).json()}
    assert {'invalid_hmac','replayed_nonce','invalid_field_or_time','unknown_device'}<=reasons
    assert demo.get('/api/dashboard',headers=admin).json()['rejected_24h']>=4


def test_tamper_is_detected_then_restored(demo):
    admin=login(demo,'admin');pharm=login(demo,'pharmacist')
    assert demo.post('/api/simulator/tamper',json={'action':'tamper'},headers=pharm).status_code==403
    assert demo.get('/api/integrity/verify',headers=admin).json()['valid']
    t=demo.post('/api/simulator/tamper',json={'action':'tamper'},headers=admin).json()
    assert t['forged']!=t['original']
    bad=demo.get('/api/integrity/verify',headers=admin).json()
    assert not bad['valid'] and bad['reason']=='reading_record_differs_from_audit'
    assert bad['broken_record']['action']=='reading'
    assert demo.post('/api/simulator/tamper',json={'action':'restore'},headers=admin).status_code==200
    assert demo.get('/api/integrity/verify',headers=admin).json()['valid']


def test_batch_edit_and_dispose_with_audit(demo):
    pharm=login(demo,'pharmacist');inspector=login(demo,'inspector')
    batches=demo.get('/api/batches',headers=pharm).json()
    b,other=batches[0],batches[1]
    assert demo.patch(f"/api/batches/{b['id']}",json={'name':'Renamed'},headers=inspector).status_code==403
    assert demo.patch(f"/api/batches/{b['id']}",json={'lot':other['lot']},headers=pharm).status_code==409
    assert demo.patch(f"/api/batches/{b['id']}",json={'expires':'2020-01-01'},headers=pharm).status_code==422
    r=demo.patch(f"/api/batches/{b['id']}",json={'name':'Renamed Vaccine','expires':'2028-01-31'},headers=pharm)
    assert r.status_code==200 and r.json()['name']=='Renamed Vaccine' and r.json()['expires']=='2028-01-31'
    assert demo.request('DELETE',f"/api/batches/{b['id']}",json={'reason':'x'},headers=pharm).status_code==422
    assert demo.request('DELETE',f"/api/batches/{b['id']}",json={'reason':'Expired stock'},headers=pharm).status_code==200
    assert all(x['id']!=b['id'] for x in demo.get('/api/batches',headers=pharm).json())
    actions=[e['action'] for e in demo.get('/api/audit',headers=inspector).json()]
    assert 'batch_updated' in actions and 'batch_disposed' in actions
    assert demo.get('/api/integrity/verify',headers=inspector).json()['valid']


def test_user_admin_enable_disable_and_role(demo):
    admin=login(demo,'admin');pharm=login(demo,'pharmacist')
    assert demo.get('/api/admin/users',headers=pharm).status_code==403
    users={u['username']:u for u in demo.get('/api/admin/users',headers=admin).json()}
    assert demo.patch(f"/api/admin/users/{users['admin']['id']}",json={'enabled':False},headers=admin).status_code==409
    assert demo.patch(f"/api/admin/users/{users['inspector']['id']}",json={'enabled':False},headers=admin).status_code==200
    assert demo.post('/api/auth/login',json={'username':'inspector','password':'ColdChainDemo_Inspector2026!'}).status_code==401
    assert demo.patch(f"/api/admin/users/{users['pharmacist']['id']}",json={'role':'Inspector'},headers=admin).status_code==200
    # Server-side role check uses the database row, so the old token loses write access at once.
    data={'name':'X Vaccine','lot':'LOT-ROLE-1','expires':'2028-01-01','fridge_id':'FRIDGE_A'}
    assert demo.post('/api/batches',json=data,headers=pharm).status_code==403


def test_login_lockout_is_per_username(demo):
    for _ in range(10):
        assert demo.post('/api/auth/login',json={'username':'admin','password':'wrong-password'}).status_code==401
    assert demo.post('/api/auth/login',json={'username':'admin','password':'ColdChainDemo_Admin2026!'}).status_code==429
    login(demo,'pharmacist')  # another account from the same IP is unaffected


def test_dashboard_feed_hides_raw_readings_and_reports_fridge_state(demo):
    admin=login(demo,'admin')
    d=demo.get('/api/dashboard',headers=admin).json()
    assert all(e['action']!='reading' for e in d['events'])
    for f in d['fridges']:
        assert {'red_latch','batch_count','online','buffered'}<=set(f)
    # 30 minutes of seeded history gives the health model at least one cooling run.
    assert all(d['predictions'][f]['health']['score'] is not None for f in ('FRIDGE_A','FRIDGE_B'))


def test_ai_report_and_plot(demo):
    inspector=login(demo,'inspector')
    r=demo.get('/api/ai/report',headers=inspector).json()
    assert r['metrics']['horizon_minutes']==30 and 'temp_c' in r['metrics']['feature_importances']
    assert set(r['live'])=={'FRIDGE_A','FRIDGE_B'}
    assert demo.get('/api/ai/report').status_code==401
    assert demo.get('/api/ai/validation.png').headers['content-type']=='image/png'


def _cycle(minutes,degraded):
    rows=[];temp=6.9;comp=False;off=60;t0=datetime.datetime(2026,1,1,tzinfo=datetime.timezone.utc)
    for i in range(minutes*12):
        temp,comp,turned=Simulator.physics(temp,comp,off,True,False,degraded and i>=minutes*6,False)
        off=0 if turned else off+5
        rows.append({'observed_at':(t0+datetime.timedelta(seconds=5*i)).isoformat(),'temp_c':round(temp,2),'door_open':0,'mains_ok':1,'compressor_on':int(comp)})
    return list(reversed(rows))


def test_compressor_health_drops_when_cooling_weakens():
    healthy=compressor_health(_cycle(80,False),1.0)
    weak=compressor_health(_cycle(80,True),1.0)
    assert healthy['score']>=90
    assert weak['score']<50 and weak['trend']=='weakening'


def test_public_page_shows_plain_language_verdict(demo):
    admin=login(demo,'admin')
    token=demo.get('/api/batches',headers=admin).json()[0]['public_token']
    page=demo.get('/check/'+token).text
    assert 'Safe to use' in page and 'Heat budget' in page
    assert demo.get('/check/not-a-real-token').status_code==404


def test_move_requires_fresh_destination(demo):
    pharm=login(demo,'pharmacist')
    b=next(x for x in demo.get('/api/batches',headers=pharm).json() if x['fridge_id']=='FRIDGE_A')
    with transaction() as c:c.execute("UPDATE fridges SET last_seen='2020-01-01T00:00:00+00:00' WHERE id='FRIDGE_B'")
    r=demo.post(f"/api/batches/{b['id']}/move",json={'fridge_id':'FRIDGE_B'},headers=pharm)
    assert r.status_code==409 and 'online' in r.json()['detail']


def test_switch_change_publishes_immediately_like_firmware(demo):
    pharm=login(demo,'pharmacist')
    before=demo.get('/api/dashboard',headers=pharm).json()['fridges'][0]
    assert demo.post('/api/simulator/FRIDGE_A/control',json={'door_open':True},headers=pharm).status_code==200
    after=demo.get('/api/dashboard',headers=pharm).json()['fridges'][0]
    assert after['last_seq']==before['last_seq']+1 and after['door_open']==1


def test_hardware_view_assets_and_font_policy(demo):
    js=demo.get('/static/hardware.js')
    assert js.status_code==200 and 'window.HW' in js.text
    page=demo.get('/')
    assert '/static/hardware.js' in page.text and 'page-hardware' in page.text
    csp=page.headers['content-security-policy']
    assert 'https://fonts.gstatic.com' in csp and "script-src 'self'" in csp


def test_self_registration_is_read_only_until_admin_approves(demo):
    from coldchain import app as appmod
    appmod.registrations.clear()
    r=demo.post('/api/auth/register',json={'username':'Nurse.Rahim@clinic.bd','password':'GoodPass123','requested_role':'Pharmacist'})
    assert r.status_code==201,r.text
    assert r.json()['role']=='Inspector'
    nurse={'Authorization':'Bearer '+r.json()['access_token']}
    data={'name':'X Vaccine','lot':'LOT-REG-1','expires':'2028-01-01','fridge_id':'FRIDGE_A'}
    assert demo.post('/api/batches',json=data,headers=nurse).status_code==403
    # role can't be chosen directly, duplicate names are refused case-insensitively
    assert demo.post('/api/auth/register',json={'username':'evil','password':'GoodPass123','requested_role':'Admin'}).status_code==422
    assert demo.post('/api/auth/register',json={'username':'nurse.rahim@clinic.bd','password':'GoodPass123'}).status_code==409
    assert demo.post('/api/auth/register',json={'username':'a b','password':'GoodPass123'}).status_code==422
    admin=login(demo,'admin')
    u=next(x for x in demo.get('/api/admin/users',headers=admin).json() if x['username']=='Nurse.Rahim@clinic.bd')
    assert u['requested_role']=='Pharmacist'
    assert demo.patch(f"/api/admin/users/{u['id']}",json={'role':'Pharmacist'},headers=admin).status_code==200
    assert demo.post('/api/batches',json=data,headers=nurse).status_code==201
    assert next(x for x in demo.get('/api/admin/users',headers=admin).json() if x['id']==u['id'])['requested_role'] is None
    # login is case-insensitive on the username
    assert demo.post('/api/auth/login',json={'username':'NURSE.RAHIM@CLINIC.BD','password':'GoodPass123'}).status_code==200


def test_registration_rate_limit(demo):
    from coldchain import app as appmod
    appmod.registrations.clear()
    for i in range(5):
        assert demo.post('/api/auth/register',json={'username':f'user{i}x','password':'GoodPass123'}).status_code==201
    assert demo.post('/api/auth/register',json={'username':'user9x','password':'GoodPass123'}).status_code==429


def test_manual_probe_control(demo):
    pharm=login(demo,'pharmacist');insp=login(demo,'inspector')
    assert demo.post('/api/simulator/FRIDGE_A/probe',json={'temp_c':9.5},headers=insp).status_code==403
    assert demo.post('/api/simulator/FRIDGE_A/probe',json={'temp_c':99},headers=pharm).status_code==422
    assert demo.post('/api/simulator/FRIDGE_A/probe',json={'temp_c':9.5},headers=pharm).status_code==200
    f=demo.get('/api/dashboard',headers=pharm).json()['fridges'][0]
    assert f['temp_c']==9.5
