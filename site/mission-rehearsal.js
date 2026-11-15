import {RouteFollower} from './mission-world.js?v=mission-1';

/** The same complete motor simulation runs in the browser and verification CLI. */
export async function rehearseRoute(world,path,{onFrame=()=>{},cancelled=()=>false,yieldFrame=async()=>{}}={}){
  const follower=new RouteFollower(path);let maxTilt=0,contact=null;
  while(world.elapsed<210&&!follower.done){
    for(let i=0;i<600&&!follower.done;i++){
      if(cancelled())return {cancelled:true};
      const input=follower.command(world);world.step(input.v,input.w,input.brake);
      if(world.steps%10===0){
        const s=world.state(),c=world.contacts();maxTilt=Math.max(maxTilt,s.tilt);
        if(c.high||c.wall||c.gateBody||s.tilt>25||!s.finite){contact={...c,tilt:s.tilt};break;}
      }
    }
    onFrame(world);if(contact)break;await yieldFrame();
  }
  return {passed:follower.done&&!contact,maxTilt,contact,elapsed:world.elapsed,final:world.state(),reason:contact?'contact':follower.done?'completed':'timeout'};
}

export async function rehearseCrossing(world,{onFrame=()=>{},cancelled=()=>false,yieldFrame=async()=>{}}={}){
  if(!world.legAction('cross'))return {passed:false,reason:'not_aligned_before_threshold'};
  let maxTilt=0,contact=null,actions=[];
  while(world.elapsed<210){
    for(let i=0;i<600;i++){
      if(cancelled())return {cancelled:true};
      const l=world.legControl;
      if(l.waiting){actions.push({...l.waiting});l.command(l.waiting.action);}
      world.step();
      if(world.steps%10===0){const s=world.state(),c=world.contacts();maxTilt=Math.max(maxTilt,s.tilt);if(c.high||c.wall||c.gateBody||s.tilt>25||!s.finite){contact={...c,tilt:s.tilt};break;}}
      if(l.error||l.mode==='complete')break;
    }
    onFrame(world);if(contact||world.legControl.error||world.legControl.mode==='complete')break;await yieldFrame();
  }
  const complete=world.legControl.mode==='complete',allWheelsOver=world.anchors().every(p=>p[0]-.086>world.course.barrier.far);
  return {passed:complete&&allWheelsOver&&!contact&&!world.legControl.error,reason:contact?'contact':world.legControl.error||(!complete?'timeout':!allWheelsOver?'wheels_not_clear':'completed'),actions,maxTilt,contact,elapsed:world.elapsed,final:world.state()};
}
