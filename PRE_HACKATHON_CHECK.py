"""Offline readiness assessment without revealing keys, passwords or credentials.

A PASS here proves only file/tool availability, not that physical hardware works.
"""
from __future__ import annotations
import argparse
import datetime as dt
import importlib.util
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
ROOT=Path(__file__).resolve().parent

def check() -> list[tuple[str,str,str]]:
    outcomes=[]
    def add(label, status, detail): outcomes.append((label,status,detail))
    needed=['START_DEMO_WINDOWS.bat','START_HARDWARE_WINDOWS.bat','PREPARE_HARDWARE.py',
      'UPDATE_NETWORK.py','UPLOAD_ESP32_WINDOWS.bat','CHECK_HARDWARE_READY.py',
      'firmware/ColdChain_ESP32/ColdChain_ESP32.ino','models/forecast.joblib',
      'web/index.html','coldchain/app.py','requirements.txt']
    missing=[x for x in needed if not (ROOT/x).is_file()]
    add('Project source', 'PASS' if not missing else 'FAIL',
        'Required project files present' if not missing else 'Missing: '+', '.join(missing))
    venv=ROOT/'.venv'/'Scripts'/'python.exe'
    add('Windows Python environment','PASS' if venv.is_file() else 'PENDING',
        'Prepared .venv found' if venv.is_file() else 'Run START_DEMO_WINDOWS.bat once before the event')
    cli=ROOT/'tools'/'arduino-cli'/'arduino-cli.exe'
    global_cli=shutil.which('arduino-cli')
    cli_path=str(cli) if cli.is_file() else global_cli
    add('Arduino CLI','PASS' if cli_path else 'PENDING',
        'Arduino CLI executable available' if cli_path else 'Run PREPARE_LAPTOP_WINDOWS.bat at home')
    if cli_path:
        try:
            result=subprocess.run([cli_path,'core','list'],capture_output=True,text=True,timeout=12)
            installed='esp32:esp32' in result.stdout
            add('ESP32 compiler/core','PASS' if installed else 'PENDING',
                'Espressif core appears installed' if installed else 'ESP32 core missing or cannot be listed')
        except (OSError,subprocess.TimeoutExpired):
            add('ESP32 compiler/core','PENDING','arduino-cli core list could not be run')
    mos=shutil.which('mosquitto') or next((str(p) for p in [
        Path(os.environ.get('ProgramFiles','C:/Program Files'))/'mosquitto'/'mosquitto.exe',
        ROOT/'tools'/'mosquitto'/'mosquitto.exe'] if p.is_file()),None)
    add('Eclipse Mosquitto','PASS' if mos else 'PENDING',
        'Broker executable found' if mos else 'Install official Mosquitto Windows package before the event')
    private=ROOT/'.env'
    pairs=[ROOT/'firmware'/f'ColdChain_{k}'/f'ColdChain_{k}.ino' for k in 'AB']
    heads=[ROOT/'firmware'/f'ColdChain_{k}'/'secrets.h' for k in 'AB']
    present=private.is_file() and all(p.is_file() for p in pairs+heads)
    add('Private A/B firmware profiles','PASS' if present else 'PENDING',
        'Two board profiles and private environment present' if present else 'Run PREPARE_HARDWARE_WINDOWS.bat for your chosen hotspot')
    if present:
        result=subprocess.run([sys.executable,str(ROOT/'CHECK_HARDWARE_READY.py')],
                              capture_output=True,text=True,timeout=15)
        add('HMAC profile consistency','PASS' if result.returncode==0 else 'FAIL',
            'Backend and A/B keys match' if result.returncode==0 else 'Device IDs/keys mismatch; see CHECK_HARDWARE_WINDOWS.bat')
    else:add('HMAC profile consistency','PENDING','Requires both private board profiles')
    add('Physical wiring, firmware upload, real telemetry','PENDING','Only verifiable after organizer hardware is provided')
    add('Full 30-minute Wi-Fi outage and 60-second door alarm','PENDING','Record actual physical test evidence onsite')
    return outcomes

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--save',action='store_true');args=parser.parse_args()
    status=check()
    lines=['ColdChain V8 — Hackathon preparation status',
      f'Generated UTC: {dt.datetime.now(dt.timezone.utc).isoformat()}',
      'NO PRIVATE SECRETS ARE INCLUDED. Checks do not imply physical certification.',
      '',*[f'[{st}] {name}: {detail}' for name,st,detail in status]]
    report='\n'.join(lines)+'\n'
    print(report)
    if args.save:
        folder=ROOT/'report';folder.mkdir(exist_ok=True)
        file=folder/'MY_PC_PREFLIGHT.txt';file.write_text(report,encoding='utf-8')
        print('Report saved:',file)
    return 1 if any(st=='FAIL' for _,st,_ in status) else 0
if __name__=='__main__':raise SystemExit(main())
