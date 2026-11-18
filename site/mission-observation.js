/** Session knowledge contains sensor hit cells only, never a truth mesh. */
export class SessionObservation {
  constructor(mission, saved = null) {
    this.mission = mission;
    this.version = saved?.version || 0;
    this.cells = new Map((saved?.cells || []).map(cell => [cell.index, {...cell}]));
    this.hits = new Map((saved?.hits || []).map(hit => [this.hitKey(hit), structuredClone(hit)]));
  }
  hitKey(hit) { return hit.target + ':' + hit.point.map(v => Math.floor(v / .025)).join(':'); }
  ingest(observation) {
    const grid = this.mission.grid;
    let added = 0, valid = 0, raised=0;
    for (const hit of observation?.hits || []) {
      if (!['T1','T2'].includes(hit.target) || hit.point?.length !== 3 || !hit.point.every(Number.isFinite)) continue;
      if (hit.normal?.length !== 3 || !hit.normal.every(Number.isFinite) || Math.hypot(...hit.normal) < .8) continue;
      const [px,py,pz] = hit.point, x = Math.floor((px-grid.x0)/grid.res), y = Math.floor((py-grid.y0)/grid.res);
      if (x<0 || y<0 || x>=grid.nx || y>=grid.ny || pz<=0) continue;
      valid++;
      this.hits.set(this.hitKey(hit), structuredClone(hit));
      const index = x*grid.ny+y;
      if (this.mission.observation_state[index]===1 || this.mission.known_nogo[index]) continue;
      const previous = this.cells.get(index);
      if (!previous) {
        this.cells.set(index,{index,target:hit.target,x:grid.x0+(x+.5)*grid.res,y:grid.y0+(y+.5)*grid.res,top:pz});
        added++;
      } else if (pz>=previous.top+grid.res) {previous.top=pz;raised++;}
    }
    // A revision is a planning change, not another click from the same angle.
    if (added||raised) this.version++;
    return {changed:added+raised>0,added,raised,valid,version:this.version,cells:this.cells.size,
      reason:added+raised?'new_measured_surface_cells':'no_new_surface_cells',source:'Current MuJoCo camera ray hits'};
  }
  planningMission() {
    const state=Uint8Array.from(this.mission.observation_state);
    for (const index of this.cells.keys()) state[index]=1;
    return {...this.mission,observation_state:state,observation_version:this.version};
  }
  snapshot() { return {version:this.version,cells:[...this.cells.values()].map(c=>({...c})),hits:[...this.hits.values()].map(h=>structuredClone(h)),source:'Current measured ray hits; frozen R1 layer retained separately'}; }
}

export const INITIAL_JUDGMENTS=Object.freeze({pass:'我觉得能过',detour:'我想绕开',unsure:'我拿不准'});

/** The same immutable event identities are exported and used in the recap. */
export class DecisionJournal {
  constructor(saved=null) { this.initial=saved?.initial?structuredClone(saved.initial):null;this.events=structuredClone(saved?.events||[]);this.sequence=saved?.sequence||0; }
  record(type,detail={},state=null) {
    const event={sequence:++this.sequence,type,simSeconds:state?.elapsed??null,pose:state?{x:state.x,y:state.y,yaw:state.yaw}:null,detail:structuredClone(detail)};
    this.events.push(event);return event;
  }
  judge(choice,state) {
    if(this.initial||!Object.hasOwn(INITIAL_JUDGMENTS,choice))return false;
    this.initial=this.record('initialJudgment',{choice,label:INITIAL_JUDGMENTS[choice]},state);return true;
  }
  snapshot() { return {initial:structuredClone(this.initial),events:structuredClone(this.events),sequence:this.sequence}; }
}
