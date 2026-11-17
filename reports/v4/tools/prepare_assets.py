"""Verify the curated images bundled with the report before building."""
import hashlib
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'asset-sources.json').read_text(encoding='utf-8'))
for item in manifest['assets']:
    path = root / item['file']
    if not path.is_file():
        raise SystemExit(f'Missing report asset: {item["file"]}')
    if path.suffix != '.svg' and hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
        raise SystemExit(f'Report asset hash mismatch: {item["file"]}')
print(f'Verified {len(manifest["assets"])} bundled report assets')
