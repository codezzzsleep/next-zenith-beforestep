/** Certificates bind real rehearsals to a selection, route and stationary pose. */
export const wrapAngle=a=>Math.atan2(Math.sin(a),Math.cos(a));
export function sameAnchor(state,anchor){
  return !!anchor&&Math.hypot(state.x-anchor.x,state.y-anchor.y)<.065&&Math.abs(wrapAngle(state.yaw-anchor.yaw))<.08&&state.speed<.025&&(anchor.poseName===undefined||anchor.poseName===state.poseName)&&(anchor.z===undefined||Math.abs(state.z-anchor.z)<.035)&&(anchor.tilt===undefined||Math.abs(state.tilt-anchor.tilt)<.8);
}
export function completeWorldProof(proof){
  if(!proof?.passed||proof.cancelled||!proof.plan?.path?.length||!Array.isArray(proof.expectedWorlds)||!proof.expectedWorlds.length||!Array.isArray(proof.results))return false;
  if(proof.expectedWorlds.some(tasks=>!Array.isArray(tasks)||!tasks.length||tasks.some(id=>!Number.isFinite(id))))return false;
  const identity=tasks=>[...tasks].sort((a,b)=>a-b).join(':');
  const expected=new Set(proof.expectedWorlds.map(identity)),actual=new Set();
  for(const result of proof.results){if(!result.passed||result.cancelled||result.reason!=='completed'||!Array.isArray(result.tasks)||!result.tasks.length||result.tasks.some(id=>!Number.isFinite(id)))return false;actual.add(identity(result.tasks));}
  return proof.expectedWorlds.length===expected.size&&proof.results.length===expected.size&&actual.size===expected.size&&[...expected].every(id=>actual.has(id));
}
export function usableProof(proof,state,revision,observationVersion=0){
  const complete=proof?.expectedWorlds?completeWorldProof(proof):!!proof?.passed;
  return complete&&proof.revision===revision&&(proof.observationVersion??0)===observationVersion&&sameAnchor(state,proof.anchor);
}
export function progressOnPath(state,path){
  let best=Infinity,index=1;
  for(let i=1;i<path.length;i++){
    const a=path[i-1],b=path[i],dx=b[0]-a[0],dy=b[1]-a[1],t=Math.max(0,Math.min(1,((state.x-a[0])*dx+(state.y-a[1])*dy)/(dx*dx+dy*dy)));
    const distance=Math.hypot(state.x-a[0]-t*dx,state.y-a[1]-t*dy);
    if(distance<best){best=distance;index=i;}
  }
  return {distance:best,index};
}
