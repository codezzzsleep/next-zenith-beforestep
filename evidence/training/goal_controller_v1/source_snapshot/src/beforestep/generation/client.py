"""Lux3D requests with durable task IDs, explicit submission and safe resume."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import re
import shlex
import time
import urllib.error
import urllib.request
import uuid
import zipfile

from beforestep.paths import ROOT

BASE = 'https://api.aholo3d.cn'
LEDGER = ROOT / 'outputs/generation'


class ProviderRejected(RuntimeError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(f'Lux3D rejected request: code={code} message={message[:160]}')


def load_credentials(path=None):
    if os.environ.get('AHOLO_API_KEY', '').strip():
        return
    path = Path(path or os.environ.get('AHOLO_ENV_FILE', ROOT.parent / '.env'))
    if path.is_file():
        for line in path.read_text().splitlines():
            match = re.match(r'\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*[=:]\s*(.*)', line)
            if match and match[1].lower() in ('aholo_api_key', 'api_key', 'lux3d_api_key'):
                value = shlex.split(match[2], comments=True)
                if value:
                    os.environ['AHOLO_API_KEY'] = value[0]
    if not os.environ.get('AHOLO_API_KEY', '').strip():
        raise RuntimeError('Configure AHOLO_API_KEY or pass --env-file; never commit the key.')


def atomic_json(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush(); os.fsync(f.fileno())
    temporary.replace(path)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def api(method, path, body=None, timeout=60):
    load_credentials()
    request = urllib.request.Request(BASE + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Authorization': os.environ['AHOLO_API_KEY'], 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f'Lux3D HTTP {error.code}') from None
    if isinstance(result, int) and path.endswith('/task/create'):
        return result
    if isinstance(result, dict) and 'c' not in result and path == '/asset/v1/token' and result.get('ousToken'):
        return result
    if not isinstance(result, dict):
        raise RuntimeError('Lux3D returned an unsupported response')
    if str(result.get('c')) != '0':
        raise ProviderRejected(result.get('c'), str(result.get('m', '')))
    return result.get('d')


def upload_image(path):
    path = Path(path)
    credential = api('GET', '/asset/v1/token')
    token, domain = credential['ousToken'], credential['globalDomain'].rstrip('/')
    data = path.read_bytes()
    if len(data) > int(credential.get('blockSize') or 1048576):
        raise ValueError(f'Input image exceeds upload block size: {path.name}; encode a JPEG input first.')
    boundary = '----beforestep' + uuid.uuid4().hex
    content_type = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="md5"\r\n\r\n'
            f'{hashlib.md5(data).hexdigest()}\r\n--{boundary}\r\n'
            f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
            f'Content-Type: {content_type}\r\n\r\n').encode() + data + f'\r\n--{boundary}--\r\n'.encode()
    request = urllib.request.Request(domain + '/ous/api/v2/single/upload', data=body, method='POST',
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}', 'ous-token-v2': token})
    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.load(response)
    if str(result.get('c')) != '0':
        raise RuntimeError('Asset upload rejected')
    payload = result.get('d') or {}
    if isinstance(payload, dict):
        for field in ('url', 'fileUrl', 'accessUrl', 'downloadUrl'):
            if payload.get(field): return payload[field]
    task = payload.get('obsTaskId') or payload.get('taskId') or payload.get('taskid') or payload.get('task_id') or payload.get('id')
    if not task:
        raise RuntimeError(f'Upload response has no task identity; data fields={list(payload) if isinstance(payload, dict) else type(payload).__name__}')
    for _ in range(60):
        request = urllib.request.Request(domain + f'/ous/api/v2/upload/status?obsTaskId={task}',
                                         headers={'ous-token-v2': token})
        with urllib.request.urlopen(request, timeout=60) as response:
            status = json.load(response).get('d') or {}
        if str(status.get('status')) == '5':
            for field in ('url', 'fileUrl', 'accessUrl', 'downloadUrl'):
                if status.get(field): return status[field]
            for field in ('url', 'fileUrl'):
                if (status.get('fileInfo') or {}).get(field): return status['fileInfo'][field]
            raise RuntimeError('Upload complete without asset URL')
        time.sleep(2)
    raise TimeoutError('Asset upload did not complete')


def request_identity(request, item):
    paths = item.get('paths') or [item['path']]
    payload = {'sample_id': item['id'], 'mode': request['mode'],
               'version': request.get('version', 'G1-Turbo'),
               'faceCount': request.get('faceCount', 30000),
               'input_sha256': [sha(ROOT / p) for p in paths]}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def submit(request, item):
    identity = request_identity(request, item)
    path = LEDGER / 'tasks' / f'{identity}.json'
    if path.exists():
        record = json.loads(path.read_text())
        if record.get('task_id') or record.get('status') == 'uncertain':
            return record
    paths = item.get('paths') or [item['path']]
    urls = []
    for p in paths:
        cached = LEDGER / 'uploads' / (sha(ROOT / p) + '.json')
        if cached.exists():
            url = json.loads(cached.read_text())['url']
        else:
            url = upload_image(ROOT / p)
            atomic_json(cached, {'url': url, 'created_at': time.time()})
        urls.append(url)
    record = {'id': item['id'], 'identity': identity, 'status': 'uncertain',
              'inputs': paths, 'input_sha256': [sha(ROOT / p) for p in paths],
              'submitted_at': time.time(), 'task_id': None, 'api_field': request['mode'],
              'n_images': len(paths)}
    # A lost create response must never be silently retried.
    atomic_json(path, record)
    body = {'version': request.get('version', 'G1-Turbo'),
            'faceCount': request.get('faceCount', 30000), 'aiPredictSize': True,
            request['mode']: urls if request['mode'] == 'imgs' else urls[0]}
    try:
        result = api('POST', '/lux3d/v1/generate/img-to-3d/task/create', body, timeout=120)
    except ProviderRejected as error:
        record.update(status='not_submitted', rejection_code=error.code)
        atomic_json(path, record)
        raise
    record['task_id'] = result['taskId'] if isinstance(result, dict) else int(result)
    record['status'] = 'pending'
    atomic_json(path, record)
    print(json.dumps({'sample': item['id'], 'task_id': record['task_id'], 'status': 'pending'}), flush=True)
    return record


def fetch_glb(task, record):
    urls = [o['content'] for o in task.get('outputs', []) if isinstance(o, dict) and o.get('content')]
    if not urls:
        urls = task.get('resultUrls') or task.get('urls') or []
    destination = ROOT / 'assets/candidates' / str(record['task_id'])
    destination.mkdir(parents=True, exist_ok=True)
    for index, url in enumerate(urls):
        download = LEDGER / 'downloads' / f'{record["task_id"]}_{index}'
        download.parent.mkdir(parents=True, exist_ok=True)
        partial = download.with_suffix('.part')
        with urllib.request.urlopen(url, timeout=300) as response, partial.open('wb') as f:
            expected = response.headers.get('Content-Length')
            received = 0
            while block := response.read(1 << 20):
                f.write(block)
                received += len(block)
            f.flush(); os.fsync(f.fileno())
        if expected and received != int(expected):
            raise RuntimeError('Incomplete asset download; resume the existing task')
        partial.replace(download)
        glb = destination / 'tex_mesh.glb'
        if zipfile.is_zipfile(download):
            with zipfile.ZipFile(download) as archive:
                candidates = [n for n in archive.namelist() if n.lower().endswith('.glb')]
                candidates.sort(key=lambda n: (not n.endswith('tex_mesh.glb'), n))
                if candidates: glb.write_bytes(archive.read(candidates[0]))
        elif download.read_bytes()[:4] == b'glTF':
            download.replace(glb)
        elif download.open('rb').read(4) == b'PK\x03\x04':
            raise RuntimeError('Truncated asset archive; resume the existing task')
        if glb.is_file():
            if glb.read_bytes()[:4] != b'glTF': raise ValueError('Downloaded asset is not a GLB')
            return str(glb.relative_to(ROOT)), sha(glb)
    raise RuntimeError('Successful task has no downloadable GLB')


def poll(record, timeout=3600):
    if record.get('status') in ('ok', 'failed', 'uncertain'):
        return record
    path = LEDGER / 'tasks' / f'{record["identity"]}.json'
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        task = api('GET', f'/lux3d/v1/generate/task/get?taskid={record["task_id"]}')
        status = task.get('status')
        if status in (3, 'success', 'SUCCESS'):
            try:
                record['glb'], record['glb_sha256'] = fetch_glb(task, record)
            except (RuntimeError, OSError, ValueError, zipfile.BadZipFile):
                # Provider success is durable even when transport is incomplete.
                # Persist a retryable state without storing signed URLs or secrets.
                record.update(status='download_pending', last_download_error_at=time.time())
                atomic_json(path, record)
                print(json.dumps({'sample': record['id'], 'task_id': record['task_id'],
                                  'status': 'download_pending'}), flush=True)
                time.sleep(10)
                continue
            record.update(status='ok', finished_at=time.time(), consumed_credits=task.get('consumedCredits'))
            atomic_json(path, record)
            print(json.dumps({'sample': record['id'], 'task_id': record['task_id'], 'status': 'ok'}), flush=True)
            return record
        if status in (4, -1, 'failed', 'FAILED'):
            record.update(status='failed', finished_at=time.time(), consumed_credits=task.get('consumedCredits'))
            atomic_json(path, record)
            return record
        time.sleep(10)
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(prog='beforestep generate')
    parser.add_argument('--request', required=True)
    parser.add_argument('--env-file')
    parser.add_argument('--submit', action='store_true', help='Explicitly create missing paid tasks')
    parser.add_argument('--wait', action='store_true')
    parser.add_argument('--timeout', type=float, default=3600)
    args = parser.parse_args(argv)
    load_credentials(args.env_file)
    request_path = ROOT / args.request
    request = json.loads(request_path.read_text())
    records = []
    for item in request['items']:
        identity = request_identity(request, item)
        ledger = LEDGER / 'tasks' / f'{identity}.json'
        existing = json.loads(ledger.read_text()) if ledger.is_file() else None
        if existing and existing.get('status') != 'not_submitted':
            records.append(existing)
        elif args.submit:
            deadline = time.monotonic() + args.timeout
            while True:
                try:
                    records.append(submit(request, item))
                    break
                except ProviderRejected as error:
                    if error.code != 'GENERATION_CONCURRENCY_LIMIT_EXCEEDED' or not args.wait or time.monotonic() > deadline:
                        raise
                    print(json.dumps({'sample': item['id'], 'status': 'waiting_for_provider_slot'}), flush=True)
                    time.sleep(10)
        else:
            raise RuntimeError(f'Missing task {item["id"]}; use --submit to create it')
    if args.wait:
        with ThreadPoolExecutor(max_workers=4) as pool:
            records = list(pool.map(lambda r: poll(r, args.timeout), records))
    atomic_json(request_path.parent / 'lux_result.json', {'schema': 'beforestep-lux-result/v1', 'tasks': records})
    print(json.dumps({'tasks': len(records), 'ok': sum(r['status'] == 'ok' for r in records),
                      'pending': sum(r['status'] in ('pending', 'download_pending', 'uncertain') for r in records)}), flush=True)
