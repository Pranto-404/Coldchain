"""Update only the ESP32 Wi-Fi/hotspot broker details. Never rotate device secrets.

Edits both private headers in-place, preserving the existing device keys and
backend .env. Reflash both boards after the change.
"""
from __future__ import annotations
import argparse
import getpass
import json
import re
import sys
from pathlib import Path
from PREPARE_HARDWARE import ROOT, validate_host, c_string

DEFINES = ('WIFI_SSID', 'WIFI_PASSWORD', 'MQTT_BROKER_IP')

def update_headers(ssid: str, password: str, host: str, root: Path = ROOT) -> int:
    if not ssid or len(ssid.encode('utf-8')) > 32:
        raise ValueError('Wi-Fi SSID must be between 1 and 32 bytes.')
    if len(password) < 8 or any(c in ssid+password for c in '\r\n'):
        raise ValueError('WPA2 password must be at least 8 characters; no newlines allowed.')
    try:
        host=validate_host(host)
    except argparse.ArgumentTypeError as exc:
        raise ValueError(str(exc)) from exc
    cfg=root/'.env'
    if not cfg.exists():
        raise ValueError('Hardware config missing. Run PREPARE_HARDWARE_WINDOWS.bat first.')
    replacements={
      'WIFI_SSID':ssid,
      'WIFI_PASSWORD':password,
      'MQTT_BROKER_IP':host,
    }
    old_and_new=[]
    for board in 'AB':
        header=root/'firmware'/f'ColdChain_{board}'/'secrets.h'
        if not header.exists():
            raise ValueError(f'{header} missing. Prepare hardware first.')
        contents=header.read_text(encoding='utf-8')
        if f'#define DEVICE_ID "FRIDGE_{board}"' not in contents:
            raise ValueError(f'Board {board} ID invalid; no changes were made.')
        if not re.search(r'^#define DEVICE_SECRET "[^"\r\n]+"$',contents,re.M):
            raise ValueError(f'Board {board} secret missing; no changes were made.')
        updated=contents
        for macro,value in replacements.items():
            line=f'#define {macro} {c_string(value)}'
            pattern=rf'^#define {macro} .*?$'
            updated,count=re.subn(pattern,lambda m:line,updated,flags=re.M)
            if count!=1:
                raise ValueError(f'Expected exactly one {macro} in board {board}.')
        old_and_new.append((header,contents,updated))
    # All preconditions validated before any edits. Restore on a write failure.
    changed=[]
    try:
        for path,old,new in old_and_new:
            path.write_text(new,encoding='utf-8')
            changed.append((path,old))
    except OSError:
        for path,old in changed:
            path.write_text(old,encoding='utf-8')
        raise
    private_summary=root/'ONSITE_PRIVATE_CREDENTIALS.txt'
    if private_summary.exists():
        summary=private_summary.read_text(encoding='utf-8')
        summary=re.sub(r'^Broker runs on laptop; ESP32s connect to [^\r\n]+$',
                       f'Broker runs on laptop; ESP32s connect to {host}:1883',summary,flags=re.M)
        private_summary.write_text(summary,encoding='utf-8')
    print('[OK] Wi-Fi/broker IP updated in both board headers; device identities preserved.')
    print('[NEXT] Recompile and reflash both ESP32 boards for the new network.')
    print('Broker LAN IP:',host)
    print('Passwords and unique HMAC keys were NOT rotated or printed.')
    return 0

def main():
    p=argparse.ArgumentParser(description='Change hotspot parameters without changing HMAC keys.')
    p.add_argument('--ssid'); p.add_argument('--wifi-password'); p.add_argument('--host-ip')
    args=p.parse_args()
    try:
        ssid=args.ssid if args.ssid is not None else input('New Wi-Fi/hotspot SSID: ').strip()
        pw=args.wifi_password if args.wifi_password is not None else getpass.getpass('New Wi-Fi password (hidden): ')
        ip=args.host_ip if args.host_ip is not None else input('Laptop IPv4 on Wi-Fi/hotspot: ').strip()
        return update_headers(ssid,pw,ip)
    except (ValueError,EOFError,KeyboardInterrupt) as exc:
        print('[ERROR]', str(exc) or 'Canceled',file=sys.stderr)
        return 1
if __name__=='__main__':raise SystemExit(main())
