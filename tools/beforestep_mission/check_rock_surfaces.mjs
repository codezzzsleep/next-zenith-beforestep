import fs from 'node:fs';
import assert from 'node:assert/strict';
import {gunzipSync} from 'node:zlib';
import {pathToFileURL} from 'node:url';
import {rockSurface} from '../../site/rock-surface.js';

const repo = process.env.BEFORESTEP_SOURCE_ROOT
  ? pathToFileURL(process.env.BEFORESTEP_SOURCE_ROOT.replace(/\/$/, '') + '/')
  : new URL('../../', import.meta.url);
const {default: load} = await import(new URL('site/vendor/mujoco/mujoco.js', repo));
const {unpackTar, installAssets} = await import(new URL('site/robot-physics.js', repo));
const {MissionWorld} = await import(new URL('site/mission-world.js', repo));
const THREE = await import(new URL('site/vendor/three/three.module.js', repo));
const asset = path => fs.readFileSync(new URL(path, repo));
const mission = JSON.parse(gunzipSync(asset('site/media/mission/mission.json.gz')));
const mj = await load({wasmBinary: gunzipSync(asset('site/vendor/mujoco/mujoco.wasm.gz'))});
installAssets(mj, unpackTar(gunzipSync(asset('site/media/mission/worlds.tar.gz'))));
const world = new MissionWorld(mj, mission), before = world.physicalState(), model = world.packet();
const appearance = JSON.parse(gunzipSync(fs.readFileSync(new URL('../../site/media/mission/appearance/scan-uv.json.gz', import.meta.url))));
const report = {passed: false, originalPackageUsed: true, physicsUnchanged: false, rocks: []};
try {
  for (let g = 0; g < model.ngeom; g++) {
    const role = model.geom_roles[g];
    if (!['T1', 'T2'].includes(role) || model.geom_type[g] !== 7 || model.geom_group[g] === 3) continue;
    const id = model.geom_dataid[g], va = model.mesh_vertadr[id], vn = model.mesh_vertnum[id];
    const fa = model.mesh_faceadr[id], fn = model.mesh_facenum[id];
    const original = {positions: model.mesh_vert.slice(va * 3, (va + vn) * 3), indices: model.mesh_face.slice(fa * 3, (fa + fn) * 3)};
    const copies = {positions: original.positions.slice(), indices: original.indices.slice()};
    const surface = rockSurface(original.positions, original.indices), edges = new Map(), used = new Set();
    const uvs = appearance.uvs[appearance.meshes[model.mesh_names[id]]];
    assert(uvs && uvs.length === original.positions.length / 3 * 2);
    const textured = rockSurface(original.positions, original.indices, uvs);
    assert.deepEqual(textured.uvs, new Float32Array(uvs), 'render UVs must retain the original texture coordinates');
    assert.deepEqual(rockSurface(textured.positions, textured.indices), surface, 'UV seams must retain the identical closed physical-world surface');
    let volume = 0;
    for (let i = 0; i < surface.indices.length; i += 3) {
      const f = Array.from(surface.indices.slice(i, i + 3));
      for (let k = 0; k < 3; k++) {
        const a = f[k], b = f[(k + 1) % 3], key = [Math.min(a,b), Math.max(a,b)].join(':');
        const edge = edges.get(key) || {count: 0, winding: 0};
        edge.count++; edge.winding += a < b ? 1 : -1; edges.set(key, edge); used.add(a);
      }
      const [a,b,c] = f.map(v => Array.from(surface.positions.slice(v * 3, v * 3 + 3)));
      volume += (a[0]*(b[1]*c[2]-b[2]*c[1]) + a[1]*(b[2]*c[0]-b[0]*c[2]) + a[2]*(b[0]*c[1]-b[1]*c[0])) / 6;
    }
    const boundaryEdges = [...edges.values()].filter(e => e.count === 1).length;
    const nonManifoldEdges = [...edges.values()].filter(e => e.count !== 2).length;
    const inconsistentWinding = [...edges.values()].filter(e => e.winding !== 0).length;
    assert.equal(boundaryEdges, 0, role + ' must have no open surface boundary');
    assert.equal(nonManifoldEdges, 0, role + ' must be a closed manifold');
    assert.equal(inconsistentWinding, 0, role + ' must have consistent outward winding');
    assert(volume > 0, role + ' must enclose a positive solid volume');
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(surface.positions, 3));
    geometry.setIndex(new THREE.BufferAttribute(surface.indices, 1)); geometry.computeVertexNormals();
    const normals = geometry.attributes.normal;
    for (const v of used) assert(Math.abs(Math.hypot(normals.getX(v), normals.getY(v), normals.getZ(v)) - 1) < 1e-5);
    assert.deepEqual(original, copies, 'display reconstruction must not modify source buffers');
    report.rocks.push({role, sourceMesh: model.mesh_names[id], inputVertices: vn, inputFaces: fn,
      displayVertices: surface.positions.length / 3, displayFaces: surface.indices.length / 3,
      boundaryEdges, nonManifoldEdges, inconsistentWinding, enclosedVolume: volume,
      eulerCharacteristic: used.size - edges.size + surface.indices.length / 3, smoothNormals: true,
      originalUVsRetained: true, texturedSurfaceClosed: true, texturedVertices: textured.positions.length / 3});
    geometry.dispose();
  }
  assert.equal(report.rocks.length, 2);
  assert.deepEqual(world.physicalState(), before);
  report.physicsUnchanged = true; report.passed = true;
} finally { world.destroy(); }
if (process.argv[2]) fs.writeFileSync(process.argv[2], JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report));
