import time
from .conftest import reading
from coldchain.db import connect,transaction
from coldchain.core import verified_integrity,ingest

def create_batch(client,auth,lot='LOT-999',fridge='FRIDGE_A'):
    r=client.post('/api/batches',headers=auth['admin'],json={'name':'Insulin Test','lot':lot,'expires':'2027-12-31','fridge_id':fridge})
    assert r.status_code==201,r.text
    return r.json()

def test_jwt_rbac_and_public_qr(client,auth):
    assert client.get('/api/dashboard').status_code==401
    assert client.get('/api/dashboard',headers=auth['inspector']).status_code==200
    data={'name':'MMR','lot':'MMR-123','expires':'2027-12-31','fridge_id':'FRIDGE_B'}
    assert client.post('/api/batches',headers=auth['inspector'],json=data).status_code==403
    assert client.post('/api/admin/users',headers=auth['pharmacist'],json={'username':'x_user','password':'TestPassword!','role':'Admin'}).status_code==403
    r=client.post('/api/batches',headers=auth['pharmacist'],json=data)
    assert r.status_code==201
    token=r.json()['public_token']
    assert client.get('/api/public/batch/'+token).json()['status']=='Safe'
    assert client.get('/api/public/qr/'+token+'.png').headers['content-type']=='image/png'
    assert 'MMR' in client.get('/check/'+token).text

def test_replay_signature_rejection_and_dedup(client,auth):
    m=reading('FRIDGE_A',100,4.0)
    assert client.post('/api/device/ingest',json=m).status_code==200
    again=m.copy();assert client.post('/api/device/ingest',json=again).status_code==409 # repeated nonce
    retry=reading('FRIDGE_A',100,4.0)
    r=client.post('/api/device/ingest',json=retry)
    assert r.status_code==200 and r.json()['duplicate']
    damaged=reading('FRIDGE_A',101,5.0);damaged['temp_c_100']=550
    assert client.post('/api/device/ingest',json=damaged).status_code==401
    far=reading('FRIDGE_A',102,5.0);far['sent_at']-=900
    assert client.post('/api/device/ingest',json=far).status_code==401
    c=connect()
    assert c.execute('SELECT COUNT(*) FROM readings').fetchone()[0]==1
    reasons=[r[0] for r in c.execute('SELECT reason FROM invalid_messages')]
    assert 'replayed_nonce' in reasons and 'invalid_hmac' in reasons and 'invalid_field_or_time' in reasons
    c.close()

def test_exposure_above_12_counts_double_and_discard(client,auth):
    batch=create_batch(client,auth)
    base=int(time.time())-2000
    # 31 one-minute samples: 30 minutes at 13 C spends the full 60-minute exposure budget.
    for seq in range(31):
        m=reading('FRIDGE_A',seq+1,13.0,base+seq*60)
        result=client.post('/api/device/ingest',json=m)
        assert result.status_code==200,(seq,result.text)
    current=client.get('/api/batches',headers=auth['pharmacist']).json()[0]
    assert current['status']=='Discard' and current['remaining_seconds']==0
    assert current['exposure_seconds']==3600
    assert client.post('/api/batches/'+batch['id']+'/move',headers=auth['pharmacist'],json={'fridge_id':'FRIDGE_B'}).status_code==409
    assert client.post('/api/batches/'+batch['id']+'/admin-reset',headers=auth['pharmacist']).status_code==403
    ok=client.post('/api/batches/'+batch['id']+'/admin-reset',headers=auth['admin'])
    assert ok.status_code==200
    assert client.get('/api/batches',headers=auth['admin']).json()[0]['status']=='Safe'

def test_exposure_threshold_and_8c_boundary(client,auth):
    create_batch(client,auth)
    base=int(time.time())-5400
    for seq in range(37):
        assert client.post('/api/device/ingest',json=reading('FRIDGE_A',seq+1,8.0,base+seq*60)).status_code==200
    batch=client.get('/api/batches',headers=auth['admin']).json()[0]
    assert batch['exposure_seconds']==0
    for seq in range(37,87):
        assert client.post('/api/device/ingest',json=reading('FRIDGE_A',seq+1,9.0,base+seq*60)).status_code==200
    batch=client.get('/api/batches',headers=auth['admin']).json()[0]
    assert batch['status']=='At Risk' and batch['remaining_pct']<20

def test_integrity_detects_mutation(client,auth):
    create_batch(client,auth)
    assert client.get('/api/integrity/verify',headers=auth['inspector']).json()['valid']
    with transaction() as c:c.execute("UPDATE audit SET details='TAMPERED' WHERE id=1")
    result=client.get('/api/integrity/verify',headers=auth['inspector']).json()
    assert not result['valid'] and result['first_broken_id']==1

def test_relocation_and_preserve_dose(client,auth):
    b=create_batch(client,auth)
    base=int(time.time())
    assert client.post('/api/device/ingest',json=reading('FRIDGE_B',1,4.0,base)).status_code==200
    assert client.post('/api/device/ingest',json=reading('FRIDGE_A',1,9.5,base)).status_code==200
    rec=client.get('/api/dashboard',headers=auth['pharmacist']).json()['recommendations']
    assert any(x['batch_id']==b['id'] and x['to_fridge']=='FRIDGE_B' for x in rec)
    moved=client.post('/api/relocations/confirm',headers=auth['pharmacist'],json={'batch_id':b['id'],'target_fridge_id':'FRIDGE_B'})
    assert moved.status_code==200,moved.text
    changed=client.get('/api/batches',headers=auth['pharmacist']).json()[0]
    assert changed['fridge_id']=='FRIDGE_B'
    assert client.post('/api/relocations/confirm',headers=auth['pharmacist'],json={'batch_id':b['id'],'target_fridge_id':'FRIDGE_B'}).status_code==409

def test_timestamp_nonmonotonic_and_invalid_expiry(client,auth):
    r=client.post('/api/batches',headers=auth['pharmacist'],json={'name':'Test','lot':'EXP-1','expires':'2020-01-01','fridge_id':'FRIDGE_A'})
    assert r.status_code==422
    t=int(time.time())-60
    assert client.post('/api/device/ingest',json=reading('FRIDGE_A',10,5,t)).status_code==200
    assert client.post('/api/device/ingest',json=reading('FRIDGE_A',11,5,t-10)).status_code==409


def test_only_authorized_can_change_simulation_controls(client,auth):
    # Live mode disables simulation controls even if roles would otherwise permit them.
    assert client.post('/api/simulator/FRIDGE_A/control',headers=auth['inspector'],json={'mains_ok':False}).status_code==403
    assert client.post('/api/simulator/FRIDGE_A/control',headers=auth['admin'],json={'mains_ok':False}).status_code==404

def test_conflicting_duplicate_sequence_is_rejected(client,auth):
    good=reading('FRIDGE_A',2,5.1)
    assert client.post('/api/device/ingest',json=good).status_code==200
    changed=reading('FRIDGE_A',2,10.1)
    response=client.post('/api/device/ingest',json=changed)
    assert response.status_code==409
    assert 'sequence_payload_conflict' in str(client.get('/api/security/rejections',headers=auth['inspector']).json())


def test_integrity_detects_changed_sensor_table(client,auth):
    assert client.post('/api/device/ingest',json=reading('FRIDGE_A',1,5.2)).status_code==200
    with transaction() as c:c.execute('UPDATE readings SET temp_c=20 WHERE seq=1')
    r=client.get('/api/integrity/verify',headers=auth['inspector']).json()
    assert not r['valid'] and r['reason']=='reading_record_differs_from_audit'


def test_simulator_generates_signed_telemetry(client,auth):
    from coldchain.simulator import Simulator
    sim=Simulator()
    sim.tick()
    d=client.get('/api/dashboard',headers=auth['admin']).json()
    assert len(d['fridges'])==2
    assert all(f['last_seq']==0 and f['simulated']==1 for f in d['fridges'])
    assert all(f['battery_pct']<=100 for f in d['fridges'])

def test_door_open_over_60_seconds_generates_alert_record(client,auth):
    from coldchain.security import signature
    from coldchain.core import secret_for
    start=int(time.time())-71
    a=reading('FRIDGE_A',1,4.8,start);a['door_open']=True;a['signature']=signature(secret_for('FRIDGE_A'),a)
    assert client.post('/api/device/ingest',json=a).status_code==200
    b=reading('FRIDGE_A',2,4.9,int(time.time()));b['door_open']=True;b['signature']=signature(secret_for('FRIDGE_A'),b)
    assert client.post('/api/device/ingest',json=b).status_code==200
    c=connect()
    alert=c.execute('SELECT status FROM alert_outbox ORDER BY id DESC LIMIT 1').fetchone()
    assert alert and alert['status']=='not_configured' # no fake claim SMS/Telegram was delivered
    assert c.execute('SELECT door_alerted FROM fridges WHERE id="FRIDGE_A"').fetchone()[0]==1
    c.close()


def test_simulated_wifi_recovery_in_order_and_power_status(client,auth):
    from coldchain.simulator import Simulator
    sim=Simulator()
    with transaction() as c:
        c.execute('UPDATE simulation_controls SET wifi_ok=0,mains_ok=0 WHERE fridge_id="FRIDGE_A"')
    for _ in range(4):sim.tick()
    c=connect()
    assert c.execute('SELECT COUNT(*) FROM readings WHERE fridge_id="FRIDGE_A"').fetchone()[0]==0
    assert c.execute('SELECT COUNT(*) FROM readings WHERE fridge_id="FRIDGE_B"').fetchone()[0]==4
    c.close()
    with transaction() as c:c.execute('UPDATE simulation_controls SET wifi_ok=1 WHERE fridge_id="FRIDGE_A"')
    sim.tick()
    c=connect()
    a=[dict(x) for x in c.execute('SELECT seq,mains_ok FROM readings WHERE fridge_id="FRIDGE_A" ORDER BY seq')]
    assert len(a)==5 and [x['seq'] for x in a]==[0,1,2,3,4]
    assert all(x['mains_ok']==0 for x in a)
    c.close()
