"""Independent source-level and output checks; run after analysis."""
import argparse,json,zipfile,re
from pathlib import Path
import pandas as pd,numpy as np
ap=argparse.ArgumentParser();ap.add_argument('--raw',type=Path,required=True);raw=ap.parse_args().raw;p=Path(__file__).resolve().parent
m=pd.read_csv(p/'data/modeling-appearances.csv');b=json.loads((p/'data/board.json').read_text());s=json.loads((p/'data/summary.json').read_text())
assert len(m)==s['n'] and sum(m.year==2025)==s['testN']
assert not m.duplicated(['gid','id']).any()
assert (m.p_seq>1).all() and (m.p_bfp>0).all() and (m.priorRelief>=5).all()
assert not m.suspended.any() and not m.doubleAppearance.any()
assert np.isfinite(m[s['models']['workload']['columns']].to_numpy()).all()
assert ((m.p7>=m.p3)&(m.p3>=m.p1)).all()
assert np.allclose(m.y,(m.p_k-m.p_w+m.p_iw)/m.p_bfp,atol=1e-6)
# Rebuild workload from source CSVs, independent of the exported feature table.
plays=[];pitching=[]
for y in [2023,2024,2025]:
 z=zipfile.ZipFile(raw/f'{y}.zip');a=pd.read_csv(z.open(f'{y}plays.csv'),usecols=['pitcher','date','gametype','nump']);a=a[a.gametype=='regular'];a['day']=pd.to_datetime(a.date.astype(str));plays.append(a)
 q=pd.read_csv(z.open(f'{y}pitching.csv'));pitching.append(q[(q.gametype=='regular')&(q.stattype=='value')])
plays=pd.concat(plays);daily=plays.groupby(['pitcher','day']).nump.sum();pitches=pd.concat(pitching)
for r in m.sample(120,random_state=99).itertuples():
 date=pd.to_datetime(str(r.date));history=daily.loc[r.id];prior=history[history.index<date]
 assert r.rest==(date-prior.index.max()).days-1
 for days,col in [(1,'p1'),(3,'p3'),(7,'p7')]:
  expected=prior[prior.index>=date-pd.Timedelta(days=days)].sum();assert getattr(r,col)==expected
for r in b:
 assert len(r['prior7'])==7 and sum(r['prior7'])==r['p7'] and sum(r['prior7'][-3:])==r['p3'] and r['prior7'][-1]==r['p1']
# Independently calculate both frozen prediction errors from published coefficients.
test=m[m.year==2025]
for name,model in s['models'].items():
 pred=np.full(len(test),model['intercept'])
 for col,coef in model['coefficients'].items():pred+=test[col].to_numpy()*coef
 rmse=np.sqrt(np.average((test.y-pred)**2,weights=test.p_bfp));assert abs(rmse-model['rmse'])<1e-6
# No same-game outcomes or future-use fields are among model inputs.
forbidden={'p_bfp','p_k','ubb','pitches','y','net','pitcher_days_until_next_game'}
assert not forbidden.intersection(s['models']['workload']['columns'])
html=(p/'index.html').read_text()
for href in re.findall(r'(?:src|href)="([^"#]+)"',html):
 if not href.startswith(('http','data:')):assert (p/href).exists(),href
v=pd.read_csv(p/'data/toronto-velocity.csv');assert (v.ffN>=5).all() and (v.priorFFN>=3).all();assert np.allclose(v.deltaV,v.velocity-v.priorV)
# Revision 2: frozen diagnostics and strictly dated source history.
d=json.loads((p/'data/diagnostics.json').read_text());frozen=pd.read_csv(p/'data/frozen-predictions.csv')
assert len(frozen)==len(test) and not frozen.duplicated(['gid','id']).any()
assert d['longGaps']==int((test.rest>=14).sum())
for pid,dates in d['histories'].items():
 assert dates==sorted(dates)
 for date,count in dates:assert count==daily.loc[(pid,pd.Timestamp(date))]
for r in b:
 hist=dict(d['histories'][r['id']]);today=pd.Timestamp(r['dateISO'])
 expected=sum(hist.get((today-pd.Timedelta(days=i)).strftime('%Y-%m-%d'),0) for i in range(1,8))
 assert expected==r['p7']
for record in d['checks']:
 a=test
 if record['label']=='Late & close':a=a[(a.entry>=7)&(abs(a.margin)<=3)]
 elif record['label']=='No long MLB gaps':a=a[a.rest<=6]
 elif record['label']=='Short outings':a=a[a.p_bfp<=6]
 assert len(a)==record['n'] and a.id.nunique()==record['pitchers']
 source=a.merge(frozen[['gid','id','context','workload']],on=['gid','id'],validate='one_to_one')
 weights=np.ones(len(source)) if record['weight']=='equal' else source.p_bfp
 for model in ['context','workload']:
  expected=100*np.sqrt(np.average((source.y-source[model])**2,weights=weights));assert abs(expected-record[model])<1e-6
 assert abs(record['delta']-(record['workload']-record['context']))<1e-9
assert np.allclose([d['checks'][0]['lo'],d['checks'][0]['hi']],np.array(s['rmseDeltaCI'])*100)
assert sum(a['n'] for a in d['monthly'])==len(test)
assert v.name.notna().all()
result={'status':'passed','sourceWorkloadSamples':120,'boardHistories':len(b),'predictionChecks':2,'modelingRows':len(m),'velocityRows':len(v),'diagnosticSlices':len(d['checks']),'historyPitchers':len(d['histories']),'checks':['unique appearance keys','cohort exclusions','nonnegative nested workload windows','outcome formula','source-derived rest and pitch windows','all board history sums','independent frozen model RMSE','no outcome/future fields in predictors','velocity sample rules','local page references','raw-source daily dossier histories','all dossier prior-7 totals','independent diagnostic subset errors','primary confidence interval preserved','monthly coverage','Toronto display names']}
(p/'data/verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
