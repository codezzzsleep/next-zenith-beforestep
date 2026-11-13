"""Check the saved first-segment handoff without rerunning its terminal route."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from beforestep import scene as S
from experimental.crossing.runtime import write
from experimental.crossing.route.world import ROUTE,EVIDENCE,register
from experimental.crossing.route.execution import hashes,leg_segment

if __name__=='__main__':
    scene=json.loads((EVIDENCE/'scene-stress_v8_gate.json').read_text());name=scene['name']
    folder=ROUTE/name/'connection-precheck'
    if (folder/'result.json').exists():print('Terminal connection check exists; skipped');sys.exit(0)
    source=ROUTE/name/'prechecks'/scene['attempt']/'detour'
    state=json.loads((source/'segment1/physical-state.json').read_text())
    register(scene);S.configure(name)
    spec,rb,meta=S.scene_spec(source/'scene')
    e=S.make_env(spec);e.restore_state(state,strict=True,mode='same_scene')
    before=hashes(e);after=hashes(e)
    handoff={'source':str((source/'segment1/physical-state.json').relative_to(ROOT)),
        'restoration':'Complete env-state/v2 restored at initialization into the exact saved first-segment world',
        'before':before,'after':after,'equal':before==after,'first_segment_not_rerun':True}
    write(folder/'handoff.json',handoff)
    result=leg_segment(e,scene,rb,spec['route_threshold_index'],folder/'observed-leg-segment')
    report={'schema':'beforestep-route-connection-precheck/v1','handoff':handoff,'second_segment':result,
        'passed':handoff['equal'] and result['arrived'],'diagnostic_only':True,'new_lux_tasks':0}
    write(folder/'result.json',report);write(EVIDENCE/'connection-precheck.json',report)
    print(json.dumps({'passed':report['passed'],'status':result['status']},ensure_ascii=False),flush=True)
