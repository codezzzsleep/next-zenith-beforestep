"""Archive terminal gait development attempts, reusing the published v72 matrix."""
import argparse
import json
from pathlib import Path
import re
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
    archives = []
    reused = []
    buckets = {}
    for attempt in data['attempts']:
        assert attempt['job_status'] in ('complete', 'failed', 'unregistered'), attempt['attempt']
        if attempt['attempt'] == 'gait-v72-capability-v1':
            reused.append({'attempt': attempt['attempt'],
                           'manifest': 'evidence/crossing/calibration/capability-v72-manifest.json'})
            continue
        version = int(re.match(r'gait-v(\d+)', attempt['attempt'])[1])
        buckets.setdefault((version - 1) // 20, []).append(attempt)
    public = ROOT / 'evidence/crossing/development'
    public.mkdir(parents=True, exist_ok=True)
    for bucket, attempts in sorted(buckets.items()):
        archive = public / f'{args.tag}-v{bucket*20+1:03d}-{(bucket+1)*20:03d}.tar.gz'
        if not archive.exists():
            with tarfile.open(archive, 'w:gz', compresslevel=1) as bundle:
                for attempt in attempts:
                    folder = ROOT / 'outputs/crossing/calibration' / attempt['attempt']
                    bundle.add(folder, arcname='attempts/' + folder.name,
                               filter=lambda info: None if info.name.endswith('.coordinator.lock') else info)
                bundle.add(data_path, arcname='development.json')
        entry = {'path': str(archive.relative_to(ROOT)), 'bytes': archive.stat().st_size,
                 'sha256': sha(archive), 'attempts': [a['attempt'] for a in attempts],
                 'download': 'https://media.githubusercontent.com/media/codezzzsleep/next-zenith-beforestep/main/'
                     + str(archive.relative_to(ROOT))}
        archives.append(entry)
        print(json.dumps({'path': entry['path'], 'bytes': entry['bytes']}), flush=True)
    write(public / (args.tag + '-manifest.json'), {
        'schema': 'beforestep-crossing-development-bundles/v1',
        'data': args.data, 'data_sha256': sha(data_path),
        'archive_count': len(archives), 'archives': archives, 'reused': reused,
        'raw_runs': [{key: row[key] for key in
                      ['raw_path', 'result_sha256', 'trajectory_sha256', 'contacts_sha256']}
                     for attempt in data['attempts'] for row in attempt['trials']],
    })


if __name__ == '__main__':
    main()
