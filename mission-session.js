/** Certificates bind real rehearsals to a selection, route and stationary pose. */
export const wrapAngle=a=>Math.atan2(Math.sin(a),Math.cos(a));
export function sameAnchor(state,anchor){
  return !!anchor&&Math.hypot(state.x-anchor.x,state.y-anchor.y)<.065&&Math.abs(wrapAngle(state.yaw-anchor.yaw))<.08&&state.speed<.025&&(anchor.poseName===undefined||anchor.poseName===state.poseName)&&(anchor.z===undefined||Math.abs(state.z-anchor.z)<.035)&&(anchor.tilt===undefined||Math.abs(state.tilt-anchor.tilt)<.8);
}
export function usableProof(proof,state,revision){return !!proof?.passed&&proof.revision===revision&&sameAnchor(state,proof.anchor);}
export function progressOnPath(state,path){
  let best=Infinity,index=1;
  for(let i=1;i<path.length;i++){
    const a=path[i-1],b=path[i],dx=b[0]-a[0],dy=b[1]-a[1],t=Math.max(0,Math.min(1,((state.x-a[0])*dx+(state.y-a[1])*dy)/(dx*dx+dy*dy)));
    const distance=Math.hypot(state.x-a[0]-t*dx,state.y-a[1]-t*dy);
    if(distance<best){best=distance;index=i;}
  }
  return {distance:best,index};
}
