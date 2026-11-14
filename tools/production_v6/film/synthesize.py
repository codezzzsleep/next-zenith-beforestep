"""MiniMax narration with durable request records and no stored credentials."""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
import hashlib
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import load_state, resolve, OUT, save, sha, status

p = argparse.ArgumentParser()
p.add_argument('--only')
args = p.parse_args()
work = OUT / 'film'
audio = work / 'audio'
audio.mkdir(exist_ok=True)
env = dict(os.environ)
credential_file = Path(os.environ.get('BEFORESTEP_ROOT', str(Path(__file__).resolve().parents[3]))) / '.env'
if credential_file.exists():
    for line in credential_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line: continue
        k, v = line.removeprefix('export ').split('=', 1)
        env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
key = env.get('MINIMAX_API_KEY', '').strip()
assert key, 'MiniMax key is not configured; no request submitted'
endpoint = env.get('MINIMAX_API_BASE_URL', env.get('MINIMAX_BASE_URL', 'https://api.minimaxi.com')).rstrip('/')
if not endpoint.endswith('/v1/t2a_v2'): endpoint += '/v1/t2a_v2'
model = env.get('MINIMAX_TTS_MODEL', 'speech-2.8-hd')
voice = env.get('MINIMAX_VOICE_ID', 'Chinese (Mandarin)_Reliable_Executive')
plan = json.loads((work / 'plan.json').read_text())
job = {'id': 'MiniMax-film-narration', 'pid': os.getpid(), 'status': 'running', 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'credential_location': str(credential_file), 'endpoint': endpoint, 'model': model, 'voice_id': voice,
       'completed': [], 'current': None, 'live_jobs': [], 'credentials_stored': False}
save(work / 'tts-job.json', job)
state = load_state(work / 'state.json')
state.update(status='MiniMax_narration_running', live_jobs=[{'id': job['id'], 'pid': os.getpid(), 'ledger': str(work / 'tts-job.json')}])
save(work / 'state.json', state)
status('MiniMax中文配音启动', work / 'tts-job.json', '用户已配置凭据；逐句生成、即时保存trace与音频SHA，不保存或传输凭据至GPU')
try:
    last_request = 0.0
    for group in plan['groups']:
        for sentence in group['sentences']:
            name = sentence['id']
            if args.only and name != args.only: continue
            request = {'model': model, 'text': sentence['text'], 'stream': False, 'output_format': 'hex', 'language_boost': 'Chinese',
                       'voice_setting': {'voice_id': voice, 'speed': 1.03, 'vol': 1, 'pitch': 0},
                       'pronunciation_dict': {'tone': ['Lux3D/勒克斯三维', 'BeforeStep/Before Step']},
                       'audio_setting': {'sample_rate': 32000, 'bitrate': 128000, 'format': 'mp3', 'channel': 1}}
            data = json.dumps(request, ensure_ascii=False).encode()
            identity = hashlib.sha256(data).hexdigest()
            ledger = audio / (name + '.json')
            dest = audio / (name + '.mp3')
            if ledger.exists():
                previous = json.loads(ledger.read_text())
                assert previous['identity'] == identity, 'Narration changed; preserve the original request before creating a new one'
                if previous['status'] == 'complete' and dest.exists():
                    assert sha(dest) == previous['sha256']
                    job['completed'].append(name); save(work / 'tts-job.json', job); continue
                if previous['status'] in ['submitting', 'uncertain']:
                    raise RuntimeError('Do not repeat an uncertain TTS request: ' + name)
                if previous['status'] == 'provider_failed' and previous.get('base_resp', {}).get('status_code') == 1002:
                    # An explicit RPM rejection returned no audio. Preserve it;
                    # only this known rejection is safe to resubmit at a lower rate.
                    archive = audio / (name + '-rate-limit-' + str(time.time_ns()) + '.json')
                    save(archive, previous)
                else:
                    raise RuntimeError('Prior TTS request requires inspection: ' + name)
            row = {'id': name, 'identity': identity, 'status': 'submitting', 'request': request,
                   'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'credentials_stored': False}
            save(ledger, row)
            job['current'] = {'id': name, 'ledger': str(ledger), 'identity': identity}; save(work / 'tts-job.json', job)
            try:
                delay = 8.0 - (time.monotonic() - last_request)
                if delay > 0: time.sleep(delay)
                last_request = time.monotonic()
                http = urllib.request.Request(endpoint, data=data, headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
                response = json.loads(urllib.request.urlopen(http, timeout=60).read())
            except Exception as error:
                row.update(status='uncertain', error_type=type(error).__name__)
                save(ledger, row)
                raise RuntimeError('TTS response uncertain for ' + name + '; request not repeated') from None
            row.update(trace_id=response.get('trace_id'), base_resp=response.get('base_resp'), extra_info=response.get('extra_info'))
            if response.get('base_resp', {}).get('status_code') != 0:
                row.update(status='provider_failed'); save(ledger, row)
                raise RuntimeError('MiniMax rejected ' + name + ': ' + json.dumps(response.get('base_resp'), ensure_ascii=False))
            payload = response.get('data') or {}
            assert payload.get('audio'), 'TTS returned no audio'
            dest.write_bytes(bytes.fromhex(payload['audio']))
            probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(dest)], text=True))
            row.update(status='complete', path=str(dest), sha256=sha(dest), bytes=dest.stat().st_size,
                       duration_s=float(probe['format']['duration']), finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
            save(ledger, row)
            job['completed'].append(name); job['current'] = None; save(work / 'tts-job.json', job)
            print(name, f'{row["duration_s"]:.3f}s', 'saved', flush=True)
    job.update(status='complete', live_jobs=[], finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    save(work / 'tts-job.json', job)
    state.update(status='narration_audio_ready', live_jobs=[], next='Measure all audio and align shots/captions; compose film')
    save(work / 'state.json', state)
    status('逐句中文配音完成', work / 'tts-job.json', f'{len(job["completed"])}句音频即时落盘与trace/SHA齐；下一步按实测时长剪辑')
except BaseException as error:
    job.update(status='failed', error=str(error), live_jobs=[]); save(work / 'tts-job.json', job)
    state.update(status='narration_error_review_required', live_jobs=[], next='Inspect tts-job/audio ledger before retrying; continue visual edit preparation')
    save(work / 'state.json', state)
    raise
