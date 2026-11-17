/** Actual motor worker: checkpoint resets, certificate invalidation and modes. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {accepted} from '../../site/mission-planner.js';
import {MissionRun} from '../../site/mission-run.js';
import {MissionWorld} from '../../site/mission-world.js?v=immersive-1';

const root = new URL('../../site/', import.meta.url).pathname;
const mission = JSON.parse(gunzipSync(fs.readFileSync(root + 'media/mission/mission.json.gz')));
const selected = [...mission.candidates.filter(c => c.target === 'T1' && accepted(c, mission.thresholds)).slice(0, 1), ...mission.candidates.filter(c => c.target === 'T2' && accepted(c, mission.thresholds)).slice(0, 2)].map(c => c.task_id);
const run = new MissionRun();
const events = [];
const checks = [];
const savedPoses = new Map();
let lastPhysicalSnapshot;
const physicalState = MissionWorld.prototype.physicalState;
// Read-only inspection of the state returned at the exact save boundary.
// A later settled pose is a different physical observation, not the snapshot.
MissionWorld.prototype.physicalState = function() {
  const snapshot = physicalState.call(this);
  lastPhysicalSnapshot = structuredClone(snapshot);
  return snapshot;
};
let tick, live, qpos;
globalThis.onmessage = null;
globalThis.setInterval = fn => { tick = fn; return 1; };
globalThis.postMessage = message => {
  if (message.type === 'state' && message.channel === 'live') {
    live = message.state;
    qpos = Array.from(message.data.qpos);
    run.update(live, mission);
  } else if (message.type !== 'world' && message.type !== 'state') {
    if (message.type === 'checkpointSaved') savedPoses.set(message.checkpoint.id, lastPhysicalSnapshot.qpos);
    events.push(message);
    run.event(message);
    if (message.type === 'resetDone') run.selectionChanged(selected);
  }
};
await import('../../site/mission-worker.js');
const send = data => globalThis.onmessage({data});
const array = path => new Uint8Array(fs.readFileSync(root + path)).buffer;
const maxError = (a, b) => Math.max(...a.map((v, i) => Math.abs(v - b[i])));
function advanceUntil(predicate, limit, label) {
  for (let i = 0; i < limit && !predicate(); i++) tick();
  assert(predicate(), `${label}: ${JSON.stringify({phase: live.phase, x: live.x, legs: live.legs?.phase})}`);
}
async function observe() {
  await send({type: 'input', v: .36, w: 0, brake: false});
  advanceUntil(() => live.showcase.stage === 'observe', 1000, 'observation checkpoint');
  assert(live.stable);
  await send({type: 'modelViewed', taskId: selected[0], rotated: true});
}
async function toThreshold(requestId) {
  await send({type: 'preview', requestId});
  assert(live.proof?.usable);
  await send({type: 'execute'});
  advanceUntil(() => live.phase === 'gate' && !live.automatic, 16000, 'drive to threshold');
  for (let i = 0; i < 40; i++) tick();
  assert(live.stable);
}
async function crossAndFinish(id) {
  await send({type: 'gatePreview', requestId: id});
  assert(live.gateProof?.usable);
  await send({type: 'cross', assisted: true});
  const commands = [];
  for (let i = 0; i < 18000 && live.phase === 'crossing'; i++) {
    const waiting = live.legs?.waiting;
    if (waiting && (waiting.action !== 'lift' || live.stable)) {
      const before = live.actionCount;
      await send({type: 'legAction', action: waiting.action});
      if (live.actionCount > before) commands.push(waiting);
    }
    tick();
  }
  assert.equal(live.phase, 'finish-drive');
  assert.equal(commands.length, 12);
  await send({type: 'wheelMode'});
  for (let i = 0; i < 30; i++) tick();
  if (live.gameMode === 'explore') assert.equal(live.checkpoint.id, 'finish');
  await send({type: 'input', v: .36, w: 0, brake: false});
  advanceUntil(() => live.phase === 'complete', 5000, 'goal arrival');
  assert(live.goalDistance < .35);
  assert.equal(live.actionCount, 12);
  return {commands: commands.length, terminal: {...live, legs: undefined}, record: run.record()};
}

run.selectionChanged(selected);
await send({type: 'init', mission, wasm: array('vendor/mujoco/mujoco.wasm.gz'), bundle: array('media/mission/worlds.tar.gz'), showcase: true, gameMode: 'explore'});
await send({type: 'selection', selected});
await observe();
assert.equal(live.checkpoint.id, 'observation');
const observationPose = [...savedPoses.get('observation')];
const preview = send({type: 'preview', requestId: 'cancelled-by-checkpoint'});
await new Promise(resolve => setTimeout(resolve, 25));
await send({type: 'retryCheckpoint', qpos: Array(23).fill(100)});
await preview;
assert(maxError(qpos, observationPose) < 1e-12);
assert.equal(live.proof, null);
assert.equal(live.gateProof, null);
assert.equal(live.showcase.stage, 'observe');
assert(!events.some(e => e.type === 'previewDone' && e.requestId === 'cancelled-by-checkpoint'));
checks.push('Observation reset uses the exact worker-owned pose, ignores supplied pose, and cancels an in-flight real rehearsal');

await send({type: 'modelViewed', taskId: selected[0], rotated: true});
await send({type: 'manualContinue'});
await send({type: 'legSelect', index: 0});
await send({type: 'legAction', action: 'lift'});
for (let i = 0; i < 40; i++) tick();
assert(live.legs);
await send({type: 'retryCheckpoint'});
assert.equal(live.legs, null);
assert.equal(live.actionCount, 0);
assert(maxError(qpos, observationPose) < 1e-12);
checks.push('Reset destroys active leg control and restores player-action count without advancing or teleport-driving the robot');

await send({type: 'modelViewed', taskId: selected[0], rotated: true});
await toThreshold('practice-route');
assert.equal(live.checkpoint.id, 'threshold');
const thresholdPose = [...savedPoses.get('threshold')];
await send({type: 'gatePreview', requestId: 'old-gate'});
assert(live.gateProof?.passed);
await send({type: 'cross', assisted: true});
for (let i = 0; i < 50; i++) tick();
await send({type: 'retryCheckpoint'});
assert.equal(live.phase, 'gate');
assert.equal(live.legs, null);
assert.equal(live.proof, null);
assert.equal(live.gateProof, null);
assert(maxError(qpos, thresholdPose) < 1e-12);
await send({type: 'execute'});
assert.equal(events.at(-1).type, 'commandRejected');
checks.push('Threshold reset preserves its measured position and invalidates both route and crossing certificates');
const practice = await crossAndFinish('new-gate');
assert(practice.record.completed);
assert.equal(practice.record.mode, 'explore');
assert.equal(practice.record.checkpointUses, 3);
checks.push('Checkpoint exploration still completes twelve player commands, returns to wheel drive and reaches the physical goal');

await send({type: 'reset', gameMode: 'challenge'});
await send({type: 'selection', selected});
run.selectionChanged(selected);
assert.equal(live.gameMode, 'challenge');
assert.equal(live.checkpoint, null);
await observe();
assert.equal(live.checkpoint, null);
const beforeRejected = [...qpos];
await send({type: 'retryCheckpoint', checkpointId: 'threshold', qpos: Array(23).fill(100)});
assert.equal(events.at(-1).type, 'commandRejected');
assert(maxError(qpos, beforeRejected) < 1e-12);
checks.push('Challenge cannot inherit a practice checkpoint or switch modes through a resume command');
await toThreshold('challenge-route');
const challenge = await crossAndFinish('challenge-gate');
assert.equal(challenge.record.mode, 'challenge');
assert.equal(challenge.record.checkpointUses, 0);
assert.equal(challenge.terminal.checkpoint, null);
assert(challenge.record.badges.find(b => b.id === 'challenge').earned);
checks.push('Full challenge completes the real model-world and wheel-leg chain from the start with a separate completed record');

const result = {passed: true, checks, practice, challenge, scope: 'Independent game verification; original research, generated assets and controllers unchanged'};
if (process.argv[2]) fs.writeFileSync(process.argv[2], JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify({passed: true, checks, practiceGoal: practice.terminal.goalDistance, challengeGoal: challenge.terminal.goalDistance}));
