import * as THREE from './vendor/three/three.module.js';
import {OrbitControls} from './vendor/three/OrbitControls.js';
import './gallery-viewer.js?v=report-v3-1';
import {inflateGzip,clamp} from './robot-physics.js?v=mission-1';
import {accepted,admissionChecks,planRoute,modelWorlds} from './mission-planner.js?v=mission-1';
const $=id=>document.getElementById(id),canvas=$('world'),stage=canvas.parentElement;
let world,worker,renderer,scene,camera,carCamera,controls,goalRing,routeLine,displayMeshes,footMarker,view=0,objects=[],modelObjects=[],miniRect={x:0,y:0,w:0,h:0};
const temp=new THREE.Vector3(),robotQuaternion=new THREE.Quaternion();
let mission,ready=false,checked=false,selected=[],focusId=null,phase='observation',paused=true,previewResults=[],currentPlan=null,gateResult=null,gateScan=null,lastUI=0,keys=new Set(),joystick=[0,0],touchBrake=false,stickPointer=null;
const labels=['右前','左前','右后','左后'];
const say=t=>$('stage-message').textContent=t;
const post=m=>worker?.postMessage(m);
function setupScene(){
  renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:false,preserveDrawingBuffer:true});
  renderer.setPixelRatio(Math.min(devicePixelRatio,1));renderer.shadowMap.enabled=false;
  renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.shadowMap.autoUpdate=false;
  renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.1;
  scene=new THREE.Scene();scene.background=new THREE.Color('#0b1320');scene.fog=new THREE.Fog('#0b1320',19,60);
  camera=new THREE.PerspectiveCamera(49,1,.03,100);camera.up.set(0,0,1);camera.position.set(-2.2,-2.8,2.4);
  carCamera=new THREE.PerspectiveCamera(68,16/9,.03,80);carCamera.up.set(0,0,1);
  controls=new OrbitControls(camera,canvas);controls.enableDamping=true;controls.enablePan=false;
  controls.minDistance=1.25;controls.maxDistance=12;controls.maxPolarAngle=Math.PI*.47;
  controls.target.set(0,0,.3);controls.update();
  scene.add(new THREE.HemisphereLight('#e6e8ec','#666970',1.4));
  const sun=new THREE.DirectionalLight('#ffffff',2.0);sun.position.set(-9,-7,8);sun.castShadow=true;
  sun.shadow.mapSize.set(1024,1024);Object.assign(sun.shadow.camera,{left:-13,right:13,top:8,bottom:-8,near:.1,far:35});
  sun.shadow.bias=-.0003;sun.shadow.normalBias=.01;scene.add(sun);
  const grid=new THREE.GridHelper(24,48,'#8b96aa','#53627a');grid.rotation.x=Math.PI/2;grid.position.set(5,0,.005);
  grid.material.transparent=true;grid.material.opacity=.1;scene.add(grid);
  goalRing=new THREE.Group();
  const ring=new THREE.Mesh(new THREE.TorusGeometry(.35,.025,10,64),new THREE.MeshBasicMaterial({color:'#53cdb9'}));ring.position.z=.035;
  goalRing.add(ring);
  const flag=new THREE.Mesh(new THREE.CylinderGeometry(.008,.008,1.15,8),new THREE.MeshStandardMaterial({color:'#a9b6cb'}));
  flag.rotation.x=Math.PI/2;flag.position.set(0,0,.575);goalRing.add(flag);
  const fabric=new THREE.Mesh(new THREE.PlaneGeometry(.32,.16),new THREE.MeshBasicMaterial({color:'#53cdb9',side:THREE.DoubleSide}));
  fabric.rotation.x=Math.PI/2;fabric.position.set(.16,0,1.07);goalRing.add(fabric);scene.add(goalRing);
  footMarker=new THREE.Mesh(new THREE.TorusGeometry(.105,.009,8,40),new THREE.MeshBasicMaterial({color:'#f0a93b',depthTest:false}));footMarker.renderOrder=5;footMarker.visible=false;scene.add(footMarker);
  const points=[];let seed=42;
  const rand=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
  for(let i=0;i<190;i++)points.push((rand()-.5)*120,(rand()-.5)*120,15+rand()*50);
  const stars=new THREE.BufferGeometry();stars.setAttribute('position',new THREE.Float32BufferAttribute(points,3));
  scene.add(new THREE.Points(stars,new THREE.PointsMaterial({color:'#d6deea',size:.05,sizeAttenuation:true})));
}
function groundTexture(){
  const c=document.createElement('canvas');c.width=c.height=128;const ctx=c.getContext('2d'),image=ctx.createImageData(128,128);
  let seed=67;for(let i=0;i<image.data.length;i+=4){seed=(seed*1103515245+12345)>>>0;const n=108+(seed%37);image.data.set([n,n,n,255],i);}ctx.putImageData(image,0,0);
  const tex=new THREE.CanvasTexture(c);tex.wrapS=tex.wrapT=THREE.RepeatWrapping;tex.repeat.set(25,18);tex.colorSpace=THREE.SRGBColorSpace;return tex;
}
function buildGeometry(){
  for(const {mesh}of objects){scene.remove(mesh);mesh.geometry.dispose();mesh.material.dispose();}objects=[];modelObjects=[];

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
    else if(type===1){
      const id=m.geom_dataid[g],nr=m.hfield_nrow[id],nc=m.hfield_ncol[id],adr=m.hfield_adr[id],sz=m.hfield_size.slice(id*4,id*4+4);
      geometry=new THREE.PlaneGeometry(sz[0]*2,sz[1]*2,nc-1,nr-1);const p=geometry.attributes.position;
      for(let k=0;k<p.count;k++){const col=k%nc,row=nr-1-Math.floor(k/nc);p.setZ(k,m.hfield_data[adr+row*nc+col]*sz[2]);}geometry.computeVertexNormals();
    }else if(type===6)geometry=new THREE.BoxGeometry(s[0]*2,s[1]*2,s[2]*2);
    else if(type===2)geometry=new THREE.SphereGeometry(s[0],16,12);
    else if(type===5){geometry=new THREE.CylinderGeometry(s[0],s[0],s[1]*2,16);geometry.rotateX(Math.PI/2);}
    else if(type===3){geometry=new THREE.CapsuleGeometry(s[0],s[1]*2,8,12);geometry.rotateX(Math.PI/2);}
    else continue;
    let rgba=m.geom_rgba.slice(g*4,g*4+4);const mat=m.geom_matid[g];if(mat>=0)rgba=m.mat_rgba.slice(mat*4,mat*4+4);
    const color=type<=1?new THREE.Color('#a3a3a3'):new THREE.Color().setRGB(Math.max(.015,rgba[0]),Math.max(.015,rgba[1]),Math.max(.015,rgba[2]),THREE.SRGBColorSpace);
    if(type>1&&color.r>color.b*1.3&&color.r>color.g)color.set('#848484');
    const isModel=m.geom_group[g]===4;
    const material=isModel?new THREE.MeshBasicMaterial({color:'#8d9fb6',transparent:true,opacity:.3,depthWrite:false,depthTest:false,side:THREE.DoubleSide}):
      new THREE.MeshStandardMaterial({color,roughness:mat>=0?.6:.97,metalness:mat>=0?.13:0,map:type<=1?soil:null});
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
    if(mesh.renderOrder===3)mesh.visible=true;

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
  renderer.setScissorTest(false);renderer.setViewport(0,0,stage.clientWidth,stage.clientHeight);renderer.shadowMap.needsUpdate=false;
  if(view===1){carCamera.aspect=stage.clientWidth/stage.clientHeight;carCamera.updateProjectionMatrix();renderer.render(scene,carCamera);}
  else renderer.render(scene,camera);
  if(routeLine)routeLine.visible=false;
  const r=miniRect;renderer.setScissorTest(true);renderer.setScissor(r.x,r.y,r.w,r.h);renderer.setViewport(r.x,r.y,r.w,r.h);
  renderer.setClearColor('#0b1320');renderer.clear(true,true,true);carCamera.aspect=16/9;carCamera.updateProjectionMatrix();renderer.render(scene,carCamera);
  renderer.setScissorTest(false);renderer.setClearColor(scene.background);
  if(routeLine)routeLine.visible=true;
}
function setView(next){
  view=next;controls.enabled=view!==1;if(!world)return;const s=world.state();
  if(view===0){controls.target.set(s.x,s.y,s.z+.05);camera.position.set(s.x-1.05,s.y-1.55,s.z+1.05);controls.update();}
  if(view===2){controls.target.set(6.3,0,.1);camera.position.set(6.3,-.01,7.4);controls.update();}
}
function drawRoute(plan){
  currentPlan=plan;if(routeLine){scene.remove(routeLine);routeLine.geometry.dispose();routeLine.material.dispose();routeLine=null;}
  if(!plan?.path)return;const geometry=new THREE.BufferGeometry().setFromPoints(plan.path.map(p=>new THREE.Vector3(p[0],p[1],.035)));
  routeLine=new THREE.Line(geometry,new THREE.LineBasicMaterial({color:'#f0a93b',depthTest:false}));routeLine.renderOrder=4;scene.add(routeLine);
}
const sourceBase='https://media.githubusercontent.com/media/codezzzsleep/next-zenith-beforestep/3e4acf64d18e638d0c1342793fc367ed92955135/';
function inputURL(c){return sourceBase+c.input;}
function focusCandidate(c){
  focusId=c.task_id;document.querySelectorAll('.candidate').forEach(b=>b.classList.toggle('focused',Number(b.dataset.task)===focusId));
  $('input-'+c.target).src=inputURL(c);document.querySelectorAll('[data-target]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.target===c.target)));
  $('model-detail').hidden=false;$('model-name').textContent=`高石 ${c.target==='T1'?'A':'B'} / 候选 ${c.sample} · Lux3D ${c.task_id}`;
  $('checks').replaceChildren();for(const check of admissionChecks(c,mission.thresholds)){const row=document.createElement('div');row.className=check.pass?'passed':'rejected';const name=document.createElement('span'),value=document.createElement('span');name.textContent=check.label;value.textContent=`${check.value.toFixed(3)} · ${check.pass?'通过':'不通过'}`;row.append(name,value);$('checks').append(row);}
  $('model-source').href='gallery.html?v=site-design-3';$('raw-model').dataset.source=sourceBase+c.original_model;if($('model-detail').open)$('raw-model').src=$('raw-model').dataset.source;
}
function renderCandidates(){
  $('candidates').replaceChildren();for(const target of ['T1','T2']){
    const group=document.createElement('div');group.className='candidate-group';const title=document.createElement('strong');title.textContent=`高石 ${target==='T1'?'A':'B'} · 照片生成的完整候选`;group.append(title);const grid=document.createElement('div');grid.className='candidate-grid';
    for(const c of mission.candidates.filter(c=>c.target===target).sort((a,b)=>a.sample.localeCompare(b.sample))){
      const b=document.createElement('button');b.className='candidate'+(checked&&!accepted(c,mission.thresholds)?' rejected':'');b.dataset.task=c.task_id;b.setAttribute('aria-pressed',String(selected.includes(c.task_id)));b.innerHTML=`${c.sample}<small>${checked?(accepted(c,mission.thresholds)?selected.includes(c.task_id)?'已选 ✓':'可选择':'被拒'):'待核对'}</small>`;
      b.onclick=()=>{if(!['candidates','decision'].includes(phase))return;focusCandidate(c);if(!checked){say('先用原观测核对候选，看看哪些完整形状可信。');return;}if(!accepted(c,mission.thresholds)){say('这份模型与可见观测不符，不能放进预演。可展开查看具体原因。');return;}selected=selected.includes(c.task_id)?selected.filter(id=>id!==c.task_id):[...selected,c.task_id];previewResults=[];phase='candidates';renderCandidates();inspect();updateUI();};grid.append(b);
    }group.append(grid);$('candidates').append(group);
  }
  const a=selected.filter(id=>mission.candidates.find(c=>c.task_id===id).target==='T1').length,b=selected.length-a;$('selection-summary').textContent=checked?`已选 A ${a} 份 × B ${b} 份 = ${a*b} 个预演世界`:'11 份真实生成结果，等待观测核对。';
  if(focusId)focusCandidate(mission.candidates.find(c=>c.task_id===focusId));
}
function inspect(){
  const show=selected.length?selected:['T1','T2'].map(t=>mission.candidates.find(c=>c.target===t&&accepted(c,mission.thresholds)).task_id);
  post({type:'inspect',selected:show});if(checked)drawRoute(planRoute(mission,selected));
}
function reset(){if(!ready)return;stopInput();checked=false;selected=[];phase='observation';previewResults=[];gateResult=gateScan=null;drawRoute(null);post({type:'reset'});$('debrief').hidden=true;$('model-detail').open=false;$('preview-results').hidden=true;$('candidates').hidden=true;$('check').hidden=true;$('selection-summary').textContent='';$('observation-cover').hidden=false;updateUI();}
function sendInput(){
  const v=clamp((keys.has('w')||keys.has('ArrowUp')?1:0)-(keys.has('s')||keys.has('ArrowDown')?1:0)-joystick[1],-1,1)*.36,w=clamp((keys.has('a')||keys.has('ArrowLeft')?1:0)-(keys.has('d')||keys.has('ArrowRight')?1:0)-joystick[0],-1,1)*.8;
  post({type:'input',v,w,brake:keys.has(' ')||touchBrake});
}
function stopInput(){keys.clear();joystick=[0,0];touchBrake=false;stickPointer=null;$('stick').style.transform='';$('touch-brake').classList.remove('active');sendInput();}
function updateUI(){
  if(!ready)return;const s=world.state(),l=s.legs;let step=0,title,text,action,disabled=false;
  const busy=['preview','gate-preview','wheel-trial'].includes(phase),drive=['execute','gate','finish-drive'].includes(phase);
  document.querySelector('.camera-mini-label').hidden=phase==='observation';$('pause').hidden=!['execute','crossing','finish-drive'].includes(phase);$('pause').textContent=paused?'继续':'暂停';$('touch-controls').hidden=!drive;$('follow').hidden=phase!=='execute'||s.automatic;
  $('candidates').hidden=phase==='observation';$('check').hidden=checked||phase==='observation';$('check').disabled=busy;$('preview-progress').hidden=!busy;
  $('leg-console').hidden=!['crossing','finish-drive'].includes(phase);$('gate-info').hidden=!['gate','gate-preview','crossing','finish-drive','complete'].includes(phase);
  document.querySelectorAll('.candidate').forEach(b=>b.disabled=!['candidates','decision'].includes(phase));
  if(phase==='observation'){title='前面有路，石头后面呢？';text='先查看这两块高石的真实照片，再把 Lux3D 生成的完整形状带进路线判断。';action='查看 Lux3D 生成结果';}
  else if(phase==='candidates'){
    step=1;title=checked?'这些背面，会改变你怎么走。':'完整形状，还得和观测对得上。';text=checked?'绿色模型构成预演世界。点选 A、B 候选，路线与需要验证的组合随之改变。':'用原观测检查轮廓、尺寸、表面贴合与已知空地；点击候选可查看完整指标。';action=checked?'在所选模型里完整预演':'用原观测核对候选';disabled=checked&&!modelWorlds(mission,selected).length;
  }else if(phase==='preview'){step=2;title='让这条路线，在每个可能的世界里走完。';text='你选的完整模型正在作为碰撞几何参与计算。每个组合都从起点行驶到门槛前。';action='物理预演中…';disabled=true;}
  else if(phase==='decision'){step=2;const passed=previewResults.length&&previewResults.every(r=>r.passed);title=passed?'所选世界通过，现在交给机器人。':'有模型世界没能通过，请调整候选。';text=passed?`${previewResults.length} 个组合均完成绕行。执行会回到原月面场景；按方向键或摇杆可随时接管。`:'查看未通过的组合，重新选择可信模型并预演。';action=passed?'执行这条经过预演的路线':'返回候选选择';}
  else if(phase==='execute'){step=3;title=s.automatic?'模型里的判断，变成实际绕行。':'你正在接管轮行。';text=s.automatic?'机器人按通过预演的路线绕开高石。方向键、WASD 或摇杆可以接管；到门槛前会停下来观察。':'WASD / 方向键或摇杆驾驶，空格刹车。也可以继续按已验证路线驶向门槛。';action='正在绕行…';disabled=true;}
  else if(phase==='gate'){step=4;title=gateResult?.passed?'跨越预演通过，轮到你迈腿。':'车轮被挡住了，先试一遍怎么迈。';text=gateResult?.passed?'点击开始，然后逐条腿完成抬起、前移、落地。控制器辅助调整支撑与重心。':'机器人相机测到可见门槛。用这份几何预演跨越，看看车身与轮腿能否通过。';action=gateResult?.passed?'开始亲手逐腿跨越':'预演可见门槛的跨越';disabled=!!gateResult&&!gateResult.passed;}
  else if(phase==='gate-preview'){step=4;title='用刚看到的几何，试一遍逐腿跨越。';text='门槛测量直接进入轮腿控制器。检查四轮过线、车身接触与平衡，再交给你操作。';action='跨越预演中…';disabled=true;}
  else if(phase==='wheel-trial'){step=4;title='同一块门槛，先试试只用轮子。';text='这里固定腿姿，向前驱动车轮。观察轮子被门槛挡住的实际反馈，再决定下一步。';action='轮行尝试中…';disabled=true;}
  else if(phase==='crossing'){
    step=4;title=l?.waiting?`${labels[l.waiting.leg]}腿：${{lift:'抬起',advance:'前移',land:'落地'}[l.waiting.action]}`:'让支撑与重心慢慢就位。';text=l?.waiting?{lift:'点下方高亮的“抬起”，让轮子离地并高于门槛。',advance:'轮子已离地。点“前移”，把它送到门槛另一侧。',land:'轮子已越过门槛。点“落地”，在另一侧重新支撑。'}[l.waiting.action]:'动作就绪时，下方高亮下一步。四条腿的 12 个主要动作分别由你触发。';action=paused?'点击右上继续':'操作下方高亮轮腿动作';disabled=true;
  }else if(phase==='finish-drive'){step=5;title=l?'四条腿都过去了，回到轮行。':'最后一小段，用轮子抵达。';text=l?'点击下方“回到轮行”，恢复轮子驱动，再驶入绿色圆圈。':'W / ↑ 或摇杆前进；进入绿色圆圈后，机器人会自动制动停稳。';action='等待抵达终点';disabled=true;}
  else if(phase==='complete'){step=5;title='抵达。照片、模型、判断和行动连起来了。';text='这次通行依靠模型判断高石背面的路线，也依靠轮腿跨越挡住车轮的门槛。';action='换一组候选，再试';}
  else{title='这次行动没能通过。';text='调整路线或重新开始。预演结果要由实际行动检验。';action='重新开始';}
  $('coach-step').textContent=`0${step+1} / ${['观察','核对 3D','模型预演','实际绕行','逐腿跨越','抵达与回顾'][step]}`;$('coach-title').textContent=title;$('coach-text').textContent=text;$('next').textContent=action;$('next').disabled=disabled;
  document.querySelectorAll('[data-step]').forEach(b=>{const n=Number(b.dataset.step);b.classList.toggle('done',n<step);if(n===step)b.setAttribute('aria-current','step');else b.removeAttribute('aria-current');});
  $('distance').textContent=s.goalDistance.toFixed(1)+' m';$('speed').textContent=s.speed.toFixed(2);$('tilt').textContent=s.tilt.toFixed(1)+'°';
  const candidateWorld=world.model.file!=='truth.xml',combo=mission.worlds.find(w=>w.file===world.model.file),comboLabel=combo?.tasks.map(id=>{const c=mission.candidates.find(c=>c.task_id===id);return (c.target==='T1'?'A / ':'B / ')+c.sample;}).join(' × ');$('scene-label').textContent=phase==='observation'?'机器人观察 / 原 R1 记录照片':candidateWorld?'Lux3D 模型世界 · '+comboLabel:phase==='gate-preview'?'可见门槛 · 物理跨越预演':phase==='wheel-trial'?'同一门槛 · 固定腿姿轮行试验':'原月面环境 · 实时机器人行动';
  if(l){$('leg-title').textContent='操作'+labels[l.selected]+'腿';$('leg-state').textContent=l.waiting?'等待你的动作':l.busy?'重心与关节调整中':'轮腿支撑';$('cross-count').textContent=`${l.crossed.length} / 4`;
    document.querySelectorAll('[data-leg]').forEach(b=>{const j=Number(b.dataset.leg);b.setAttribute('aria-pressed',String(j===l.selected));b.disabled=paused||l.busy||l.lifted||!!l.waiting;b.classList.toggle('airborne',l.loads[j]<.1);b.querySelector('small').textContent=l.loads[j]<.1?'离地':`${l.loads[j].toFixed(1)} N`;});
    document.querySelectorAll('[data-action]').forEach(b=>{b.disabled=paused||!l.waiting||b.dataset.action!==l.waiting.action;b.classList.toggle('next-action',!b.disabled);});
    $('leg-hint').textContent=l.waiting?`接下来：${labels[l.waiting.leg]}腿${{lift:'抬起',advance:'前移',land:'落地'}[l.waiting.action]}。点高亮动作，或按 ${ {lift:'J',advance:'K',land:'L'}[l.waiting.action]}。`:'其余轮腿支撑，等待动作就位。';
  }
  $('wheel-mode').hidden=phase!=='finish-drive'||!l;document.querySelectorAll('[data-pose]').forEach(b=>b.disabled=!!l||busy);
  $('wheel-trial').disabled=phase!=='gate';
  document.documentElement.dataset.missionPhase=phase;document.documentElement.dataset.missionReady='true';
}
$('next').onclick=()=>{
  if(!ready)return;
  if(phase==='observation'){phase='candidates';$('observation-cover').hidden=true;focusId=mission.candidates.find(c=>c.target==='T1').task_id;renderCandidates();inspect();setView(2);say('这些完整石头来自本次原 R1 观测的真实 Lux3D 返回。');}
  else if(phase==='candidates'&&!checked){$('check').click();return;}
  else if(phase==='candidates'&&checked){phase='preview';$('preview-results').hidden=false;$('preview-conclusion').textContent='正在逐个运行完整预演…';post({type:'preview',selected});}
  else if(phase==='decision'){if(previewResults.every(r=>r.passed)){phase='execute';post({type:'execute'});setView(0);$('preview-progress').hidden=true;say('按模型预演通过的路线，开始实际绕行。');}else{phase='candidates';inspect();}}
  else if(phase==='gate'){if(gateResult?.passed){phase='crossing';post({type:'cross'});setView(0);if(innerWidth<760)requestAnimationFrame(()=>$('leg-console').scrollIntoView({block:'end',behavior:'smooth'}));}else{phase='gate-preview';$('preview-text').textContent='可见门槛 · 完整跨越预演';$('preview-bar').value=0;$('preview-bar').max=1;post({type:'gatePreview'});}}
  else if(['complete','failed'].includes(phase))reset();updateUI();
};
$('check').onclick=()=>{checked=true;selected=mission.candidates.filter(c=>accepted(c,mission.thresholds)).map(c=>c.task_id);renderCandidates();inspect();say('11 份候选中，8 份符合原观测。请选择要同时验证的完整形状。');updateUI();};
$('model-detail').addEventListener('toggle',()=>{if($('model-detail').open&&$('raw-model').dataset.source)$('raw-model').src=$('raw-model').dataset.source;});
$('raw-model').addEventListener('error',()=>say('原模型暂时无法加载，可在模型陈列室查看。任务场景仍可操作。'));
for(const b of document.querySelectorAll('[data-target]'))b.onclick=()=>{if(!mission)return;focusCandidate(mission.candidates.find(c=>c.target===b.dataset.target));};
$('reset').onclick=$('again').onclick=reset;$('camera').onclick=()=>ready&&setView((view+1)%3);$('pause').onclick=()=>{stopInput();post({type:'pause',value:!paused});};$('follow').onclick=()=>post({type:'follow'});$('wheel-mode').onclick=()=>post({type:'wheelMode'});
$('cancel-preview').onclick=()=>{post({type:'cancel'});phase='candidates';gateResult=null;updateUI();};
$('wheel-trial').onclick=()=>{post({type:'wheelTrial'});$('preview-text').textContent='同一门槛 · 固定腿姿轮行尝试';$('preview-bar').max=1;$('preview-bar').value=0;};
for(const b of document.querySelectorAll('[data-action]'))b.onclick=()=>{if(!b.disabled)post({type:'legAction',action:b.dataset.action});};
for(const b of document.querySelectorAll('[data-leg]'))b.onclick=()=>post({type:'legSelect',index:Number(b.dataset.leg)});
for(const b of document.querySelectorAll('[data-pose]'))b.onclick=()=>post({type:'pose',value:b.dataset.pose});
document.addEventListener('keydown',e=>{if(!ready||/INPUT|TEXTAREA|SELECT/.test(e.target.tagName)||e.target.closest('aholo-gallery-viewer'))return;const key=e.key.length===1?e.key.toLowerCase():e.key;
  if(['w','a','s','d','ArrowUp','ArrowDown','ArrowLeft','ArrowRight',' '].includes(key)&&['execute','gate','finish-drive'].includes(phase)){e.preventDefault();keys.add(key);sendInput();}
  if(e.repeat)return;if(['j','k','l'].includes(key)&&phase==='crossing'&&!paused){e.preventDefault();post({type:'legAction',action:{j:'lift',k:'advance',l:'land'}[key]});}if(['1','2','3','4'].includes(key)){const b=document.querySelector('[data-leg="'+(Number(key)-1)+'"]');if(b&&!b.disabled)post({type:'legSelect',index:Number(key)-1});}if(key==='r')reset();if(key==='v')setView((view+1)%3);
});
document.addEventListener('keyup',e=>{keys.delete(e.key.length===1?e.key.toLowerCase():e.key);sendInput();});canvas.addEventListener('pointerdown',()=>canvas.focus());
window.addEventListener('blur',stopInput);document.addEventListener('visibilitychange',()=>{if(document.hidden){stopInput();post({type:'pause',value:true});}});
const pad=$('joystick');function padMove(e){const b=pad.getBoundingClientRect(),r=b.width*.35;let x=(e.clientX-b.left-b.width/2)/r,y=(e.clientY-b.top-b.height/2)/r;const length=Math.hypot(x,y);if(length>1){x/=length;y/=length;}joystick=[x,y];$('stick').style.transform=`translate(${x*r*.72}px,${y*r*.72}px)`;sendInput();}
pad.addEventListener('pointerdown',e=>{e.preventDefault();stickPointer=e.pointerId;pad.setPointerCapture(e.pointerId);padMove(e);});pad.addEventListener('pointermove',e=>{if(e.pointerId===stickPointer)padMove(e);});for(const name of ['pointerup','pointercancel','lostpointercapture'])pad.addEventListener(name,()=>{joystick=[0,0];stickPointer=null;$('stick').style.transform='';sendInput();});
$('touch-brake').addEventListener('pointerdown',e=>{e.preventDefault();touchBrake=true;$('touch-brake').setPointerCapture(e.pointerId);$('touch-brake').classList.add('active');sendInput();});for(const name of ['pointerup','pointercancel','lostpointercapture'])$('touch-brake').addEventListener(name,()=>{touchBrake=false;$('touch-brake').classList.remove('active');sendInput();});
function fail(error){$('fallback').hidden=false;$('fallback-text').textContent=error.message||String(error);document.documentElement.dataset.missionError='true';$('next').disabled=true;}
async function init(){
  try{
    if(!window.WebAssembly||!window.DecompressionStream)throw new Error('请使用较新的 Chrome、Edge 或 Safari 打开任务。');setupScene();resize();
    const get=async path=>{const r=await fetch(path);if(!r.ok)throw new Error('任务资源暂时无法加载：'+path);return r.arrayBuffer();};
    const [data,display,wasm,bundle]=await Promise.all([get('media/mission/mission.json.gz?v=mission-1').then(inflateGzip),get('media/mission/display.json.gz?v=mission-1').then(inflateGzip),get('vendor/mujoco/mujoco.wasm.gz'),get('media/mission/worlds.tar.gz?v=mission-1')]);
    mission=JSON.parse(new TextDecoder().decode(data));displayMeshes=JSON.parse(new TextDecoder().decode(display));for(const t of ['T1','T2'])$('input-'+t).src=inputURL(mission.candidates.find(c=>c.target===t&&accepted(c,mission.thresholds)));
    worker=new Worker('./mission-worker.js?v=mission-1',{type:'module'});worker.onerror=e=>fail(new Error(e.message));
    worker.onmessage=({data:m})=>{
      if(m.type==='error'){fail(new Error(m.message));return;}
      if(m.type==='world'){if(world)world.model=m.model;else world={model:m.model,state(){return this.snapshot;}};world.needsBuild=true;}
      if(m.type==='state'){
        world.data=m.data;world.snapshot=m.state;phase=m.state.phase;paused=m.state.paused;
        if(world.needsBuild){buildGeometry();world.needsBuild=false;goalRing.position.set(...mission.goal,.01);setView(view);}
      }
      if(m.type==='ready'){ready=true;updateUI();say('任务就绪。先看照片，再让生成的完整 3D 参与判断。');}
      if(m.type==='plan'){
        drawRoute(m.plan);$('world-results').replaceChildren();$('world-count').textContent=m.worlds.length+' 个组合';$('preview-bar').max=m.worlds.length;$('preview-bar').value=0;
        for(const [i,w]of m.worlds.entries()){const cell=document.createElement('span');cell.id='pane-'+i;cell.textContent=w.tasks.map(id=>mission.candidates.find(c=>c.task_id===id).sample).join(' × ');$('world-results').append(cell);}
      }
      if(m.type==='previewProgress'){$('preview-text').textContent=`组合 ${m.index+1} / ${m.total} · 正在从起点试走`;document.querySelectorAll('#world-results span').forEach(b=>b.classList.remove('running'));$('pane-'+m.index)?.classList.add('running');}
      if(m.type==='previewResult'){const c=$('pane-'+m.index);if(c){c.className=m.result.passed?'passed':'failed';c.textContent+=(m.result.passed?' ✓':' ×');} $('preview-bar').value=m.index+1;}
      if(m.type==='previewDone'){previewResults=m.results;phase=m.passed?'decision':'candidates';$('preview-conclusion').textContent=m.passed?`${m.results.length} 个组合全部通过，可以执行。`:'预演未通过，请调整候选并再次检查。';updateUI();}
      if(m.type==='gateObserved'){gateScan=m.scan;$('gate-measurement').textContent=`机器人相机测量：高 ${(m.scan.heightAboveGround*100).toFixed(1)} cm，可见深度 ${(m.scan.depth*100).toFixed(1)} cm。`;say('模型路线已执行到门槛前。现在用刚测到的几何，判断轮腿怎样跨越。');setView(0);}
      if(m.type==='gatePreviewDone'){gateResult=m.result;$('preview-bar').value=1;say(m.result.passed?'跨越预演通过。开始亲手操作四条腿。':'跨越预演没能通过：'+({not_aligned_before_threshold:'车头还没有对正门槛',contact:'出现了车身接触',timeout:'动作未能完整完成',wheels_not_clear:'还有轮子未越过门槛'}[m.result.reason]||m.result.reason));}
      if(m.type==='wheelTrialDone'){say(m.clear?'轮行已经通过门槛。': '固定腿姿的轮行未能通过。回到同一位置，试试逐腿跨越。');$('wheel-trial').textContent=m.clear?'轮行通过':'轮行未通过 · 再试';}
      if(m.type==='crossed')say('四轮已过门槛。回到轮行，抵达绿色终点。');
      if(m.type==='missionFailed')say(m.reason);
      if(m.type==='missionComplete'){$('debrief').hidden=false;$('debrief-results').innerHTML=`<div><strong>${selected.length}</strong><p>符合观测的完整 3D 候选</p></div><div><strong>${previewResults.length}</strong><p>模型世界完成路线预演</p></div><div><strong>12 / 12</strong><p>你亲手触发的逐腿动作</p></div>`;say('任务完成。你选择的模型进入了预演，也影响了实际行动。');}
      if(m.type==='commandRejected')say(m.reason);
      if(m.type==='resetDone'){$('observation-cover').hidden=false;setView(0);}
      if(ready)updateUI();
    };
    worker.postMessage({type:'init',mission,wasm,bundle},[wasm,bundle]);
    let lastDraw=0;const loop=t=>{if(ready&&world.data){const interval=['preview','gate-preview','wheel-trial'].includes(phase)?80:33;if(t-lastDraw>=interval){syncGeometry();render();lastDraw=t;}if(t-lastUI>150){updateUI();lastUI=t;}}requestAnimationFrame(loop);};requestAnimationFrame(loop);
  }catch(error){fail(error);}
}
new ResizeObserver(resize).observe(stage);init();
