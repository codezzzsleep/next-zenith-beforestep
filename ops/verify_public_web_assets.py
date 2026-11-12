"""Download every indexed web asset from the deployed site and check its SHA."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='https://codezzzsleep.github.io/next-zenith-beforestep/')
    parser.add_argument('--out', default='evidence/award/acceptance/web-assets-pages.json')
    args = parser.parse_args()
    expected = (ROOT / 'evidence/web-assets/index.json').read_bytes()
    with urlopen(Request(urljoin(args.url, 'evidence/web-assets/index.json'), headers={'Cache-Control': 'no-cache'}), timeout=30) as response:
        assert response.read() == expected, 'Wait for the deployed index to match the delivered bundle'
    index = json.loads(expected)

    def check(item):
        digest, size = hashlib.sha256(), 0
        with urlopen(urljoin(args.url, item['path']), timeout=30) as response:
            assert response.status == 200
            while block := response.read(1 << 20):
                digest.update(block)
                size += len(block)
        assert digest.hexdigest() == item['sha256'] and size == item['bytes'], item['path']
        return size

    errors, checked, total = [], 0, 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs = {pool.submit(check, item): item['path'] for item in index['items']}
        for future in as_completed(jobs):
            try:
                total += future.result()
                checked += 1
            except Exception as error:
                errors.append({'path': jobs[future], 'error': str(error)})
            if (checked + len(errors)) % 50 == 0:
                print(json.dumps({'checked': checked, 'errors': len(errors)}), flush=True)
    result = {'passed': not errors and checked == len(index['items']),
              'verified_at': datetime.now(timezone.utc).isoformat(), 'url': args.url,
              'indexed_files_checked': checked, 'downloaded_bytes': total,
              'all_deployed_asset_sha_and_size_exact': not errors,
              'index_sha256': hashlib.sha256(expected).hexdigest(), 'errors': errors}
    (ROOT / args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(result, ensure_ascii=False))
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
