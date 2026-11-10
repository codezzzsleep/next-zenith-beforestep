"""R1 observation quality, bounded independent sampling and legacy regressions."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from beforestep import scene as S
from beforestep.navigation import map as N
from beforestep.generation import records as LX


class TargetViewTests(unittest.TestCase):
    def target(self):
        cells = np.zeros_like(N.GX, dtype=bool)
        cells[125:132, 41:46] = True
        return {'cells': cells, 'H': .42}

    def test_nearer_camera_has_more_native_pixels(self):
        target = self.target()
        near, _ = N.target_px((4.5, .1), target)
        far, _ = N.target_px((2.5, .1), target)
        self.assertGreater(near, far)

    def test_quality_priority_target_aim_and_too_close_exclusion(self):
        state = np.full(N.GX.shape, N.FREE, np.int8)
        need = np.zeros_like(state, dtype=bool); need[140:145, 50:55] = True
        occ = np.zeros_like(need)
        with patch.object(N, 'visible_cells', return_value=60):
            candidates = N.choose_second_look(state, (3., .1), need, occ, target=self.target())
        self.assertTrue(candidates)
        self.assertGreaterEqual(candidates[0][5], 512)
        seen_low = False
        target = self.target(); tx, ty = np.nonzero(target['cells'])
        center = [N.XS[tx].mean(), N.YS[ty].mean()]
        for x, y, yaw, score, n, px in candidates:
            self.assertAlmostEqual(yaw, np.arctan2(center[1]-y, center[0]-x))
            _, distance = N.target_px((x+.42*np.cos(yaw), y+.42*np.sin(yaw)), target)
            self.assertGreaterEqual(distance, .8)
            if px < 512: seen_low = True
            elif seen_low: self.fail('Qualified viewpoints must precede every low-resolution viewpoint')

    def test_target_none_preserves_frozen_complete_ranking(self):
        root = S.ROOT
        golden = json.loads((root/'tests/fixtures/r1_second_look_legacy.json').read_text())
        run = root/golden['run']; state=np.load(run/'decision/look1_state.npy')
        data=np.load(run/'traj.npz'); free=N.swept(data['qpos'][data['t']<=golden['first_look_time'],:2])
        previous=S.SCENE_ID
        try:
            S.configure('stress_v8')
            x=golden['pose'][0]
            unknown=np.isin(state,[N.DARK,N.HIDDEN,N.UNSEEN])&~N.prior_nogo()
            need=unknown&(N.GX>x+1)&(N.GX<x+4.5)
            occ=N.occupancy(state,'conservative',known_free=free)
            actual=N.choose_second_look(state,golden['pose'],need,occ,target=None)
            np.testing.assert_array_equal(np.asarray(actual),np.asarray(golden['candidates']))
        finally:S.configure(previous)


class InputBatchTests(unittest.TestCase):
    def state(self, prefix, ok):
        return {'native_ok':ok, 'crops': {k:{'path':prefix+'/'+k+'.png','sha256':k}
                for k in ('A1','A2','B1','B2','C1','C2')}}

    def test_two_images_require_both_native_views_to_pass(self):
        for first_ok in (False,True):
            for second_ok in (False,True):
                first=self.state('first',first_ok); second=self.state('second',second_ok)
                mode,items=LX.items_for_look(2,first,second)
                self.assertEqual(mode,'imgs' if first_ok and second_ok else 'img')
                self.assertEqual(len(items),3 if mode=='imgs' else 6)
                if mode=='img':self.assertTrue(all(it['path'].startswith('second/') for it in items))

    def test_retry_preserves_exact_input_bytes_and_occurs_only_once(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); target=root/'target'; target.mkdir()
            ids=('A1','A2','B1','B2','C1','C2')
            for name in ids:(root/(name+'.jpg')).write_bytes(b'original-'+name.encode())
            items=[{'id':name,'path':name+'.jpg','sha256':hashlib.sha256((root/(name+'.jpg')).read_bytes()).hexdigest()} for name in ids]
            with patch.object(LX,'ROOT',root):
                LX.write_request(target,'img',items)
                result={'tasks':[{'id':it['id'],'status':'failed','inputs':[it['path']]} for it in items]}
                (target/'lux_result.json').write_text(json.dumps(result))
                original=(target/'lux_request.json').read_bytes()
                self.assertIsNone(LX.prepare_second_batch(target,{'admitted_ids':[]},1))
                retry=LX.prepare_second_batch(target,{'admitted_ids':[]},2)
                self.assertIsNotNone(retry)
                self.assertEqual((target/'lux_request.json').read_bytes(),original)
                second=json.loads(retry.read_text())['items']
                self.assertEqual([x['id'] for x in second],[x+'b' for x in ids])
                self.assertEqual([x['path'] for x in second],[x['path'] for x in items])
                self.assertEqual([x['sha256'] for x in second],[x['sha256'] for x in items])
                self.assertEqual(LX.pending_request(target),retry)
                self.assertIsNone(LX.read_result(target))
                self.assertIsNone(LX.prepare_second_batch(target,{'admitted_ids':[]},2))
                (retry.parent/'lux_result.json').write_text(json.dumps({'tasks':[
                    {'id':x['id'],'status':'failed','inputs':[x['path']]} for x in second]}))
                self.assertEqual(LX.read_result(target),[])
                self.assertIsNone(LX.pending_request(target))
                self.assertIsNone(LX.prepare_second_batch(target,{'admitted_ids':[]},2))


if __name__=='__main__':unittest.main()
