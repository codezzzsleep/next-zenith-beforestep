import * as THREE from './vendor/three/three.module.js';
import {OrbitControls} from './vendor/three/OrbitControls.js';
import {rockSurface} from './rock-surface.js?v=original-materials-20261118-1';
/** Drawing consumes worker snapshots only. First / third / inset share one snapshot. */
export class MissionScene{
  constructor(canvas,{dream=false,display,mission,robotSkin,appearance,onAnchor=()=>{}}={}){
    this.canvas=canvas;this.dream=dream;this.display=display;this.mission=mission;this.robotSkin=robotSkin;this.appearance=appearance;this.onAnchor=onAnchor;this.objects=[];this.skinObjects=[];this.seen=new Map();this.view=1;this.pip=true;this.followCamera=true;
    this.renderer=new THREE.WebGLRenderer({canvas,antialias:true,preserveDrawingBuffer:true});this.renderer.setPixelRatio(Math.min(devicePixelRatio,1.75));const debug=this.renderer.getContext().getExtension('WEBGL_debug_renderer_info');this.frameInterval=debug&&/SwiftShader/i.test(this.renderer.getContext().getParameter(debug.UNMASKED_RENDERER_WEBGL))?125:33;this.renderer.outputColorSpace=THREE.SRGBColorSpace;this.renderer.toneMapping=THREE.ACESFilmicToneMapping;this.renderer.toneMappingExposure=1.0;
    this.renderer.shadowMap.enabled=!dream;this.renderer.shadowMap.type=THREE.PCFSoftShadowMap;this.renderer.shadowMap.autoUpdate=false;
    this.scene=new THREE.Scene();this.scene.background=new THREE.Color('#0b1320');this.scene.fog=new THREE.Fog('#0b1320',22,65);
    this.camera=new THREE.PerspectiveCamera(49,1,.03,100);this.camera.up.set(0,0,1);this.camera.position.set(1,-2,2);
    this.car=new THREE.PerspectiveCamera(50,1,.04,80);this.car.up.set(0,0,1);
    this.controls=new OrbitControls(this.camera,canvas);this.controls.enableDamping=true;this.dirty=true;this.controls.addEventListener("change",()=>this.dirty=true);this.controls.enablePan=false;this.controls.minDistance=.8;this.controls.maxDistance=dream?10:5;this.controls.maxPolarAngle=Math.PI*.48;
    this.controls.addEventListener('start',()=>{this.followCamera=false;});
    this.scene.add(new THREE.HemisphereLight('#dce3eb','#141820',.32));const sun=new THREE.DirectionalLight('#fff5e2',3.0),el=THREE.MathUtils.degToRad(appearance?.manifest.sun.elevation_deg??10),az=THREE.MathUtils.degToRad(appearance?.manifest.sun.azimuth_deg??35);sun.target.position.set(5,0,0);sun.position.set(5-Math.cos(el)*Math.cos(az)*28,Math.cos(el)*Math.sin(az)*28,Math.sin(el)*28);sun.castShadow=!dream;sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-14,right:14,top:9,bottom:-9,near:.1,far:80});sun.shadow.bias=-.0002;sun.shadow.normalBias=.004;this.scene.add(sun,sun.target);
    const starGeometry=new THREE.BufferGeometry(),points=[];let seed=42;const random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};for(let i=0;i<230;i++)points.push((random()-.5)*160,(random()-.5)*160,14+random()*65);starGeometry.setAttribute('position',new THREE.Float32BufferAttribute(points,3));this.scene.add(new THREE.Points(starGeometry,new THREE.PointsMaterial({size:.045,color:'#c2d1e6'})));
    this.goal=new THREE.Mesh(new THREE.TorusGeometry(.35,.022,10,64),new THREE.MeshBasicMaterial({color:'#53cdb9'}));this.goal.position.set(...mission.goal,.04);this.scene.add(this.goal);
    this.marker=new THREE.Mesh(new THREE.TorusGeometry(.105,.012,8,40),new THREE.MeshBasicMaterial({color:'#f0a93b',depthTest:false}));this.marker.renderOrder=5;this.marker.visible=false;this.scene.add(this.marker);
    this.soil=appearance?.textures.regolith??null;
    this.perception=false;this.perceptionPalette=[new THREE.MeshBasicMaterial({color:'#e0e7eb'}),new THREE.MeshBasicMaterial({color:'#617b90'}),new THREE.MeshBasicMaterial({color:'#a0b1bd'}),new THREE.MeshBasicMaterial({color:'#607485'})];
    new ResizeObserver(()=>this.resize()).observe(canvas.parentElement);
  }
  setModel(model){
    for(const mesh of this.planningMeshes||[])mesh.visible=false;
    this.canvas.dataset.planningHypotheses='0';
    this.model=model;for(const {mesh}of [...this.objects,...this.skinObjects]){this.scene.remove(mesh);mesh.geometry.dispose();mesh.material.dispose();}this.objects=[];this.skinObjects=[];this.dirty=true;const m=model,cache=new Map();
    const skinReady=this.makeRobotSkin(m);
    for(let g=0;g<m.ngeom;g++){
      if(m.geom_group[g]===3||skinReady&&m.geom_roles[g]==='robot')continue;const type=m.geom_type[g],s=m.geom_size.slice(g*3,g*3+3),role=m.geom_roles[g],high=role==='T1'||role==='T2',solid=high&&!this.dream;let geometry,texture=null;
      if(type===7){
        const id=m.geom_dataid[g],family=this.appearance?.meshes[m.mesh_names[id]],uvs=this.appearance?.uvs[family];texture=this.appearance?.textures[family]??null;const originalSurface=solid||!!texture,key=(originalSurface?'original:':'lod:')+id;if(!cache.has(key)){
          const geom=new THREE.BufferGeometry(),lod=this.display[m.mesh_names[id]];
          if(lod&&!originalSurface){geom.setAttribute('position',new THREE.Float32BufferAttribute(lod.positions,3));geom.setIndex(lod.indices);const p=m.mesh_pos.slice(id*3,id*3+3),q=m.mesh_quat.slice(id*4,id*4+4),inverse=new THREE.Matrix4().makeRotationFromQuaternion(new THREE.Quaternion(q[1],q[2],q[3],q[0])).invert();inverse.multiply(new THREE.Matrix4().makeTranslation(-p[0],-p[1],-p[2]));geom.applyMatrix4(inverse);}
          else{const va=m.mesh_vertadr[id],vn=m.mesh_vertnum[id],fa=m.mesh_faceadr[id],fn=m.mesh_facenum[id],original={positions:m.mesh_vert.slice(va*3,(va+vn)*3),indices:m.mesh_face.slice(fa*3,(fa+fn)*3)},surface=originalSurface?rockSurface(original.positions,original.indices,texture?uvs:null):original;geom.setAttribute('position',new THREE.Float32BufferAttribute(surface.positions,3));geom.setIndex(new THREE.BufferAttribute(new Uint32Array(surface.indices),1));if(surface.uvs)geom.setAttribute('uv',new THREE.BufferAttribute(surface.uvs,2));if(surface.normals)geom.setAttribute('normal',new THREE.BufferAttribute(surface.normals,3));}
          if(!geom.attributes.normal)geom.computeVertexNormals();cache.set(key,geom);
        }geometry=cache.get(key).clone();
      }else if(type===0)geometry=new THREE.PlaneGeometry(30,20);
      else if(type===1){const id=m.geom_dataid[g],nr=m.hfield_nrow[id],nc=m.hfield_ncol[id],adr=m.hfield_adr[id],sz=m.hfield_size.slice(id*4,id*4+4);geometry=new THREE.PlaneGeometry(sz[0]*2,sz[1]*2,nc-1,nr-1);const p=geometry.attributes.position;for(let k=0;k<p.count;k++){const col=k%nc,row=nr-1-Math.floor(k/nc);p.setZ(k,m.hfield_data[adr+row*nc+col]*sz[2]);}geometry.computeVertexNormals();}
      else if(type===6)geometry=new THREE.BoxGeometry(s[0]*2,s[1]*2,s[2]*2);
      else if(type===2)geometry=new THREE.SphereGeometry(s[0],16,12);
      else if(type===5){geometry=new THREE.CylinderGeometry(s[0],s[0],s[1]*2,16);geometry.rotateX(Math.PI/2);}
      else if(type===3){geometry=new THREE.CapsuleGeometry(s[0],s[1]*2,8,12);geometry.rotateX(Math.PI/2);}else continue;
      const hiddenModel=m.geom_group[g]===4;
      let rgba=m.geom_rgba.slice(g*4,g*4+4),mat=m.geom_matid[g];if(mat>=0)rgba=m.mat_rgba.slice(mat*4,mat*4+4);
      const color=type<=1?new THREE.Color('#83858a'):new THREE.Color().setRGB(Math.max(.025,rgba[0]),Math.max(.025,rgba[1]),Math.max(.025,rgba[2]),THREE.SRGBColorSpace);
      if(type>1&&color.r>color.b*1.3&&color.r>color.g)color.set('#92949c');
      if(texture||type<=1)color.set('#ffffff');
      const material=new THREE.MeshStandardMaterial({color,roughness:role==='robot'?.5:.97,metalness:role==='robot'?.2:0,map:type<=1?this.soil:texture});
      if(type<=1){const p=geometry.attributes.position,uv=geometry.attributes.uv,tile=this.appearance?.manifest.soil_tile_m??.9;for(let v=0;v<p.count;v++)uv.setXY(v,p.getX(v)/tile,p.getY(v)/tile);uv.needsUpdate=true;material.bumpMap=this.soil;material.bumpScale=.008;}
      if(high&&this.dream&&this.comparison){material.color.set('#f0a93b');material.transparent=true;material.opacity=.38;material.depthWrite=false;}
      const mesh=new THREE.Mesh(geometry,material);mesh.matrixAutoUpdate=false;mesh.visible=!hiddenModel;mesh.castShadow=!this.dream&&(!!texture||high||type===6&&role==='environment');mesh.receiveShadow=!this.dream;this.scene.add(mesh);this.objects.push({g,mesh,role,high,hiddenModel,textured:!!texture,leg:m.leg_geoms[g]});
    }
    cache.forEach(g=>g.dispose());this.renderer.shadowMap.needsUpdate=true;this.canvas.dataset.totalRockVertices=String(this.objects.filter(o=>o.high&&!this.dream).reduce((n,o)=>n+o.mesh.geometry.attributes.position.count,0));this.canvas.dataset.rockSurfaceMode=this.dream?'candidate':'complete-textured';this.canvas.dataset.observedHits=String(this.seen.size);this.canvas.dataset.texturedScanMeshes=String(this.objects.filter(o=>o.textured).length);this.canvas.dataset.appearanceTextures=String(Object.keys(this.appearance?.textures??{}).length);
  }
  makeRobotSkin(model){
    if(!this.robotSkin?.parts||!model.body_names)return false;
    const map=[['base_link','base_link',-1]];
    for(const [source,target,leg] of [['fr','FR',0],['fl','FL',1],['hr','RR',2],['hl','RL',3]]){
      for(const [part,body] of [['hipx','hip'],['hipy','thigh'],['knee','calf'],['wheel','wheel_link']])map.push([`${source}_${part}`,`${target}_${body}`,part==='wheel'?leg:-1]);
    }
    if(map.some(([part,body])=>!this.robotSkin.parts[part]||model.body_names.indexOf(body)<0))return false;
    for(const [part,body,leg] of map){
      const data=this.robotSkin.parts[part],geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(data.positions,3));geometry.setIndex(data.indices);geometry.computeVertexNormals();
      const wheel=part.endsWith('_wheel'),color=wheel?'#242a31':part==='base_link'?'#dce3e6':part.endsWith('_hipx')?'#6d7a80':'#b7c4c9';
      const material=new THREE.MeshStandardMaterial({color,roughness:wheel?.9:.48,metalness:wheel?.05:.27});const mesh=new THREE.Mesh(geometry,material);mesh.matrixAutoUpdate=false;mesh.castShadow=!this.dream;mesh.receiveShadow=!this.dream;this.scene.add(mesh);this.skinObjects.push({mesh,body:model.body_names.indexOf(body),leg});
    }
    this.canvas.dataset.robotParts=String(this.skinObjects.length);return true;
  }
  update(data,state){
    const previous=this.state;if(!this.dream&&!state.paused&&(!previous||Math.hypot(state.x-previous.x,state.y-previous.y)>.001||Math.abs(state.yaw-previous.yaw)>.005||state.legs?.busy))this.renderer.shadowMap.needsUpdate=true;
    this.dirty=true;this.data=data;this.state=state;
    for(const object of this.objects){const {g,mesh,leg}=object,p=g*3,r=g*9,rot=data.geom_xmat,pos=data.geom_xpos;mesh.matrix.set(rot[r],rot[r+1],rot[r+2],pos[p],rot[r+3],rot[r+4],rot[r+5],pos[p+1],rot[r+6],rot[r+7],rot[r+8],pos[p+2],0,0,0,1);mesh.matrixWorldNeedsUpdate=true;mesh.material.emissive.set(leg>=0&&state.legs?.selected===leg?'#b86a0c':'#000000');}
    for(const {body,mesh,leg} of this.skinObjects){const p=body*3,r=body*9,rot=data.body_xmat,pos=data.body_xpos;mesh.matrix.set(rot[r],rot[r+1],rot[r+2],pos[p],rot[r+3],rot[r+4],rot[r+5],pos[p+1],rot[r+6],rot[r+7],rot[r+8],pos[p+2],0,0,0,1);mesh.matrixWorldNeedsUpdate=true;mesh.material.emissive.set(leg>=0&&state.legs?.selected===leg?'#b86a0c':'#000000');}
    const q=data.qpos,quaternion=new THREE.Quaternion(q[4],q[5],q[6],q[3]),origin=new THREE.Vector3(q[0],q[1],q[2]);
    this.car.position.copy(new THREE.Vector3(.42,0,-.00125).applyQuaternion(quaternion).add(origin));this.car.up.copy(new THREE.Vector3(0,0,1).applyQuaternion(quaternion));this.car.lookAt(new THREE.Vector3(Math.cos(-6*Math.PI/180)*3,0,Math.sin(-6*Math.PI/180)*3).applyQuaternion(quaternion).add(this.car.position));
    if(!(this.dream&&this.comparison&&this.view===2)){const target=new THREE.Vector3(state.x,state.y,state.z+.03),delta=target.clone().sub(this.controls.target);this.controls.target.add(delta);if(!this.dream&&this.view!==2&&this.followCamera)this.camera.position.lerp(new THREE.Vector3(state.x-1.5*Math.cos(state.yaw)+1.4*Math.sin(state.yaw),state.y-1.5*Math.sin(state.yaw)-1.4*Math.cos(state.yaw),state.z+.85),.12);else this.camera.position.add(delta);this.controls.update();}
    const foot=state.legs?.positions[state.legs.selected];this.marker.visible=!!foot;if(foot)this.marker.position.set(foot[0],foot[1],foot[2]-.065);
  }
  observe(observation){
    if(this.dream)return;let changed=false;for(const hit of observation.hits){const k=hit.target+':'+hit.point.map(v=>Math.floor(v/.1)).join(',');if(!this.seen.has(k)){this.seen.set(k,hit);changed=true;}}if(!changed)return;
    // Observation is evidence for the robot, not a mask that cuts holes in matter.
    this.canvas.dataset.observedHits=String(this.seen.size);
  }
  setPerception(value){if(this.dream||this.perception===value)return;this.perception=value;this.dirty=true;}
  renderView(camera){
    if(!this.perception){this.renderer.render(this.scene,camera);return;}
    const originals=[],background=this.scene.background,fog=this.scene.fog,shadows=this.renderer.shadowMap.enabled;
    for(const object of this.objects){const type=this.model.geom_type[object.g];originals.push([object.mesh,object.mesh.material]);object.mesh.material=this.perceptionPalette[type<=1?0:object.high?1:object.role==='robot'?3:2];}
    for(const object of this.skinObjects){originals.push([object.mesh,object.mesh.material]);object.mesh.material=this.perceptionPalette[3];}
    this.scene.background=new THREE.Color('#d3dee5');this.scene.fog=null;this.renderer.shadowMap.enabled=false;
    try{this.renderer.render(this.scene,camera);}finally{for(const [mesh,material]of originals)mesh.material=material;this.scene.background=background;this.scene.fog=fog;this.renderer.shadowMap.enabled=shadows;}
  }
  clearPreview(){
    if(!this.dream||!this.data&&!this.model)return;
    for(const {mesh}of [...this.objects,...this.skinObjects]){this.scene.remove(mesh);mesh.geometry.dispose();mesh.material.dispose();}
    this.objects=[];this.skinObjects=[];this.model=null;this.data=null;this.state=null;this.started=false;this.dirty=true;
  }
  route(plan,passed=false){
    if(this.line){this.scene.remove(this.line);this.line.geometry.dispose();this.line.material.dispose();}this.line=null;if(!plan?.path)return;
    this.line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(plan.path.map(p=>new THREE.Vector3(p[0],p[1],.04))),new THREE.LineDashedMaterial({color:passed?'#53cdb9':'#f0a93b',dashSize:.12,gapSize:passed?0:.09,depthTest:true,depthWrite:false}));this.line.computeLineDistances();this.line.renderOrder=4;this.scene.add(this.line);
  }
  compare(comparison, policy='imagination', passed=false){
    if(!this.dream)return;
    for(const object of this.comparisonObjects||[]){this.scene.remove(object);object.geometry?.dispose();object.material.map?.dispose();object.material.dispose();}
    this.comparisonObjects=[];this.planningMeshes=[];this.comparison=comparison;this.dirty=true;
    if(!comparison){delete this.canvas.dataset.comparison;return;}
    const add=object=>{this.scene.add(object);this.comparisonObjects.push(object);return object;};
    if(!this.data)for(const id of comparison.selected){
      const candidate=this.mission.candidates.find(c=>c.task_id===id),surface=this.display[candidate?.world_mesh];if(!surface)continue;
      const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(surface.positions,3));geometry.setIndex(surface.indices);geometry.computeVertexNormals();
      const mesh=add(new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({color:'#d5ad67',roughness:.98,transparent:true,opacity:.78,side:THREE.DoubleSide})));mesh.userData.taskId=id;this.planningMeshes.push(mesh);
    }
    this.canvas.dataset.planningHypotheses=String(this.planningMeshes.length);
    const g=this.mission.grid,c=document.createElement('canvas');c.width=g.nx;c.height=g.ny;
    const ctx=c.getContext('2d'),pixels=ctx.createImageData(g.nx,g.ny);
    for(let x=0;x<g.nx;x++)for(let y=0;y<g.ny;y++){
      const i=x*g.ny+y,p=((g.ny-1-y)*g.nx+x)*4;
      const color=comparison.visible[i]?[141,224,232,245]:comparison.added[i]?[240,169,59,150]:this.mission.known_nogo[i]?[86,99,118,175]:[2,3,4].includes(this.mission.observation_state[i])?[74,93,115,(x+y)%5<2?80:35]:[122,139,155,25];
      pixels.data.set(color,p);
    }
    ctx.putImageData(pixels,0,0);const texture=new THREE.CanvasTexture(c);texture.magFilter=THREE.NearestFilter;texture.colorSpace=THREE.SRGBColorSpace;
    const plane=add(new THREE.Mesh(new THREE.PlaneGeometry(g.nx*g.res,g.ny*g.res),new THREE.MeshBasicMaterial({map:texture,transparent:true,depthWrite:false,toneMapped:false})));
    plane.position.set(g.x0+g.nx*g.res/2,g.y0+g.ny*g.res/2,.045);
    const outline=(cells,color,dashed)=>{
      const points=[];
      for(let x=0;x<g.nx;x++)for(let y=0;y<g.ny;y++){
        if(!cells[x*g.ny+y])continue;
        const x0=g.x0+x*g.res,y0=g.y0+y*g.res,x1=x0+g.res,y1=y0+g.res;
        if(x===0||!cells[(x-1)*g.ny+y])points.push(x0,y0,.06,x0,y1,.06);
        if(x===g.nx-1||!cells[(x+1)*g.ny+y])points.push(x1,y0,.06,x1,y1,.06);
        if(y===0||!cells[x*g.ny+y-1])points.push(x0,y0,.06,x1,y0,.06);
        if(y===g.ny-1||!cells[x*g.ny+y+1])points.push(x0,y1,.06,x1,y1,.06);
      }
      const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(points,3));
      const material=dashed?new THREE.LineDashedMaterial({color,dashSize:.06,gapSize:.035,depthTest:false}):new THREE.LineBasicMaterial({color,depthTest:false});
      const line=add(new THREE.LineSegments(geometry,material));if(dashed)line.computeLineDistances();line.renderOrder=3;
    };
    outline(comparison.visible,'#8de0e8',false);outline(comparison.added,'#f0a93b',true);
    for(const [plan,color,dashed]of [[comparison.visiblePlan,'#abb6c4',true],[comparison.hypothesisPlan,passed&&policy==='imagination'?'#53cdb9':'#f0a93b',false]]){
      if(!plan.path)continue;
      const positions=[];
      for(let i=1;i<plan.path.length;i++){
        const a=plan.path[i-1],b=plan.path[i],dx=b[0]-a[0],dy=b[1]-a[1],length=Math.hypot(dx,dy);if(length<1e-8)continue;
        const nx=-dy/length*.024,ny=dx/length*.024;
        for(let d=0;d<length;d+=dashed?.26:length){
          const end=Math.min(length,d+(dashed?.16:length)),u=d/length,v=end/length;
          const x0=a[0]+dx*u,y0=a[1]+dy*u,x1=a[0]+dx*v,y1=a[1]+dy*v;
          positions.push(x0+nx,y0+ny,.09,x1+nx,y1+ny,.09,x1-nx,y1-ny,.09,x0+nx,y0+ny,.09,x1-nx,y1-ny,.09,x0-nx,y0-ny,.09);
        }
      }
      const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
      const line=add(new THREE.Mesh(geometry,new THREE.MeshBasicMaterial({color,depthTest:false,side:THREE.DoubleSide,toneMapped:false})));
      line.renderOrder=5;
    }
    const label=(text,point)=>{
      const canvas=document.createElement('canvas');canvas.width=256;canvas.height=64;const context=canvas.getContext('2d');
      context.fillStyle='#0b1320dc';context.fillRect(0,0,256,64);context.font='500 30px "BeforeStep Sans",sans-serif';context.textAlign='center';context.textBaseline='middle';context.fillStyle='#f5f2ea';context.fillText(text,128,32);
      const map=new THREE.CanvasTexture(canvas);map.colorSpace=THREE.SRGBColorSpace;
      const sprite=add(new THREE.Sprite(new THREE.SpriteMaterial({map,depthTest:false,toneMapped:false})));
      sprite.scale.set(.85,.2125,1);sprite.position.set(point[0],point[1],.22);sprite.renderOrder=6;
    };
    for(const target of comparison.targets)label('高石 '+(target.target==='T1'?'A':'B'),[target.point[0],target.point[1]+.5]);
    label('试路起点',[comparison.start[0],comparison.start[1]-.42]);label('门槛整备点',[this.mission.dock[0],this.mission.dock[1]+.45]);
    const origin=add(new THREE.Mesh(new THREE.TorusGeometry(.09,.014,8,32),new THREE.MeshBasicMaterial({color:'#f5f2ea',depthTest:false})));
    origin.position.set(...comparison.start,.09);origin.renderOrder=6;
    if(comparison.exposure?.margin<0){
      const warning=add(new THREE.Mesh(new THREE.TorusGeometry(.105,.018,8,32),new THREE.MeshBasicMaterial({color:'#e46a5d',depthTest:false})));
      warning.position.set(...comparison.exposure.point,.1);warning.renderOrder=7;
    }
    this.canvas.dataset.comparison=JSON.stringify({selected:comparison.selected,visibleCells:comparison.visible.reduce((n,v)=>n+v,0),hypothesisCells:comparison.added.reduce((n,v)=>n+v,0),visibleRoute:!!comparison.visiblePlan.path,hypothesisRoute:!!comparison.hypothesisPlan.path,clearanceMargin:comparison.exposure?.margin,passed:passed&&policy==='imagination'});
    if(this.view===2)this.fitComparison();else this.fitSpatialComparison();
  }
  fitSpatialComparison(){
    if(!this.comparison)return;const middle=(this.comparison.start[0]+this.mission.dock[0])/2;this.controls.target.set(middle,0,.15);this.camera.position.set(middle-1.7,-4.5,3.3);this.controls.update();
  }
  fitComparison(){
    const g=this.mission.grid,x0=this.comparison.start[0]-.55,x1=this.mission.dock[0]+.6,y0=g.y0+.1,y1=g.y0+g.ny*g.res-.1;
    const b=this.canvas.getBoundingClientRect(),aspect=(b.width||360)/(b.height||195),height=Math.max((y1-y0)/2,(x1-x0)/2/aspect)/Math.tan(THREE.MathUtils.degToRad(this.camera.fov/2))*1.12;
    this.controls.target.set((x0+x1)/2,(y0+y1)/2,0);this.camera.position.set((x0+x1)/2,(y0+y1)/2-.001,height);this.controls.update();
  }
  setObjective(point){
    if(!this.objectiveMarker){this.objectiveMarker=new THREE.Mesh(new THREE.TorusGeometry(.18,.018,8,40),new THREE.MeshBasicMaterial({color:'#e4b45e'}));this.scene.add(this.objectiveMarker);}
    this.objectiveMarker.visible=!!point;
    if(point)this.objectiveMarker.position.set(point[0],point[1],.035);
    this.dirty=true;
  }
  setView(view){
    this.dirty=true;this.view=view;this.followCamera=true;this.controls.enabled=view!==1;if(this.dream&&this.comparison){if(view===2){this.fitComparison();return;}this.fitSpatialComparison();return;}if(!this.state)return;const s=this.state;this.controls.target.set(s.x,s.y,s.z);
    if(view===0||view===1)this.camera.position.set(s.x-1.5*Math.cos(s.yaw)+1.4*Math.sin(s.yaw),s.y-1.5*Math.sin(s.yaw)-1.4*Math.cos(s.yaw),s.z+.85);
    if(view===2)this.camera.position.set(s.x-.3,s.y-.001,s.z+5);this.controls.update();
  }
  resize(){const b=this.canvas.getBoundingClientRect();if(!b.width||!b.height||this.sizeW===b.width&&this.sizeH===b.height)return;this.sizeW=b.width;this.sizeH=b.height;this.renderer.setSize(b.width,b.height,false);this.camera.aspect=b.width/b.height;this.camera.updateProjectionMatrix();}
  draw(){
    if(!this.data&&!(this.dream&&this.comparison)||this.state?.paused&&!this.dirty&&!this.dream)return;this.dirty=false;this.resize();if(this.dream&&this.comparison&&this.view===2)this.fitComparison();const b=this.canvas.getBoundingClientRect(),w=b.width,h=b.height,r=this.renderer;
    const visibleHeight=this.compactBrain?Math.max(180,Math.min(h-445,330)):h;r.setScissorTest(false);r.setViewport(0,h-visibleHeight,w,visibleHeight);this.camera.aspect=w/visibleHeight;this.camera.updateProjectionMatrix();this.car.aspect=w/visibleHeight;this.car.fov=2*Math.atan(Math.tan(34*Math.PI/180)/this.car.aspect)*180/Math.PI;this.car.updateProjectionMatrix();this.renderView(this.view===1?this.car:this.camera);
    if(this.pip&&!this.dream){
      const bw=Math.min(w*(this.compactBrain?.28:.3),this.compactBrain?118:240),bh=bw*9/16,x=w-bw-(this.insetOffset||18),y=this.compactBrain?h-visibleHeight+12:h>600?158:130;r.setScissorTest(true);r.setScissor(x,y,bw,bh);r.setViewport(x,y,bw,bh);r.clear(true,true,true);this.car.aspect=16/9;this.car.fov=2*Math.atan(Math.tan(34*Math.PI/180)/(16/9))*180/Math.PI;this.car.updateProjectionMatrix();const old=this.camera.aspect;this.camera.aspect=16/9;this.camera.updateProjectionMatrix();this.renderView(this.view===1?this.camera:this.car);this.camera.aspect=old;this.camera.updateProjectionMatrix();r.setScissorTest(false);
      this.canvas.dataset.pip=JSON.stringify({x,y,w:bw,h:bh,stateTime:this.state.elapsed});
    }
    if(!this.dream){const p=new THREE.Vector3(this.state.x,this.state.y,this.state.z+.28).project(this.view===1?this.car:this.camera);this.onAnchor({x:(p.x*.5+.5)*w,y:(-.5*p.y+.5)*visibleHeight,visible:p.z<1&&this.view!==1});}
    this.canvas.dataset.viewportHeight=String(visibleHeight);this.canvas.dataset.simulationTime=String(this.state?.elapsed??0);this.canvas.dataset.view=String(this.view);this.canvas.dataset.displayMode=this.perception?'2d-observation':this.dream?'local-space-model':'physical-execution';
  }
  resetSeen(){this.seen.clear();this.canvas.dataset.observedHits='0';}
}
