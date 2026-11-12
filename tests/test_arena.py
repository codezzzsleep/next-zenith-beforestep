"""Information boundaries and rigid geometry, independent of final score."""
import unittest
import numpy as np
from experimental.arena.common import ROOT,OUT,read
from experimental.arena.capsules import transplant
from experimental.arena.llm import validate
from beforestep.navigation import map as N


class ArenaContracts(unittest.TestCase):
    def test_disjoint_seed_ranges_and_holdout_capsules(self):
        cfg=read(ROOT/'experimental/arena/parameters.json');seen=set()
        for k in ['development','train','validation','sealed','ood','fidelity']:
            r=cfg[k];s=set(range(r['seed_start'],r['seed_start']+r['count']));self.assertFalse(s&seen);seen|=s
        v1=read(ROOT/'config/training/navigation_v1.json')
        for k in ['train','validation','test','ood','physical']:
            r=v1[k];self.assertFalse(seen&set(range(r['seed_start'],r['seed_start']+r['count'])))
        lib=read(OUT/'capsules.json');held=set(lib['heldout_scenes'])
        for c in lib['capsules']:self.assertEqual(c['split']=='heldout',c['scene'] in held)

    def test_transplant_preserves_camera_and_sun_relative_geometry(self):
        c=next(c for c in read(OUT/'capsules.json')['capsules'] if c['eligible']);t=transplant(c,17,[.3,-.2])
        a=np.array(c['camera_world']['world_pos']);b=np.array(t['camera_world']['world_pos'])
        for key,p in c['truth_rocks'].items():
            q=t['truth_rocks'][key];self.assertAlmostEqual(np.linalg.norm(a[:2]-[p['x'],p['y']]),np.linalg.norm(b[:2]-[q['x'],q['y']]),places=10)
            self.assertAlmostEqual(p['yaw']+c['source_scene'].get('sun',{'azimuth_deg':35})['azimuth_deg'],q['yaw']+t['sun']['azimuth_deg'])

    def test_fixed_option_validation(self):
        with self.assertRaises(ValueError):validate({'option_id':'invented'},[{'id':'stop'}])
        with self.assertRaises(ValueError):validate({'option_id':True},[{'id':'stop'}])
        with self.assertRaises(ValueError):validate({'option_id':'stop'},[{'id':'stop'}])
        with self.assertRaises(ValueError):validate({'option_id':'stop','reason':'move','x':9},[{'id':'stop'}])
        self.assertEqual(validate({'option_id':'stop','reason':'insufficient support'},[{'id':'stop'}])['option_id'],'stop')

    def test_local_unknown_does_not_cause_premature_stop(self):
        from experimental.arena.policies import viewpoints
        from experimental.arena.numerical import plan
        folder=OUT/'prechecks/viewpoint-local-diagnostic'
        for seed in [8100004,8100038]:
            with np.load(folder/f'{seed}.npz') as a:
                card={'state':a['state'],'position':a['position'],'yaw':float(a['yaw'])}
                history=read(folder/f'{seed}.json')['observations']
                card['look_history']=[(np.array(o['position']),o['yaw']) for o in history]
                options=viewpoints(card,a['occ'])
                self.assertTrue(options,'A safe local view exists in the recorded development map')
                for option in options:
                    self.assertGreater(option['expected_new_cells'],0)
                    if option['path']:self.assertIsNotNone(plan(a['occ'],a['position'],option['position']))
        state=np.full((N.NX,N.NY),N.DARK,np.int8)
        self.assertEqual(viewpoints({'state':state,'position':np.array([2.,0.]),'yaw':0.},np.zeros_like(state,bool)),[])

    def test_registration_requires_unchanged_committed_protocol(self):
        import subprocess,tempfile
        from pathlib import Path
        from unittest.mock import patch
        from experimental.arena import registration
        from experimental.arena.common import write,sha
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);out=root/'evidence';protocol=root/'docs/arena-protocol.md'
            protocol.parent.mkdir();protocol.write_text('Registered before evaluation\n')
            parameters=root/'parameters.json';parameters.write_text('{"resolution":0.05}\n')
            subprocess.run(['git','init','-q',str(root)],check=True)
            subprocess.run(['git','add','.'],cwd=root,check=True)
            subprocess.run(['git','-c','user.name=Arena Test','-c','user.email=arena-test@example.invalid','commit','-qm','Register'],cwd=root,check=True)
            commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
            write(out/'prechecks/final.json',{'passed':True})
            record={'commit':commit,'frozen_files_sha256':{'docs/arena-protocol.md':sha(protocol),'parameters.json':sha(parameters)}}
            write(out/'protocol.json',record)
            with patch.object(registration,'ROOT',root),patch.object(registration,'OUT',out):
                self.assertEqual(registration.require_registration()['commit'],commit)
                parameters.write_text('{"resolution":0.1}\n')
                with self.assertRaises(AssertionError):registration.require_registration()
                parameters.write_text('{"resolution":0.05}\n')
                protocol.write_text('Uncommitted replacement protocol\n')
                record['frozen_files_sha256']['docs/arena-protocol.md']=sha(protocol)
                write(out/'protocol.json',record)
                with self.assertRaises(AssertionError):registration.require_registration()

    def test_llm_timeout_is_not_resubmitted_and_parse_retry_is_bounded(self):
        import json,tempfile
        from pathlib import Path
        from unittest.mock import patch
        from experimental.arena import llm
        class Response:
            status=200
            def __init__(self,content):self.content=content
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self):return json.dumps({'choices':[{'message':{'content':self.content}}]}).encode()
        class Client:
            def __init__(self,timeout=False):self.calls=0;self.timeout=timeout
            def open(self,*args,**kwargs):
                self.calls+=1
                if self.timeout:raise TimeoutError('Uncertain submission')
                return Response('{truncated' if self.calls==1 else json.dumps({'option_id':'stop','reason':'insufficient observation'}))
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);env=root/'config.env'
            env.write_text('base_URL=https://example.invalid/v1\nAI_API_key=unit-test-placeholder\nmodel=unit-test-model\n')
            card={'world_id':'unit-test','options':[{'id':'stop','kind':'stop'}]}
            client=Client(True);advisor=llm.Advisor(env,root/'timeout')
            with patch.object(llm.urllib.request,'build_opener',return_value=client):
                self.assertEqual(advisor.choose(card)['status'],'failed')
                self.assertTrue(advisor.choose(card)['reused_record'])
            self.assertEqual(client.calls,1)
            client=Client();advisor=llm.Advisor(env,root/'parse')
            with patch.object(llm.urllib.request,'build_opener',return_value=client):
                self.assertEqual(advisor.choose(card)['status'],'ok')
            self.assertEqual(client.calls,2);self.assertEqual(len(list((root/'parse').glob('*.json'))),2)

    def test_dark_pixels_supply_no_depth_at_any_pose(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from beforestep.visualization import camera as VZ
        from experimental.arena.geometry import camera_at
        cam=camera_at([2.,0.],0.)
        vm=SimpleNamespace(sync=lambda q:None,mj=SimpleNamespace(mj_name2id=lambda *args:0,mjtObj=SimpleNamespace(mjOBJ_CAMERA=0)),
                           m=SimpleNamespace(cam_fovy=[70.]),d=SimpleNamespace(cam_xpos=np.array([cam['world_pos']]),cam_xmat=np.array([np.array(cam['R_world_from_camera']).ravel()])))
        env=SimpleNamespace(data=SimpleNamespace(qpos=[]))
        for distance in [.2,2.]:
            with patch.object(VZ,'camera_rgbd',return_value=(np.zeros((8,8,3),np.uint8),np.full((8,8),distance))):
                ob=N.observe(vm,env)
            self.assertFalse(np.isfinite(ob['zmax']).any())
            self.assertFalse(((ob['state']==N.ROCK)|(ob['state']==N.FREE)).any())

    def test_accelerated_geometry_and_visibility_match_frozen_functions(self):
        from experimental.arena.numerical import triangle_height,visible_gain
        from beforestep.navigation import shadows as SH
        import trimesh
        tri=np.array([[-.2,-.2,.1],[.3,-.2,.3],[.05,.2,.8]])
        expected=SH.add_mesh_height(np.zeros((14,14)),trimesh.Trimesh(tri,[[0,1,2]],process=False),(-.3,-.3))
        actual=np.maximum(0,triangle_height(tri,np.array([[0,1,2]]),(14,14),np.array([-.3,-.3]),N.RES))
        np.testing.assert_allclose(actual,expected,atol=1e-12)
        rng=np.random.default_rng(12);state=np.zeros((N.NX,N.NY),np.int8);state[rng.random(state.shape)<.003]=N.ROCK
        cells=np.column_stack([rng.integers(60,180,200),rng.integers(8,72,200)])
        self.assertEqual(visible_gain(state,np.array([2.13,-.43]),.37,cells),N.visible_cells(state,[2.13,-.43],.37,cells))

    def test_accelerated_planner_preserves_frozen_route(self):
        from experimental.arena.numerical import plan
        occ=np.ones((N.NX,N.NY),bool);occ[70:150,18:75]=False;occ[104:120,40:56]=True
        start=[3.,0.];goal=[6.,.36]
        expected=N.plan(occ,start,goal);actual=plan(occ,start,goal)
        self.assertIsNotNone(expected);np.testing.assert_allclose(actual,expected,atol=1e-8)

    def test_execution_does_not_observe_en_route(self):
        from experimental.arena.evaluate import execute_geometric
        field=np.zeros((N.NX,N.NY),bool);field[120:125,35:45]=True
        trace,hit=execute_geometric([[6.,0.]],np.array([2.,0.]),field)
        self.assertIsNotNone(hit);self.assertLess(trace[-1][0],6.)

    def test_planning_buffer_is_not_counted_as_physical_collision(self):
        from experimental.arena.evaluate import execute_geometric
        occ=np.zeros((N.NX,N.NY),bool);occ[:,40]=True
        _,hit=execute_geometric([[3.,.37]],np.array([2.,.37]),occ)
        self.assertIsNone(hit)
        _,hit=execute_geometric([[3.,.31]],np.array([2.,.31]),occ)
        self.assertIsNotNone(hit)

    def test_no_truth_field_enters_network(self):
        import torch
        from experimental.arena.model import HiddenOccupancy,features,infer
        shape=(N.NX,N.NY);zeros=np.zeros(shape);state=np.full(shape,N.UNSEEN,np.int8)
        class Evidence(dict):
            def __getitem__(self,k):
                if k in ('truth','raw','truth_occ'):raise AssertionError('Privileged geometry accessed')
                return super().__getitem__(k)
        card=Evidence(state=state,position=np.array([2.,0.]),yaw=0.,sun={'azimuth_deg':35.},cover=zeros,accepted=zeros,predicted_shadow=zeros,metric_maps=np.zeros((5,*shape)),zmax=zeros,known_free=zeros)
        torch.set_num_threads(1);model=HiddenOccupancy();prob=infer(model,card)
        self.assertEqual(prob.shape,shape);self.assertTrue(np.isfinite(prob).all())
        x=features(card,True);self.assertFalse(x[6:15].any())
        i,j=N.cell_of(2.42,0.)
        self.assertAlmostEqual(float(x[19,i,j]),np.hypot(.005,.025)/14,places=7)
