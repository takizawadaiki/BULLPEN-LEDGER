import json
from pathlib import Path
p=Path(__file__).resolve().parent
d={k:json.loads((p/f'data/{k}.json').read_text()) for k in ['summary','board','toronto']}
(p/'research-data.js').write_text('const RESEARCH = '+json.dumps(d,separators=(',',':'))+';\n')
