"""Passwords are bcrypt only. Prefer pip bcrypt; Linux libxcrypt fallback permits offline evaluation."""
import base64, ctypes, ctypes.util, hashlib, hmac, json, secrets, threading, time
from typing import Any
try:
    import bcrypt as _bcrypt
except ImportError:
    _bcrypt = None
_crypt_lock=threading.Lock()
_crypt=None
if _bcrypt is None:
    try:
        _crypt=ctypes.CDLL(ctypes.util.find_library('crypt') or 'libcrypt.so.1')
        _crypt.crypt.restype=ctypes.c_char_p
        _crypt.crypt.argtypes=[ctypes.c_char_p,ctypes.c_char_p]
    except (OSError, AttributeError):
        _crypt=None

def hash_password(p: str) -> str:
    if len(p)<8: raise ValueError('Minimum password length is 8')
    if _bcrypt:
        return _bcrypt.hashpw(p.encode(),_bcrypt.gensalt(rounds=12)).decode()
    if _crypt:
        alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789./'
        salt='$2b$12$'+''.join(secrets.choice(alphabet) for _ in range(22))
        with _crypt_lock:
            return _crypt.crypt(p.encode(),salt.encode()).decode()
    raise RuntimeError('bcrypt not installed; run pip install -r requirements.txt')

def check_password(p: str, encoded: str) -> bool:
    if _bcrypt:
        try: return _bcrypt.checkpw(p.encode(), encoded.encode())
        except (ValueError, TypeError): return False
    if _crypt:
        with _crypt_lock:
            check=_crypt.crypt(p.encode(),encoded.encode())
        return bool(check) and hmac.compare_digest(check.decode(),encoded)
    raise RuntimeError('bcrypt not installed')

# Deterministic integer temperature prevents JSON float canonicalization mismatch across devices.
CANON_KEYS=('device_id','seq','observed_at','temp_c_100','door_open','mains_ok','compressor_on','battery_pct','sent_at','nonce')
def canonical(message:dict[str,Any])->bytes:
    return '|'.join(str(int(message[k])) if isinstance(message[k],bool) else str(message[k]) for k in CANON_KEYS).encode()
def signature(secret:str, message:dict)->str:
    return hmac.new(secret.encode(),canonical(message),hashlib.sha256).hexdigest()
def verify_signature(secret:str, message:dict)->bool:
    sig=message.get('signature','')
    return isinstance(sig,str) and hmac.compare_digest(signature(secret,message),sig)
def audit_hash(prev:str, timestamp:str, actor:str, action:str, data_json:str)->str:
    return hashlib.sha256(f'{prev}|{timestamp}|{actor}|{action}|{data_json}'.encode()).hexdigest()
