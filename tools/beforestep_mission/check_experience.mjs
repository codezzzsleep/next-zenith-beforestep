/** New game checks are independent of frozen research results. */
import assert from 'node:assert/strict';
import fs from 'node:fs';import {gunzipSync} from 'node:zlib';
import {sameAnchor,usableProof,progressOnPath} from '../../site/mission-session.js';
import {accepted,planRoute,modelWorlds} from '../../site/mission-planner.js';
import load from '../../site/vendor/mujoco/mujoco.js';import {installAssets,unpackTar} from '../../site/robot-physics.js';import {MissionWorld} from '../../site/mission-world.js';
const root=new URL('../../site/',import.meta.url).pathname,m=JSON.parse(gunzipSync(fs.readFileSync(root+'media/mission/mission.json.gz')));
const anchor={x:2.3,y:-.5,yaw:0,speed:0},proof={passed:true,anchor,revision:2};
assert(usableProof(proof,anchor,2));assert(!usableProof(proof,anchor,3));assert(!usableProof({...proof,passed:false},anchor,2));assert(!sameAnchor({...anchor,x:2.5},anchor));assert(!sameAnchor({...anchor,yaw:.2},anchor));assert(!sameAnchor({...anchor,speed:.1},anchor));assert(!sameAnchor({...anchor,z:.5},{...anchor,z:.38}));
assert.equal(progressOnPath({x:2,y:0},[[0,0],[3,0],[4,1]]).index,1);assert(progressOnPath({x:2,y:.2},[[0,0],[3,0]]).distance>.09);
const all=m.candidates.filter(c=>accepted(c,m.thresholds)).map(c=>c.task_id),one=[m.candidates.find(c=>c.target==='T1'&&accepted(c,m.thresholds)).task_id,m.candidates.find(c=>c.target==='T2'&&accepted(c,m.thresholds)).task_id];
assert.equal(modelWorlds(m,all).length,12);assert.equal(modelWorlds(m,one).length,1);assert.notDeepEqual(planRoute(m,all).path,planRoute(m,[],'optimistic').path);
const mj=await load({wasmBinary:gunzipSync(fs.readFileSync(root+'vendor/mujoco/mujoco.wasm.gz'))});installAssets(mj,unpackTar(gunzipSync(fs.readFileSync(root+'media/mission/worlds.tar.gz'))));
const w=new MissionWorld(mj,m),before=w.physicalState(),seen=w.observeRocks();assert(seen.hits.length>0);assert(seen.hits.every(h=>h.normal.length===3&&h.point.length===3&&Math.hypot(...h.normal)>.9));assert.deepEqual(w.physicalState(),before);
const packet=w.packet();assert(packet.geom_roles.includes('T1'));assert(packet.geom_roles.includes('T2'));assert(packet.leg_geoms.includes(0));
// A dream can run motor steps without modifying the live robot.
const dream=new MissionWorld(mj,m,modelWorlds(m,one)[0].file,before);for(let i=0;i<300;i++)dream.step(.18,0,false);assert.deepEqual(w.physicalState(),before);assert(dream.state().x>w.state().x);dream.destroy();w.setPose('high');for(let i=0;i<600;i++)w.step(0,0,true);const heightSnapshot=w.physicalState(),heightDream=new MissionWorld(mj,m,modelWorlds(m,one)[0].file,heightSnapshot);assert.equal(heightDream.poseName,'high');assert.deepEqual(heightDream.pose,heightSnapshot.pose);assert.equal(heightDream.driveV,heightSnapshot.driveV);heightDream.destroy();w.reset();for(let i=0;i<2400&&w.state().yaw<1.9;i++)w.step(0,.7,false);const turned=w.observeRocks();assert(w.state().yaw>1.5);assert(turned.hits.length<seen.hits.length/4);w.destroy();
const result={passed:true,certificateChecks:9,allWorlds:12,singleWorld:1,routeChanged:true,liveVisibleHits:seen.hits.length,liveTargets:seen.targets,dreamDoesNotMutateLive:true,turningCameraChangesVisibleSurfaces:true,controllerPosePreservedInDream:true,scope:'New interactive experience; separate from research results'};
if(process.argv[2])fs.writeFileSync(process.argv[2],JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
