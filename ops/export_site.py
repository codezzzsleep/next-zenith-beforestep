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
    if (ROOT / 'site/homepage-integration.json').exists():
        from integrate_owner_homepage import rebuild_data
        rebuild_data(ROOT / 'site')
    if (ROOT / 'site/data/gallery.json').exists():
        from build_gallery_data import main as build_gallery
        build_gallery()
    if (ROOT / 'site/site-theme.css').exists():
        from apply_home_theme import main as apply_theme
        apply_theme()
    demo_pending = not (ROOT / 'site/data/award-demo.json').exists()
    ignore = ['video-scene', '__pycache__'] + (['award-demo.html', 'award-demo.js'] if demo_pending else [])
    shutil.copytree(ROOT/'site',output,dirs_exist_ok=True, ignore=shutil.ignore_patterns(*ignore))
    if demo_pending:
        for name in ('award-demo.html', 'award-demo.js'):
            stale = output / name
            if stale.exists():
                stale.unlink()
    for directory in ('docs','experiments','config'):
        shutil.copytree(ROOT/directory,output/directory,dirs_exist_ok=True)
    # The viewer links JSON results. Full trajectories, physics meshes and
    # training source snapshots remain in the repository and release ZIP.
    def linked_evidence(path):
        award_media = ('award' in path.parts and path.suffix in ('.png', '.jpg', '.md', '.srt'))
        web_asset = 'web-assets' in path.parts
        return (path.suffix in ('.json','.jsonl','.log') or award_media or web_asset) and 'source_snapshot' not in path.parts
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
    award_manifest = ROOT / 'evidence/award/asset-iterations/manifest.json'
    curated_paths = []
    if award_manifest.exists():
        for row in json.loads(award_manifest.read_text())['versions']:
            curated_paths.extend(item['path'] for item in
                [row['model'], row['viewer'], row['input'], *row.get('additional_inputs', []), *row['frozen_config']])
            if row['viewer']['path'].startswith('site/'):
                used_glbs.add(row['viewer']['path'].removeprefix('site/'))
    demo_data = ROOT / 'site/data/award-demo.json'
    if demo_data.exists():
        demo = json.loads(demo_data.read_text())
        used_glbs.update(row['glb'] for row in demo['candidates'])
        # Keep the exact bounded review objects reachable from its public
        # manifest, including immutable objects shared with earlier runs.
        manifest = json.loads((ROOT / demo['manifest']).read_text())
        for relative in {row['public_object'] for row in manifest['files'] if row.get('public_object')}:
            source = (ROOT / relative).resolve()
            assert source.is_relative_to(ROOT / 'evidence') and source.is_file(), relative
            target = output / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
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
    for relative in set(curated_paths):
        source = (ROOT / relative).resolve()
        if not source.is_relative_to(ROOT) or not source.is_file():
            raise ValueError('Invalid curated award artifact: ' + relative)
        if relative.startswith('site/'):
            continue
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    (output/'.nojekyll').touch()
    print(output)


if __name__=='__main__':main()
