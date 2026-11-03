"""Round 1: presentation scenes are real endpoints but explicitly synthetic."""
import os
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from coldchain.app import app
from coldchain.db import connect


@pytest.fixture
def demo_client(tmp_path,monkeypatch):
    monkeypatch.setenv('DB_PATH',str(tmp_path/'round1.sqlite'))
    monkeypatch.setenv('DEMO_MODE','1')
    monkeypatch.setenv('MQTT_ENABLED','0')
    monkeypatch.delenv('PUBLIC_BASE_URL',raising=False)
    # Seed deterministic synthetic samples without a concurrent 5-second simulator
    # background thread racing our SQLite transaction assertions.
    with patch('coldchain.simulator.Simulator.start',lambda self:self.seed_synthetic_baseline()):
        with TestClient(app,base_url='http://127.0.0.1:8012') as client:
            yield client


def user_header(client,username):
    role=username.capitalize()
    response=client.post('/api/auth/login',json={
        'username':username,'password':f'ColdChainDemo_{role}2026!'})
    assert response.status_code==200,response.text
    return {'Authorization':'Bearer '+response.json()['access_token']}


def test_exposure_scene_role_guard_and_synthetic_math(demo_client):
    admin=user_header(demo_client,'admin')
    inspector=user_header(demo_client,'inspector')
    endpoint='/api/simulator/round1/exposure'
    assert demo_client.post(endpoint,json={'scenario':'discard'},headers=inspector).status_code==403
    assert demo_client.post(endpoint,json={'scenario':'bad'},headers=admin).status_code==422
    for scene,status,left,weighted in [('safe','Safe',100,0),('at_risk','At Risk',15,51),('discard','Discard',0,60)]:
        result=demo_client.post(endpoint,json={'scenario':scene},headers=admin)
        assert result.status_code==200,result.text
        body=result.json()
        assert body['status']==status
        assert body['remaining_pct']==left
        assert body['exposure_seconds']==weighted*60
        assert body['lot']=='SIM-R1-EXPOSURE'
    c=connect()
    assert c.execute("SELECT COUNT(*) FROM batches WHERE lot='SIM-R1-EXPOSURE'").fetchone()[0]==1
    assert c.execute("SELECT COUNT(*) FROM readings WHERE source='simulator'").fetchone()[0]>=16
    c.close()
    assert demo_client.get('/api/integrity/verify',headers=inspector).json()['valid']


def test_forecast_scene_and_pharmacist_relocation(demo_client):
    admin=user_header(demo_client,'admin')
    pharmacist=user_header(demo_client,'pharmacist')
    inspector=user_header(demo_client,'inspector')
    endpoint='/api/simulator/round1/forecast'
    assert demo_client.post(endpoint,json={'scenario':'rising_risk'},headers=inspector).status_code==403
    response=demo_client.post(endpoint,json={'scenario':'rising_risk'},headers=admin)
    assert response.status_code==200,response.text
    data=response.json()
    pred=data['predictions']['FRIDGE_A']
    assert pred['forecast']['warning'] is True
    assert pred['forecast']['predicted_c']>8
    assert isinstance(pred['health']['score'],int)
    assert 0<=pred['health']['score']<=100
    assert data['recommendations'], 'Expected at least one safe destination for seeded samples'
    rec=data['recommendations'][0]
    assert rec['from_fridge']=='FRIDGE_A'
    assert rec['to_fridge']=='FRIDGE_B'
    assert demo_client.post('/api/relocations/confirm',headers=inspector,json={
        'batch_id':rec['batch_id'],'target_fridge_id':rec['to_fridge']}).status_code==403
    moved=demo_client.post('/api/relocations/confirm',headers=pharmacist,json={
        'batch_id':rec['batch_id'],'target_fridge_id':rec['to_fridge']})
    assert moved.status_code==200,moved.text
    assert moved.json()['to']=='FRIDGE_B'
    assert demo_client.get('/api/integrity/verify',headers=inspector).json()['valid']


def test_public_qr_uses_active_port_when_no_override(demo_client):
    admin=user_header(demo_client,'admin')
    result=demo_client.post('/api/simulator/round1/exposure',headers=admin,json={'scenario':'at_risk'}).json()
    token=result['public_token']
    seen=[]
    from qrcode import make as real_make
    def spy(payload):
        seen.append(payload)
        return real_make(payload)
    with patch('coldchain.app.qrcode.make',side_effect=spy):
        response=demo_client.get(f'/api/public/qr/{token}.png')
    assert response.status_code==200
    assert seen==[f'http://127.0.0.1:8012/check/{token}']
    public=demo_client.get('/api/public/batch/'+token)
    assert public.status_code==200
    assert public.json()['status']=='At Risk'


def test_round1_scenes_disabled_when_not_demo(client,auth):
    assert client.post('/api/simulator/round1/exposure',headers=auth['admin'],json={'scenario':'discard'}).status_code==404
    assert client.post('/api/simulator/round1/forecast',headers=auth['admin'],json={'scenario':'rising_risk'}).status_code==404
