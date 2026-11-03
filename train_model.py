"""Reproducible SYNTHETIC model training/evaluation; results are not clinical or hardware validation."""
import json,random,math
from pathlib import Path
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import mean_absolute_error,mean_squared_error,precision_score,recall_score,f1_score,confusion_matrix
import joblib
from coldchain.ml import BASE,MODEL,FEATURES
SEED=20261021

def simulate(seed,length=145):
    rng=np.random.default_rng(seed)
    t=float(rng.uniform(2.7,8.2)); ambient=float(rng.uniform(18,32)); insulation=rng.uniform(.006,.015)
    compressor=False;last_off=-20; power=True;door=False
    # Each trajectory has independent randomly scheduled disturbances and hardware strength.
    weakness=float(rng.choice([1.0,1.0,1.0,.82,.65,.40]))
    off_start=int(rng.integers(14,108));off_len=int(rng.integers(10,55))
    door_start=int(rng.integers(13,105));door_len=int(rng.integers(9,50))
    degradation_start=int(rng.integers(0,100));cooling=float(rng.uniform(.16,.36))
    series=[]
    for minute in range(length):
        power=not(off_start<=minute<off_start+off_len and seed%3!=0)
        door=(door_start<=minute<door_start+door_len and seed%4!=0)
        weak=weakness if minute>=degradation_start else 1.
        if not power:compressor=False;last_off=minute
        elif t<=3 and compressor:compressor=False;last_off=minute
        elif t>=7 and not compressor and minute-last_off>=1:compressor=True
        rate=insulation*(ambient-t)+(0.125 if door else 0.)-(cooling*weak if compressor and power else 0.)
        t=float(np.clip(t+rate+rng.normal(0,.032),1,35))
        series.append({'temp_c':t,'door_open':int(door),'mains_ok':int(power),'compressor_on':int(compressor)})
    return series

def row_features(window):
    v=np.array([r['temp_c'] for r in window]);first=v[0];last=v[-1]
    return [float(last),float(np.clip((last-first)/max(len(window)-1,1),-1.5,1.5)),float(v.mean()),float(v.std()),int(window[-1]['door_open']),int(window[-1]['mains_ok']),int(window[-1]['compressor_on']),float(np.mean([x['compressor_on'] for x in window]))]

def main():
    X=[];y=[];groups=[]
    for trajectory in range(220):
        seq=simulate(seed=SEED+trajectory)
        for i in range(6,len(seq)-30,2):
            X.append(row_features(seq[i-5:i+1]));y.append(seq[i+30]['temp_c']);groups.append(trajectory)
    X=np.asarray(X);y=np.asarray(y);groups=np.asarray(groups)
    tr,te=next(GroupShuffleSplit(n_splits=1,test_size=.22,random_state=SEED).split(X,y,groups))
    reg=RandomForestRegressor(n_estimators=30,max_depth=10,min_samples_leaf=10,n_jobs=-1,random_state=SEED)
    reg.fit(X[tr],y[tr]);pred=reg.predict(X[te]);actual_breach=y[te]>8;pred_breach=pred>8
    metrics={
      'data_provenance':'SYNTHETIC PHYSICS SIMULATION ONLY; NOT CLINICALLY VALIDATED',
      'seed':SEED,'trajectories':220,'distinct_train_trajectories':int(len(np.unique(groups[tr]))),
      'distinct_test_trajectories':int(len(np.unique(groups[te]))),
      'train_rows':int(len(tr)),'test_rows':int(len(te)),
      'features':FEATURES,'horizon_minutes':30,
      'mean_absolute_error_c':round(float(mean_absolute_error(y[te],pred)),3),
      'root_mean_squared_error_c':round(float(np.sqrt(mean_squared_error(y[te],pred))),3),
      'breach_precision':round(float(precision_score(actual_breach,pred_breach,zero_division=0)),3),
      'breach_recall':round(float(recall_score(actual_breach,pred_breach,zero_division=0)),3),
      'breach_f1':round(float(f1_score(actual_breach,pred_breach,zero_division=0)),3),
      'breach_confusion_matrix_tn_fp_fn_tp':confusion_matrix(actual_breach,pred_breach,labels=[False,True]).ravel().astype(int).tolist(),
      'feature_importances':{f:round(float(w),4) for f,w in zip(FEATURES,reg.feature_importances_)},
      'limitations':['Synthetic-only data distribution','No external or site-specific temperature calibration','No independent real-fridge holdout','Sensor noise/device latency may differ in field','Thirty-minute forecasting may be unreliable outside training envelope']
    }
    MODEL.parent.mkdir(parents=True,exist_ok=True);joblib.dump(reg,MODEL,compress=3)
    out=BASE/'report';out.mkdir(exist_ok=True)
    (out/'model_metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
    fig,ax=plt.subplots(figsize=(7.3,4.7));ax.scatter(y[te][::6],pred[::6],alpha=.26,s=10,c='#159988')
    ax.plot([0,35],[0,35],'--',c='#cf6670',linewidth=1.5,label='Ideal forecast')
    ax.axhline(8,ls=':',c='#df9d49',linewidth=1);ax.axvline(8,ls=':',c='#df9d49',linewidth=1)
    ax.set(xlabel='Actual temperature after 30 minutes (°C)',ylabel='Predicted temperature (°C)',title='ColdChain 30-minute forecast — synthetic holdout',xlim=(0,35),ylim=(0,35));ax.grid(alpha=.12);ax.legend(loc='upper left')
    fig.tight_layout();fig.savefig(out/'forecast_validation.png',dpi=180);plt.close(fig)
    print(json.dumps(metrics,indent=2))
    return metrics
if __name__=='__main__': main()
