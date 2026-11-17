/** Verify the visual links follow the actual MuJoCo body transforms. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {registerHooks} from 'node:module';
import {gunzipSync} from 'node:zlib';
import * as THREE from '../../site/vendor/three/three.module.js';
import load from '../../site/vendor/mujoco/mujoco.js';
import {unpackTar,installAssets} from '../../site/robot-physics.js';
import {MissionWorld} from '../../site/mission-world.js';
// The browser uses an import map for OrbitControls' bare "three" import.
registerHooks({resolve(specifier,context,next){return next(specifier==='three'?new URL('../../site/vendor/three/three.module.js',import.meta.url).href:specifier,context);}});
const {MissionScene}=await import('../../site/mission-scene.js');

const root=new URL('../../site/',import.meta.url).pathname;
const unpack=file=>gunzipSync(fs.readFileSync(root+file));
const mission=JSON.parse(unpack('media/mission/mission.json.gz'));
const robotSkin=JSON.parse(unpack('media/mission/m20-skin.json.gz'));
const mj=await load({wasmBinary:unpack('vendor/mujoco/mujoco.wasm.gz')});
installAssets(mj,unpackTar(unpack('media/mission/worlds.tar.gz')));
const world=new MissionWorld(mj,mission,'truth.xml');
for(let i=0;i<250;i++)world.step(0,0,true);
const model=world.packet();

// Exercise the same methods as the renderer without requiring a browser GPU.
const scene=Object.create(MissionScene.prototype);
Object.assign(scene,{robotSkin,scene:new THREE.Scene(),skinObjects:[],objects:[],canvas:{dataset:{}},
  display:JSON.parse(unpack('media/mission/display.json.gz')),dream:true,soil:null,
  car:new THREE.PerspectiveCamera(),camera:new THREE.PerspectiveCamera(),
  controls:{target:new THREE.Vector3(),update(){}},marker:new THREE.Object3D()});
scene.setModel(model);
assert.equal(scene.skinObjects.length,17);
assert(scene.objects.every(object=>object.role!=='robot'),'original visual robot is hidden');
const update=()=>scene.update(world.renderData(),world.state());
update();
for(const {body,mesh} of scene.skinObjects){
  const position=world.data.xpos.slice(body*3,body*3+3);
  const actual=new THREE.Vector3().setFromMatrixPosition(mesh.matrix);
  assert(actual.distanceTo(new THREE.Vector3(...position))<1e-8);
}
const base=scene.skinObjects.find(part=>model.body_names[part.body]==='base_link');
const before=new THREE.Vector3().setFromMatrixPosition(base.mesh.matrix);
for(let i=0;i<600;i++)world.step(.2,0,false);
update();
const after=new THREE.Vector3().setFromMatrixPosition(base.mesh.matrix);
assert(after.distanceTo(before)>.05,'visual robot must follow driven physics');
console.log(JSON.stringify({passed:true,parts:scene.skinObjects.length,drivenDistance:after.distanceTo(before),physics:'unchanged Go2W world'}));
world.destroy();
