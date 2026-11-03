"""Wait for fresh, non-simulated samples from both ESP32 boards via backend HTTP API."""
import argparse
import datetime as dt
import json
from pathlib import Path
import time
import urllib.request
import urllib.error

ROOT=Path(__file__).resolve().parent

def password():
    p=ROOT/'ONSITE_PRIVATE_CREDENTIALS.txt'
    if not p.exists():raise RuntimeError('Missing ONSITE_PRIVATE_CREDENTIALS.txt; run PREPARE_HARDWARE_WINDOWS.bat')
    for line in p.read_text(encoding='utf-8').splitlines():
        if line.startswith('admin: '):return line.split(': ',1)[1]
    raise RuntimeError('Admin password not found in private credentials file')

def api(base,path,data=None,token=None):
    headers={'Accept':'application/json'}
    if token:headers['Authorization']='Bearer '+token
    if data is not None:headers['Content-Type']='application/json'
    request=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers=headers)
    with urllib.request.urlopen(request,timeout=8) as response:
        return json.load(response)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--wait',type=int,default=90,help='Seconds to wait for both devices (0 = check once)')
    args=parser.parse_args()
    base=f'http://127.0.0.1:{args.port}'
    try:
        login=api(base,'/api/auth/login',{'username':'admin','password':password()})
    except (urllib.error.URLError,RuntimeError,ValueError) as e:
        print(f'[FAIL] Cannot log in to local hardware backend at {base}: {e}')
        return 1
    token=login['access_token']
    start=time.monotonic()
    while True:
        try:data=api(base,'/api/dashboard',token=token)
        except (urllib.error.URLError,ValueError) as e:
            print(f'[FAIL] Dashboard unavailable: {e}')
            return 1
        passed=set()
        print('\nDevice freshness status (all UTC):')
        for device in data.get('fridges',[]):
            t=device.get('last_seen')
            age=10**6
            if t:
                observed=dt.datetime.fromisoformat(t.replace('Z','+00:00'))
                age=(dt.datetime.now(dt.timezone.utc)-observed).total_seconds()
            ok=(age<=25 and not bool(device.get('simulated')) and device.get('last_seq',-1)>=0)
            if ok:passed.add(device['id'])
            print(f"  {device['id']}: {'LIVE' if ok else 'WAITING'}; "
                  f"age={int(age) if t else '-'}s; last_seq={device.get('last_seq')}; "
                  f"temp={device.get('temp_c')}; simulated={bool(device.get('simulated'))}")
        if {'FRIDGE_A','FRIDGE_B'}<=passed:
            print('[PASS] Two independent recent real-device sources detected by the backend.')
            print('Still verify real temperature accuracy, OLED, relay/LED, alarm and offline recovery physically.')
            return 0
        if time.monotonic()-start>=args.wait:
            print('[NOT READY] Both devices are not reporting live data within 25 seconds.')
            print('Check Wi-Fi SSID/password, broker IP/firewall, Serial Monitor and unique device keys.')
            return 1
        time.sleep(min(5,max(0,args.wait-(time.monotonic()-start))))

if __name__=='__main__':raise SystemExit(main())
