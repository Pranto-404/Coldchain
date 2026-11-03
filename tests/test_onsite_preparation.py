"""Offline-only QA for two device profiles and private-config safety."""
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def test_prepare_creates_consistent_unique_profiles(tmp_path):
    shutil.copytree(ROOT/'firmware'/'ColdChain_ESP32',tmp_path/'firmware'/'ColdChain_ESP32')
    shutil.copy(ROOT/'PREPARE_HARDWARE.py',tmp_path/'PREPARE_HARDWARE.py')
    shutil.copy(ROOT/'CHECK_HARDWARE_READY.py',tmp_path/'CHECK_HARDWARE_READY.py')
    cmd=[sys.executable,str(tmp_path/'PREPARE_HARDWARE.py'), '--ssid','TestHotspot',
         '--wifi-password','PrivateHotspotPassword123', '--host-ip','192.168.137.1']
    out=subprocess.run(cmd,capture_output=True,text=True)
    assert out.returncode==0,out.stderr+out.stdout
    assert (tmp_path/'.env').exists()
    a=(tmp_path/'firmware'/'ColdChain_A'/'secrets.h').read_text()
    b=(tmp_path/'firmware'/'ColdChain_B'/'secrets.h').read_text()
    assert '#define DEVICE_ID "FRIDGE_A"' in a
    assert '#define DEVICE_ID "FRIDGE_B"' in b
    assert '192.168.137.1' in a and '192.168.137.1' in b
    keya=re.search(r'#define DEVICE_SECRET "([^"]+)"',a).group(1)
    keyb=re.search(r'#define DEVICE_SECRET "([^"]+)"',b).group(1)
    assert len(keya)>=32 and len(keyb)>=32 and keya!=keyb
    assert (tmp_path/'firmware'/'ColdChain_A'/'ColdChain_A.ino').exists()
    assert (tmp_path/'firmware'/'ColdChain_B'/'ColdChain_B.ino').exists()
    verify=subprocess.run([sys.executable,str(tmp_path/'CHECK_HARDWARE_READY.py')],capture_output=True,text=True)
    assert verify.returncode==0,verify.stdout
    # Setup twice should not rotate secrets silently or overwrite private accounts.
    second=subprocess.run(cmd,capture_output=True,text=True)
    assert second.returncode==2
    assert keya in (tmp_path/'firmware'/'ColdChain_A'/'secrets.h').read_text()


def test_invalid_host_does_not_write_private_files(tmp_path):
    shutil.copytree(ROOT/'firmware'/'ColdChain_ESP32',tmp_path/'firmware'/'ColdChain_ESP32')
    shutil.copy(ROOT/'PREPARE_HARDWARE.py',tmp_path/'PREPARE_HARDWARE.py')
    out=subprocess.run([sys.executable,str(tmp_path/'PREPARE_HARDWARE.py'),
                        '--ssid','TestWiFi','--wifi-password','TestingPassWord',
                        '--host-ip','127.0.0.1'],capture_output=True,text=True)
    assert out.returncode!=0
    assert not (tmp_path/'.env').exists()


def test_wrong_board_secret_detected(tmp_path):
    shutil.copytree(ROOT/'firmware'/'ColdChain_ESP32',tmp_path/'firmware'/'ColdChain_ESP32')
    shutil.copy(ROOT/'PREPARE_HARDWARE.py',tmp_path/'PREPARE_HARDWARE.py')
    shutil.copy(ROOT/'CHECK_HARDWARE_READY.py',tmp_path/'CHECK_HARDWARE_READY.py')
    cmd=[sys.executable,str(tmp_path/'PREPARE_HARDWARE.py'), '--ssid','TestWiFi',
         '--wifi-password','TestingPassWord', '--host-ip','192.168.0.5']
    assert subprocess.run(cmd,capture_output=True).returncode==0
    p=tmp_path/'firmware'/'ColdChain_B'/'secrets.h'
    p.write_text(p.read_text().replace('FRIDGE_B','FRIDGE_A'))
    check=subprocess.run([sys.executable,str(tmp_path/'CHECK_HARDWARE_READY.py')],capture_output=True,text=True)
    assert check.returncode!=0
    assert 'Board B ID incorrect' in check.stdout
