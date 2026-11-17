import * as THREE from './vendor/three/three.module.js';
import {OrbitControls} from './vendor/three/OrbitControls.js';
/** Drawing consumes worker snapshots only. First / third / inset share one snapshot. */
export class MissionScene{
  constructor(canvas,{dream=false,display,mission,onAnchor=()=>{}}={}){
    this.canvas=canvas;this.dream=dream;this.display=display;this.mission=mission;this.onAnchor=onAnchor;this.objects=[];this.seen=new Map();this.view=1;this.pip=true;
    this.renderer=new THREE.WebGLRenderer({canvas,antialias:true,preserveDrawingBuffer:true});this.renderer.setPixelRatio(Math.min(devicePixelRatio,1.75));const debug=this.renderer.getContext().getExtension('WEBGL_debug_renderer_info');this.frameInterval=debug&&/SwiftShader/i.test(this.renderer.getContext().getParameter(debug.UNMASKED_RENDERER_WEBGL))?125:33;this.renderer.outputColorSpace=THREE.SRGBColorSpace;this.renderer.toneMapping=THREE.ACESFilmicToneMapping;this.renderer.toneMappingExposure=1.25;
    this.scene=new THREE.Scene();this.scene.background=new THREE.Color('#0b1320');this.scene.fog=new THREE.Fog('#0b1320',22,65);
    this.camera=new THREE.PerspectiveCamera(49,1,.03,100);this.camera.up.set(0,0,1);this.camera.position.set(1,-2,2);
    this.car=new THREE.PerspectiveCamera(50,1,.04,80);this.car.up.set(0,0,1);
    this.controls=new OrbitControls(this.camera,canvas);this.controls.enableDamping=true;this.dirty=true;this.controls.addEventListener("change",()=>this.dirty=true);this.controls.enablePan=false;this.controls.minDistance=.8;this.controls.maxDistance=dream?10:5;this.controls.maxPolarAngle=Math.PI*.48;
    this.scene.add(new THREE.HemisphereLight('#f5f2ea','#586175',1.7));const sun=new THREE.DirectionalLight('#ffffff',2.2);sun.position.set(-9,-7,8);this.scene.add(sun);
    const starGeometry=new THREE.BufferGeometry(),points=[];let seed=42;const random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};for(let i=0;i<230;i++)points.push((random()-.5)*160,(random()-.5)*160,14+random()*65);starGeometry.setAttribute('position',new THREE.Float32BufferAttribute(points,3));this.scene.add(new THREE.Points(starGeometry,new THREE.PointsMaterial({size:.045,color:'#c2d1e6'})));
    this.goal=new THREE.Mesh(new THREE.TorusGeometry(.35,.022,10,64),new THREE.MeshBasicMaterial({color:'#53cdb9'}));this.goal.position.set(...mission.goal,.04);this.scene.add(this.goal);
    this.marker=new THREE.Mesh(new THREE.TorusGeometry(.105,.012,8,40),new THREE.MeshBasicMaterial({color:'#f0a93b',depthTest:false}));this.marker.renderOrder=5;this.marker.visible=false;this.scene.add(this.marker);
    if(!dream)this.addUnknownMap();
    const soil=document.createElement('canvas');soil.width=soil.height=128;const ctx=soil.getContext('2d'),image=ctx.createImageData(128,128);for(let i=0;i<image.data.length;i+=4){const n=100+Math.floor(random()*65);image.data.set([n,n,n,255],i);}ctx.putImageData(image,0,0);this.soil=new THREE.CanvasTexture(soil);this.soil.wrapS=this.soil.wrapT=THREE.RepeatWrapping;this.soil.repeat.set(32,20);this.soil.colorSpace=THREE.SRGBColorSpace;
    new ResizeObserver(()=>this.resize()).observe(canvas.parentElement);
  }
  addUnknownMap(){
    const g=this.mission.grid,c=document.createElement('canvas');c.width=g.nx;c.height=g.ny;const ctx=c.getContext('2d'),pixels=ctx.createImageData(g.nx,g.ny);
    for(let x=0;x<g.nx;x++)for(let y=0;y<g.ny;y++){
      const unknown=[2,3,4].includes(this.mission.observation_state[x*g.ny+y]),i=((g.ny-1-y)*g.nx+x)*4;
      pixels.data.set(unknown?[132,153,178,(x+y)%5<2?120:55]:[0,0,0,0],i);
    }ctx.putImageData(pixels,0,0);const texture=new THREE.CanvasTexture(c);texture.magFilter=THREE.NearestFilter;
    const plane=new THREE.Mesh(new THREE.PlaneGeometry(g.nx*g.res,g.ny*g.res),new THREE.MeshBasicMaterial({map:texture,transparent:true,depthWrite:false}));plane.position.set(g.x0+g.nx*g.res/2,g.y0+g.ny*g.res/2,.025);this.scene.add(plane);
    this.unknown=plane;
  }
  setModel(model){
    this.model=model;for(const {mesh}of this.objects){this.scene.remove(mesh);mesh.geometry.dispose();mesh.material.dispose();}this.objects=[];this.dirty=true;const m=model,cache=new Map();
    for(let g=0;g<m.ngeom;g++){
      if(m.geom_group[g]===3)continue;const type=m.geom_type[g],s=m.geom_size.slice(g*3,g*3+3);let geometry;
      if(type===7){
        const id=m.geom_dataid[g];if(!cache.has(id)){
          const geom=new THREE.BufferGeometry(),lod=this.display[m.mesh_names[id]];
          if(lod){geom.setAttribute('position',new THREE.Float32BufferAttribute(lod.positions,3));geom.setIndex(lod.indices);const p=m.mesh_pos.slice(id*3,id*3+3),q=m.mesh_quat.slice(id*4,id*4+4),inverse=new THREE.Matrix4().makeRotationFromQuaternion(new THREE.Quaternion(q[1],q[2],q[3],q[0])).invert();inverse.multiply(new THREE.Matrix4().makeTranslation(-p[0],-p[1],-p[2]));geom.applyMatrix4(inverse);}
          else{const va=m.mesh_vertadr[id],vn=m.mesh_vertnum[id],fa=m.mesh_faceadr[id],fn=m.mesh_facenum[id];geom.setAttribute('position',new THREE.Float32BufferAttribute(m.mesh_vert.slice(va*3,(va+vn)*3),3));geom.setIndex(Array.from(m.mesh_face.slice(fa*3,(fa+fn)*3)));}
          geom.computeVertexNormals();cache.set(id,geom);
        }geometry=cache.get(id).clone();
      }else if(type===0)geometry=new THREE.PlaneGeometry(30,20);
      else if(type===1){const id=m.geom_dataid[g],nr=m.hfield_nrow[id],nc=m.hfield_ncol[id],adr=m.hfield_adr[id],sz=m.hfield_size.slice(id*4,id*4+4);geometry=new THREE.PlaneGeometry(sz[0]*2,sz[1]*2,nc-1,nr-1);const p=geometry.attributes.position;for(let k=0;k<p.count;k++){const col=k%nc,row=nr-1-Math.floor(k/nc);p.setZ(k,m.hfield_data[adr+row*nc+col]*sz[2]);}geometry.computeVertexNormals();}
      else if(type===6)geometry=new THREE.BoxGeometry(s[0]*2,s[1]*2,s[2]*2);
      else if(type===2)geometry=new THREE.SphereGeometry(s[0],16,12);
      else if(type===5){geometry=new THREE.CylinderGeometry(s[0],s[0],s[1]*2,16);geometry.rotateX(Math.PI/2);}
      else if(type===3){geometry=new THREE.CapsuleGeometry(s[0],s[1]*2,8,12);geometry.rotateX(Math.PI/2);}else continue;
      const role=m.geom_roles[g],hiddenModel=m.geom_group[g]===4,high=role==='T1'||role==='T2';
      let rgba=m.geom_rgba.slice(g*4,g*4+4),mat=m.geom_matid[g];if(mat>=0)rgba=m.mat_rgba.slice(mat*4,mat*4+4);
      const color=type<=1?new THREE.Color('#83858a'):new THREE.Color().setRGB(Math.max(.025,rgba[0]),Math.max(.025,rgba[1]),Math.max(.025,rgba[2]),THREE.SRGBColorSpace);
      if(type>1&&color.r>color.b*1.3&&color.r>color.g)color.set('#92949c');
      const material=new THREE.MeshStandardMaterial({color,roughness:role==='robot'?.5:.97,metalness:role==='robot'?.2:0,map:type<=1?this.soil:null});
      if(high&&!this.dream){
        geometry=geometry.toNonIndexed();geometry.computeVertexNormals();geometry.setAttribute('observed',new THREE.Float32BufferAttribute(new Float32Array(geometry.attributes.position.count),1));
        material.side=THREE.DoubleSide;material.onBeforeCompile=shader=>{shader.vertexShader='attribute float observed; varying float vObserved;\n'+shader.vertexShader;shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nvObserved = observed;');shader.fragmentShader='varying float vObserved;\n'+shader.fragmentShader;shader.fragmentShader=shader.fragmentShader.replace('#include <clipping_planes_fragment>','#include <clipping_planes_fragment>\nif(vObserved < 0.95) discard;');};
      }
      const mesh=new THREE.Mesh(geometry,material);mesh.matrixAutoUpdate=false;mesh.visible=!hiddenModel;this.scene.add(mesh);this.objects.push({g,mesh,role,high,hiddenModel,leg:m.leg_geoms[g]});
    }
    cache.forEach(g=>g.dispose());this.canvas.dataset.totalRockVertices=String(this.objects.filter(o=>o.high&&!this.dream).reduce((n,o)=>n+o.mesh.geometry.attributes.position.count,0));
  }
  update(data,state){
    this.dirty=true;this.data=data;this.state=state;
    for(const object of this.objects){const {g,mesh,leg}=object,p=g*3,r=g*9,rot=data.geom_xmat,pos=data.geom_xpos;mesh.matrix.set(rot[r],rot[r+1],rot[r+2],pos[p],rot[r+3],rot[r+4],rot[r+5],pos[p+1],rot[r+6],rot[r+7],rot[r+8],pos[p+2],0,0,0,1);mesh.matrixWorldNeedsUpdate=true;mesh.material.emissive.set(leg>=0&&state.legs?.selected===leg?'#b86a0c':'#000000');}
    const q=data.qpos,quaternion=new THREE.Quaternion(q[4],q[5],q[6],q[3]),origin=new THREE.Vector3(q[0],q[1],q[2]);
    this.car.position.copy(new THREE.Vector3(.42,0,-.00125).applyQuaternion(quaternion).add(origin));this.car.up.copy(new THREE.Vector3(0,0,1).applyQuaternion(quaternion));this.car.lookAt(new THREE.Vector3(Math.cos(-6*Math.PI/180)*3,0,Math.sin(-6*Math.PI/180)*3).applyQuaternion(quaternion).add(this.car.position));
    const target=new THREE.Vector3(state.x,state.y,state.z+.03),delta=target.clone().sub(this.controls.target);this.controls.target.add(delta);this.camera.position.add(delta);this.controls.update();
    const foot=state.legs?.positions[state.legs.selected];this.marker.visible=!!foot;if(foot)this.marker.position.set(foot[0],foot[1],foot[2]-.065);
  }
  observe(observation){
    if(this.dream)return;let changed=false;for(const hit of observation.hits){const k=hit.target+':'+hit.point.map(v=>Math.floor(v/.1)).join(',');if(!this.seen.has(k)){this.seen.set(k,hit);changed=true;}}if(!changed)return;
    const p=new THREE.Vector3(),normal=new THREE.Vector3(),mat=new THREE.Matrix3();
    for(const {mesh,high,role}of this.objects){if(!high)continue;const positions=mesh.geometry.attributes.position,normals=mesh.geometry.attributes.normal,observed=mesh.geometry.attributes.observed;mat.getNormalMatrix(mesh.matrix);
      for(let i=0;i<positions.count;i++){
        if(observed.getX(i))continue;p.fromBufferAttribute(positions,i).applyMatrix4(mesh.matrix);normal.fromBufferAttribute(normals,i).applyMatrix3(mat).normalize();const base=[p.x,p.y,p.z].map(v=>Math.floor(v/.1));let found=false;
        for(let x=-1;x<=1&&!found;x++)for(let y=-1;y<=1&&!found;y++)for(let z=-1;z<=1&&!found;z++){
          const hit=this.seen.get(role+':'+[base[0]+x,base[1]+y,base[2]+z].join(','));if(!hit)continue;
          if(p.distanceTo(new THREE.Vector3(...hit.point))<.155&&(!hit.normal||normal.dot(new THREE.Vector3(...hit.normal))>.25))found=true;
        }if(found)observed.setX(i,1);
      }observed.needsUpdate=true;
    }
    this.canvas.dataset.observedVertices=String(this.objects.filter(o=>o.high).reduce((n,o)=>n+Array.from(o.mesh.geometry.attributes.observed.array).filter(Boolean).length,0));
  }
  route(plan,passed=false){
    if(this.line){this.scene.remove(this.line);this.line.geometry.dispose();this.line.material.dispose();}this.line=null;if(!plan?.path)return;
    this.line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(plan.path.map(p=>new THREE.Vector3(p[0],p[1],.04))),new THREE.LineDashedMaterial({color:passed?'#53cdb9':'#f0a93b',dashSize:.12,gapSize:passed?0:.09,depthTest:false}));this.line.computeLineDistances();this.line.renderOrder=4;this.scene.add(this.line);
  }
  setObjective(point){
    if(!this.objectiveMarker){this.objectiveMarker=new THREE.Mesh(new THREE.TorusGeometry(.18,.018,8,40),new THREE.MeshBasicMaterial({color:'#e4b45e'}));this.scene.add(this.objectiveMarker);}
    this.objectiveMarker.visible=!!point;
    if(point)this.objectiveMarker.position.set(point[0],point[1],.035);
    this.dirty=true;
  }
  setView(view){
    this.dirty=true;this.view=view;this.controls.enabled=view!==1;if(!this.state)return;const s=this.state;this.controls.target.set(s.x,s.y,s.z);
    if(view===0||view===1)this.camera.position.set(s.x-1.5*Math.cos(s.yaw)+1.4*Math.sin(s.yaw),s.y-1.5*Math.sin(s.yaw)-1.4*Math.cos(s.yaw),s.z+1.2);
    if(view===2)this.camera.position.set(s.x-.3,s.y-.001,s.z+5);this.controls.update();
  }
  resize(){const b=this.canvas.getBoundingClientRect();if(!b.width||!b.height||this.sizeW===b.width&&this.sizeH===b.height)return;this.sizeW=b.width;this.sizeH=b.height;this.renderer.setSize(b.width,b.height,false);this.camera.aspect=b.width/b.height;this.camera.updateProjectionMatrix();}
  draw(){
    if(!this.data||this.state.paused&&!this.dirty&&!this.dream)return;this.dirty=false;this.resize();const b=this.canvas.getBoundingClientRect(),w=b.width,h=b.height,r=this.renderer;
    const visibleHeight=this.compactBrain?Math.max(180,Math.min(h-445,330)):h;r.setScissorTest(false);r.setViewport(0,h-visibleHeight,w,visibleHeight);this.camera.aspect=w/visibleHeight;this.camera.updateProjectionMatrix();this.car.aspect=w/visibleHeight;this.car.fov=2*Math.atan(Math.tan(34*Math.PI/180)/this.car.aspect)*180/Math.PI;this.car.updateProjectionMatrix();r.render(this.scene,this.view===1?this.car:this.camera);
    if(this.pip&&!this.dream){
      const bw=Math.min(w*(this.compactBrain?.28:.3),this.compactBrain?118:240),bh=bw*9/16,x=w-bw-(this.insetOffset||18),y=this.compactBrain?h-visibleHeight+12:h>600?158:130;r.setScissorTest(true);r.setScissor(x,y,bw,bh);r.setViewport(x,y,bw,bh);r.clear(true,true,true);this.car.aspect=16/9;this.car.fov=2*Math.atan(Math.tan(34*Math.PI/180)/(16/9))*180/Math.PI;this.car.updateProjectionMatrix();const old=this.camera.aspect;this.camera.aspect=16/9;this.camera.updateProjectionMatrix();r.render(this.scene,this.view===1?this.camera:this.car);this.camera.aspect=old;this.camera.updateProjectionMatrix();r.setScissorTest(false);
      this.canvas.dataset.pip=JSON.stringify({x,y,w:bw,h:bh,stateTime:this.state.elapsed});
    }
    if(!this.dream){const p=new THREE.Vector3(this.state.x,this.state.y,this.state.z+.28).project(this.view===1?this.car:this.camera);this.onAnchor({x:(p.x*.5+.5)*w,y:(-.5*p.y+.5)*visibleHeight,visible:p.z<1&&this.view!==1});}
    this.canvas.dataset.viewportHeight=String(visibleHeight);this.canvas.dataset.simulationTime=String(this.state.elapsed);this.canvas.dataset.view=String(this.view);
  }
  resetSeen(){this.seen.clear();}
}
