"""Clearly labeled synthetic twin. DOES NOT assert hardware has been tested."""
import time,datetime,secrets,threading,os,math
from .db import connect
from .security import signature
from .core import ingest,secret_for

TICK_S=5
# Physics in degrees C per 5-second tick, kept inside the envelope the forecast model was trained on
# (idle warming ~0.15 C/min) so normal thermostat cycling is not mistaken for a fault.
LEAK=0.012         # ambient heat gain, ~0.14 C/min
DOOR=0.06          # extra gain while the door is open, ~0.7 C/min
SPIKE=0.05         # artificial thermal load, ~0.6 C/min
COOL=0.11          # healthy compressor, ~1.2 C/min net cooling
COOL_DEGRADED=0.04 # weak compressor, ~0.34 C/min net cooling
MIN_OFF_S=60

class Simulator:
    def __init__(self):
        self.stop_event=threading.Event();self.thread=None;self.lock=threading.RLock()
        self.states={'FRIDGE_A':{'temp':4.75,'compressor':False,'last_off':time.monotonic()-120,'battery':100,'queue':[]},'FRIDGE_B':{'temp':4.15,'compressor':False,'last_off':time.monotonic()-120,'battery':100,'queue':[]}}
    def start(self):
        self.seed_synthetic_baseline()
        self.thread=threading.Thread(target=self.run,name='coldchain-simulator',daemon=True);self.thread.start()
    def stop(self):
        self.stop_event.set()
        if self.thread:self.thread.join(timeout=3)
    def run(self):
        while not self.stop_event.is_set():
            try:self.tick()
            except Exception as e:print('Simulator tick error:',repr(e))
            self.stop_event.wait(TICK_S)
    def tick(self):
        with self.lock:
            return self._tick()

    def runtime(self,fid):
        s=self.states.get(fid)
        if not s:return {}
        off_for=time.monotonic()-s['last_off']
        return {'sim_temp':round(s['temp'],2),'sim_compressor':bool(s['compressor']),'buffered':len(s['queue']),
                'battery':int(s['battery']),'min_off_remaining':0 if s['compressor'] else max(0,int(MIN_OFF_S-off_for))}

    @staticmethod
    def physics(temp,compressor,off_for,mains,door,degraded,spike):
        """One 5 s step of the same thermostat the ESP32 runs: ON at 7 C, OFF at 3 C, 60 s minimum off."""
        turned_off=False
        if not mains:
            turned_off=compressor;compressor=False
        elif temp<=3.0 and compressor:
            compressor=False;turned_off=True
        elif temp>=7.0 and not compressor and off_for>=MIN_OFF_S:
            compressor=True
        change=LEAK+(DOOR if door else 0)+(SPIKE if spike else 0)
        if compressor and mains:change-=COOL_DEGRADED if degraded else COOL
        return max(1.2,min(24.5,temp+change)),compressor,turned_off

    def seed_synthetic_baseline(self,minutes=30):
        """Seed explicitly synthetic history so charts, forecast and compressor health are visible immediately.

        Only seeds a fridge with zero readings; never changes existing historical records.
        All rows pass the regular signed ingest path, and are labeled as simulator samples.
        """
        from .db import transaction,append_audit
        with self.lock:
            c=connect()
            empty=[fid for fid in self.states if not c.execute('SELECT 1 FROM readings WHERE fridge_id=? LIMIT 1',(fid,)).fetchone()]
            c.close()
            if not empty:return
            now_epoch=int(time.time());steps=minutes*60//TICK_S
            for fid in empty:
                s=self.states[fid]
                # Start near the 7 C cut-in so the seeded half hour contains a full cooling run.
                temp=6.2 if fid=='FRIDGE_A' else 5.6;compressor=False;off_for=MIN_OFF_S
                for idx in range(steps):
                    temp,compressor,turned_off=self.physics(temp,compressor,off_for,True,False,False,False)
                    off_for=0 if turned_off else off_for+TICK_S
                    record={'device_id':fid,'seq':idx,'observed_at':now_epoch-(steps-idx)*TICK_S,
                        'temp_c_100':round(temp*100),'door_open':False,'mains_ok':True,
                        'compressor_on':compressor,'battery_pct':100,
                        'sent_at':now_epoch,'nonce':secrets.token_hex(12)}
                    record['signature']=signature(secret_for(fid),record)
                    ingest(record,'simulator')
                s['temp']=temp;s['compressor']=compressor;s['last_off']=time.monotonic()-off_for
            with transaction() as c:
                append_audit(c,'simulator','synthetic_baseline_seeded',{
                    'demo_only':True,'fridges':empty,'samples_per_fridge':steps,
                    'note':'Synthetic startup history, not collected from real sensors.'})

    def stage_rising_risk(self):
        """Place synthetic twins in a forecast-risk scenario without forging historical samples."""
        from .db import transaction,append_audit
        with self.lock:
            with transaction() as c:
                c.execute('UPDATE simulation_controls SET door_open=0,mains_ok=1,degraded=1,wifi_ok=1,heat_spike=1 WHERE fridge_id=?',('FRIDGE_A',))
                c.execute('UPDATE simulation_controls SET door_open=0,mains_ok=1,degraded=0,wifi_ok=1,heat_spike=0 WHERE fridge_id=?',('FRIDGE_B',))
                append_audit(c,'simulator','round1_rising_risk_staged',{
                    'demo_only':True,'fridge':'FRIDGE_A',
                    'note':'Synthetic simulator initial state. Forecast computed from model, not a verified physical reading.'})
            self.states['FRIDGE_A']['temp']=max(self.states['FRIDGE_A']['temp'],6.6)
            self.states['FRIDGE_A']['queue']=[]
            self.states['FRIDGE_B']['temp']=min(self.states['FRIDGE_B']['temp'],4.6)
            self.states['FRIDGE_B']['queue']=[]
            self._tick()

    def start_cooling_run(self,fid):
        """Bring a twin to the 7 C cut-in so a weakened compressor is measurable straight away."""
        with self.lock:
            s=self.states[fid]
            if not s['compressor']:s['temp']=max(s['temp'],7.0);s['last_off']=min(s['last_off'],time.monotonic()-MIN_OFF_S)

    def reset(self):
        """Return both twins to normal operation."""
        from .db import transaction,append_audit
        with self.lock:
            with transaction() as c:
                c.execute('UPDATE simulation_controls SET door_open=0,mains_ok=1,degraded=0,wifi_ok=1,heat_spike=0')
                append_audit(c,'simulator','simulation_reset',{'demo_only':True})
            for s in self.states.values():
                s['temp']=min(s['temp'],6.0);s['battery']=max(s['battery'],100)

    def publish_now(self):
        """Send a sample immediately with the new switch states, as the ESP32 does on a door change."""
        with self.lock:
            return self._tick(advance=False)

    def _tick(self,advance=True):
        c=connect();controls={x['fridge_id']:dict(x) for x in c.execute('SELECT * FROM simulation_controls')};records={x['id']:dict(x) for x in c.execute('SELECT id,last_seq FROM fridges')};c.close()
        for fid,s in self.states.items():
            p=controls[fid];mains=bool(p['mains_ok']);door=bool(p['door_open']);degraded=bool(p['degraded'])
            off_for=time.monotonic()-s['last_off']
            if advance:
                s['temp'],s['compressor'],turned_off=self.physics(s['temp'],s['compressor'],off_for,mains,door,degraded,bool(p['heat_spike']))
                if turned_off:s['last_off']=time.monotonic()
                s['battery']=min(100,max(0,s['battery']-(1 if not mains else -1)))
            elif not mains and s['compressor']:
                s['compressor']=False;s['last_off']=time.monotonic()  # relay drops the instant mains fails
            seq=max(records[fid]['last_seq'],max([x['seq'] for x in s['queue']],default=-1))+1
            observed=int(time.time())
            sample={'device_id':fid,'seq':seq,'observed_at':observed,'temp_c_100':round(s['temp']*100),'door_open':door,'mains_ok':mains,'compressor_on':bool(s['compressor']),'battery_pct':int(s['battery'])}
            if not p['wifi_ok']:
                s['queue'].append(sample)
                if len(s['queue'])>720:s['queue'].pop(0) # demo-only in-memory 60min (5s samples)
                continue
            pending=s['queue']+[sample];s['queue']=[]
            for index,record in enumerate(pending):
                record['sent_at']=int(time.time());record['nonce']=secrets.token_hex(12)
                record['signature']=signature(secret_for(fid),record)
                try:result=ingest(record,'simulator')
                except Exception:
                    s['queue']=pending[index:];break
                if not result.get('accepted'):
                    s['queue']=pending[index:];break
