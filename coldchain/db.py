import os,sqlite3,uuid,json,datetime
from contextlib import contextmanager
from .security import hash_password,audit_hash

def now(): return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
def iso_epoch(s:str)->int: return int(datetime.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp())
def connect():
    db=sqlite3.connect(os.getenv('DB_PATH','./coldchain.db'),timeout=15,check_same_thread=False)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA busy_timeout=15000')
    return db
@contextmanager
def transaction():
    con=connect()
    try:
        con.execute('BEGIN IMMEDIATE')
        yield con
        con.commit()
    except: con.rollback(); raise
    finally: con.close()

def append_audit(con, actor, action, data):
    data_json=json.dumps(data,sort_keys=True,separators=(',',':'),default=str)
    prev=con.execute('SELECT digest FROM audit ORDER BY id DESC LIMIT 1').fetchone()
    before=prev['digest'] if prev else 'GENESIS'
    at=now(); digest=audit_hash(before,at,actor,action,data_json)
    con.execute('INSERT INTO audit(at,actor,action,details,prev_hash,digest) VALUES(?,?,?,?,?,?)',(at,actor,action,data_json,before,digest))

def initialize():
    with transaction() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('Admin','Pharmacist','Inspector')),enabled INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS fridges(id TEXT PRIMARY KEY, label TEXT NOT NULL, last_seen TEXT, temp_c REAL, door_open INTEGER DEFAULT 0, mains_ok INTEGER DEFAULT 1, compressor_on INTEGER DEFAULT 0, battery_pct INTEGER DEFAULT 100, door_open_since TEXT, door_alerted INTEGER DEFAULT 0, last_seq INTEGER DEFAULT -1, simulated INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS readings(id INTEGER PRIMARY KEY, fridge_id TEXT NOT NULL REFERENCES fridges(id), seq INTEGER NOT NULL, observed_at TEXT NOT NULL, temp_c REAL NOT NULL, door_open INTEGER NOT NULL, mains_ok INTEGER NOT NULL, compressor_on INTEGER NOT NULL, battery_pct INTEGER NOT NULL, source TEXT NOT NULL, UNIQUE(fridge_id,seq));
        CREATE INDEX IF NOT EXISTS ix_readings_fridge_time ON readings(fridge_id,observed_at);
        CREATE TABLE IF NOT EXISTS nonces(fridge_id TEXT NOT NULL, nonce TEXT NOT NULL, sent_at INTEGER NOT NULL, PRIMARY KEY(fridge_id,nonce));
        CREATE TABLE IF NOT EXISTS invalid_messages(id INTEGER PRIMARY KEY, at TEXT NOT NULL, device_id TEXT, reason TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY, name TEXT NOT NULL, lot TEXT UNIQUE NOT NULL, expires TEXT NOT NULL, fridge_id TEXT NOT NULL REFERENCES fridges(id), public_token TEXT UNIQUE NOT NULL, exposure_seconds REAL NOT NULL DEFAULT 0, discard_latched INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, at TEXT NOT NULL, actor TEXT NOT NULL, action TEXT NOT NULL, details TEXT NOT NULL, prev_hash TEXT NOT NULL, digest TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS simulation_controls(fridge_id TEXT PRIMARY KEY REFERENCES fridges(id), door_open INTEGER DEFAULT 0, mains_ok INTEGER DEFAULT 1, degraded INTEGER DEFAULT 0, wifi_ok INTEGER DEFAULT 1, heat_spike INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS alert_outbox(id INTEGER PRIMARY KEY, at TEXT NOT NULL, fridge_id TEXT, channel TEXT NOT NULL, status TEXT NOT NULL, detail TEXT NOT NULL);
        ''')
        for fid,label in [('FRIDGE_A','Fridge Alpha'),('FRIDGE_B','Fridge Beta')]:
            c.execute('INSERT OR IGNORE INTO fridges(id,label) VALUES(?,?)',(fid,label))
            c.execute('INSERT OR IGNORE INTO simulation_controls(fridge_id) VALUES(?)',(fid,))
        for username,role,envname in [('admin','Admin','ADMIN_PASSWORD'),('pharmacist','Pharmacist','PHARMACIST_PASSWORD'),('inspector','Inspector','INSPECTOR_PASSWORD')]:
            if c.execute('SELECT 1 FROM users WHERE username=?',(username,)).fetchone(): continue
            pwd=os.getenv(envname,'')
            if not pwd or pwd.startswith('CHANGE_ME'):
                if os.getenv('DEMO_MODE','0')=='1': pwd=f'ColdChainDemo_{role}2026!'
                else: raise RuntimeError(f'Set a strong {envname} in .env')
            c.execute('INSERT INTO users(username,password_hash,role) VALUES(?,?,?)',(username,hash_password(pwd),role))
        # Demo batches are clearly simulation examples, never medical-record claims.
        if os.getenv('DEMO_MODE','0')=='1' and not c.execute('SELECT 1 FROM batches LIMIT 1').fetchone():
            for name,lot,fridge in [('Insulin Glargine','SIM-INS-001','FRIDGE_A'),('MMR Vaccine','SIM-MMR-002','FRIDGE_A'),('Hepatitis B Vaccine','SIM-HEP-003','FRIDGE_B')]:
                c.execute('INSERT INTO batches(id,name,lot,expires,fridge_id,public_token,created_at) VALUES(?,?,?,?,?,?,?)',(str(uuid.uuid4()),name,lot,'2027-12-31',fridge,uuid.uuid4().hex,now()))
        if not c.execute('SELECT 1 FROM audit LIMIT 1').fetchone():append_audit(c,'system','database_initialized',{'demo':os.getenv('DEMO_MODE','0')=='1'})
