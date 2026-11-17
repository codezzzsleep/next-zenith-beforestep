/** Checks the game layer's evidence boundaries and persistent record behavior. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {MissionRun, GAME_VERSION, RECORD_KEY, chapterFor, nextHypotheses, readRecords, saveRecord, bestRecord} from '../../site/mission-run.js';
import {accepted} from '../../site/mission-planner.js';

const root = new URL('../../site/', import.meta.url).pathname;
const mission = JSON.parse(gunzipSync(fs.readFileSync(root + 'media/mission/mission.json.gz')));
const chosen = [...mission.candidates.filter(c => c.target === 'T1' && accepted(c, mission.thresholds)).slice(0, 1), ...mission.candidates.filter(c => c.target === 'T2' && accepted(c, mission.thresholds)).slice(0, 2)].map(c => c.task_id);
const checks = [];
const state = (more = {}) => ({x: 2.3, y: -.5, elapsed: 0, speed: 0, tilt: 1, phase: 'explore', actionCount: 0, automatic: false, paused: false, showcase: {completed: false}, ...more});

const cancelled = new MissionRun();
cancelled.selectionChanged(chosen);
cancelled.event({type: 'previewDone', passed: true, requestId: 'old', revision: 1, results: [{}, {}], selected: chosen});
cancelled.event({type: 'dreamClosed'});
cancelled.event({type: 'routeStarted', requestId: 'old', revision: 1});
assert.equal(cancelled.summary().worlds, 0);
assert.equal(cancelled.summary().score, 0);
cancelled.event({type: 'missionFailed'});
assert.equal(cancelled.record(), null);
checks.push('Cancelled rehearsal and failed attempt cannot become a used route or completed record');

const changed = new MissionRun();
changed.selectionChanged(chosen);
changed.event({type: 'previewDone', passed: true, requestId: 'p1', revision: 1, results: [{}, {}], selected: chosen});
changed.selectionChanged(nextHypotheses(mission, chosen));
changed.event({type: 'routeStarted', requestId: 'p1', revision: 1});
assert.equal(changed.summary().worlds, 0);
checks.push('A selection change cannot earn a route award from the previous hypothesis');

const run = new MissionRun('challenge');
run.selectionChanged(chosen);
for (const target of ['T1', 'T2']) run.modelViewed(mission.candidates.find(c => c.target === target && chosen.includes(c.task_id)));
run.update(state(), mission);
run.update(state({x: 2.5, elapsed: 1, speed: .2}), mission);
run.update(state({x: 2.5, elapsed: 8, paused: true}), mission);
run.update(state({x: 2.5, elapsed: 20}), mission);
assert.equal(run.actionSeconds, 1);
run.event({type: 'previewDone', passed: true, requestId: 'p2', revision: 2, results: [{}, {}], selected: chosen});
run.event({type: 'routeStarted', requestId: 'wrong', revision: 2});
assert.equal(run.summary().worlds, 0);
run.event({type: 'routeStarted', requestId: 'p2', revision: 2});
run.update(state({x: mission.dock[0], elapsed: 30, actionCount: 12, phase: 'crossing', showcase: {completed: true}, legs: {busy: true}}), mission);
run.event({type: 'crossed'});
run.event({type: 'missionComplete', state: {goalDistance: .2}, actions: 12});
assert.equal(run.summary().score, 100);
assert.equal(run.summary().worlds, 2);
assert(run.summary().badges.find(b => b.id === 'challenge').earned);
const record = run.record(1234);
assert(record);
assert.equal(run.record(), null);
checks.push('Only actual matching route use, deliberate model views, leg relay and arrival earn the full game score');

const practice = new MissionRun('explore');
practice.selectionChanged(chosen);
practice.update(state({x: 8, elapsed: 100, speed: .2}), mission);
practice.event({type: 'checkpointRestored'});
practice.update(state({x: 2.8, elapsed: 8}), mission);
practice.update(state({x: 3, elapsed: 9, speed: .2}), mission);
assert.equal(practice.actionSeconds, 1);
assert(Math.abs(practice.manualMeters - .2) < 1e-9);
assert.equal(practice.checkpointUses, 1);
assert.equal(practice.completed, false);
checks.push('Checkpoint reset cannot count a time jump or teleport distance as player action');

const storage = {value: '[]', getItem(key) { assert.equal(key, RECORD_KEY); return this.value; }, setItem(key, value) { assert.equal(key, RECORD_KEY); this.value = value; }};
assert(saveRecord(storage, record).saved);
assert.equal(bestRecord(readRecords(storage), 'challenge').score, 100);
assert.equal(bestRecord(readRecords(storage), 'explore'), null);
assert(!saveRecord(storage, {...record, completed: false}).saved);
assert(!saveRecord(storage, {...record, checkpointUses: 1}).saved);
assert(!saveRecord(storage, {...record, version: 'old'}).saved);
storage.value = '{broken';
assert.deepEqual(readRecords(storage), []);
const unavailable = {getItem() { throw new Error('storage unavailable'); }, setItem() { throw new Error('quota'); }};
assert(!saveRecord(unavailable, record).saved);
checks.push('Modes stay separate, invalid/completed-after-checkpoint challenges are rejected, and blocked storage remains playable');

const seen = new Set();
let selection = chosen;
for (let i = 0; i < 6; i++) {
  const a = selection.find(id => mission.candidates.find(c => c.task_id === id).target === 'T1');
  seen.add(a);
  assert(selection.every(id => accepted(mission.candidates.find(c => c.task_id === id), mission.thresholds)));
  assert.equal(selection.filter(id => mission.candidates.find(c => c.task_id === id).target === 'T2').length, 2);
  selection = nextHypotheses(mission, selection);
}
assert.equal(seen.size, 6);
assert.equal(chapterFor(state({x: mission.dock[0], showcase: {completed: true}}), mission), 2);
assert.equal(chapterFor(state({phase: 'complete'}), mission), 4);
checks.push('Replay cycles six real admitted A hypotheses and retains the real B worlds without modifying the scene');

const result = {passed: true, version: GAME_VERSION, checks, scope: 'Game facts, personal records and archived-hypothesis replay; independent of R1/R2/R3'};
if (process.argv[2]) fs.writeFileSync(process.argv[2], JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result));
