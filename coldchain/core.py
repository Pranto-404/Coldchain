import os,time,uuid,datetime,sqlite3,json
from fastapi import HTTPException
from .db import connect,transaction,now,append_audit,iso_epoch
from .security import verify_signature
from .alerts import send_alert
from .ml import predict,compressor_health

def secret_for(device): return os.getenv(f'DEVICE_{device}_SECRET', f'SimulatedOnly_{device}_Key2026')
def batch_status(r):
    if r['discard_latched'] or float(r['exposure_seconds']) >= 3600: return 'Discard'
    return 'At Risk' if (3600-float(r['exposure_seconds']))/3600 < 0.2 else 'Safe'
def batch_view(row):
    v=dict(row); v['status']=batch_status(row); v['remaining_seconds']=max(0,round(3600-float(row['exposure_seconds']),1))
    v['remaining_pct']=round(100*v['remaining_seconds']/3600,1)
    v['expired']=row['expires']<datetime.date.today().isoformat()
    return v

def invalid(device,reason):
    with transaction() as c:
        c.execute('INSERT INTO invalid_messages(at,device_id,reason) VALUES(?,?,?)',(now(),str(device)[:60],reason))
        append_audit(c,'security','telemetry_rejected',{'device':str(device)[:60],'reason':reason})

def ingest(message,source='device'):
    if not isinstance(message,dict): raise ValueError('Invalid payload')
    device=str(message.get('device_id',''))
    if device not in ('FRIDGE_A','FRIDGE_B'):
        invalid(device,'unknown_device'); raise ValueError('Unknown device')
    required=('seq','observed_at','temp_c_100','door_open','mains_ok','compressor_on','battery_pct','sent_at','nonce','signature')
    if any(k not in message for k in required):
        invalid(device,'missing_fields'); raise ValueError('Missing fields')
    try:
        seq=int(message['seq']); observed=int(message['observed_at']); sent=int(message['sent_at']); temp100=int(message['temp_c_100']); bat=int(message['battery_pct'])
        for field in ('door_open','mains_ok','compressor_on'):
            if not isinstance(message[field],bool): raise ValueError('Bool field')
        if not(0<=seq<=2147483647 and -4000<=temp100<=6500 and 0<=bat<=100 and len(str(message['nonce']))>=12): raise ValueError('Bounds')
        if abs(time.time()-sent)>120 or observed>sent+120 or observed<sent-86400: raise ValueError('Timestamp window')
    except (TypeError,ValueError) as e:
        invalid(device,'invalid_field_or_time'); raise ValueError('Malformed or outdated telemetry') from e
    if not verify_signature(secret_for(device),message):
        invalid(device,'invalid_hmac'); raise ValueError('Invalid HMAC')
    observed_iso=datetime.datetime.fromtimestamp(observed,datetime.timezone.utc).replace(microsecond=0).isoformat()
    with transaction() as c:
        if c.execute('SELECT 1 FROM nonces WHERE fridge_id=? AND nonce=?',(device,message['nonce'])).fetchone():
            c.execute('INSERT INTO invalid_messages(at,device_id,reason) VALUES(?,?,?)',(now(),device,'replayed_nonce'))
            append_audit(c,'security','telemetry_rejected',{'device':device,'reason':'replayed_nonce'})
            return {'accepted':False,'reason':'replayed_nonce'}
        c.execute('INSERT INTO nonces(fridge_id,nonce,sent_at) VALUES(?,?,?)',(device,str(message['nonce']),sent))
        c.execute('DELETE FROM nonces WHERE sent_at < ?',(int(time.time())-86400,))
        duplicate=c.execute('SELECT * FROM readings WHERE fridge_id=? AND seq=?',(device,seq)).fetchone()
        if duplicate:
            identical=(int(round(duplicate['temp_c']*100))==temp100 and
                       duplicate['observed_at']==observed_iso and
                       int(duplicate['door_open'])==int(message['door_open']) and
                       int(duplicate['mains_ok'])==int(message['mains_ok']) and
                       int(duplicate['compressor_on'])==int(message['compressor_on']) and
                       int(duplicate['battery_pct'])==bat)
            if identical:return {'accepted':True,'duplicate':True,'seq':seq}
            c.execute('INSERT INTO invalid_messages(at,device_id,reason) VALUES(?,?,?)',(now(),device,'sequence_payload_conflict'))
            append_audit(c,'security','telemetry_rejected',{'device':device,'reason':'sequence_payload_conflict','seq':seq})
            return {'accepted':False,'reason':'sequence_payload_conflict'}
        last=c.execute('SELECT * FROM readings WHERE fridge_id=? ORDER BY seq DESC LIMIT 1',(device,)).fetchone()
        if last and seq<=last['seq']:
            c.execute('INSERT INTO invalid_messages(at,device_id,reason) VALUES(?,?,?)',(now(),device,'out_of_order_sequence'))
            append_audit(c,'security','telemetry_rejected',{'device':device,'reason':'out_of_order_sequence','seq':seq})
            return {'accepted':False,'reason':'out_of_order_sequence'}
        # A clear data gap is not assigned a fabricated heat dose.
        if last:
            dt=observed-iso_epoch(last['observed_at'])
            if dt<0:
                append_audit(c,'security','nonmonotonic_observation',{'device':device,'seq':seq})
                return {'accepted':False,'reason':'nonmonotonic_observation'}
            if 0<dt<=90 and float(last['temp_c'])>8:
                units=dt*(2 if float(last['temp_c'])>12 else 1)
                for b in c.execute('SELECT * FROM batches WHERE fridge_id=? AND discard_latched=0',(device,)).fetchall():
                    old=batch_status(b); new_exposure=min(3600,float(b['exposure_seconds'])+units)
                    latched=int(new_exposure>=3600)
                    c.execute('UPDATE batches SET exposure_seconds=?,discard_latched=? WHERE id=?',(new_exposure,latched,b['id']))
                    after='Discard' if latched else ('At Risk' if (3600-new_exposure)/3600<0.2 else 'Safe')
                    if old!=after: append_audit(c,'system','batch_status_change',{'batch_id':b['id'],'lot':b['lot'],'from':old,'to':after,'exposure_s':round(new_exposure)})
            elif dt>90:
                append_audit(c,'system','telemetry_gap',{'fridge':device,'seconds':dt})
        c.execute('INSERT INTO readings(fridge_id,seq,observed_at,temp_c,door_open,mains_ok,compressor_on,battery_pct,source) VALUES(?,?,?,?,?,?,?,?,?)',
                  (device,seq,observed_iso,temp100/100,int(message['door_open']),int(message['mains_ok']),int(message['compressor_on']),bat,source))
        f=c.execute('SELECT * FROM fridges WHERE id=?',(device,)).fetchone()
        door_since=f['door_open_since'] if message['door_open'] else None
        alerted=f['door_alerted'] if message['door_open'] else 0
        if message['door_open'] and not f['door_open']: door_since=observed_iso; alerted=0
        if message['door_open'] and door_since and not alerted and observed-iso_epoch(door_since)>60:
            status=send_alert(c,device,f'ColdChain: {device} door open over 60 seconds at {observed_iso}. Check vaccine safety.')
            alerted=1
            append_audit(c,'system','door_alert',{'fridge':device,'delivery':status})
        c.execute('UPDATE fridges SET last_seen=?,temp_c=?,door_open=?,mains_ok=?,compressor_on=?,battery_pct=?,door_open_since=?,door_alerted=?,last_seq=?,simulated=? WHERE id=?',
                  (observed_iso,temp100/100,int(message['door_open']),int(message['mains_ok']),int(message['compressor_on']),bat,door_since,alerted,seq,int(source=='simulator'),device))
        # Record all accepted samples in a verifiable chain; auditors can detect edited temperature records.
        append_audit(c,device,'reading',{'device':device,'seq':seq,'observed_at':observed_iso,'temp_c_100':temp100,'door_open':message['door_open'],'mains_ok':message['mains_ok'],'compressor_on':message['compressor_on'],'battery_pct':bat})
        return {'accepted':True,'duplicate':False,'seq':seq}
class ReplayDetected(ValueError): pass

def verified_integrity():
    from .security import audit_hash
    c=connect(); rows=c.execute('SELECT * FROM audit ORDER BY id').fetchall()
    expected='GENESIS'
    for r in rows:
        if r['prev_hash']!=expected or audit_hash(expected,r['at'],r['actor'],r['action'],r['details'])!=r['digest']:
            c.close(); return {'valid':False,'checked':r['id'],'first_broken_id':r['id'],'reason':'hash_chain_mismatch'}
        if r['action']=='reading':
            d=json.loads(r['details'])
            measured=c.execute('SELECT * FROM readings WHERE fridge_id=? AND seq=?',(d['device'],d['seq'])).fetchone()
            if not measured or (measured['observed_at']!=d['observed_at'] or
                int(round(measured['temp_c']*100))!=d['temp_c_100'] or
                int(measured['door_open'])!=int(d['door_open']) or
                int(measured['mains_ok'])!=int(d['mains_ok']) or
                int(measured['compressor_on'])!=int(d['compressor_on']) or
                int(measured['battery_pct'])!=int(d['battery_pct'])):
                c.close();return {'valid':False,'checked':r['id'],'first_broken_id':r['id'],'reason':'reading_record_differs_from_audit'}
        expected=r['digest']
    c.close()
    return {'valid':True,'checked':len(rows),'latest_hash':expected}

def health_reference():
    """Optional expected healthy cooling rate (C/min). The simulator's accelerated physics uses ~0.9."""
    raw=os.getenv('COMPRESSOR_REF_C_PER_MIN','')
    try:return float(raw) if raw else (1.0 if os.getenv('DEMO_MODE')=='1' else None)
    except ValueError:return None

def predictions_for_all(c):
    result={}
    for f in c.execute('SELECT * FROM fridges ORDER BY id'):
        rows=c.execute('SELECT * FROM readings WHERE fridge_id=? ORDER BY seq DESC LIMIT 720',(f['id'],)).fetchall()
        forecast=predict(rows[:61]); health=compressor_health(rows,health_reference())
        result[f['id']]={'forecast':forecast,'health':health}
    return result

def fridge_is_fresh(f,max_age=60):
    return bool(f['last_seen']) and time.time()-iso_epoch(f['last_seen'])<=max_age

def risk_reason(f,forecast):
    if f['temp_c']>8:return f"Currently {f['temp_c']:.1f}°C (above 8°C)"
    if f['temp_c']<2:return f"Currently {f['temp_c']:.1f}°C (below 2°C, freezing risk)"
    if not f['mains_ok']:return 'Mains power lost; running on battery with no cooling'
    if forecast.get('warning'):return f"AI forecast {forecast['predicted_c']:.1f}°C in 30 minutes"
    return 'Unsafe conditions'

def relocation_suggestions(c,all_predict=None):
    if all_predict is None: all_predict=predictions_for_all(c)
    fridges=[dict(x) for x in c.execute('SELECT * FROM fridges ORDER BY id')]
    moves=[]
    for f in fridges:
        if f['temp_c'] is None:continue
        predicted=all_predict[f['id']]['forecast']
        if 2<=f['temp_c']<=8 and f['mains_ok'] and not predicted['warning']: continue
        alternatives=[x for x in fridges if x['id']!=f['id'] and x['temp_c'] is not None and fridge_is_fresh(x,30) and 2.5<=x['temp_c']<=6.5 and x['mains_ok'] and not x['door_open'] and not all_predict[x['id']]['forecast']['warning']]
        if not alternatives:continue
        # Prefer the destination with the most headroom below 8 C over the next 30 minutes.
        target=min(alternatives,key=lambda x:all_predict[x['id']]['forecast'].get('predicted_c') or x['temp_c'])
        reason=risk_reason(f,predicted)
        batches=[batch_view(x) for x in c.execute('SELECT * FROM batches WHERE fridge_id=?',(f['id'],))]
        # Least remaining heat budget first: those batches lose the most from further exposure.
        for b in sorted(batches,key=lambda b:(b['remaining_pct'],b['expires'])):
            if b['status']=='Discard' or b['expired']:continue
            moves.append({'batch_id':b['id'],'lot':b['lot'],'name':b['name'],'from_fridge':f['id'],'to_fridge':target['id'],
                          'reason':reason,'priority':'high' if b['status']=='At Risk' or f['temp_c']>8 else 'normal',
                          'target_temp_c':target['temp_c'],'target_forecast_c':all_predict[target['id']]['forecast'].get('predicted_c'),
                          'remaining_pct':b['remaining_pct']})
    return moves
