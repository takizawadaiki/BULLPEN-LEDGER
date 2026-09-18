"""Run from workspace root: python outputs/bullpen-analysis/analyze.py --raw work/bullpen"""
import argparse,json,zipfile,hashlib
from pathlib import Path
import numpy as np,pandas as pd
import statsmodels.api as sm
from scipy.stats import t as student_t
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
ap=argparse.ArgumentParser();ap.add_argument('--raw',type=Path,required=True);args=ap.parse_args();raw=args.raw;out=Path(__file__).resolve().parent;(out/'data').mkdir(exist_ok=True)
frames=[];daily=[];names={};audits=[]
for y in [2023,2024,2025]:
 z=zipfile.ZipFile(raw/f'{y}.zip')
 p=pd.read_csv(z.open(f'{y}pitching.csv'));g=pd.read_csv(z.open(f'{y}gameinfo.csv'));people=pd.read_csv(z.open(f'{y}allplayers.csv'))
 plays=pd.read_csv(z.open(f'{y}plays.csv'),usecols=['gid','pitcher','date','gametype','nump','pa','inning','score_v','score_h','pitteam','outs_pre','br1_pre','br2_pre','br3_pre'])
 plays=plays[plays.gametype=='regular'].copy();assert not ((plays.pa==1)&plays.nump.isna()).any()
 plays['day']=pd.to_datetime(plays.date.astype(str));plays['nump']=plays.nump.fillna(0)
 daily.append(plays.groupby(['pitcher','day']).nump.sum().rename('pitches').reset_index())
 stats=plays.groupby(['gid','pitcher']).agg(pitches=('nump','sum'),entry=('inning','first'),score_v=('score_v','first'),score_h=('score_h','first'))
 first=plays.drop_duplicates(['gid','pitcher']).set_index(['gid','pitcher']);stats['inherited']=first[['br1_pre','br2_pre','br3_pre']].notna().sum(axis=1)
 p=p[(p.gametype=='regular')&(p.stattype=='value')].copy();p=p.merge(stats,left_on=['gid','id'],right_index=True,validate='one_to_one')
 p=p.merge(g[['gid','suspend','temp','hometeam']],on='gid',validate='many_to_one');p['year']=y;p['day']=pd.to_datetime(p.date.astype(str));p['home']=(p.team==p.hometeam).astype(int);p['margin']=np.where(p.home,p.score_h-p.score_v,p.score_v-p.score_h);p['absMargin']=abs(p.margin)
 people=people[~people.team.isin(['ALS','NLS'])];roles=people.groupby('id')[['g','g_p']].sum();eligible=roles.index[roles.g_p>=roles.g*.5];p['pitcherRole']=p.id.isin(eligible)
 for r in people.itertuples():names[r.id]=f'{r.first} {r.last}'
 p['suspended']=p.suspend.notna();p['relief']=p.p_seq>1
 audits.append({'year':y,'regularGames':int((g.gametype=='regular').sum()),'pitchingAppearances':len(p),'reliefAppearances':int(p.relief.sum()),'suspendedGames':int(g[g.gametype=='regular'].suspend.notna().sum()),'missingPaPitchCounts':int(((plays.pa==1)&plays.nump.isna()).sum())})
 frames.append(p)
f=pd.concat(frames,ignore_index=True).sort_values(['id','day','number']).reset_index(drop=True);loads=pd.concat(daily).sort_values(['pitcher','day'])
# Dated workload includes suspended-game continuation dates and pitching starts.
loadmap={pid:dict(zip(q.day.map(lambda x:x.toordinal()),q.pitches)) for pid,q in loads.groupby('pitcher')}
features=[]
for r in f.itertuples():
 today=r.day.toordinal();hist=loadmap[r.id];past=[d for d in hist if d<today];last=max(past) if past else None
 row={'rest':today-last-1 if last else 99,'p1':hist.get(today-1,0),'p3':sum(hist.get(today-k,0) for k in range(1,4)),'p7':sum(hist.get(today-k,0) for k in range(1,8)),'previous':hist[last] if last else 0,'consecutive':int(today-1 in hist)+int(today-1 in hist and today-2 in hist)}
 features.append(row)
f=pd.concat([f,pd.DataFrame(features)],axis=1);f['ubb']=f.p_w-f.p_iw;assert (f.ubb>=0).all();f['net']=f.p_k-f.ubb;f['y']=f.net/f.p_bfp.replace(0,np.nan)
# Expanding baseline includes prior relief appearances only, resets each season.
f['priorRelief']=f.groupby(['id','year']).relief.cumsum()-f.relief.astype(int)
for col in ['net','p_bfp']:
 f['_v']=np.where(f.relief&~f.suspended,f[col],0);f['prior_'+col]=f.groupby(['id','year'])._v.cumsum()-f._v
f['baseline']=(f.prior_net+100*.15)/(f.prior_p_bfp+100)
f['doubleAppearance']=f.groupby(['id','day']).id.transform('size')>1
f['restGroup']=np.select([f.rest==0,f.rest==1,f.rest==2],['0 days','1 day','2 days'],default='3+ days')
f['b2b']=(f.rest==0).astype(int);f['rest1']=(f.rest==1).astype(int);f['rest2']=(f.rest==2).astype(int);f['heavyYesterday']=(f.p1>=20).astype(int);f['threeDays']=(f.consecutive>=2).astype(int)
f['p3_10']=f.p3/10;f['p7_10']=f.p7/10;f['month']=f.day.dt.month
eligible=f.relief&f.pitcherRole&(f.p_bfp>0)&(f.priorRelief>=5)&~f.suspended&~f.doubleAppearance
m=f[eligible].copy();train=m[m.year<2025].copy();test=m[m.year==2025].copy()
context=['baseline','entry','absMargin','inherited','home','temp','month'];workload=['b2b','rest1','rest2','p3_10','p7_10','heavyYesterday','threeDays']
median=train.temp.median()
for q in [m,train,test]:q['temp']=q.temp.fillna(median);q['absMargin']=q.absMargin.clip(upper=10)
models={};preds={}
for label,cols in [('context',context),('workload',context+workload)]:
 scaler=StandardScaler();x=scaler.fit_transform(train[cols]);model=Ridge(alpha=100);model.fit(x,train.y,sample_weight=train.p_bfp);pred=model.predict(scaler.transform(test[cols]));preds[label]=pred
 assert np.isfinite(pred).all()
 assert np.allclose(pred,np.sum(scaler.transform(test[cols])*model.coef_,axis=1)+model.intercept_)
 models[label]={'rmse':float(np.sqrt(np.average((test.y-pred)**2,weights=test.p_bfp))),'mae':float(np.average(abs(test.y-pred),weights=test.p_bfp)),'columns':cols,'coefficients':dict(zip(cols,(model.coef_/scaler.scale_).tolist())),'intercept':float(model.intercept_-np.sum(model.coef_*scaler.mean_/scaler.scale_))}
test['pred_context']=preds['context'];test['pred_workload']=preds['workload'];test['err_context']=(test.y-preds['context'])**2*test.p_bfp;test['err_workload']=(test.y-preds['workload'])**2*test.p_bfp
cluster=test.groupby('id')[['err_context','err_workload','p_bfp']].sum().to_numpy();rng=np.random.default_rng(71);deltas=[]
for _ in range(1000):
 a=cluster[rng.integers(0,len(cluster),len(cluster))].sum(axis=0);deltas.append(np.sqrt(a[1]/a[2])-np.sqrt(a[0]/a[2]))
# Weighted pitcher-season fixed effects, development seasons only.
cols=context+workload;t=train.copy();t['group']=t.id+'_'+t.year.astype(str);w=t.p_bfp
X=t[cols].copy();Y=t.y.copy()
for col in cols:
 weighted=(X[col]*w).groupby(t.group).transform('sum')/w.groupby(t.group).transform('sum');X[col]-=weighted
Y-= (Y*w).groupby(t.group).transform('sum')/w.groupby(t.group).transform('sum')
fit=sm.WLS(Y,X,weights=w).fit(cov_type='cluster',cov_kwds={'groups':t.id})
# Correct cluster finite-sample scaling for the absorbed pitcher-season intercepts.
k=np.linalg.matrix_rank(X.to_numpy());G=t.group.nunique();nobs=len(t)
se=fit.bse*np.sqrt((nobs-k)/(nobs-k-G));critical=student_t.ppf(.975,t.id.nunique()-1)
coef=[{'feature':c,'estimate':float(fit.params[c]*100),'lo':float((fit.params[c]-critical*se[c])*100),'hi':float((fit.params[c]+critical*se[c])*100)} for c in workload]
# Descriptive rest strata: cluster-bootstrap raw minus prior baseline.
strata=[]
for period,q in [('2023–2024',train),('2025',test)]:
 for group in ['0 days','1 day','2 days','3+ days']:
  a=q[q.restGroup==group].copy();a['residual']=(a.y-a.baseline)*a.p_bfp;g=a.groupby('id')[['residual','p_bfp']].sum().to_numpy();boots=[]
  for _ in range(500):
   b=g[rng.integers(0,len(g),len(g))].sum(axis=0);boots.append(b[0]/b[1]*100)
  strata.append({'period':period,'rest':group,'n':len(a),'pitchers':a.id.nunique(),'bf':int(a.p_bfp.sum()),'rate':float(a.net.sum()/a.p_bfp.sum()*100),'delta':float(a.residual.sum()/a.p_bfp.sum()*100),'lo':float(np.quantile(boots,.025)),'hi':float(np.quantile(boots,.975))})
# Held-out operational board is a historical record of actual appearances, not a roster.
board=test.copy();board['name']=board.id.map(names);board['dateISO']=board.day.dt.strftime('%Y-%m-%d');board['modelChange']=(board.pred_workload-board.pred_context)*100
board['prior7']=[ [loadmap[r.id].get(r.day.toordinal()-k,0) for k in range(7,0,-1)] for r in board.itertuples()]
boardcols=['prior7','gid','id','name','team','opp','dateISO','rest','p1','p3','p7','previous','consecutive','entry','margin','inherited','baseline','p_bfp','p_k','ubb','pitches','y','modelChange']
board[boardcols].to_csv(out/'data/heldout-appearances.csv',index=False,float_format='%.6f')
# Complete modeling table for audit/reproduction.
m.drop(columns=['_v'],errors='ignore').to_csv(out/'data/modeling-appearances.csv',index=False,float_format='%.6f')
f.to_pickle(raw/'all-appearances.pkl')
summary={'audit':audits,'n':len(m),'trainN':len(train),'testN':len(test),'pitchers':m.id.nunique(),'testPitchers':test.id.nunique(),'testBF':int(test.p_bfp.sum()),'models':models,'rmseDelta':models['workload']['rmse']-models['context']['rmse'],'rmseDeltaCI':np.quantile(deltas,[.025,.975]).tolist(),'coefficients':coef,'strata':strata,'excluded':{'suspendedRelief':int((f.relief&f.suspended).sum()),'sameDayDoubleRelief':int((f.relief&f.doubleAppearance).sum()),'insufficientPriorRelief':int((f.relief&(f.priorRelief<5)).sum()),'nonPitcherRoleRelief':int((f.relief&~f.pitcherRole).sum())}}
(out/'data/summary.json').write_text(json.dumps(summary,indent=2));(out/'data/board.json').write_text(board[boardcols].round(5).to_json(orient='records'))
manifest={'retrieved':'2026-09-17','sources':json.loads((raw/'download-manifest.json').read_text()) if (raw/'download-manifest.json').exists() else [{'url':f'https://www.retrosheet.org/downloads/{y}/{y}csvs.zip','sha256':hashlib.sha256((raw/f'{y}.zip').read_bytes()).hexdigest()} for y in [2023,2024,2025]],'seed':71,'training':[2023,2024],'test':[2025]};(out/'data/source-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(summary,indent=2))
