"""Supplementary pitch-type-specific Toronto velocity analysis."""
import argparse,json,unicodedata,zipfile,hashlib
from pathlib import Path
import numpy as np,pandas as pd
ap=argparse.ArgumentParser();ap.add_argument('--raw',type=Path,required=True);raw=ap.parse_args().raw;out=Path(__file__).resolve().parent
norm=lambda s:''.join(c.lower() for c in unicodedata.normalize('NFKD',str(s)) if c.isascii() and c.isalpha())
names={};displayNames={}
for y in [2024,2025]:
 z=zipfile.ZipFile(raw/f'{y}.zip');people=pd.read_csv(z.open(f'{y}allplayers.csv'))
 for r in people.itertuples():
  names[norm(f'{r.last}{r.first}')]=r.id;displayNames[r.id]=f'{r.first} {r.last}'
s=pd.concat([pd.read_csv(raw/f'tor-{y}{h}.csv',low_memory=False) for y in [2024,2025] for h in ['a','b']],ignore_index=True)
assert not s.duplicated(['game_pk','at_bat_number','pitch_number']).any()
s['pitteam']=np.where(s.inning_topbot=='Top',s.home_team,s.away_team);assert (s.pitteam=='TOR').all()
s['id']=s.player_name.map(norm).map(names);assert s.id.notna().all(),s[s.id.isna()].player_name.unique()
s['day']=pd.to_datetime(s.game_date);s['year']=s.day.dt.year
# Identify ambiguities, join only unique pitcher-date appearances on both sources.
a=pd.read_pickle(raw/'all-appearances.pkl');a=a[(a.team=='TOR')&a.year.isin([2024,2025])&~a.doubleAppearance&~a.suspended]
groups=s.groupby(['id','day','game_pk']);counts=groups.size().rename('statcastRows').reset_index();counts=counts[~counts.duplicated(['id','day'],keep=False)]
# Real tracked pitches have measured release speed; automatic balls/strikes may lack it.
real=s[s.release_speed.notna()].groupby(['id','day','game_pk']).size().rename('trackedPitches').reset_index();counts=counts.merge(real,how='left')
ff=s[(s.pitch_type=='FF')&s.release_speed.between(70,110)].groupby(['id','day','game_pk']).agg(velocity=('release_speed','mean'),ffN=('release_speed','size')).reset_index()
v=counts.merge(ff,on=['id','day','game_pk'],how='left').merge(a,on=['id','day'],validate='one_to_one')
v['difference']=v.statcastRows-v.pitches
v=v.sort_values(['id','day']);qual=v[v.relief&(v.ffN>=5)].copy();qual['priorFFN']=qual.groupby(['id','year']).cumcount();qual['priorV']=qual.groupby(['id','year']).velocity.transform(lambda x:x.shift().rolling(5,min_periods=3).mean());qual['deltaV']=qual.velocity-qual.priorV
q=qual[(qual.priorFFN>=3)&(qual.priorRelief>=5)].copy();q['dateISO']=q.day.dt.strftime('%Y-%m-%d');q['name']=q.id.map(displayNames);assert q.name.notna().all()
rng=np.random.default_rng(71);stats=[]
for year in [2024,2025]:
 for rest in ['0 days','1 day','2 days','3+ days']:
  b=q[(q.year==year)&(q.restGroup==rest)];c=b.groupby('id').deltaV.agg(['sum','count']).to_numpy();bs=[]
  for _ in range(1000):
   t=c[rng.integers(0,len(c),len(c))].sum(axis=0);bs.append(t[0]/t[1])
  stats.append({'year':year,'rest':rest,'n':len(b),'pitchers':b.id.nunique(),'delta':float(b.deltaV.mean()),'lo':float(np.quantile(bs,.025)),'hi':float(np.quantile(bs,.975))})
result={'rawPitches':len(s),'games':int(s.game_pk.nunique()),'matchedAppearances':len(v),'pitchCountExact':int((v.difference==0).sum()),'pitchCountWithin2':int((abs(v.difference)<=2).sum()),'eligible':len(q),'stats':stats,'rows':json.loads(q[['id','name','dateISO','year','restGroup','p3','p7','ffN','velocity','priorV','deltaV']].round(4).to_json(orient='records'))}
(out/'data/toronto.json').write_text(json.dumps(result,indent=2));q.to_csv(out/'data/toronto-velocity.csv',index=False)
print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
