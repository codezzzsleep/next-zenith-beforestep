/** Verified original gzip assets, read directly from a stored CDN ZIP. */
export class StartupLoader {
  constructor(manifest, {onProgress = () => {}, fetcher = globalThis.fetch.bind(globalThis), cacheStorage = globalThis.caches, base = new URL('./', import.meta.url).href, headerTimeout = 5000, idleTimeout = 20000} = {}) {
    this.manifest = manifest;
    this.fetcher = fetcher;
    this.cacheStorage = cacheStorage;
    this.base = base;
    this.onProgress = onProgress;
    this.headerTimeout = headerTimeout;
    this.idleTimeout = idleTimeout;
    this.files = new Map(manifest.files.map(f => [f.path, {...f, loaded: 0, source: '', status: 'waiting'}]));
    this.promises = new Map();
    this.total = manifest.files.reduce((sum, f) => sum + f.bytes, 0);
    this.cachePromise = this.openCache();
  }
  async openCache() {
    try { return await this.cacheStorage?.open('beforestep-startup-assets-v1'); } catch { return null; }
  }
  key(file) { return new URL('__beforestep_startup__/' + file.sha256, this.base).href; }
  snapshot() {
    return {total: this.total, loaded: [...this.files.values()].reduce((sum, f) => sum + f.loaded, 0), assets: [...this.files.values()].map(({path, bytes, loaded, source, status}) => ({path, bytes, loaded, source, status}))};
  }
  notify(file, loaded, source, status = 'downloading') {
    Object.assign(file, {loaded: Math.min(file.bytes, loaded), source, status});
    this.onProgress(this.snapshot());
  }
  async valid(bytes, expected, size) {
    if (bytes.byteLength !== size) return false;
    const digest = await crypto.subtle.digest('SHA-256', bytes);
    return [...new Uint8Array(digest)].map(n => n.toString(16).padStart(2, '0')).join('') === expected;
  }
  async cached(file) {
    try {
      const cache = await this.cachePromise, hit = await cache?.match(this.key(file));
      if (!hit) return null;
      const bytes = await hit.arrayBuffer();
      if (await this.valid(bytes, file.sha256, file.bytes)) { this.notify(file, file.bytes, 'cache', 'ready'); return bytes; }
      await cache.delete(this.key(file));
    } catch {}
    return null;
  }
  async remember(file, bytes) {
    try { const cache = await this.cachePromise; await cache?.put(this.key(file), new Response(bytes.slice(0), {headers: {'Content-Type': 'application/gzip'}})); } catch {}
  }
  async read(response, size, progress, controller) {
    if (!response.ok) throw new Error('资源暂时无法读取：HTTP ' + response.status);
    if (!response.body) {
      const bytes = await response.arrayBuffer();
      if (bytes.byteLength !== size) throw new Error('资源未完整下载');
      progress(size); return bytes;
    }
    const reader = response.body.getReader(), chunks = []; let count = 0;
    let idle = setTimeout(() => controller.abort(), this.idleTimeout);
    try {
      while (true) {
        const {value, done} = await reader.read(); if (done) break;
        count += value.byteLength;
        if (count > size) { controller.abort(); throw new Error('资源长度与原记录不一致'); }
        chunks.push(value); progress(count);
        clearTimeout(idle); idle = setTimeout(() => controller.abort(), this.idleTimeout);
      }
    } finally { clearTimeout(idle); reader.releaseLock(); }
    if (count !== size) throw new Error('资源未完整下载');
    const bytes = new Uint8Array(count); let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
    return bytes.buffer;
  }
  async response(url, headers, controller) {
    const timer = setTimeout(() => controller.abort(), this.headerTimeout);
    try { return await this.fetcher(url, {headers, credentials: 'omit', signal: controller.signal}); }
    finally { clearTimeout(timer); }
  }
  mirrorUrl(mirror) {
    const url = new URL(mirror.url); url.searchParams.set('v', 'cdn-startup-20261118'); return url.href;
  }
  async archive(mirror) {
    if (!this.archivePromise) this.archivePromise = (async () => {
      const controller = new AbortController(), response = await this.response(this.mirrorUrl(mirror), {}, controller);
      const bytes = await this.read(response, this.manifest.archive_bytes, count => {
        for (const file of this.files.values()) if (file.status !== 'ready') this.notify(file, Math.round(file.bytes * count / this.manifest.archive_bytes), mirror.id);
      }, controller);
      if (!await this.valid(bytes, this.manifest.archive_sha256, this.manifest.archive_bytes)) throw new Error('下载包与原记录不一致');
      return bytes;
    })();
    return this.archivePromise;
  }
  async fromMirror(file, mirror) {
    const controller = new AbortController(); let response;
    try { response = await this.response(this.mirrorUrl(mirror), {Range: `bytes=${file.offset}-${file.offset + file.bytes - 1}`}, controller); }
    catch (error) { controller.abort(); throw error; }
    if (response.status === 200) {
      await response.body?.cancel(); controller.abort();
      const archive = await this.archive(mirror);
      return archive.slice(file.offset, file.offset + file.bytes);
    }
    if (response.status !== 206) { await response.body?.cancel(); controller.abort(); throw new Error('资源线路不支持分段读取'); }
    return this.read(response, file.bytes, count => this.notify(file, count, mirror.id), controller);
  }
  async download(file) {
    const hit = await this.cached(file); if (hit) return hit;
    for (const mirror of this.manifest.mirrors.filter(m => m.enabled)) {
      try {
        this.notify(file, 0, mirror.id);
        const bytes = await this.fromMirror(file, mirror);
        if (!await this.valid(bytes, file.sha256, file.bytes)) throw new Error('资源与原记录不一致');
        this.notify(file, file.bytes, mirror.id, 'ready'); await this.remember(file, bytes); return bytes;
      } catch { this.notify(file, 0, 'origin', 'retrying'); }
    }
    const controller = new AbortController();
    const response = await this.response(new URL(file.path, this.base).href, {}, controller);
    const bytes = await this.read(response, file.bytes, count => this.notify(file, count, 'origin'), controller);
    if (!await this.valid(bytes, file.sha256, file.bytes)) throw new Error('原资源与记录不一致，请重新加载');
    this.notify(file, file.bytes, 'origin', 'ready'); await this.remember(file, bytes); return bytes;
  }
  get(path) {
    const file = this.files.get(path); if (!file) throw new Error('未知启动资源：' + path);
    if (!this.promises.has(path)) this.promises.set(path, this.download(file));
    return this.promises.get(path);
  }
}
