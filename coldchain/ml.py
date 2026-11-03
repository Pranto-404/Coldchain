"""Trained RandomForest 30-min forecast on SYNTHETIC thermal scenarios; field validation required."""
from pathlib import Path
import os
import numpy as np
BASE=Path(__file__).resolve().parents[1]
MODEL=BASE/'models'/'forecast.joblib'
FEATURES=['temp_c','slope_c_per_min','mean_c','std_c','door_open','mains_ok','compressor_on','compressor_duty']
_cached=None

def feature_vector(rows):
    if not rows: return None
    seq=list(reversed(rows)) # incoming rows newest to oldest
    first=seq[0]; last=seq[-1]
    temps=np.array([float(x['temp_c']) for x in seq]);
    try:
        from .db import iso_epoch
        mins=max((iso_epoch(last['observed_at'])-iso_epoch(first['observed_at']))/60,1/12)
    except Exception: mins=max((len(seq)-1)/12,1/12)
    slope=float((temps[-1]-temps[0])/mins)
    return [float(last['temp_c']),float(np.clip(slope,-1.5,1.5)),float(temps.mean()),float(temps.std()),int(last['door_open']),int(last['mains_ok']),int(last['compressor_on']),float(np.mean([int(x['compressor_on']) for x in seq]))]

def predict(rows):
    global _cached
    fv=feature_vector(rows)
    if not fv:return {'predicted_c':None,'warning':False,'method':'insufficient data'}
    if _cached is None and MODEL.exists():
        try:
            import joblib
            _cached=joblib.load(MODEL)
        except Exception:pass
    if _cached is not None:
        predicted=float(_cached.predict([fv])[0]); method='RandomForest / synthetic-training'
    else:
        # Explicit non-ML fallback, not silently mislabeled as AI.
        temp,slope,_,_,door,power,compressor,duty=fv
        trend=np.clip(slope*12,-4,5)
        bias=(2.8 if not power else 0)+(1.8 if door else 0)-(1.0 if compressor and power else 0)
        predicted=temp+float(trend)+bias
        method='engineering fallback / untrained'
    predicted=float(np.clip(predicted,-5,35))
    temp,slope=fv[0],fv[1]
    # Linear time-to-breach estimate from the 5-minute trend, shown alongside the model output.
    eta=None
    if temp<=8 and slope>0.01: eta=round((8-temp)/slope,1)
    return {'predicted_c':round(predicted,2),'warning':predicted>8,'method':method,
            'current_c':round(temp,2),'slope_c_per_min':round(slope,3),
            'minutes_to_8c':eta if eta is not None and eta<=120 else None}

def compressor_runs(rows):
    """Split history into uninterrupted compressor-on runs (door closed, mains on).

    Each run's cooling rate is (start temp - end temp) / duration, which is robust to the
    0.0625 C quantization of a DS18B20 that makes per-sample deltas very noisy."""
    from .db import iso_epoch
    seq=list(reversed(rows))
    runs=[];cur=[]
    for r in seq:
        ok=r['compressor_on'] and r['mains_ok'] and not r['door_open']
        if ok and cur and iso_epoch(r['observed_at'])-iso_epoch(cur[-1]['observed_at'])>30:
            runs.append(cur);cur=[]
        if ok:cur.append(r)
        elif cur:runs.append(cur);cur=[]
    if cur:runs.append(cur)
    out=[]
    for run in runs:
        minutes=(iso_epoch(run[-1]['observed_at'])-iso_epoch(run[0]['observed_at']))/60
        if minutes>=1:
            out.append({'start':run[0]['observed_at'],'minutes':round(minutes,2),
                        'rate_c_per_min':round((float(run[0]['temp_c'])-float(run[-1]['temp_c']))/minutes,3)})
    return out

def compressor_health(rows,reference=None):
    """0-100 score: latest cooling-run rate compared with this fridge's best recent run
    (or a configured reference rate). A weakening compressor cools more slowly."""
    runs=compressor_runs(rows)
    if not runs:return {'score':None,'note':'Waiting for a compressor run of at least 1 minute','runs':0}
    recent=runs[-1]['rate_c_per_min']
    learned=float(np.percentile([r['rate_c_per_min'] for r in runs],90)) if len(runs)>=3 else max(r['rate_c_per_min'] for r in runs)
    baseline=max(learned,reference or 0)
    if baseline<=0:return {'score':0,'note':'Compressor running but temperature is not falling','runs':len(runs),'recent_rate':recent}
    score=int(np.clip(round(100*recent/baseline),0,100))
    trend='weakening' if score<70 else 'normal'
    return {'score':score,'trend':trend,'runs':len(runs),'recent_rate':recent,'baseline_rate':round(baseline,3),
            'note':f'Latest run cools {recent:.2f} C/min vs baseline {baseline:.2f} C/min over {len(runs)} runs'}
