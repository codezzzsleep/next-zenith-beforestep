"""Compare the normal editable sandbox's first-eye qualitative plans to runs.

The sandbox computes its own geometric shadow estimate, never substitutes the
saved RGB-D map. Every mismatch is reported. A separate exact-map check verifies
the numerical distance transform and the browser port of the route planner.
"""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np

from beforestep import scene as S
from beforestep.navigation import map as N

ROOT = S.ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='outputs/qa/r2/sandbox-consistency.json')
    args = parser.parse_args()
    data = json.loads((ROOT / 'site/data/sandbox.json').read_text())
    cases = []
    for preset in data['presets']:
        S.configure(preset['id'])
        level = next(r for r in json.loads((ROOT / 'site/data/levels.json').read_text())['levels'] if r['id'] == preset['id'])
        actual = ROOT / level['runs']['imagination']['source']
        from beforestep.evaluation import truth_footprints
        truth = np.logical_or.reduce(list(truth_footprints(actual).values()))
        expected = {}
        exact = []
        for key, run in level['runs'].items():
            events = [json.loads(line) for line in (ROOT / run['source'] / 'events.jsonl').read_text().splitlines()]
            first = next(e for e in events if e['kind'] == 'plan' and e['look'] == 1)
            path = first['path']
            margin = N.path_clearance(path, preset['observation']['pose'][:2], N.clearance(truth))['drive_margin_m'] if path else None
            expected[key] = {'route': path is not None, 'intrudes': margin < 0 if margin is not None else None}
        # The optimistic saved first map is sufficient to test the shared planner.
        state = np.array(preset['observation']['map']['values']).reshape(N.GX.shape)
        occ = N.occupancy(state, 'optimistic')
        start = preset['observation']['pose'][:2]
        path = N.plan(occ, start, preset['definition']['goal'])
        exact = {'occupancy': occ.ravel().astype(int).tolist(), 'clearance': N.clearance(occ).ravel().tolist(),
                 'start': start, 'goal': preset['definition']['goal'], 'route': path is not None}
        cases.append({'id': preset['id'], 'definition': preset['definition'], 'expected': expected, 'exact': exact})
    with tempfile.TemporaryDirectory() as tmp:
        planner = Path(tmp) / 'planner.mjs'; planner.write_bytes((ROOT / 'site/sandbox-planner.js').read_bytes())
        input_path = Path(tmp) / 'input.json'; input_path.write_text(json.dumps({'data': data, 'cases': cases}))
        script = Path(tmp) / 'check.mjs'
        script.write_text("""import fs from 'node:fs';
import {observe,occupancies,plan,intrusion,clearance} from './planner.mjs';
const input=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),rows=[];
for(const c of input.cases){const obs=observe(c.definition,input.data.library),occ=occupancies(c.definition,obs),actual={};
 for(const key of ['optimistic','conservative','imagination']){const p=plan(occ[key],c.definition.first_stop,c.definition.goal,input.data.drive_radius,input.data.turn_radius);actual[key]={route:p!==null,intrudes:p?intrusion(p,c.definition.first_stop,obs.truth,input.data.robot.half_wid)>0:null};}
 const field=clearance(c.exact.occupancy),error=Math.max(...field.map((v,i)=>Math.abs(v-c.exact.clearance[i])));
 const p=plan(c.exact.occupancy,c.exact.start,c.exact.goal,input.data.drive_radius,input.data.turn_radius);
 rows.push({scene:c.id,expected:c.expected,sandbox:actual,consistent:Object.keys(actual).every(k=>actual[k].route===c.expected[k].route&&actual[k].intrudes===c.expected[k].intrudes),exact_map_clearance_max_error_m:error,exact_map_route_agrees:(p!==null)===c.exact.route});}
console.log(JSON.stringify(rows));""")
        result = subprocess.run(['node', str(script), str(input_path)], capture_output=True, text=True, check=True)
        rows = json.loads(result.stdout)
    assert all(r['exact_map_clearance_max_error_m'] < 1e-10 and r['exact_map_route_agrees'] for r in rows)
    report = {'schema': 'beforestep-sandbox-consistency/v1', 'scene_count': len(rows),
              'consistent_scenes': sum(r['consistent'] for r in rows),
              'inconsistent_scenes': [r['scene'] for r in rows if not r['consistent']], 'scenes': rows,
              'development_anchor_only': data['development_anchor_only'],
              'scope': 'Normal editable geometric first-eye approximation compared with actual first plan. Exact-map numerical port check is separate.'}
    out = ROOT / args.out; out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ('scene_count', 'consistent_scenes', 'inconsistent_scenes')}))


if __name__ == '__main__':
    main()
