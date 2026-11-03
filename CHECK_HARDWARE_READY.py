"""Check private hardware setup without printing secrets. Standard library only."""
import argparse
import re
import socket
from pathlib import Path

BASE=Path(__file__).resolve().parent

def read_env(path):
    values={}
    for line in path.read_text(encoding='utf-8').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            key,val=line.split('=',1)
            values[key.strip()]=val.strip()
    return values


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--require-broker',action='store_true')
    args=p.parse_args()
    errors=[]
    file=BASE/'.env'
    if not file.exists():
        print('[FAIL] .env missing. Run PREPARE_HARDWARE_WINDOWS.bat.')
        return 1
    cfg=read_env(file)
    for k in ('JWT_SECRET','DEVICE_FRIDGE_A_SECRET','DEVICE_FRIDGE_B_SECRET'):
        if len(cfg.get(k,''))<32:errors.append(f'{k} must be at least 32 characters')
    if cfg.get('DEVICE_FRIDGE_A_SECRET')==cfg.get('DEVICE_FRIDGE_B_SECRET'):
        errors.append('Both ESP32 nodes are using the same secret')
    if cfg.get('DEMO_MODE')!='0' or cfg.get('MQTT_ENABLED')!='1':
        errors.append('Hardware mode requires DEMO_MODE=0 and MQTT_ENABLED=1')
    for letter in 'AB':
        folder=BASE/'firmware'/f'ColdChain_{letter}'
        if not (folder/f'ColdChain_{letter}.ino').is_file() or not (folder/'hardware_pins.h').is_file():
            errors.append(f'Firmware sketch for board {letter} is missing')
        header=folder/'secrets.h'
        if not header.exists():
            errors.append(f'Board {letter} private header missing')
        else:
            content=header.read_text(encoding='utf-8')
            match=re.search(r'^#define DEVICE_SECRET "([^"]+)"',content,re.MULTILINE)
            if not match or match.group(1)!=cfg.get(f'DEVICE_FRIDGE_{letter}_SECRET'):
                errors.append(f'Board {letter} and backend device keys do not match')
            if f'#define DEVICE_ID "FRIDGE_{letter}"' not in content:
                errors.append(f'Board {letter} ID incorrect')
    if args.require_broker:
        host=cfg.get('MQTT_HOST','127.0.0.1')
        try:
            port=int(cfg.get('MQTT_PORT','1883'))
            with socket.create_connection((host,port),timeout=2):pass
        except (OSError,ValueError):
            errors.append(f'MQTT broker not reachable at {host}:{cfg.get("MQTT_PORT","1883")}; start Mosquitto first')
    if errors:
        for error in errors:print('[FAIL]',error)
        return 1
    print('[OK] Hardware config: private keys, both board profiles, and environment are consistent.')
    if args.require_broker:print('[OK] MQTT TCP port accessible (this alone does not prove device telemetry).')
    return 0

if __name__=='__main__':raise SystemExit(main())
