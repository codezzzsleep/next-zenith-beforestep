/** Session knowledge and permission checks, with real MuJoCo sensor rays. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gunzipSync} from 'node:zlib';
import loadMujoco from '../../site/vendor/mujoco/mujoco.js';
import {unpackTar,installAssets} from '../../site/robot-physics.js';
import {MissionWorld,RouteFollower} from '../../site/mission-world.js';
import {SessionObservation,DecisionJournal} from '../../site/mission-observation.js';
import {completeWorldProof,usableProof} from '../../site/mission-session.js';
import {planRoute,modelWorlds} from '../../site/mission-planner.js';

const read=name=>gunzipSync(fs.readFileSync(new URL('../../site/'+name,import.meta.url)));
const mission=JSON.parse(read('media/mission/mission.json.gz'));
const baseline=JSON.stringify(mission.observation_state);
const mj=await loadMujoco({wasmBinary:read('vendor/mujoco/mujoco.wasm.gz')});
installAssets(mj,unpackTar(read('media/mission/worlds.tar.gz')));
const world=new MissionWorld(mj,mission);
for(let i=0;i<250;i++)world.step(0,0,true);
const pose=world.physicalState(),knowledge=new SessionObservation(mission),rays=world.observeRocks();
const first=knowledge.ingest(rays);
assert(first.valid>0);
const validIndices=new Set(rays.hits.map(hit=>{
  const g=mission.grid,x=Math.floor((hit.point[0]-g.x0)/g.res),y=Math.floor((hit.point[1]-g.y0)/g.res);
  return x*g.ny+y;
}));
for(const index of knowledge.cells.keys())assert(validIndices.has(index),'only actual ray-hit cells may enter the session layer');
const version=knowledge.version;
assert(!knowledge.ingest(rays).changed);
assert.equal(knowledge.version,version);
assert(!knowledge.ingest({hits:[{target:'T1',point:[NaN,0,1],normal:[0,0,1]}]}).changed);
assert.equal(JSON.stringify(mission.observation_state),baseline);
assert.notEqual(knowledge.planningMission().observation_state,mission.observation_state);
world.sensorYaw=.4;
const second=knowledge.ingest(world.observeRocks());
const beforeSupplemental=knowledge.version;
assert.deepEqual(world.physicalState(),pose,'optical reorientation and observation must not move the robot');
world.sensorYaw=0;
const approach=new RouteFollower(planRoute(mission,[5958948,5959025,5958934]).path);
while(world.state().x<3.2&&world.elapsed<40){const c=approach.command(world);world.step(c.v,c.w,c.brake);}
for(let i=0;i<500;i++)world.step(0,0,true);
const supplemental=knowledge.ingest(world.observeRocks());
assert(supplemental.changed&&supplemental.added>0,'moving along the known approach must bring real additional surface cells');
assert(!world.bodyContact());
assert.equal(knowledge.version,beforeSupplemental+1);
const restored=new SessionObservation(mission,JSON.parse(JSON.stringify(knowledge.snapshot())));
assert.deepEqual(restored.snapshot(),knowledge.snapshot());
const journal=new DecisionJournal();
assert(journal.judge('unsure',world.state()));assert(!journal.judge('pass',world.state()));
assert.equal(new DecisionJournal(journal.snapshot()).initial.detail.choice,'unsure');

const selected=[5958948,5959025,5958934],worlds=modelWorlds(mission,selected);
assert.equal(worlds.length,2);
const state=world.state(),proof={passed:true,revision:7,observationVersion:knowledge.version,
  anchor:state,expectedWorlds:worlds.map(w=>w.tasks),plan:planRoute(mission,selected,'imagination',[state.x,state.y]),
  results:worlds.map(w=>({tasks:w.tasks,passed:true,reason:'completed'}))};
assert(completeWorldProof(proof));assert(usableProof(proof,state,7,knowledge.version));
for(const changed of [
  {...proof,expectedWorlds:[]},
  {...proof,expectedWorlds:[worlds[0].tasks,worlds[0].tasks],results:[proof.results[0]]},
  {...proof,results:proof.results.slice(0,1)},
  {...proof,results:[proof.results[0],proof.results[0]]},
  {...proof,results:proof.results.map(r=>({...r,reason:'timeout'}))},
  {...proof,results:proof.results.map(r=>({...r,cancelled:true}))},
  {...proof,plan:{path:[]}},
])assert(!completeWorldProof(changed));
assert(!usableProof(proof,state,8,knowledge.version));
assert(!usableProof(proof,state,7,knowledge.version+1));
assert(!usableProof(proof,{...state,x:state.x+.12},7,knowledge.version));
const report={passed:true,checks:['real_sensor_cells_only','frozen_baseline_unchanged','duplicate_and_invalid_observation_no_revision',
  'optical_view_does_not_move_robot','checkpoint_knowledge_and_initial_judgment_exact','all_worlds_required_no_cancel_timeout_duplicate_or_stale_permission'],
  sensorHits:rays.hits.length,firstObservation:first,secondAngleObservation:second,supplementalObservation:supplemental,supplementalPose:{x:state.x,y:state.y,yaw:state.yaw},worlds:worlds.length,scope:'Current interactive session; frozen research results not rerun'};
console.log(JSON.stringify(report));
world.destroy();
