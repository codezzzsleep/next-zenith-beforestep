import * as THREE from './vendor/three/three.module.js';
import {OrbitControls} from './vendor/three/OrbitControls.js';
import {COURSES,inflateGzip,modelRoute,clamp} from './robot-physics.js?v=wheellegs-2';

const $=id=>document.getElementById(id), canvas=$('world'),stage=canvas.parentElement;
const keys=new Set();let joystick=[0,0],touchBrake=false,stickPointer=null;
let world,worker,renderer,scene,camera,carCamera,controls,goalRing,routeLine,displayMeshes;
let ready=false,started=false,paused=true,modelsOn=false,auto=false,route=null,routeIndex=0;
let lastFrame=0,frameCount=0,view=0,goalHold=0,uiElapsed=0,objects=[],modelObjects=[];
const temp=new THREE.Vector3(),matrix=new THREE.Matrix4(),robotQuaternion=new THREE.Quaternion();
let miniRect={x:0,y:0,w:0,h:0};
let selectedLeg=0,practiceWheel=false,practiceFoot=false,lastLegAction='',crossDone=false,footMarker;
const legLabels=['右前','左前','右后','左后'];
let best={};try{best=JSON.parse(localStorage.getItem('beforestep.play.v2')||'{}');}catch{}
const time=s=>`${String(Math.floor(s/60)).padStart(2,'0')}:${String(Math.floor(s%60)).padStart(2,'0')}`;
function say(text){$('status').textContent=text;}
function sendInput(){
  const v=clamp((keys.has('w')||keys.has('ArrowUp')?1:0)-(keys.has('s')||keys.has('ArrowDown')?1:0)-joystick[1],-1,1)*.45;
  const w=clamp((keys.has('a')||keys.has('ArrowLeft')?1:0)-(keys.has('d')||keys.has('ArrowRight')?1:0)-joystick[0],-1,1)*.95;
  worker?.postMessage({type:'input',v,w,brake:keys.has(' ')||touchBrake});
  if(v||w||keys.has(' ')||touchBrake){auto=false;$('navigate').setAttribute('aria-pressed','false');$('navigate').textContent='按模型参考路线驾驶';}
}
function stopInput(){keys.clear();joystick=[0,0];touchBrake=false;stickPointer=null;$('stick').style.transform='';$('touch-brake').classList.remove('active');sendInput();}
function cancelAuto(){auto=false;worker?.postMessage({type:'cancelAuto'});$('navigate').setAttribute('aria-pressed','false');$('navigate').textContent='按模型参考路线驾驶';}
function setPaused(value){paused=value;worker?.postMessage({type:'paused',value});}

function setupScene(){
  renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:false,preserveDrawingBuffer:true});
  renderer.setPixelRatio(Math.min(devicePixelRatio,1));renderer.shadowMap.enabled=false;
  renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.shadowMap.autoUpdate=false;
  renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.1;
  scene=new THREE.Scene();scene.background=new THREE.Color('#192227');scene.fog=new THREE.Fog('#192227',19,60);
  camera=new THREE.PerspectiveCamera(49,1,.03,100);camera.up.set(0,0,1);camera.position.set(-2.2,-2.8,2.4);
  carCamera=new THREE.PerspectiveCamera(68,16/9,.03,80);carCamera.up.set(0,0,1);
  controls=new OrbitControls(camera,canvas);controls.enableDamping=true;controls.enablePan=false;
  controls.minDistance=1.25;controls.maxDistance=12;controls.maxPolarAngle=Math.PI*.47;
  controls.target.set(0,0,.3);controls.update();
  scene.add(new THREE.HemisphereLight('#dbeef4','#68706b',1.4));
  const sun=new THREE.DirectionalLight('#fff7e8',2.0);sun.position.set(-9,-7,8);sun.castShadow=true;
  sun.shadow.mapSize.set(1024,1024);Object.assign(sun.shadow.camera,{left:-13,right:13,top:8,bottom:-8,near:.1,far:35});
  sun.shadow.bias=-.0003;sun.shadow.normalBias=.01;scene.add(sun);
  const grid=new THREE.GridHelper(24,48,'#879281','#515b52');grid.rotation.x=Math.PI/2;grid.position.set(5,0,.005);
  grid.material.transparent=true;grid.material.opacity=.1;scene.add(grid);
  goalRing=new THREE.Group();
  const ring=new THREE.Mesh(new THREE.TorusGeometry(.65,.025,10,64),new THREE.MeshBasicMaterial({color:'#a5f1cb'}));ring.position.z=.035;
  goalRing.add(ring);
  const flag=new THREE.Mesh(new THREE.CylinderGeometry(.008,.008,1.15,8),new THREE.MeshStandardMaterial({color:'#bdd5bc'}));
  flag.rotation.x=Math.PI/2;flag.position.set(0,0,.575);goalRing.add(flag);
  const fabric=new THREE.Mesh(new THREE.PlaneGeometry(.32,.16),new THREE.MeshBasicMaterial({color:'#9de6c5',side:THREE.DoubleSide}));
  fabric.rotation.x=Math.PI/2;fabric.position.set(.16,0,1.07);goalRing.add(fabric);scene.add(goalRing);
  footMarker=new THREE.Mesh(new THREE.TorusGeometry(.105,.009,8,40),new THREE.MeshBasicMaterial({color:'#9de6c5',depthTest:false}));footMarker.renderOrder=5;footMarker.visible=false;scene.add(footMarker);
  const points=[];let seed=42;
  const rand=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
  for(let i=0;i<190;i++)points.push((rand()-.5)*120,(rand()-.5)*120,15+rand()*50);
  const stars=new THREE.BufferGeometry();stars.setAttribute('position',new THREE.Float32BufferAttribute(points,3));
  scene.add(new THREE.Points(stars,new THREE.PointsMaterial({color:'#d1dfda',size:.05,sizeAttenuation:true})));
}
function groundTexture(){
  const c=document.createElement('canvas');c.width=c.height=128;const ctx=c.getContext('2d'),image=ctx.createImageData(128,128);
  let seed=67;for(let i=0;i<image.data.length;i+=4){seed=(seed*1103515245+12345)>>>0;const n=108+(seed%37);image.data.set([n,n,n,255],i);}ctx.putImageData(image,0,0);
  const tex=new THREE.CanvasTexture(c);tex.wrapS=tex.wrapT=THREE.RepeatWrapping;tex.repeat.set(25,18);tex.colorSpace=THREE.SRGBColorSpace;return tex;
}
function buildGeometry(){
  const m=world.model,cache=new Map(),soil=groundTexture();
  for(let g=0;g<m.ngeom;g++){
    if(m.geom_group[g]===3)continue;
    const type=m.geom_type[g],s=m.geom_size.slice(g*3,g*3+3);let geometry;
    if(type===7){
      const id=m.geom_dataid[g];
      if(!cache.has(id)){
        const geom=new THREE.BufferGeometry(),va=m.mesh_vertadr[id],vn=m.mesh_vertnum[id],fa=m.mesh_faceadr[id],fn=m.mesh_facenum[id];
        const name=m.mesh_names[id],lod=displayMeshes?.[name];
        if(lod){
          geom.setAttribute('position',new THREE.Float32BufferAttribute(lod.positions,3));geom.setIndex(lod.indices);
          const position=m.mesh_pos.slice(id*3,id*3+3),quat=m.mesh_quat.slice(id*4,id*4+4);
          const inverse=new THREE.Matrix4().makeRotationFromQuaternion(new THREE.Quaternion(quat[1],quat[2],quat[3],quat[0])).invert();
          inverse.multiply(new THREE.Matrix4().makeTranslation(-position[0],-position[1],-position[2]));geom.applyMatrix4(inverse);
        }else{
          geom.setAttribute('position',new THREE.BufferAttribute(new Float32Array(m.mesh_vert.slice(va*3,(va+vn)*3)),3));
          geom.setIndex(new THREE.BufferAttribute(new Uint32Array(m.mesh_face.slice(fa*3,(fa+fn)*3)),1));
        }
        geom.computeVertexNormals();cache.set(id,geom);
      }geometry=cache.get(id);
    }else if(type===0){geometry=new THREE.PlaneGeometry(30,20);}
    else if(type===6)geometry=new THREE.BoxGeometry(s[0]*2,s[1]*2,s[2]*2);
    else if(type===2)geometry=new THREE.SphereGeometry(s[0],16,12);
    else if(type===5){geometry=new THREE.CylinderGeometry(s[0],s[0],s[1]*2,16);geometry.rotateX(Math.PI/2);}
    else if(type===3){geometry=new THREE.CapsuleGeometry(s[0],s[1]*2,8,12);geometry.rotateX(Math.PI/2);}
    else continue;
    let rgba=m.geom_rgba.slice(g*4,g*4+4);const mat=m.geom_matid[g];if(mat>=0)rgba=m.mat_rgba.slice(mat*4,mat*4+4);
    const color=type===0?new THREE.Color('#a2aaa5'):new THREE.Color().setRGB(Math.max(.015,rgba[0]),Math.max(.015,rgba[1]),Math.max(.015,rgba[2]),THREE.SRGBColorSpace);
    const isModel=m.geom_group[g]===4;
    const material=isModel?new THREE.MeshBasicMaterial({color:'#77f1c7',transparent:true,opacity:.3,depthWrite:false,depthTest:false,side:THREE.DoubleSide}):
      new THREE.MeshStandardMaterial({color,roughness:mat>=0?.6:.97,metalness:mat>=0?.13:0,map:type===0?soil:null});
    const mesh=new THREE.Mesh(geometry,material);mesh.matrixAutoUpdate=false;mesh.castShadow=!isModel&&type!==0;mesh.receiveShadow=!isModel;
    if(isModel){mesh.visible=false;mesh.renderOrder=3;modelObjects.push(mesh);}
    scene.add(mesh);objects.push({g,mesh});
  }
}
function syncGeometry(){
  const d=world.data;
  for(const {g,mesh}of objects){
    const p=g*3,r=g*9,rot=d.geom_xmat,pos=d.geom_xpos;
    mesh.matrix.set(rot[r],rot[r+1],rot[r+2],pos[p],rot[r+3],rot[r+4],rot[r+5],pos[p+1],rot[r+6],rot[r+7],rot[r+8],pos[p+2],0,0,0,1);
    mesh.matrixWorldNeedsUpdate=true;
    if(mesh.renderOrder===3)mesh.visible=modelsOn&&world.course.rocks;
    if(g===world.model.thresholdGeom)mesh.visible=world.course.threshold;
  }
  const ls=world.state().legs;const foot=ls?.positions[ls.selected];footMarker.visible=!!foot;if(foot){footMarker.position.set(...foot);footMarker.position.z-=.075;}
  const q=world.data.qpos;robotQuaternion.set(q[4],q[5],q[6],q[3]);
  carCamera.position.copy(temp.set(.28,0,.12).applyQuaternion(robotQuaternion)).add(new THREE.Vector3(q[0],q[1],q[2]));
  const forward=new THREE.Vector3(3,0,.06).applyQuaternion(robotQuaternion).add(new THREE.Vector3(q[0],q[1],q[2]));
  carCamera.up.copy(new THREE.Vector3(0,0,1).applyQuaternion(robotQuaternion));carCamera.lookAt(forward);
  if(view===0){
    const target=new THREE.Vector3(q[0],q[1],q[2]+.05),delta=target.sub(controls.target).multiplyScalar(.12);
    controls.target.add(delta);camera.position.add(delta);controls.update();
  }
}
function resize(){
  if(!renderer)return;const w=stage.clientWidth,h=stage.clientHeight;
  renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();
  miniRect={x:w-Math.min(w*.35,240)-16,y:h-Math.min(w*.35,240)*9/16-63,w:Math.min(w*.35,240),h:Math.min(w*.35,240)*9/16};
}
function render(){
  renderer.setScissorTest(false);renderer.setViewport(0,0,stage.clientWidth,stage.clientHeight);renderer.shadowMap.needsUpdate=true;
  if(view===1){carCamera.aspect=stage.clientWidth/stage.clientHeight;carCamera.updateProjectionMatrix();renderer.render(scene,carCamera);}
  else renderer.render(scene,camera);
  for(const m of modelObjects)m.visible=false;if(routeLine)routeLine.visible=false;
  const r=miniRect;renderer.setScissorTest(true);renderer.setScissor(r.x,r.y,r.w,r.h);renderer.setViewport(r.x,r.y,r.w,r.h);
  renderer.setClearColor('#15211c');renderer.clear(true,true,true);carCamera.aspect=16/9;carCamera.updateProjectionMatrix();renderer.render(scene,carCamera);
  renderer.setScissorTest(false);renderer.setClearColor(scene.background);
  for(const m of modelObjects)m.visible=modelsOn&&world.course.rocks;if(routeLine)routeLine.visible=modelsOn;
  frameCount++;
}
function updateRoute(){
  if(routeLine){scene.remove(routeLine);routeLine.geometry.dispose();routeLine.material.dispose();routeLine=null;}
  const s=world.state();route=world.course.rocks?modelRoute([s.x,s.y],world.course.goal,world.manifest.models):null;routeIndex=0;
  if(route){const geometry=new THREE.BufferGeometry().setFromPoints(route.map(p=>new THREE.Vector3(p[0],p[1],.04)));
    routeLine=new THREE.Line(geometry,new THREE.LineBasicMaterial({color:'#b3f7d3',transparent:true,opacity:.85,depthTest:false}));
    routeLine.renderOrder=4;routeLine.visible=modelsOn;scene.add(routeLine);}
  return !!route;
}
function modelToggle(){
  if(!ready||!world.course.rocks)return;modelsOn=!modelsOn;
  if(modelsOn){updateRoute();say(route?'绿色显示已有生成模型和参考路线。你可以继续自己驾驶。':'当前位置没有可用参考路线，先后退或换个观察位置。');}
  else{cancelAuto();say('模型辅助已关闭，继续自己驾驶。');}
  $('models').setAttribute('aria-pressed',String(modelsOn));$('models').innerHTML=(modelsOn?'关闭模型辅助':'打开已有模型辅助')+' <span>'+(modelsOn?'−':'＋')+'</span>';
  $('navigate').disabled=!modelsOn||!route;
  $('model-hint').textContent=modelsOn?'模型来自项目已有的两次 Lux3D 返回。参考路线使用模型几何，遇到实际接触可以接管。':'第 3 项任务：查看完整石头形状，选择绕行。';
}
function switchCourse(index){
  if(!ready)return;stopInput();cancelAuto();modelsOn=false;world.reset(index);goalHold=0;practiceWheel=practiceFoot=crossDone=false;lastLegAction='';selectedLeg=0;$('finish').hidden=true;
  if(routeLine){scene.remove(routeLine);routeLine.geometry.dispose();routeLine.material.dispose();routeLine=null;}route=null;
  for(const b of $('courses').children)b.setAttribute('aria-pressed',String(Number(b.dataset.course)===index));
  $('begin-cross').hidden=!world.course.barrier;
  $('mission').textContent=world.course.instruction;goalRing.position.set(...world.course.goal,0);
  $('models').disabled=!world.course.rocks;$('navigate').disabled=true;$('models').setAttribute('aria-pressed','false');$('models').innerHTML='打开已有模型辅助 <span>＋</span>';
  $('model-hint').textContent='第 3 项任务：查看完整石头形状，选择绕行。';
  $('best').textContent=best[world.course.id]?'最佳 '+time(best[world.course.id]):'';
  setPaused(!started);setView(0);say(world.course.instruction);updateUI();
}
function setView(next){
  view=next;controls.enabled=view!==1;
  const s=world.state();
  if(view===0){controls.target.set(s.x,s.y,s.z+.05);camera.position.set(s.x-1.15,s.y-1.55,s.z+1.0);controls.update();}
  if(view===2){controls.target.set(5,0,0);camera.position.set(5,-.01,11.7);controls.update();}
  $('camera-label').textContent=['跟随视角','机器人视角','俯视全场'][view];
}
function updateUI(){
  const s=world.state();$('distance').textContent=s.goalDistance.toFixed(1)+' m';$('speed').innerHTML=s.speed.toFixed(2)+' <small>m/s</small>';
  $('tilt').textContent=s.tilt.toFixed(1)+'°';$('elapsed').textContent=time(s.elapsed);
  $('run-state').textContent=!started?'准备驾驶':paused?'已暂停':s.legs?'逐腿操作':auto?'模型参考驾驶':'手动驾驶';$('pause').textContent=paused?'继续':'暂停';
  for(const b of $('pose-controls').children){b.setAttribute('aria-pressed',String(b.dataset.pose===world.poseName));b.disabled=!!s.legs;}
  updateLegUI(s);updateCoach(s);
}
function complete(){
  setPaused(true);cancelAuto();stopInput();$('finish').hidden=false;
  const elapsed=world.state().elapsed;const id=world.course.id;
  if(!best[id]||elapsed<best[id]){best[id]=elapsed;try{localStorage.setItem('beforestep.play.v2',JSON.stringify(best));}catch{}}
  $('finish-text').textContent=`用时 ${time(elapsed)}。这是你这次驾驶的实时结果。`;
  $('finish-title').textContent=world.courseIndex===0?'轮行与逐腿，已掌握':world.courseIndex===1?'门槛通过！':'看清形状，完成绕行';
  $('next-course').textContent=world.courseIndex<2?'下一项任务':'再试第一项任务';say('任务完成，机器人已停稳。');
}
function frameBody(t){
  if(!ready)return;const dt=lastFrame?clamp((t-lastFrame)/1000,0,.045):0;lastFrame=t;
  if(started&&!paused&&!world.resetPending){
    const s=world.state();
    if(!s.finite)throw new Error('物理状态无法继续，请重新加载场景。');
    if(s.tilt>58){setPaused(true);cancelAuto();stopInput();say('机器人翻倒了。点击重新开始，再试一种开法。');}
    else if(s.bodyContact)say(world.course.barrier?'门槛挡住了轮行。重新开始，在门槛前进入逐腿跨越。':'车身接触高石，先后退，再参考完整模型选择绕行。');
    if(s.legs?.mode==='complete')crossDone=true;
    if(lastLegAction==='land'&&s.legs&&!s.legs.busy&&!s.legs.lifted&&s.legs.loads[s.legs.selected]>.2){practiceFoot=true;lastLegAction='';}
    if(s.goalDistance<.65&&s.speed<.16){goalHold+=dt;if(goalHold>.55){if(world.courseIndex===0){practiceWheel=true;if(practiceFoot)complete();}else if(world.courseIndex===1){if(crossDone)complete();}else complete();}}else goalHold=0;
  }
  syncGeometry();render();if(t-uiElapsed>150){updateUI();uiElapsed=t;}
  requestAnimationFrame(frame);
}
function frame(t){try{frameBody(t);}catch(e){setPaused(true);stopInput();fail(e);}}

function selectLeg(index){
  if(!ready||!started||paused)return;stopInput();cancelAuto();selectedLeg=index;worker.postMessage({type:'legSelect',index});
}
function legAction(action){
  if(!ready||!started||paused)return;const l=world.state().legs;if(l?.busy||l?.mode==='complete'||(l?.waiting&&l.waiting.action!==action)||(action==='lift'&&l?.lifted)||(action!=='lift'&&!l?.lifted))return;
  stopInput();cancelAuto();worker.postMessage({type:'legAction',action});
}
function updateLegUI(s){
  const l=s.legs;if(l)selectedLeg=l.selected;
  $('leg-title').textContent='操作'+legLabels[selectedLeg]+'腿';
  $('leg-state').textContent=l?.error?'需要重试':l?.busy?'动作执行中':l?.lifted?'轮腿已抬起':l?'支撑模式':'轮行模式';
  for(const button of $('leg-select').children){const j=Number(button.dataset.leg);button.setAttribute('aria-pressed',String(j===selectedLeg));button.disabled=!started||paused||s.speed>.08||!!l?.busy||!!l?.lifted;
    const airborne=l&&l.loads[j]<.1;button.classList.toggle('airborne',!!airborne);button.querySelector('small').textContent=airborne?'离地':l?'接地 · '+l.loads[j].toFixed(1)+' N':'接地';}
  for(const button of $('leg-actions').children){const action=button.dataset.action;const next=l?.waiting?.action||(l?.lifted?(lastLegAction==='advance'?'land':'advance'):'lift');
    button.disabled=!started||paused||s.speed>.08||!!l?.busy||!!l?.error||(l?.waiting?l.waiting.action!==action:action==='lift'?!!l?.lifted:!l?.lifted)||l?.mode==='complete';
    button.classList.toggle('next-action',!button.disabled&&next===action);}
  $('wheel-mode').disabled=!l||l.busy||l.lifted||!!l.waiting||!started||paused;
  $('begin-cross').hidden=!world.course.barrier||l?.mode==='crossing'||crossDone;
  $('begin-cross').disabled=!!l?.busy||!started||paused;
  $('cross-count').textContent=l?.mode==='crossing'||crossDone?`${l?.crossed.length??4} / 4 条腿已过门槛`:'一次抬一条腿';
  $('cross-hint').textContent=world.course.barrier?'跨越引导负责重心与支撑。每条腿的抬起、前移、落地，由你逐步触发。':'选腿后进入支撑模式。先把抬起的腿落地，再回到轮行。';
  $('leg-hint').textContent=l?.error|| (l?.busy?'正在缓慢调整重心和关节，等动作完成后继续。':l?.waiting?`接下来：${legLabels[l.waiting.leg]}腿${{lift:'抬起',advance:'前移',land:'落地'}[l.waiting.action]}。点击高亮动作。`:l?.lifted?'轮腿已经离地。前移一次约 10 厘米；落地后可选另一条腿。':'抬起时其余轮腿支撑。一次操作一条腿，落地后再选择下一条。');
}
function updateCoach(s){
  const l=s.legs;let step,title,text,progress;
  if(s.tilt>58){step='重新开始';title=world.course.barrier?'轮行没能通过门槛':'机器人失去平衡';text=world.course.barrier?'点击“重新开始”，在门槛前进入逐腿跨越，用腿的抬、移、落通过。':'点击“重新开始”，停稳后再操作轮腿。';progress='R / 重新开始';}
  else if(l?.error){step='请调整动作';title='目标超出当前可达范围';text=l.error;progress='R / 重新开始';}
  else if(world.courseIndex===0){
    step=practiceWheel?'02 / 亲手抬腿':'01 / 学会轮行';
    if(!practiceWheel){title='开进绿色区域，再停稳';text='W / ↑ 前进，A D 转向；手机用左下摇杆。到绿色区域后，试一次抬、移、落。';progress='轮行 → 逐腿';}
    else if(practiceFoot){title='回到轮行，停在绿色区域';text='点击“回到轮行”，把机器人开到绿色区域停稳，完成第一项任务。';progress='已掌握抬、移、落';}
    else{title=l?.busy?'让重心和轮腿慢慢就位':l?.lifted?'现在前移，再落地':'选一条腿，亲手抬起';text=l?.lifted?'点击“前移 K”，看轮子向前送出；接着点击“落地 L”，观察接地状态。':'在下方点选一条腿，点击“抬起 J”。高亮的轮子会离地，其余轮腿继续支撑。';progress='抬起 → 前移 → 落地';}
  }else if(world.courseIndex===1){
    step='02 / 门槛需要腿';progress=`${l?.crossed.length|| (crossDone?4:0)} / 4 条腿`;
    if(crossDone){title='四条腿已过门槛，回到轮行';text='点击“回到轮行”，前进到绿色终点并停稳。';}
    else if(l?.waiting){const a={lift:'抬起',advance:'前移',land:'落地'}[l.waiting.action];title=`${legLabels[l.waiting.leg]}腿：${a}`;text={lift:'点击“抬起”，让轮子离地并高于门槛。',advance:'轮子已离地。点击“前移”，把它送到门槛另一侧。',land:'轮子已越过门槛。点击“落地”，在另一侧恢复支撑。'}[l.waiting.action];}
    else if(l?.mode==='crossing'){title='正在调整支撑与重心';text='让其余轮腿站稳，再操作下一条腿。动作就绪时，下方会高亮下一步。';}
    else{title='轮子被挡住，试着迈腿';text='门槛高 12 厘米并横贯通道。可先试轮行；点击“进入逐腿跨越”，亲手完成四条腿的抬、移、落。';}
  }else{
    step='03 / 看清再绕行';progress=modelsOn?'完整形状已显示':'照片 → 3D → 路线';
    title=modelsOn?'沿参考路线绕行，也可以自己选路':'高石太高，先看看它的另一面';
    text=modelsOn?'绿色显示真实生成模型及绕行参考。自己驾驶，或跟随参考路线后随时用方向键接管。':'点击“打开已有模型辅助”。完整的石头形状会影响绕行距离；抬腿无法越过这些高石。';
  }
  $('coach-step').textContent=step;$('coach-title').textContent=title;$('coach-text').textContent=text;$('coach-progress').textContent=progress;
}
for(const button of $('leg-select').children)button.onclick=()=>selectLeg(Number(button.dataset.leg));
for(const button of $('leg-actions').children)button.onclick=()=>legAction(button.dataset.action);
$('begin-cross').onclick=()=>{if(!ready||!started||paused)return;stopInput();cancelAuto();worker.postMessage({type:'legAction',action:'cross'});};
$('wheel-mode').onclick=()=>{stopInput();worker.postMessage({type:'wheelMode'});};
for(const [i,course]of COURSES.entries()){
  const button=document.createElement('button');button.textContent=course.title;button.dataset.course=i;button.setAttribute('aria-pressed',String(i===0));
  button.onclick=()=>switchCourse(i);$('courses').append(button);
}
$('start').onclick=()=>{if(!ready)return;started=true;setPaused(false);$('start-layer').hidden=true;stage.classList.add('playing');$('pause').disabled=false;canvas.focus();say(world.course.instruction);};
$('pause').onclick=()=>{setPaused(!paused);stopInput();cancelAuto();updateUI();};
$('reset').onclick=$('again').onclick=()=>{if(ready)switchCourse(world.courseIndex);};
$('next-course').onclick=()=>switchCourse((world.courseIndex+1)%COURSES.length);
$('camera').onclick=()=>{if(ready)setView((view+1)%3);};$('models').onclick=modelToggle;
$('navigate').onclick=()=>{
  if(auto){cancelAuto();say('已交还手动驾驶。');return;}
  if(world.state().legs){say('先把抬起的腿落地，并回到轮行，再跟随模型参考路线。');return;}
  if(!modelsOn||!updateRoute()){say('没有可用模型参考路线，先自己调整位置。');return;}
  stopInput();auto=true;setPaused(false);worker.postMessage({type:'auto',route});$('navigate').setAttribute('aria-pressed','true');$('navigate').textContent='接管手动驾驶';say('按已有模型的参考路线行驶。按方向键或摇杆即可接管。');
};
for(const button of $('pose-controls').children)button.onclick=()=>{if(ready){world.setPose(button.dataset.pose);updateUI();say('正在调整轮腿姿态，继续驾驶看看反馈。');}};
canvas.addEventListener('pointerdown',()=>{if(started)canvas.focus();});
document.addEventListener('keydown',e=>{
  if(!ready||!started||/INPUT|TEXTAREA|SELECT/.test(e.target.tagName))return;
  const key=e.key.length===1?e.key.toLowerCase():e.key;
  if(['w','a','s','d','ArrowUp','ArrowDown','ArrowLeft','ArrowRight',' '].includes(key)){e.preventDefault();keys.add(key);sendInput();}
  if(e.repeat)return;
  if(['1','2','3','4'].includes(key))selectLeg(Number(key)-1);
  if(['j','k','l'].includes(key)){e.preventDefault();legAction({j:'lift',k:'advance',l:'land'}[key]);}
  if(key==='r')switchCourse(world.courseIndex);if(key==='h')modelToggle();if(key==='v')setView((view+1)%3);
});
document.addEventListener('keyup',e=>{keys.delete(e.key.length===1?e.key.toLowerCase():e.key);sendInput();});
window.addEventListener('blur',()=>{stopInput();cancelAuto();});
document.addEventListener('visibilitychange',()=>{if(document.hidden&&world){stopInput();cancelAuto();setPaused(true);updateUI();}});
const pad=$('joystick');
function padMove(e){const box=pad.getBoundingClientRect(),radius=box.width*.35;let x=(e.clientX-box.left-box.width/2)/radius,y=(e.clientY-box.top-box.height/2)/radius;
  const length=Math.hypot(x,y);if(length>1){x/=length;y/=length;}joystick=[x,y];$('stick').style.transform=`translate(${x*radius*.72}px,${y*radius*.72}px)`;sendInput();}
pad.addEventListener('pointerdown',e=>{if(!started)return;e.preventDefault();stickPointer=e.pointerId;pad.setPointerCapture(e.pointerId);padMove(e);});
pad.addEventListener('pointermove',e=>{if(e.pointerId===stickPointer)padMove(e);});
for(const name of ['pointerup','pointercancel','lostpointercapture'])pad.addEventListener(name,()=>{joystick=[0,0];stickPointer=null;$('stick').style.transform='';sendInput();});
const brake=$('touch-brake');brake.addEventListener('pointerdown',e=>{e.preventDefault();touchBrake=true;cancelAuto();sendInput();brake.setPointerCapture(e.pointerId);brake.classList.add('active');});
for(const name of ['pointerup','pointercancel','lostpointercapture'])brake.addEventListener(name,()=>{touchBrake=false;brake.classList.remove('active');sendInput();});
new ResizeObserver(resize).observe(stage);
function fail(error){console.error(error);$('start-layer').hidden=true;$('fallback').hidden=false;$('fallback-text').textContent=error?.message||'需要支持 WebGL 和 WebAssembly 的现代浏览器。';document.documentElement.dataset.playError='true';}
async function init(){
  try{
    if(!window.WebAssembly||!window.DecompressionStream)throw new Error('请使用较新的 Chrome、Edge 或 Safari 打开驾驶舱。');
    setupScene();resize();$('loading-text').textContent='正在加载原机器人与物理引擎…';
    const [manifest,wasm,bundle,display]=await Promise.all([
      fetch('media/robot-play/manifest.json?v=wheellegs-2').then(r=>{if(!r.ok)throw new Error('资产清单暂时无法加载');return r.json();}),
      fetch('vendor/mujoco/mujoco.wasm.gz').then(r=>{if(!r.ok)throw new Error('物理引擎暂时无法加载');return r.arrayBuffer();}),
      fetch('media/robot-play/world.tar.gz?v=wheellegs-2').then(r=>{if(!r.ok)throw new Error('机器人资产暂时无法加载');return r.arrayBuffer();}),
      fetch('media/robot-play/display.json.gz').then(r=>{if(!r.ok)throw new Error('机器人显示资产暂时无法加载');return r.arrayBuffer();}).then(inflateGzip).then(bytes=>JSON.parse(new TextDecoder().decode(bytes))),
    ]);
    $('loading-text').textContent='正在让机器人站稳…';displayMeshes=display;
    worker=new Worker('./robot-worker.js?v=wheellegs-2',{type:'module'});
    let model,engine,snapshot;
    await new Promise((resolve,reject)=>{
      worker.onerror=e=>reject(new Error(e.message));
      worker.onmessage=event=>{
        const data=event.data;
        if(data.type==='error'){reject(new Error(data.message));if(ready)fail(new Error(data.message));}
        else if(data.type==='legCommand'){if(!data.ok)say(data.action==='cross'?'先重新开始门槛关，保持车头朝前，在门槛前进入跨越。':'先完成当前动作，或跟着高亮按钮操作。');else if(data.action!=='wheelMode')lastLegAction=data.action;}
        else if(data.type==='ready'){model=data.model;engine=data.engine;}
        else if(data.type==='state'){
          snapshot=data.state;if(world){
            if(data.state.resetSeq<world.resetSeq)return;
            world.resetPending=false;world.snapshot=data.state;world.data=data.data;auto=data.state.auto;paused=data.state.paused;
            if(data.state.tilt>58)say('机器人翻倒了。点击重新开始，再试一种开法。');
          }
          else if(model){
            world={model,engine,manifest,data:data.data,snapshot:data.state,course:COURSES[0],courseIndex:0,resetSeq:0,resetPending:false,
              state(){return this.snapshot;},get poseName(){return this.snapshot.pose;},
              setPose(value){worker.postMessage({type:'pose',value});},
              reset(index){this.courseIndex=index;this.course=COURSES[index];this.resetPending=true;worker.postMessage({type:'reset',seq:++this.resetSeq,index,running:started});}};
            resolve();
          }
        }
      };
      worker.postMessage({type:'init',manifest,wasm,bundle},[wasm,bundle]);
    });
    buildGeometry();ready=true;switchCourse(Math.floor(clamp(Number(new URLSearchParams(location.search).get('course'))||0,0,2)));resize();syncGeometry();render();
    $('loading-text').textContent='机器人已就绪。你来掌握方向。';$('start').disabled=false;
    document.documentElement.dataset.playReady='true';
    window.__robotPlay={world,get state(){return {...world.state(),ready,started,paused,modelsOn,auto,course:world.course.id,frames:frameCount,engine:world.engine,routePoints:route?.length||0};},get route(){return route;},get renderer(){return renderer;}};
    requestAnimationFrame(frame);
  }catch(e){fail(e);}
}
init();
