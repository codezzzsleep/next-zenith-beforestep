"""Check local Markdown links without network requests."""
import json
from pathlib import Path
import re
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
files = [ROOT / 'README.md', *sorted((ROOT / 'docs').rglob('*.md'))]
checked = 0
missing = []
for path in files:
    text = re.sub(r'```.*?```', '', path.read_text(), flags=re.S)
    for link in re.findall(r'!?\[[^\]]*\]\(([^\n)]+)\)', text):
        link = unquote(link.split(' ')[0].strip('<>').split('#')[0])
        if not link or re.match(r'[a-z]+:', link):
            continue
        checked += 1
        if not (path.parent / link).exists():
            missing.append({'document': str(path.relative_to(ROOT)), 'link': link})
result = {'documents': len(files), 'local_links_checked': checked, 'missing': missing}
print(json.dumps(result, ensure_ascii=False, indent=2))
if missing:
    raise SystemExit(1)
