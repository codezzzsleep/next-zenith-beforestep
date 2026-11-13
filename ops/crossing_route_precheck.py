"""Run one recoverable, zero-paid gate precheck; never run a terminal identity."""
import argparse,json,sys,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
import numpy as np
import trimesh
from beforestep import scene as S
from beforestep.navigation import map as N
from experimental.crossing.runtime import write,Record,transition,stance_array,STANCE
from experimental.crossing.route.world import build,make,footprint,ROUTE,EVIDENCE
from experimental.crossing.route.execution import wheel_trial,leg_segment,first_segment,hashes

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--near',type=float,default=9.);ap.add_argument('--seed',type=int,default=22001)
    ap.add_argument('--check',choices=['contour','wheel','leg','detour'],required=True)
    ap.add_argument('--stance',choices=['fixed','high'],default='fixed');ap.add_argument('--position',choices=['center','left','right'],default='center')
    a=ap.parse_args();scene=build(a.near,a.seed)
    tag=a.check+(f'-{a.stance}-{a.position}' if a.check=='wheel' else '')
    folder=ROUTE/scene['name']/'prechecks'/scene['attempt']/tag
    if (folder/'result.json').exists():print('Terminal identity exists; skipped');sys.exit(0)
    folder.mkdir(parents=True,exist_ok=True);write(folder/'process.json',{'status':'运行中','pid':os.getpid(),'arguments':vars(a)})
    if a.check=='contour':
        S.configure(scene['base_scene']);occ=N.prior_nogo().copy()
        for p in scene['mesh_paths']:occ|=footprint(trimesh.load(ROOT/p,force='mesh',process=False))
        path=N.plan(occ,scene['staging_xy'],scene['goal'])
        np.save(folder/'occupancy.npy',occ)
        result={'check':'gate_blocks','passed':path is None,'has_path':path is not None,'path':path,
            'start':scene['staging_xy'],'goal':scene['goal'],'planner':'unchanged beforestep.navigation.map.plan','grid_resolution_m':N.RES,
            'contour':'true MuJoCo convex collision footprints; no imagined shape','new_lux_tasks':0}
    elif a.check=='detour':
        e,summary,out=first_segment(scene,folder,'imagination','truth',max_looks=2)
        result={'check':'original_detour','passed':summary['result']=='arrived','summary':summary,
            'final_hashes':hashes(e),'truth_diagnostic':True,'new_lux_tasks':0}
    else:
        e,rb,meta,index=make(scene,staging=True)
        if a.check=='wheel':
            lateral={'center':0.,'left':scene['gap_m']/2-.25,'right':-scene['gap_m']/2+.25}[a.position]
            S.place(e,scene['staging_xy'][0],lateral)
            result=wheel_trial(e,scene,index,folder,a.stance,lateral)
            result.update(check='wheel_cannot_cross',passed=not result['arrived'],position=a.position,new_lux_tasks=0)
        else:
            result=leg_segment(e,scene,rb,index,folder,truth=True)
            result.update(check='legs_cross',passed=result['status']=='clean_pass',new_lux_tasks=0)
    write(folder/'result.json',result)
    write(folder/'process.json',{'status':'终态','arguments':vars(a),'output':str(folder.relative_to(ROOT))})
    print(json.dumps({'check':tag,'passed':result['passed'],'status':result.get('status'), 'folder':str(folder.relative_to(ROOT))},ensure_ascii=False),flush=True)
