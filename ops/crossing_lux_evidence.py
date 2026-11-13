"""Preserve the five real generated models, inputs and admission originals."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from ops.crossing_development_evidence import bundle

if __name__=='__main__':
    report=json.loads((ROOT/'evidence/crossing/development-lux-first.json').read_text())
    folder=ROOT/'outputs/crossing/development'/report['revision']/f'seed-{report["seed"]}'
    files=[]
    for p in folder.rglob('*'):
        if p.is_file() and (any(part.startswith('lux') or part=='decision' for part in p.parts) or p.name=='lux-development.json'):
            files.append(p)
    for task_id in report['task_ids']:
        files.extend(p for p in (ROOT/'assets/candidates'/str(task_id)).rglob('*') if p.is_file())
    files.extend(ROOT/'evidence/crossing'/p for p in ['generation-stop.json','development-lux-first.json','final-development-status.json','development-blindness-matched-height.json','development-lux-shape-diagnostic.json'])
    archive=bundle('addendum1-first-lux',sorted(set(files)))
    indexpath=ROOT/'evidence/crossing/development/addendum1-index.json';index=json.loads(indexpath.read_text())
    index['first_lux']=archive;indexpath.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'archive_bytes':archive['bytes'],'member_sha_check':archive['member_sha_check']}))
