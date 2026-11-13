"""Keep complete calibration trajectories, contacts and source identities in public bundles."""
import argparse
import json
from pathlib import Path
import sys
import tarfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experimental.crossing.runtime import sha, write


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    parser.add_argument('--tag', required=True)
    args = parser.parse_args()
    data_path = ROOT / args.data
    data = json.loads(data_path.read_text())
    assert data['status'] == 'complete'
    public = ROOT / 'evidence/crossing/calibration'
    entries = []
    jobs = data['source_jobs']
    all_trials = [r for g in data['groups'] for r in g['trials']]
    for h in data['heights_m']:
        rows = [r for r in all_trials if r['h_m'] == h]
        archive = public / f'{args.tag}-h{int(round(h*100)):02d}cm.tar.gz'
        if not archive.exists():
            with tarfile.open(archive, 'w:gz', compresslevel=1) as bundle:
                for row in rows:
                    folder = ROOT / row['raw_path']
                    bundle.add(folder, arcname='trials/' + folder.name)
                for name in [jobs['gait'], jobs['wheel'], jobs['supplement'], 'wheel-common120-v1']:
                    source = ROOT / 'outputs/crossing/calibration' / name / 'source'
                    if source.exists():
                        bundle.add(source, arcname='source/' + name)
                bundle.add(data_path, arcname='capability.json')
        entries.append({'height_m': h, 'path': str(archive.relative_to(ROOT)),
                        'bytes': archive.stat().st_size, 'sha256': sha(archive), 'trials': len(rows),
                        'download': 'https://media.githubusercontent.com/media/codezzzsleep/next-zenith-beforestep/main/' + str(archive.relative_to(ROOT))})
        print(json.dumps({k: entries[-1][k] for k in ['height_m', 'bytes', 'trials']}), flush=True)
    archive = public / (args.tag + '-true-rocks.tar.gz')
    if not archive.exists():
        with tarfile.open(archive, 'w:gz', compresslevel=1) as bundle:
            for row in data['rocks']:
                folder = ROOT / row['raw_path']
                bundle.add(folder, arcname='trials/' + folder.name)
            source = ROOT / 'outputs/crossing/calibration' / jobs['rocks'] / 'source'
            bundle.add(source, arcname='source')
            fixtures = ROOT / 'outputs/crossing/runtime/true-rocks'
            for fixture in fixtures.glob('*-h0.120000-d0.150000-w1.200000'):
                bundle.add(fixture, arcname='fixtures/' + fixture.name)
    entries.append({'path': str(archive.relative_to(ROOT)), 'bytes': archive.stat().st_size,
                    'sha256': sha(archive), 'trials': len(data['rocks']),
                    'download': 'https://media.githubusercontent.com/media/codezzzsleep/next-zenith-beforestep/main/' + str(archive.relative_to(ROOT))})
    write(public / (args.tag + '-manifest.json'),
          {'schema': 'beforestep-crossing-complete-bundles/v1', 'data': args.data, 'data_sha256': sha(data_path),
           'trial_count': data['trial_count'], 'archives': entries, 'source_jobs': jobs,
           'raw_runs': [{'path': r['raw_path'], 'trajectory_sha256': r['trajectory_sha256'],
                         'contacts_sha256': r['contacts_sha256']} for r in all_trials + data['rocks']]})
    print(json.dumps({'archive_count': len(entries), 'bytes': sum(r['bytes'] for r in entries)}), flush=True)


if __name__ == '__main__':
    main()
