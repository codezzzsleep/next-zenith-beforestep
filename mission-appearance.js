import * as THREE from './vendor/three/three.module.js';
import {inflateGzip} from './robot-physics.js?v=mission-1';

/** Restore retained scan UVs and photo textures without replacing physics assets. */
export async function loadAppearance() {
  const base = new URL('./media/mission/appearance/', import.meta.url);
  const response = await fetch(new URL('manifest.json?v=original-materials-20261118-1', base));
  if (!response.ok) throw new Error('月面贴图暂时无法读取');
  const manifest = await response.json(), loader = new THREE.TextureLoader();
  const [surface, entries] = await Promise.all([
    fetch(new URL(manifest.uv_file, base)).then(async response => {
      if (!response.ok) throw new Error('岩石纹理坐标暂时无法读取');
      const bytes = await response.arrayBuffer(), digest = await crypto.subtle.digest('SHA-256', bytes);
      const sha = [...new Uint8Array(digest)].map(n => n.toString(16).padStart(2, '0')).join('');
      if (sha !== manifest.uv_sha256) throw new Error('岩石纹理坐标与原件不一致');
      return JSON.parse(new TextDecoder().decode(await inflateGzip(bytes)));
    }),
    Promise.all(Object.entries(manifest.textures).map(async ([id, path]) => {
      const texture = await loader.loadAsync(new URL(path, base).href);
      texture.colorSpace = THREE.SRGBColorSpace;
      texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
      texture.anisotropy = 8;
      return [id, texture];
    }))
  ]);
  return {...surface, textures: Object.fromEntries(entries), manifest};
}
