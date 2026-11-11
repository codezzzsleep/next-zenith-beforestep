"""Verify the delivered web bundle against real tasks and frozen source bytes."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import trimesh

from web_glb import parse, LIMIT

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main():
    index = read('evidence/web-assets/index.json')
    indexed = {item['path']: item for item in index['items']}
    assert len(indexed) == len(index['items'])
    for item in indexed.values():
        assert sha(item['path']) == item['sha256'], item['path']
        assert (ROOT / item['path']).stat().st_size == item['bytes']
        for source in item['sources']:
            assert sha(source['path']) == source['sha256'], source['path']
    registry = read(index['models'])
    assert not registry['not_prepared'] and not registry['missing_inputs']
    counts = Counter()
    for model in registry['models']:
        assert model['path'] in indexed and model['bytes'] <= LIMIT
        assert sha(model['source']) == model['source_sha256']
        assert sha(model['path']) == model['sha256']
        raw_doc, raw_bin = parse((ROOT / model['source']).read_bytes())
        web_doc, web_bin = parse((ROOT / model['path']).read_bytes())
        representation = model['representation']
        if representation.startswith('original_geometry_buffers_exact'):
            for field in ('accessors', 'meshes', 'nodes', 'scenes'):
                assert raw_doc.get(field) == web_doc.get(field), (model['task_id'], field)
            images = {image['bufferView'] for image in raw_doc.get('images', [])}
            for i, view in enumerate(raw_doc['bufferViews']):
                if i in images:
                    continue
                other = web_doc['bufferViews'][i]
                before = raw_bin[view.get('byteOffset', 0):view.get('byteOffset', 0)+view['byteLength']]
                after = web_bin[other.get('byteOffset', 0):other.get('byteOffset', 0)+other['byteLength']]
                assert before == after, (model['task_id'], i)
        else:
            assert representation.startswith('triangle_positions_exact_float32')
            original = trimesh.load(ROOT / model['source'], force='mesh', process=False)
            preview = trimesh.load(ROOT / model['path'], force='mesh', process=False)
            assert np.array_equal(np.asarray(original.triangles, dtype=np.float32),
                                  np.asarray(preview.triangles, dtype=np.float32))
        for source, digest, web_path in zip(model['inputs'], model['input_sha256'], model['web_inputs'], strict=True):
            assert sha(source) == digest == sha(web_path)
        counts[representation] += 1
    anchor = read(index['anchor'])
    contexts = read(index['registrations'])['contexts']
    anchor_contexts = anchor['registration_contexts']
    generated = [row for row in anchor['generated'] if row['provider_status'] == 'ok']
    assert len(generated) == index['anchor_successful_models']
    assert {r['task_id'] for r in generated} == {r['task_id'] for r in anchor_contexts}
    assert all(r['registration_available'] for r in anchor_contexts)
    for row in contexts:
        assert sha(row['source_decision']) == row['source_decision_sha256']
        decision = read(row['source_decision'])
        candidate = next(c for c in decision['candidates'] if c['id'] == row['sample'])
        assert row['metrics'] == candidate and row['admitted'] == candidate['admitted']
        assert row['reason']
        if row['registration_available']:
            assert np.array_equal(row['local_from_generated'], candidate['M'])
            frame = row['local_frame']
            c, s = np.cos(frame['yaw0']), np.sin(frame['yaw0'])
            world = np.array([[c,-s,0,frame['x0']],[s,c,0,frame['y0']],[0,0,1,0],[0,0,0,1.]])
            assert np.array_equal(row['world_from_generated'], world @ np.asarray(candidate['M']))
    for policy, run in anchor['runs'].items():
        assert run['trajectory_json'] in indexed and run['trajectory_npz'] in indexed
        exported = read(run['trajectory_json'])
        with np.load(ROOT / run['trajectory_npz']) as original:
            assert np.array_equal(exported['t'], original['t'])
            assert np.array_equal(exported['qpos'], original['qpos'])
        assert exported['summary'] == run['summary']
    for row in anchor['observations']:
        assert all(row[key] in indexed for key in ('rgb', 'depth', 'dark', 'dark_png', 'depth_mm_png'))
    assert len(anchor['runs']) == 4 and len(anchor['rehearsals']) == 12
    for row in anchor['rehearsals']:
        exported = read(row['trajectory_json'])
        with np.load(ROOT / row['trajectory_npz']) as original:
            assert np.array_equal(exported['t'], original['t'])
            assert np.array_equal(exported['qpos'], original['qpos'])
    for row in anchor['truth']:
        assert row['bytes'] <= LIMIT and sha(row['source_obj']) == row['source_obj_sha256']
    report = {'passed': True, 'verified_at': datetime.now(timezone.utc).isoformat(),
              'indexed_files': len(indexed), 'indexed_bytes': sum(r['bytes'] for r in indexed.values()),
              'real_models': len(registry['models']), 'geometry_exact': dict(counts),
              'largest_web_glb_bytes': max(row['bytes'] for row in registry['models']),
              'anchor_generated': len(anchor['generated']), 'anchor_successful': len(generated),
              'anchor_admitted': sum(r['admitted'] for r in anchor_contexts),
              'anchor_rejected': sum(not r['admitted'] for r in anchor_contexts),
              'anchor_provider_failures': sum(r['provider_status'] != 'ok' for r in anchor['generated']),
              'registration_contexts': len(contexts), 'anchor_observations': len(anchor['observations']),
              'four_full_trajectories': True, 'twelve_full_rehearsal_trajectories': True,
              'truth_models': len(anchor['truth']), 'new_paid_tasks': 0,
              'index_sha256': sha('evidence/web-assets/index.json')}
    path = ROOT / 'evidence/award/acceptance/web-assets.json'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
