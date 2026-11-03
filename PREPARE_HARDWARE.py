"""Offline Windows-friendly wizard to prepare two ESP32 profiles and backend secrets.

Never ship generated .env or firmware secrets.h publicly. Local competition prototype only.
"""
from __future__ import annotations
import argparse
import getpass
import ipaddress
import json
import os
from pathlib import Path
import secrets
import shutil
import sys

ROOT = Path(__file__).resolve().parent
FIRMWARE = ROOT / 'firmware' / 'ColdChain_ESP32' / 'ColdChain_ESP32.ino'
PIN_PROFILE = ROOT / 'firmware' / 'ColdChain_ESP32' / 'hardware_pins.h'


def validate_host(value: str) -> str:
    # Host IP is an actual LAN address, not the device's localhost loopback.
    try:
        addr = ipaddress.ip_address(value)
        if addr.version != 4 or addr.is_loopback or addr.is_multicast or addr.is_unspecified:
            raise ValueError
        return str(addr)
    except ValueError as e:
        raise argparse.ArgumentTypeError('Use the Windows computer LAN IPv4, e.g. 192.168.137.1') from e


def c_string(s: str) -> str:
    # JSON quoted values are also valid C++ string literals for standard ASCII;
    # non-ASCII Wi-Fi labels should be encoded in UTF-8 by Arduino tools.
    return json.dumps(s, ensure_ascii=True)


def collect(args):
    ssid = args.ssid if args.ssid is not None else input('Wi-Fi / phone hotspot SSID: ').strip()
    password = args.wifi_password if args.wifi_password is not None else getpass.getpass('Wi-Fi / hotspot password (not echoed): ')
    host = args.host_ip if args.host_ip is not None else input('Laptop IPv4 on this Wi-Fi, e.g. 192.168.137.1: ').strip()
    try:
        host = validate_host(host)
    except argparse.ArgumentTypeError as e:
        raise ValueError(str(e)) from e
    if not ssid or len(ssid.encode('utf-8')) > 32:
        raise ValueError('Wi-Fi SSID must be 1–32 bytes')
    if not password or len(password) < 8:
        raise ValueError('Wi-Fi password must be at least 8 characters for a WPA2 hotspot')
    if any(c in ssid + password for c in '\r\n'):
        raise ValueError('Wi-Fi details may not contain line breaks')
    return ssid,password,host


def main() -> int:
    parser = argparse.ArgumentParser(description='Create private ColdChain onsite configuration, without installing anything.')
    parser.add_argument('--ssid',help='Wi-Fi / hotspot name')
    parser.add_argument('--wifi-password',help='Wi-Fi password (omit for hidden interactive prompt)')
    parser.add_argument('--host-ip',help='Laptop IPv4 on Wi-Fi/hotspot, not 127.0.0.1')
    parser.add_argument('--force',action='store_true',help='Replace existing private config after backup; rotates secrets.')
    args=parser.parse_args()
    if not FIRMWARE.exists() or not PIN_PROFILE.exists():
        print('ERROR: Missing original firmware .ino. Extract the whole ZIP first.',file=sys.stderr)
        return 1
    targets=[ROOT/'.env', ROOT/'ONSITE_PRIVATE_CREDENTIALS.txt',
             ROOT/'firmware'/'ColdChain_A'/'secrets.h', ROOT/'firmware'/'ColdChain_B'/'secrets.h']
    if any(p.exists() for p in targets) and not args.force:
        print('Existing onsite settings found. Configuration was NOT overwritten.')
        print('If you truly need to rotate secrets, back up the project and run with --force.')
        return 2
    try:
        ssid,wifi_pass,host=collect(args)
        unique={x:secrets.token_urlsafe(48) for x in ('JWT_SECRET','DEVICE_FRIDGE_A_SECRET','DEVICE_FRIDGE_B_SECRET')}
        # Unique generated passwords, stored privately. Avoid printed default demo credentials.
        passwords={role:secrets.token_urlsafe(19) for role in ('ADMIN','PHARMACIST','INSPECTOR')}
        cfg={
            'JWT_SECRET':unique['JWT_SECRET'],
            'DEVICE_FRIDGE_A_SECRET':unique['DEVICE_FRIDGE_A_SECRET'],
            'DEVICE_FRIDGE_B_SECRET':unique['DEVICE_FRIDGE_B_SECRET'],
            'ADMIN_PASSWORD':passwords['ADMIN'],
            'PHARMACIST_PASSWORD':passwords['PHARMACIST'],
            'INSPECTOR_PASSWORD':passwords['INSPECTOR'],
            'DB_PATH':'./coldchain_onsite.db',
            'DEMO_MODE':'0',
            'MQTT_ENABLED':'1',
            'MQTT_HOST':'127.0.0.1',
            'MQTT_PORT':'1883',
            'MQTT_USERNAME':'',
            'MQTT_PASSWORD':'',
            'MQTT_TLS':'0',
            'BIND_HOST':'127.0.0.1',
            'PUBLIC_BASE_URL':'',
            'TELEGRAM_BOT_TOKEN':'',
            'TELEGRAM_CHAT_ID':'',
            'SMTP_HOST':'',
            'SMTP_PORT':'587',
            'SMTP_USERNAME':'',
            'SMTP_PASSWORD':'',
            'ALERT_EMAIL_TO':'',
        }
        if args.force:
            for path in targets:
                if path.exists():
                    backup=path.with_name(path.name+'.previous')
                    shutil.copy2(path,backup)
        (ROOT/'.env').write_text(''.join(f'{k}={v}\n' for k,v in cfg.items()),encoding='utf-8')
        for letter in ('A','B'):
            folder=ROOT/'firmware'/f'ColdChain_{letter}'
            folder.mkdir(parents=True,exist_ok=True)
            shutil.copy2(FIRMWARE,folder/f'ColdChain_{letter}.ino')
            shutil.copy2(PIN_PROFILE,folder/'hardware_pins.h')
            header=(
                '#pragma once\n'
                '// PRIVATE: generated by PREPARE_HARDWARE.py; never commit/share.\n'
                f'#define DEVICE_ID {c_string("FRIDGE_"+letter)}\n'
                f'#define DEVICE_SECRET {c_string(unique["DEVICE_FRIDGE_"+letter+"_SECRET"])}\n'
                f'#define WIFI_SSID {c_string(ssid)}\n'
                f'#define WIFI_PASSWORD {c_string(wifi_pass)}\n'
                f'#define MQTT_BROKER_IP {c_string(host)}\n'
                '#define MQTT_BROKER_PORT 1883\n'
            )
            (folder/'secrets.h').write_text(header,encoding='utf-8')
        (ROOT/'ONSITE_PRIVATE_CREDENTIALS.txt').write_text(
            'PRIVATE ColdChain on-site prototype credentials — DO NOT SHARE\n'
            'These passwords are for a trusted local hackathon network, not Internet deployment.\n\n'
            + ''.join(f'{k.lower()}: {passwords[k]}\n' for k in ('ADMIN','PHARMACIST','INSPECTOR'))
            + '\nBackend: http://127.0.0.1:8000 (port may change to 8001 etc.)\n'
            + f'Broker runs on laptop; ESP32s connect to {host}:1883\n'
            + '\nDO NOT re-run --force after flashing unless both ESP32s are reflashed and the backend DB is reassessed.\n',
            encoding='utf-8'
        )
        print('\n[OK] Created private backend config and two complete Arduino sketch folders.')
        print('  firmware/ColdChain_A/ColdChain_A.ino + secrets.h')
        print('  firmware/ColdChain_B/ColdChain_B.ino + secrets.h')
        print('  .env (private; demo mode OFF; MQTT ON)')
        print('  ONSITE_PRIVATE_CREDENTIALS.txt (private account passwords)')
        print(f'  Broker IP configured in both boards: {host}')
        print('\nNEXT: start a trusted-LAN Mosquitto broker, flash both ESP32 boards,')
        print('then double-click START_HARDWARE_WINDOWS.bat. See docs/ONSITE_DAY_GUIDE.md.')
        print('WARNING: never connect mains wiring to the sample relay controller.')
        return 0
    except (ValueError,EOFError,KeyboardInterrupt) as e:
        print(f'ERROR: {e or "Setup canceled"}',file=sys.stderr)
        return 1


if __name__=='__main__':
    raise SystemExit(main())
