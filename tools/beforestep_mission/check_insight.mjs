/** Check the decision display against retained observations and real event semantics. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {compareRoutes, routeInsight, runRecap} from '../../site/mission-insight.js';
import {MissionRun, nextObjective} from '../../site/mission-run.js';

const mission = JSON.parse(gunzipSync(fs.readFileSync(new URL('../../site/media/mission/mission.json.gz', import.meta.url))));
const selected = [5958685, 5958654, 5958934];
const comparison = compareRoutes(mission, selected);
assert.deepEqual(comparison.visiblePlan.path[0], mission.start);
assert.deepEqual(comparison.hypothesisPlan.path[0], mission.start);
assert.notDeepEqual(comparison.visiblePlan.path, comparison.hypothesisPlan.path);
assert(comparison.exposure.margin < 0);
assert(!routeInsight(comparison, 'imagination').includes('预演通过'));
for (let i = 0; i < comparison.visible.length; i++) {
  assert.equal(comparison.visible[i], mission.observation_state[i] === 1 ? 1 : 0);
  if (comparison.added[i]) assert(!comparison.visible[i] && !mission.known_nogo[i] && mission.candidates.some(c => selected.includes(c.task_id) && c.footprint[i]));
}
const withRejected = compareRoutes(mission, [...selected, 5958642]);
assert.deepEqual(withRejected.added, comparison.added);
const samePlan = compareRoutes(mission, selected, mission.start, comparison.hypothesisPlan);
assert.equal(samePlan.hypothesisPlan, comparison.hypothesisPlan);
const collision = {passed: false, reason: 'contact', contact: {high: true}, tasks: selected.slice(0, 2)};
assert(routeInsight(comparison, 'optimistic', {policy: 'optimistic', passed: false, results: [collision]}).includes('预演碰撞'));
assert(!routeInsight(comparison, 'optimistic', {policy: 'optimistic', passed: false, results: [{passed: false, reason: 'timeout'}]}).includes('碰撞'));

const run = new MissionRun('challenge');
run.selectionChanged(selected);
run.event({type:'decisionEvent',event:{sequence:1,type:'initialJudgment',detail:{choice:'pass',label:'我觉得能过'}}});
run.modelViewed(mission.candidates.find(c => c.task_id === 5958685));
run.event({type:'decisionEvent',event:{sequence:2,type:'modelViewed',detail:{taskId:5958685,target:'T1'}}});
run.event({type:'decisionEvent',event:{sequence:3,type:'selectionChanged',detail:{selected,policy:'imagination'}}});
const results = [{passed: true, reason:'completed', tasks: [5958685, 5958654]}, {passed: true, reason:'completed', tasks: [5958685, 5958934]}];
run.event({type: 'previewDone', policy: 'imagination', selected, requestId: 1, revision: 1, passed: true, results});
run.event({type: 'routeStarted', requestId: 1, revision: 1});
run.selectionChanged([5958690, 5958654, 5958934]);
run.event({type: 'previewDone', policy: 'optimistic', selected, requestId: 2, revision: 2, passed: false, results});
run.event({type: 'crossed'});
run.event({type: 'missionComplete', actions: 12, state: {goalDistance: .2}});
const summary = run.summary(), recap = runRecap(summary, mission);
assert.equal(summary.previewedWorlds, 2); // The same worlds tried twice remain two distinct worlds.
assert.deepEqual(summary.routeSelected, [...selected].sort((a, b) => a - b));
assert(recap.includes('5958685') && !recap.includes('5958690'));
assert(recap.includes('2 个候选世界') && recap.includes('12 次轮腿动作') && recap.includes('抵达并停稳'));
assert(recap.includes('我觉得能过') && recap.includes('计入背面假设'));
const legacy=runRecap({...summary,decisions:undefined,viewedTasks:undefined,assistedMeters:undefined},mission);
assert(legacy.includes('初判：未记录') && legacy.includes('执行方式：未记录'));
const branch=new MissionRun();branch.selectionChanged(selected);branch.event({type:'checkpointSaved',checkpoint:{id:'observation'}});
branch.event({type:'previewDone',selected,passed:true,results});branch.modelViewed(mission.candidates.find(c=>c.task_id===5958685));
branch.manualMeters=3;branch.event({type:'checkpointRestored',checkpoint:{id:'observation'},journal:{initial:null,events:[]}});
assert.equal(branch.previewedWorlds.size,0);assert.equal(branch.viewedTasks.size,0);assert.equal(branch.manualMeters,0);
assert.equal(branch.summary().checkpointUses,1);
assert(!runRecap(new MissionRun().summary(), mission).includes('预演通过'));
const manual = nextObjective({phase: 'explore', x: 4, showcase: {completed: true}, automatic: false}, mission);
assert(!manual.hint.includes('预演通过'));
const assisted = nextObjective({phase: 'explore', x: 4, showcase: {completed: true}, automatic: true}, mission);
assert(assisted.hint.includes('所选假设预演通过'));
console.log(JSON.stringify({passed: true, checks: ['same start, different actual planner routes', 'observed cells and admitted footprint provenance', 'projected warning separate from contact and timeout', 'recap tracks unique completed worlds and the executed selection', 'manual/assisted narrative follows actual control state'], visibleCells: comparison.visible.reduce((n, v) => n + v, 0), hypothesisCells: comparison.added.reduce((n, v) => n + v, 0)}));
