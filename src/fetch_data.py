"""Retrieve only explicitly recorded export URLs and require frozen hashes."""
from pathlib import Path
import argparse,hashlib,json,urllib.request
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);args=p.parse_args()
args.directory.mkdir(parents=True,exist_ok=True)
manifest=json.loads((ROOT/'data_manifest.json').read_text())
for item in manifest:
 dest=args.directory/item['file']
 if not dest.exists():
  req=urllib.request.Request(item['url'],headers={'User-Agent':'Academic reproducibility download'})
  with urllib.request.urlopen(req) as r:dest.write_bytes(r.read())
 digest=hashlib.sha256(dest.read_bytes()).hexdigest()
 if digest!=item['sha256']:
  raise RuntimeError(f"Frozen hash mismatch: {dest.name}; source has changed. Do not reproduce against silently changed data.")
 print(f"Verified {dest.name}: {item['bytes']} bytes")
