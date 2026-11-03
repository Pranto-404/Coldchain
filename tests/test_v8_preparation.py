"""V8 offline staging checks. No device or external services needed."""
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def stage(tmp_path):
    shutil.copytree(ROOT/'firmware'/'ColdChain_ESP32', tmp_path/'firmware'/'ColdChain_ESP32')
    for file in ('PREPARE_HARDWARE.py','UPDATE_NETWORK.py','CHECK_HARDWARE_READY.py','CONFIGURE_TELEGRAM.py'):
        shutil.copy(ROOT/file, tmp_path/file)
    args=[sys.executable,str(tmp_path/'PREPARE_HARDWARE.py'), '--ssid','PrototypeHotspot',
          '--wifi-password','Testing12345678', '--host-ip','192.168.43.10']
    out=subprocess.run(args, text=True,capture_output=True,timeout=12)
    assert out.returncode==0, out.stdout+out.stderr
    return tmp_path

def test_profile_generation_includes_editable_pins(tmp_path):
    stage(tmp_path)
    for board in 'AB':
        folder=tmp_path/'firmware'/f'ColdChain_{board}'
        ino=(folder/f'ColdChain_{board}.ino').read_text()
        pins=(folder/'hardware_pins.h').read_text()
        assert 'hardware_pins.h' in ino
        assert 'PIN_OLED_SDA' in pins and 'DOOR_OPEN_WHEN_LOW' in pins
    assert subprocess.run([sys.executable,str(tmp_path/'CHECK_HARDWARE_READY.py')],capture_output=True,timeout=12).returncode==0

def test_network_update_preserves_keys_and_username_password(tmp_path):
    stage(tmp_path)
    files=[tmp_path/'.env']+[tmp_path/'firmware'/f'ColdChain_{letter}'/'secrets.h' for letter in 'AB']
    original=[p.read_text() for p in files]
    change=[sys.executable,str(tmp_path/'UPDATE_NETWORK.py'), '--ssid','EventWifi',
        '--wifi-password','OtherPassword88', '--host-ip','192.168.137.1']
    out=subprocess.run(change,capture_output=True,text=True,timeout=12)
    assert out.returncode==0,out.stderr+out.stdout
    assert files[0].read_text()==original[0]
    for k in (1,2):
        curr=files[k].read_text()
        assert re.search(r'^#define DEVICE_SECRET "([^"\r\n]+)"',curr,re.M).group(1)==re.search(r'^#define DEVICE_SECRET "([^"\r\n]+)"',original[k],re.M).group(1)
        assert 'EventWifi' in curr and '192.168.137.1' in curr
    assert subprocess.run([sys.executable,str(tmp_path/'CHECK_HARDWARE_READY.py')],capture_output=True).returncode==0

def test_bad_network_update_does_not_mutate(tmp_path):
    stage(tmp_path)
    files=[tmp_path/'.env']+[tmp_path/'firmware'/f'ColdChain_{letter}'/'secrets.h' for letter in 'AB']
    original=[p.read_bytes() for p in files]
    change=[sys.executable,str(tmp_path/'UPDATE_NETWORK.py'), '--ssid','EventWifi',
            '--wifi-password','OtherPassword88','--host-ip','127.0.0.1']
    out=subprocess.run(change,capture_output=True,text=True,timeout=12)
    assert out.returncode!=0
    assert [p.read_bytes() for p in files]==original

def test_telegram_credentials_in_private_env_only(tmp_path):
    stage(tmp_path)
    script=[sys.executable,str(tmp_path/'CONFIGURE_TELEGRAM.py'),'--token','123456:TEST_SECRET_TOKEN','--chat-id','887766']
    out=subprocess.run(script,capture_output=True,text=True,timeout=12)
    assert out.returncode==0,out.stderr
    contents=(tmp_path/'.env').read_text()
    assert 'TELEGRAM_BOT_TOKEN=123456:TEST_SECRET_TOKEN' in contents
    assert 'TELEGRAM_CHAT_ID=887766' in contents
    assert 'TEST_SECRET_TOKEN' not in out.stdout


def test_hmac_canonical_explicit_boolean_conversion():
    ino=(ROOT/'firmware/ColdChain_ESP32/ColdChain_ESP32.ino').read_text()
    for field in ('door_open','mains_ok','compressor_on','discard_latch'):
        assert f'd["{field}"].as<bool>()' in ino
        assert f'bool(d["{field}"])' not in ino


def test_onsite_scripts_all_exist_and_named():
    for file in ('00_START_COLDCHAIN_WINDOWS.bat','PREPARE_LAPTOP_WINDOWS.bat',
                 'UPLOAD_ESP32_WINDOWS.bat','UPDATE_NETWORK_WINDOWS.bat',
                 'PRE_HACKATHON_CHECK_WINDOWS.bat','MQTT_SMOKE_TEST_WINDOWS.bat'):
        assert (ROOT/file).is_file(),file
