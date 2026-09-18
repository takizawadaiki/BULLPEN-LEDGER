"""Post-hoc checks of frozen models, plus prior-date workload histories. No refitting."""
import argparse,json,zipfile
from pathlib import Path
import pandas as pd,numpy as np
p=Path(__file__).resolve().parent;ap=argparse.ArgumentParser();ap.add_argument('--raw',type=Path,required=True);raw=ap.parse_args().raw
s=json.loads((p/'data/summary.json').read_text());m=pd.read_csv(p/'data/modeling-appearances.csv');q=m[m.year==2025].copy();train=m[m.year<2025]
for name,model in s['models'].items():
 pred=np.full(len(q),model['intercept'])
 for col,coef in model['coefficients'].items():pred+=q[col].to_numpy()*coef
 q[name]=pred
 q['e_'+name]=(q.y-pred)**2
q['naive']=np.average(train.y,weights=train.p_bfp);q['e_naive']=(q.y-q.naive)**2
rng=np.random.default_rng(1729)
def metric(a,label,definition,weight='p_bfp'):
 a=a.copy();a['w']=a[weight] if weight!='equal' else 1.
 for name in ['context','workload']:a['loss_'+name]=a['e_'+name]*a.w
 clusters=a.groupby('id')[['loss_context','loss_workload','w']].sum().to_numpy();boots=[]
 for _ in range(1000):
  z=clusters[rng.integers(0,len(clusters),len(clusters))].sum(axis=0);boots.append(100*(np.sqrt(z[1]/z[2])-np.sqrt(z[0]/z[2])))
 r={name:float(np.sqrt(np.average(a['e_'+name],weights=a.w))*100) for name in ['context','workload','naive']}
 return {'label':label,'definition':definition,'n':len(a),'pitchers':a.id.nunique(),'bf':int(a.p_bfp.sum()),**r,'delta':r['workload']-r['context'],'lo':float(np.quantile(boots,.025)),'hi':float(np.quantile(boots,.975)),'weight':weight}
checks=[metric(q,'All eligible appearances','Original evaluation cohort.'),metric(q[(q.entry>=7)&(q.margin.abs()<=3)],'Late & close','Entry inning 7+; score margin within 3. A transparent context filter, not a formal leverage index.'),metric(q[q.rest<=6],'No long MLB gaps','0–6 full days since the previous recorded MLB pitching date.'),metric(q[q.p_bfp<=6],'Short outings','At most 6 BF in the completed appearance. Outcome-conditioned descriptive subset; not a pre-entry rule.'),metric(q,'Equal appearance weight','Each appearance receives equal weight in evaluation; model fitting remains unchanged.',weight='equal')]
# Preserve the originally reported primary interval; do not replace it with bootstrap noise.
checks[0]['lo']=s['rmseDeltaCI'][0]*100;checks[0]['hi']=s['rmseDeltaCI'][1]*100
monthly=[]
q['period']=np.where(q.month<=4,'Mar–Apr',q.month.map({5:'May',6:'Jun',7:'Jul',8:'Aug',9:'Sep'}))
for label in ['Mar–Apr','May','Jun','Jul','Aug','Sep']:monthly.append(metric(q[q.period==label],label,'Frozen models, calendar-period subset.'))
q['forecast_bin']=pd.qcut(q.context,5,labels=False,duplicates='drop');cal=[]
for i,a in q.groupby('forecast_bin'):
 cal.append({'bin':int(i)+1,'n':len(a),'predicted':float(np.average(a.context,weights=a.p_bfp)*100),'observed':float(a.net.sum()/a.p_bfp.sum()*100)})
# Histories include all dated recorded MLB pitches for cohort pitchers, including starts.
ids=set(q.id);histories={};sourceRows=0
z=zipfile.ZipFile(raw/'2025.zip');plays=pd.read_csv(z.open('2025plays.csv'),usecols=['pitcher','date','gametype','nump','gid']);plays=plays[(plays.gametype=='regular')&plays.pitcher.isin(ids)];plays['pitches']=plays.nump.fillna(0)
for pid,a in plays.groupby('pitcher'):
 dates=a.groupby('date').pitches.sum();histories[pid]=[[str(int(date))[:4]+'-'+str(int(date))[4:6]+'-'+str(int(date))[6:],int(count)] for date,count in dates.items()]
# Toronto discrepancy sensitivity: existing delta/baseline held fixed; only current rows filtered.
v=pd.read_csv(p/'data/toronto-velocity.csv');quality=[]
for year in [2024,2025]:
 for label,a in [('All qualified',v[v.year==year]),('Counts within 2',v[(v.year==year)&(v.difference.abs()<=2)])]:
  b=a[a.rest==0];quality.append({'year':year,'label':label,'n':len(b),'pitchers':b.id.nunique(),'delta':float(b.deltaV.mean())})
result={'label':'Post-hoc diagnostics; models unchanged','checks':checks,'monthly':monthly,'calibration':cal,'longGaps':int((q.rest>=14).sum()),'naiveRate':float(q.naive.iloc[0]*100),'longGapDefinition':'14+ MLB off-days; no inference of physical rest','histories':histories,'torontoQuality':quality}
(p/'data/diagnostics.json').write_text(json.dumps(result,separators=(',',':')))
q[['gid','id','date','team','p_bfp','y','context','workload','naive','e_context','e_workload','e_naive','period']].to_csv(p/'data/frozen-predictions.csv',index=False,float_format='%.9f')
print(json.dumps({k:v for k,v in result.items() if k not in ['histories']},indent=2))
