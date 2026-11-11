"""Export the viewer and linked public evidence as ordinary files for hosting."""
import argparse
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    output=Path(args.out).resolve()
    if output.is_relative_to(ROOT):
        parser.error('Choose a separate export directory')
    output.mkdir(parents=True,exist_ok=True)
    shutil.copytree(ROOT/'site',output,dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('video-scene','__pycache__'))
    for directory in ('docs','experiments','config'):
        shutil.copytree(ROOT/directory,output/directory,dirs_exist_ok=True)
    # The viewer links JSON results. Full trajectories, physics meshes and
    # training source snapshots remain in the repository and release ZIP.
    def linked_evidence(path):
        return path.suffix in ('.json','.jsonl') and 'source_snapshot' not in path.parts
    evidence=output/'evidence'
    if evidence.exists():
        for path in evidence.rglob('*'):
            if path.is_file() and not linked_evidence(path):path.unlink()
    for path in (ROOT/'evidence').rglob('*'):
        if not path.is_file() or not linked_evidence(path):continue
        target=evidence/path.relative_to(ROOT/'evidence')
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target)
    assets=output/'assets';assets.mkdir(exist_ok=True)
    shutil.copy2(ROOT/'assets/manifest.json',assets/'manifest.json')
    shutil.copytree(ROOT/'assets/models',assets/'models',dirs_exist_ok=True)
    index=json.loads((ROOT/'site/data/scenes.json').read_text())
    candidates=[]
    for scene in index['scenes']:
        data=json.loads((ROOT/'site'/scene['data']).read_text())
        candidates.extend(data['candidates'])
    # Unlinked duplicate media meshes add transport cost; the complete assets
    # stay in main. Keep every candidate referenced by the current/historical UI.
    used_glbs = {candidate['glb'] for candidate in candidates} | {'media/candidate.glb'}
    for path in (output/'media').rglob('*.glb'):
        if str(path.relative_to(output)) not in used_glbs:path.unlink()
    for candidate in candidates:
        relative=Path(candidate['glb'])
        if relative.parts[0]!='assets':continue
        source=(ROOT/relative).resolve()
        if not source.is_relative_to(ROOT/'assets') or not source.is_file():
            raise ValueError('Invalid candidate asset: '+str(relative))
        target=output/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
    (output/'.nojekyll').touch()
    print(output)


if __name__=='__main__':main()
