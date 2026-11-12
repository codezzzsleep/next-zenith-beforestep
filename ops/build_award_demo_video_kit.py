"""Add a separate supplemental-demo source kit without replacing the original."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    result_path = ROOT / 'evidence/award/demo/result.json'
    result = json.loads(result_path.read_text())
    scene = result['scene']
    manifest_path = ROOT / f'evidence/award/demo/scenes/{scene}/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    sources = {row['path']: row for row in manifest['files']}
    runs = []
    for policy, record in result['runs'].items():
        if not record.get('summary'):
            runs.append({'policy': policy, 'completed': False})
            continue
        prefix = record['run'] + '/'
        files = [row for path, row in sources.items() if path.startswith(prefix)
                 and (path.endswith(('traj.npz', 'summary.json', 'run_identity.json', 'events.jsonl'))
                      or '/looks/' in path and Path(path).suffix in ('.png', '.npy', '.json'))]
        assert any(row['path'] == prefix + 'traj.npz' and row.get('public_object') for row in files)
        runs.append({'policy': policy, 'completed': True, 'run': record['run'],
                     'run_id': record['run_id'], 'summary': record['summary'], 'files': files})
    output = ROOT / 'evidence/video/award/demo'
    output.mkdir(parents=True, exist_ok=True)
    data = {'schema': 'beforestep-award-supplemental-video-source-kit/v1',
            'scene': scene, 'label': result['label'], 'runs': runs,
            'result': str(result_path.relative_to(ROOT)),
            'result_sha256': hashlib.sha256(result_path.read_bytes()).hexdigest(),
            'manifest': str(manifest_path.relative_to(ROOT)),
            'manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            'complete_archive': manifest['complete_archive'],
            'original_kit': 'evidence/video/award/index.json',
            'recorded_workflow': 'site/award-demo.html', 'video_encoded': False,
            'renderer': 'Project lead; the agent supplies real records and source identities.'}
    (output / 'index.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    (output / 'README.md').write_text(
        '# 固定补充演示的视频源\n\n' + result['label'] + '。\n\n'
        '这个目录单独追加本次真实六栏运行，不替换原锚点视频包，不参与已知/留出结论。'
        '完整观察、自检、预演、执行、失败和反事实文件的 SHA 在公开清单中；'
        'public_object 为原字节的 gzip 存储路径。完整原始模型和中断产物保留在外部 tar。\n\n'
        '[来源索引](index.json) · [逐步回放](../../../../site/award-demo.html) · '
        '[原视频包](../index.json)。负责人使用真实记录制作成片，本脚本没有渲染或编码视频。\n')
    print(json.dumps({'scene': scene, 'runs': len(runs), 'video_encoded': False}))


if __name__ == '__main__':
    main()
