/** Retain the complete original surface; weld UV seams and duplicate faces.
 * This creates display buffers only and never changes the MuJoCo model.
 */
export function rockSurface(positions, indices, uvs = null) {
  const vertices = [], remap = new Uint32Array(positions.length / 3), keys = new Map();
  for (let i = 0; i < remap.length; i++) {
    const point = Array.from(positions.slice(i * 3, i * 3 + 3));
    const key = point.map(v => Math.round(v * 1e7)).join(':');
    if (!keys.has(key)) { keys.set(key, vertices.length / 3); vertices.push(...point); }
    remap[i] = keys.get(key);
  }
  const faces = [], textureFaces = [], known = new Set();
  for (let i = 0; i < indices.length; i += 3) {
    const face = [remap[indices[i]], remap[indices[i + 1]], remap[indices[i + 2]]];
    if (new Set(face).size !== 3) continue;
    const key = [...face].sort((a, b) => a - b).join(':');
    if (known.has(key)) continue;
    known.add(key); faces.push(...face); textureFaces.push(indices[i], indices[i + 1], indices[i + 2]);
  }
  if (uvs) {
    if (uvs.length !== remap.length * 2) throw new Error('Original rock UV count must match source vertices');
    const smooth = new Float64Array(vertices.length);
    for (let i = 0; i < faces.length; i += 3) {
      const a = faces[i] * 3, b = faces[i + 1] * 3, c = faces[i + 2] * 3;
      const ab = [vertices[b]-vertices[a], vertices[b+1]-vertices[a+1], vertices[b+2]-vertices[a+2]];
      const ac = [vertices[c]-vertices[a], vertices[c+1]-vertices[a+1], vertices[c+2]-vertices[a+2]];
      const n = [ab[1]*ac[2]-ab[2]*ac[1], ab[2]*ac[0]-ab[0]*ac[2], ab[0]*ac[1]-ab[1]*ac[0]];
      for (const p of [a,b,c]) for (let k = 0; k < 3; k++) smooth[p+k] += n[k];
    }
    const normals = new Float32Array(positions.length);
    for (let i = 0; i < remap.length; i++) {
      const p = remap[i] * 3, length = Math.hypot(smooth[p],smooth[p+1],smooth[p+2]) || 1;
      for (let k = 0; k < 3; k++) normals[i*3+k] = smooth[p+k] / length;
    }
    // UV seams keep separate vertices but share geometric normals and closed faces.
    return {positions: new Float32Array(positions), indices: new Uint32Array(textureFaces),
      uvs: new Float32Array(uvs), normals};
  }
  return {positions: new Float32Array(vertices), indices: new Uint32Array(faces)};
}
