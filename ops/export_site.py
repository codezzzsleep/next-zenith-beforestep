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
    if output==ROOT or output.is_relative_to(ROOT/'site'):
        parser.error('Choose a separate export directory')
    output.mkdir(parents=True,exist_ok=True)
    shutil.copytree(ROOT/'site',output,dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('video-scene','__pycache__'))
    for directory in ('docs','evidence','experiments'):
        shutil.copytree(ROOT/directory,output/directory,dirs_exist_ok=True)
    assets=output/'assets';assets.mkdir(exist_ok=True)
    shutil.copy2(ROOT/'assets/manifest.json',assets/'manifest.json')
    shutil.copytree(ROOT/'assets/models',assets/'models',dirs_exist_ok=True)
    data=json.loads((ROOT/'site/data/demo.json').read_text())
    for candidate in data['candidates']:
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
