"""Configure optional Telegram alerts locally. No bot token is shipped.

You must create the bot and obtain a chat ID yourself. The script can send
one *explicitly authorized* test message over the Internet if requested.
"""
import argparse
import getpass
from pathlib import Path
import sys
import urllib.parse
import urllib.request
import json

ROOT=Path(__file__).resolve().parent

def update_env(path: Path, replacements: dict[str,str]):
    if not path.exists():raise ValueError('Missing .env. Run PREPARE_HARDWARE_WINDOWS.bat first.')
    raw=path.read_text(encoding='utf-8').splitlines()
    original={}
    for line in raw:
        if '=' in line and not line.startswith('#'):
            k,v=line.split('=',1)
            original[k]=v
    original.update(replacements)
    path.write_text(''.join(f'{k}={v}\n' for k,v in original.items()),encoding='utf-8')

def test_message(token:str,chat:str):
    body=urllib.parse.urlencode({'chat_id':chat,'text':'ColdChain TEST ALERT: checking notification delivery. Not a real refrigerator incident.'}).encode()
    req=urllib.request.Request(f'https://api.telegram.org/bot{token}/sendMessage',data=body)
    with urllib.request.urlopen(req,timeout=12) as resp:
        payload=json.load(resp)
    return payload.get('ok') is True

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--token');p.add_argument('--chat-id');p.add_argument('--test',action='store_true')
    args=p.parse_args()
    try:
        token=args.token if args.token is not None else getpass.getpass('Telegram bot token (hidden): ').strip()
        chat=args.chat_id if args.chat_id is not None else input('Telegram Chat ID (numeric or @channel): ').strip()
        if not token or not chat or any(c in '\n\r=' for c in token+chat):raise ValueError('Token and chat ID required; must not contain newlines/equals sign')
        if not (token.partition(':')[0].isdigit() and len(token.split(':',1))==2):raise ValueError('Bot token format looks incorrect')
        update_env(ROOT/'.env',{'TELEGRAM_BOT_TOKEN':token,'TELEGRAM_CHAT_ID':chat})
        print('[OK] Telegram credentials saved to private .env (not printed).')
        should_test=args.test
        if args.token is None and args.chat_id is None:
            should_test=input('Send ONE test Telegram message now? Y/N: ').strip().lower()=='y'
        if should_test:
            try:
                if test_message(token,chat): print('[PASS] Telegram API confirmed test message request.')
                else:print('[FAIL] Telegram API did not acknowledge test message.');return 1
            except Exception as e:
                print('[FAIL] Test delivery failed; verify token/chat/Internet:',type(e).__name__,str(e)[:200]);return 1
        print('Next: start HARDWARE mode to use these credentials for >60s door alerts.')
        return 0
    except (ValueError,KeyboardInterrupt,EOFError) as e:
        print('[ERROR]', str(e) or 'Canceled',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
