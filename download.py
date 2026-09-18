"""Cache primary-source inputs; no credentials required. Several hundred MB of disk may be used."""
import argparse,hashlib,json,time,urllib.request
from pathlib import Path
from urllib.parse import urlencode
ap=argparse.ArgumentParser();ap.add_argument('--raw',type=Path,default=Path('raw'));raw=ap.parse_args().raw;raw.mkdir(parents=True,exist_ok=True)
sources={f'{y}.zip':f'https://www.retrosheet.org/downloads/{y}/{y}csvs.zip' for y in [2023,2024,2025]}
for y in [2024,2025]:
 for h,start,end in [('a',f'{y}-03-01',f'{y}-06-30'),('b',f'{y}-07-01',f'{y}-10-01')]:
  sources[f'tor-{y}{h}.csv']='https://baseballsavant.mlb.com/statcast_search/csv?'+urlencode({'all':'true','type':'details','player_type':'pitcher','hfGT':'R|','hfTeam':'TOR|','game_date_gt':start,'game_date_lt':end})
manifest=[]
for filename,url in sources.items():
 target=raw/filename
 if not target.exists():
  print('Downloading',filename,flush=True)
  req=urllib.request.Request(url,headers={'User-Agent':'BullpenLedgerResearch/1.0'})
  with urllib.request.urlopen(req,timeout=180) as response: content=response.read()
  if filename.endswith('.zip') and not content.startswith(b'PK'):raise ValueError('Expected ZIP')
  if filename.endswith('.csv') and b'pitch_type' not in content[:1000]:raise ValueError('Expected Statcast CSV')
  target.write_bytes(content);time.sleep(2)
 manifest.append({'file':filename,'url':url,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
(raw/'download-manifest.json').write_text(json.dumps(manifest,indent=2));print('Sources cached.')
