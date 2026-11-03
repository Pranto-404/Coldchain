import os,time,secrets
import pytest
from fastapi.testclient import TestClient
from coldchain.security import signature
from coldchain.core import secret_for
from coldchain.app import app

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('DB_PATH',str(tmp_path/'app.sqlite'))
    monkeypatch.setenv('DEMO_MODE','0')
    monkeypatch.setenv('MQTT_ENABLED','0')
    monkeypatch.setenv('JWT_SECRET','signed_test_key_that_is_very_long_1234567890')
    monkeypatch.setenv('DEVICE_FRIDGE_A_SECRET','device_A_testing_random_unique_secret_1234567890')
    monkeypatch.setenv('DEVICE_FRIDGE_B_SECRET','device_B_testing_random_unique_secret_1234567890')
    monkeypatch.setenv('ADMIN_PASSWORD','SuperSecurePass123!')
    monkeypatch.setenv('PHARMACIST_PASSWORD','PharmacistPass123!')
    monkeypatch.setenv('INSPECTOR_PASSWORD','InspectorPass123!')
    with TestClient(app) as cli:yield cli

@pytest.fixture
def auth(client):
    def make(user,pw):
        r=client.post('/api/auth/login',json={'username':user,'password':pw})
        assert r.status_code==200,r.text
        return {'Authorization':'Bearer '+r.json()['access_token']}
    return {'admin':make('admin','SuperSecurePass123!'),'pharmacist':make('pharmacist','PharmacistPass123!'),'inspector':make('inspector','InspectorPass123!')}

def reading(fridge,seq,temp,observed=None,nonce=None):
    sent=int(time.time())
    m={'device_id':fridge,'seq':seq,'observed_at':observed or sent,'temp_c_100':int(round(temp*100)),
       'door_open':False,'mains_ok':True,'compressor_on':False,'battery_pct':100,
       'sent_at':sent,'nonce':nonce or secrets.token_hex(12)}
    m['signature']=signature(secret_for(fridge),m)
    return m
