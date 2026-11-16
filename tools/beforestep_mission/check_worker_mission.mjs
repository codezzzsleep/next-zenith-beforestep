/** Complete the real worker protocol, including terminal frame delivery. */
import fs from 'node:fs';import {gunzipSync} from 'node:zlib';import assert from 'node:assert/strict';
const root=new URL('../../site/',import.meta.url).pathname,mission=JSON.parse(gunzipSync(fs.readFileSync(root+'media/mission/mission.json.gz')));
const {accepted}=await import('../../site/mission-planner.js');const events=[];let tick;globalThis.onmessage=null;globalThis.postMessage=e=>{events.push(e);if(['previewDone','gatePreviewDone','crossed','missionComplete','missionFailed'].includes(e.type))console.log(e.type,e.passed??e.result?.passed??'');};globalThis.setInterval=f=>{tick=f;return 1;};
process.on('uncaughtException',e=>{const failure={passed:false,error:e.message,lastState:state(),events:events.filter(e=>['previewDone','gatePreviewDone','missionFailed','missionComplete'].includes(e.type)),scope:'New game worker protocol'};if(process.argv[2])fs.writeFileSync(process.argv[2],JSON.stringify(failure,null,2)+'\n');console.error(e);process.exit(1);});
await import('../../site/mission-worker.js');const send=data=>globalThis.onmessage({data}),array=p=>new Uint8Array(fs.readFileSync(root+p)).buffer,state=()=>events.filter(e=>e.type==='state'&&e.channel==='live').at(-1)?.state;
await send({type:'init',mission,wasm:array('vendor/mujoco/mujoco.wasm.gz'),bundle:array('media/mission/worlds.tar.gz')});const selected=[...mission.candidates.filter(c=>c.target==='T1'&&accepted(c,mission.thresholds)).slice(0,1),...mission.candidates.filter(c=>c.target==='T2'&&accepted(c,mission.thresholds))].map(c=>c.task_id);await send({type:'selection',selected});await send({type:'preview',requestId:'route'});assert(state().proof.usable);await send({type:'execute'});
for(let i=0;i<16000&&(state().phase==='explore'||state().automatic);i++)tick();assert(state().phase==='gate');for(let i=0;i<30;i++)tick();await send({type:'gatePreview',requestId:'threshold'});assert(state().gateProof.passed);await send({type:'cross',assisted:true});
const commands=[];
for(let i=0;i<18000&&state().phase==='crossing';i++){
 const s=state(),wait=s.legs?.waiting;
 if(wait&&(wait.action!=='lift'||s.stable)){
  const count=s.actionCount;await send({type:'legAction',action:wait.action});if(state().actionCount>count)commands.push(wait);
 }
 tick();
}
assert(state().phase==='finish-drive');assert.equal(commands.length,12);await send({type:'wheelMode'});assert(!state().legs);await send({type:'input',v:.36,w:0,brake:false});for(let i=0;i<5000&&state().phase!=='complete';i++)tick();
const terminal=state(),event=events.find(e=>e.type==='missionComplete');assert(event);assert.equal(terminal.phase,'complete');assert(terminal.paused);assert(terminal.goalDistance<.35);assert.equal(terminal.actionCount,12);
const result={passed:true,selected,commands,terminal,terminalSnapshotDelivered:true,realMotorPhysics:true,scope:'New game protocol; independent of frozen research experiments'};if(process.argv[2])fs.writeFileSync(process.argv[2],JSON.stringify(result,null,2)+'\n');console.log('FULL WORKER MISSION PASSED');
