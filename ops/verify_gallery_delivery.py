"""Fetch every new cover and overlay from Pages and compare source SHA/size."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--url',default='https://codezzzsleep.github.io/next-zenith-beforestep/');a=p.parse_args();covers=json.loads((ROOT/'evidence/web-assets/gallery/posters/index.json').read_text())['models'];overlays=json.loads((ROOT/'evidence/web-assets/overlays/index.json').read_text())['models'];items=covers+overlays
 def check(item):
  with urlopen(urljoin(a.url,item['path']),timeout=60) as response:raw=response.read()
  assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],item['path'];return len(raw)
 with ThreadPoolExecutor(max_workers=6) as pool:sizes=list(pool.map(check,items))
 d={'passed':True,'checked_at':datetime.now(timezone.utc).isoformat(),'url':a.url,'covers':len(covers),'overlays':len(overlays),'objects':len(items),'bytes':sum(sizes),'all_sha256_exact':True};(ROOT/'evidence/award/acceptance/C2-C4-public-assets.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d))
if __name__=='__main__':main()
