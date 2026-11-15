/** Run only independent game checks. Does not execute the frozen research suite. */
import fs from 'node:fs';import path from 'node:path';import {gunzipSync} from 'node:zlib';import {pathToFileURL} from 'node:url';
const site=path.resolve(process.argv[2]||'site'),output=process.argv[3];
const {default:load}=await import(pathToFileURL(site+'/vendor/mujoco/mujoco.js'));
const {RobotWorld,unpackTar,installAssets}=await import(pathToFileURL(site+'/robot-physics.js'));
const mj=await load({wasmBinary:gunzipSync(fs.readFileSync(site+'/vendor/mujoco/mujoco.wasm.gz'))});installAssets(mj,unpackTar(gunzipSync(fs.readFileSync(site+'/media/robot-play/world.tar.gz'))));
const world=new RobotWorld(mj,JSON.parse(fs.readFileSync(site+'/media/robot-play/manifest.json'))),result={engine:mj.mj_versionString(),manual:[],rolling:[]};
function check(test,message){if(!test)throw new Error(message);}
function untilIdle(){for(let i=0;i<18000&&world.legControl.busy;i++){world.step();check(world.state().finite&&world.state().tilt<18,'manual action lost balance');}check(!world.legControl.busy&&!world.legControl.error,'manual action did not finish');}
for(let j=0;j<4;j++){
 world.reset(0);world.selectLeg(j);const before=world.legControl.state();check(world.legAction('lift'),'lift rejected');untilIdle();const lift=world.legControl.state();
 check(lift.positions[j][2]>before.positions[j][2]+.06&&lift.loads[j]<.1,'selected wheel did not physically unload and lift');
 check(world.legAction('advance'),'advance rejected');untilIdle();const advance=world.legControl.state();check(advance.positions[j][0]>lift.positions[j][0]+.07,'selected wheel did not advance');
 check(world.legAction('land'),'land rejected');untilIdle();for(let i=0;i<250;i++)world.step();const land=world.legControl.state();check(land.loads[j]>.2&&!land.lifted,'selected wheel did not land and bear weight');
 result.manual.push({leg:j,before,lift,advance,land,state:world.state()});console.log('manual',j,'passed');
}
for(const pose of ['normal','high','low'])for(const speed of [.15,.45]){
 world.reset(1);world.setPose(pose);for(let i=0;i<1000;i++)world.step(0,0,true);let maxX=0,maxTilt=0,bodyTouch=false,maxRearX=-Infinity;
 for(let i=0;i<30000;i++){world.step(speed,0);const wheelPositions=Array.from(world.wheelBodies).map(b=>Array.from(world.data.xpos.slice(b*3,b*3+3)));maxRearX=Math.max(maxRearX,Math.min(...wheelPositions.map(p=>p[0])));maxX=Math.max(maxX,world.state().x);maxTilt=Math.max(maxTilt,world.state().tilt);if(i%10===0)bodyTouch ||= world.bodyContact();if(world.state().tilt>58)break;}
 check(maxRearX<world.course.barrier.far+.085,'all wheels crossed the threshold using wheel drive');result.rolling.push({pose,speed,maxX,maxRearX,maxTilt,bodyTouch,state:world.state()});console.log('rolling',pose,speed,'blocked at',maxX);
}
world.reset(1);check(world.legAction('cross'),'crossing rejected');let maxTilt=0,bodyTouches=0,gates=[],lastWait=null;
for(let i=0;i<85000;i++){
 const lc=world.legControl;
 if(lc.waiting){
  // Keep the foot in the air / on ground for a real pause, verifying user gates.
  const waiting={...lc.waiting},feet=lc.state().positions;for(let k=0;k<250;k++)world.step();check(lc.waiting?.action===waiting.action&&lc.waiting.leg===waiting.leg,'gate advanced without player input');
  gates.push({waiting,feet,state:world.state()});check(lc.command(waiting.action),'expected user action rejected');
 }
 world.step();maxTilt=Math.max(maxTilt,world.state().tilt);if(i%10===0&&world.bodyContact())bodyTouches++;
 check(world.state().finite&&world.state().tilt<18&&!lc.error,'guided crossing lost balance');
 if(lc.mode==='complete')break;
}
const lc=world.legControl;check(lc.mode==='complete'&&lc.crossed.length===4&&gates.length===12,'crossing did not complete all twelve user actions');
check(lc.anchors().every(p=>p[0]>world.course.barrier.far+.085),'all wheels did not clear threshold');check(bodyTouches===0,'non-wheel obstacle contact during crossing');
result.crossing={state:world.state(),legs:lc.state(),gates,maxTilt,bodyTouches};check(world.resumeWheels(),'could not resume wheel drive');world.setPose('high');for(let i=0;i<5000;i++)world.step(.3,0);check(world.state().x>3,'could not drive after landing');result.departure=world.state();
result.passed=true;if(output)fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');console.log('CONTROLS PASSED',JSON.stringify({manual:result.manual.length,rolling:result.rolling.length,gates:gates.length,maxTilt,bodyTouches}));world.destroy();
