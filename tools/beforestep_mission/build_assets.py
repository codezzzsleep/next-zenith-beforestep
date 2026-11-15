"""Package the original R1 world, real Lux worlds and observations for one mission.

This reads frozen evidence, uses the source scene composer and appends a visible
calibration threshold. No Lux request, training or frozen experiment is executed.
"""
from pathlib import Path
import argparse, copy, gzip, hashlib, io, json, sys, tarfile
import xml.etree.ElementTree as ET
import numpy as np
import trimesh


def digest(data):
    return hashlib.sha256(data).hexdigest()


def build(repo, output, cache):
    sys.path.insert(0, str(repo / 'src'))
    from beforestep import scene as S
    from beforestep.navigation import map as N
    from beforestep.simulation.environment import WheelLegEnv
    S.configure('stress_v8')
    cache.mkdir(parents=True, exist_ok=True)
    S.LW.CACHE = cache / 'meshes'
    S.LW.CACHE.mkdir(exist_ok=True)
    spec, _, _ = S.scene_spec(cache / 'r1')
    spec['_hfield_dir'] = str(cache / 'heightfields')
    env = object.__new__(WheelLegEnv)
    env.spec = spec
    env.asset_root = repo / 'assets/processed'
    xml, _ = env._compose()
    base = ET.fromstring(xml)
    option = base.find('option')
    option.set('timestep', '0.002')
    option.set('iterations', '30')
    # The high-rock region is the original R1 world; this addition is known terrain.
    gate = {'near': 9.1, 'far': 9.2, 'high': .12}
    ET.SubElement(base.find('worldbody'), 'geom', name='mission_gate', type='box',
                  pos='9.15 0 .06', size='.05 1.4 .06', friction='.9 .02 .001',
                  rgba='.67 .59 .42 1')
    buffers, display, sources = {}, {}, {}
    source_xml = ET.tostring(base, encoding='utf-8')

    def add_mesh(path):
        path = Path(path)
        data = path.read_bytes()
        key = digest(data)
        filename = key[:24] + path.suffix.lower()
        buffers['assets/' + filename] = data
        name = 'm_' + key[:24]
        if name not in display:
            mesh = trimesh.load(path, force='mesh', process=False)
            vertices = np.asarray(mesh.vertices)
            pitch = .006 if str(path).endswith(('base_0.obj', 'wheel.stl')) or 'go2w' in str(path) else .018
            cells = np.floor(vertices / pitch).astype(np.int64)
            _, inv = np.unique(cells, axis=0, return_inverse=True)
            counts = np.bincount(inv)
            reduced = np.column_stack([np.bincount(inv, weights=vertices[:, k]) / counts for k in range(3)])
            faces = inv[np.asarray(mesh.faces)]
            faces = faces[(faces[:, 0] != faces[:, 1]) & (faces[:, 1] != faces[:, 2]) & (faces[:, 2] != faces[:, 0])]
            _, indices = np.unique(np.sort(faces, axis=1), axis=0, return_index=True)
            faces = faces[np.sort(indices)]
            display[name] = {'positions': reduced.ravel().tolist(), 'indices': faces.ravel().tolist(),
                             'display_only': True, 'original_faces': len(mesh.faces)}
        rel = str(path.relative_to(repo)) if path.is_relative_to(repo) else 'deterministic scene-composer derivative'
        sources['assets/' + filename] = {'source': rel, 'sha256': key, 'bytes': len(data)}
        return name, filename

    def canonical(root):
        compiler = root.find('compiler')
        old_dir = Path(compiler.get('meshdir'))
        compiler.set('meshdir', '/play/assets')
        compiler.set('texturedir', '/play/assets')
        mapping = {}
        for asset in root.find('asset'):
            file = asset.get('file')
            if not file:
                continue
            path = Path(file) if Path(file).is_absolute() else old_dir / file
            if asset.tag == 'mesh':
                old_name = asset.get('name') or Path(file).stem
                name, filename = add_mesh(path)
                mapping[old_name] = name
                asset.set('name', name)
                asset.set('file', filename)
            else:
                data = path.read_bytes()
                filename = digest(data)[:24] + path.suffix.lower()
                buffers['assets/' + filename] = data
                asset.set('file', '/play/assets/' + filename)
        # Original walls can reuse one scan at different scales; retain scale variants.
        aliases = {}
        seen = set()
        for asset in list(root.find('asset')):
            if asset.tag != 'mesh':
                continue
            key = (asset.get('name'), asset.get('scale', '1 1 1'))
            if key in seen:
                root.find('asset').remove(asset)
            else:
                seen.add(key)
        for geom in root.iter('geom'):
            if geom.get('mesh') in mapping:
                geom.set('mesh', mapping[geom.get('mesh')])
        return root

    base = canonical(base)
    buffers['truth.xml'] = ET.tostring(base, encoding='utf-8')
    gallery = json.loads((repo / 'site/data/gallery.json').read_text())
    r1 = repo / 'evidence/reviews/beforestep_r1/lux/original_b'
    candidates = []
    thresholds = None
    for item in gallery['models']:
        context = next((c for c in item['contexts'] if c['run'] == 'evidence/reviews/beforestep_r1/lux/original_b'), None)
        if not context:
            continue
        target = context['target']
        evidence = r1 / 'looks/look1' / target / 'decide'
        decision = json.loads((evidence / 'target_decision.json').read_text())
        thresholds = decision['thresholds']
        metrics = context['metrics']
        footprint = evidence / f"footprint_{item['sample']}.npy"
        mask = np.load(footprint).astype(np.uint8).ravel().tolist() if footprint.exists() else [0] * (N.NX * N.NY)
        c = {'task_id': item['task_id'], 'sample': item['sample'], 'target': target,
             'input': item['input'], 'display_model': item['model'],
             'original_model': f"assets/candidates/{item['task_id']}/tex_mesh.glb",
             'original_sha256': item['source_sha256'], 'registration': context['world_from_generated'],
             'recorded_admitted': context['admitted'], 'reason': context['reason'],
             'metrics': {k: metrics.get(k) for k in ['scale_ratio', 'hidden_frac', 'shell_contact', 'free_intrusion_frac', 'contour_iou']},
             'footprint': mask, 'source_decision': context['source_decision']}
        if context['admitted']:
            world = evidence / f"world_{item['sample']}.obj"
            c['world_mesh'], c['world_file'] = add_mesh(world)
            c['world_source'] = str(world.relative_to(repo))
            c['world_sha256'] = digest(world.read_bytes())
        candidates.append(c)
    groups = [[c for c in candidates if c['target'] == t and c['recorded_admitted']] for t in ['T1', 'T2']]
    worlds = []
    for a in groups[0]:
        for b in groups[1]:
            root = copy.deepcopy(base)
            assets = root.find('asset')
            body = root.find('worldbody')
            for index, candidate in enumerate([a, b]):
                old = body.find(f"body[@name='obstacle{index}']")
                body.remove(old)
                ET.SubElement(assets, 'mesh', name=candidate['world_mesh'], file=candidate['world_file'])
                new = ET.SubElement(body, 'body', name=f'obstacle{index}', pos='0 0 0')
                ET.SubElement(new, 'geom', type='mesh', mesh=candidate['world_mesh'],
                              name='candidate_' + candidate['target'], rgba='.38 .76 .58 1',
                              friction='.9 .02 .001', contype='1', conaffinity='1')
            name = f"world-{a['task_id']}-{b['task_id']}.xml"
            buffers[name] = ET.tostring(root, encoding='utf-8')
            worlds.append({'tasks': [a['task_id'], b['task_id']], 'file': name})
    grid = {'x0': N.X0, 'y0': N.Y0, 'res': N.RES, 'nx': N.NX, 'ny': N.NY,
            'r_drive': N.R_DRIVE, 'r_turn': N.R_TURN, 'node_step': .1, 'max_edge': 2.6}
    data = {'schema': 'beforestep-mission/v1', 'scope': 'Independent interactive mission: original R1 high-rock world + visible calibration threshold, using retained real inputs and Lux3D returns.',
            'start': [2.3, -.5], 'dock': [8.45, 0], 'goal': [10.6, 0], 'gate': gate,
            'grid': grid, 'observation_state': np.load(r1/'decision/look1_state.npy').ravel().tolist(),
            'known_nogo': N.prior_nogo().astype(np.uint8).ravel().tolist(),
            'thresholds': thresholds, 'candidates': candidates, 'worlds': worlds,
            'source_scene': 'config/scenes/stress_v8.json', 'source_scene_sha256': digest((repo/'config/scenes/stress_v8.json').read_bytes()),
            'source_state': 'evidence/reviews/beforestep_r1/lux/original_b/decision/look1_state.npy',
            'source_state_sha256': digest((r1/'decision/look1_state.npy').read_bytes()),
            'original_checks_reused': True, 'new_generation_requests': 0,
            'recorded_observations_reused': True, 'game_results_are_research_results': False}
    output.mkdir(parents=True, exist_ok=True)
    (output/'mission.json.gz').write_bytes(gzip.compress(json.dumps(data, separators=(',', ':')).encode(), mtime=0))
    (output/'display.json.gz').write_bytes(gzip.compress(json.dumps(display, separators=(',', ':')).encode(), mtime=0))
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode='w', format=tarfile.USTAR_FORMAT) as tar:
        for name, blob in buffers.items():
            info = tarfile.TarInfo(name); info.size = len(blob); info.mode = 0o644; info.mtime = 0
            tar.addfile(info, io.BytesIO(blob))
    packed = gzip.compress(raw.getvalue(), compresslevel=9, mtime=0)
    (output/'worlds.tar.gz').write_bytes(packed)
    manifest = {'schema': 'beforestep-mission-assets/v1', 'files': sources,
                'bundle_sha256': digest(packed), 'bundle_bytes': len(packed),
                'sources': ['config/scenes/stress_v8.json', 'src/beforestep/scene.py', 'evidence/reviews/beforestep_r1/lux/original_b'],
                'candidate_count': len(candidates), 'admitted_count': len(groups[0]) + len(groups[1]), 'world_count': len(worlds),
                'robot_physics_unchanged': True, 'display_lod_only': True,
                'appendix': 'Visible 12cm x 10cm threshold is an independent mission addition; original R1 and formal scores remain frozen.'}
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'files': len(buffers), 'bundle_bytes': len(packed), 'candidates': len(candidates), 'worlds': len(worlds)}))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--cache', type=Path, required=True)
    args = p.parse_args()
    build(args.source, args.output, args.cache)
