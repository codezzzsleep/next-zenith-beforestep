let sdkPromise;
const loadSDK = () => sdkPromise ??= import('./vendor/aholo-viewer/index.js');

class AholoGalleryViewer extends HTMLElement {
  static observedAttributes = ['src'];

  constructor() {
    super();
    this.loaded = false;
    this.loadVersion = 0;
    this.points = new Map();
    this.yaw = 20 * Math.PI / 180;
    this.pitch = 16 * Math.PI / 180;
  }

  get src() { return this.getAttribute('src'); }
  set src(value) { this.setAttribute('src', value); }
  get poster() { return this.getAttribute('poster'); }
  set poster(value) { this.setAttribute('poster', value); }

  connectedCallback() {
    this.setAttribute('role', 'img');
    this.setAttribute('aria-label', this.getAttribute('alt') || '真实 Lux3D 模型，拖动旋转');
    this.tabIndex = 0;
    if (!this.controlsAttached) this.attachControls();
    this.observer ??= new ResizeObserver(() => this.resize());
    this.observer.observe(this);
    if (this.src) this.loadModel(this.src);
  }

  disconnectedCallback() {
    ++this.loadVersion;
    this.observer?.disconnect();
    this.viewer?.destroy();
    this.viewer = null;
  }

  attributeChangedCallback(name, previous, value) {
    if (name === 'src' && value && value !== previous && this.isConnected) this.loadModel(value);
  }

  clearModel(model) {
    if (!model) return;
    this.viewer.getScene().remove(model);
    model.traverse(node => { if (node.geometry) node.freeAllGpuResourceOwned?.(); });
  }

  async loadModel(url) {
    const version = ++this.loadVersion;
    this.loaded = false;
    this.lastError = '';
    this.dataset.loaded = 'false';
    this.style.backgroundImage = this.poster ? `url("${this.poster}")` : '';
    try {
      const sdk = await loadSDK();
      if (version !== this.loadVersion) return;
      if (!this.viewer) {
        this.viewer = sdk.createViewer('beforestep-gallery', this, {});
        this.camera = new sdk.PerspectiveCamera(45, 1, .001, 1000);
        this.camera.up.set(0, 1, 0);
        this.viewer.setCamera(this.camera);
        this.viewer.getScene().add(new sdk.AmbientLight(0xffffff, 1));
        this.light = new sdk.DirectionalLight(0xffffff, .7);
        this.light.target = new sdk.Object3D();
        this.viewer.getScene().add([this.light, this.light.target]);
        sdk.setViewerConfig(this.viewer, {pipeline: {
          Background: {background: {active: sdk.BackgroundMode.BasicBackground,
            basic: {color: new sdk.Color(25 / 255, 30 / 255, 32 / 255)}}, ground: {enabled: false}},
          Splatting: {enabled: false}, TAA: {enabled: false},
        }});
        this.viewer.requestRenderHandler = () => this.requestRender();
      }
      const viewer = this.viewer;
      const response = await fetch(new URL(url, document.baseURI).href);
      if (!response.ok) throw new Error(`Model HTTP ${response.status}`);
      const buffer = await response.arrayBuffer();
      const result = await sdk.GLTFLoader.loadGLTF(buffer,
        {textureLoader: path => sdk.downloadTexture(path, {context: viewer})});
      if (version !== this.loadVersion) {
        result.scene.traverse(node => { if (node.geometry) node.freeAllGpuResourceOwned?.(); });
        return;
      }
      this.clearModel(this.model);
      this.model = result.scene;
      viewer.getScene().add(this.model);
      const bounds = new sdk.Box3().setFromObject(this.model);
      this.target = bounds.getCenter(new sdk.Vector3());
      const size = bounds.getSize(new sdk.Vector3());
      this.radius = Math.max(size.length() / 2, .001);
      this.yaw = 20 * Math.PI / 180;
      this.pitch = 16 * Math.PI / 180;
      this.fitDistance = this.radius / Math.sin(Math.PI / 8) * 1.15;
      this.distance = this.fitDistance;
      this.camera.near = this.radius / 1000;
      this.camera.far = this.radius * 100;
      this.light.target.position.copy(this.target);
      this.light.position.set(this.target.x + this.radius * 3, this.target.y + this.radius * 4,
        this.target.z + this.radius * 3);
      this.style.backgroundImage = '';
      this.resize();
      this.loaded = true;
      this.dataset.loaded = 'true';
      this.dispatchEvent(new Event('load'));
    } catch (error) {
      if (version !== this.loadVersion) return;
      this.lastError = String(error);
      this.dataset.loaded = 'error';
      this.dispatchEvent(new CustomEvent('error', {detail: String(error)}));
    }
  }

  resize() {
    if (!this.viewer || !this.target) return;
    const box = this.getBoundingClientRect();
    if (!box.width || !box.height) return;
    this.camera.aspect = box.width / box.height;
    this.camera.updateProjectionMatrix();
    this.viewer.resize();
    this.requestRender();
  }

  requestRender() {
    if (this.renderQueued) return;
    this.renderQueued = true;
    requestAnimationFrame(() => {
      this.renderQueued = false;
      if (!this.viewer || !this.target) return;
      const radius = this.distance;
      this.camera.position.set(this.target.x + radius * Math.sin(this.yaw) * Math.cos(this.pitch),
        this.target.y + radius * Math.sin(this.pitch),
        this.target.z + radius * Math.cos(this.yaw) * Math.cos(this.pitch));
      this.camera.lookAt(this.target);
      this.viewer.render();
    });
  }

  zoom(factor) {
    if (!this.fitDistance) return;
    this.distance = Math.min(this.fitDistance * 8,
      Math.max(this.fitDistance * .3, this.distance * factor));
    this.requestRender();
  }

  attachControls() {
    this.controlsAttached = true;
    this.addEventListener('pointerdown', event => {
      this.points.set(event.pointerId, [event.clientX, event.clientY]);
      this.setPointerCapture(event.pointerId);
      this.pinchDistance = null;
    });
    this.addEventListener('pointermove', event => {
      const previous = this.points.get(event.pointerId);
      if (!previous) return;
      this.points.set(event.pointerId, [event.clientX, event.clientY]);
      if (this.points.size === 1) {
        this.yaw -= (event.clientX - previous[0]) * .01;
        this.pitch = Math.max(-1.45, Math.min(1.45, this.pitch + (event.clientY - previous[1]) * .01));
        this.requestRender();
      } else {
        const [a, b] = [...this.points.values()];
        const distance = Math.hypot(a[0] - b[0], a[1] - b[1]);
        if (this.pinchDistance && distance) this.zoom(this.pinchDistance / distance);
        this.pinchDistance = distance;
      }
    });
    for (const type of ['pointerup', 'pointercancel']) this.addEventListener(type, event => {
      this.points.delete(event.pointerId);
      this.pinchDistance = null;
    });
    this.addEventListener('wheel', event => {
      event.preventDefault();
      this.zoom(Math.exp(event.deltaY * .001));
    }, {passive: false});
    this.addEventListener('keydown', event => {
      if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
        event.preventDefault();
        this.yaw += event.key === 'ArrowLeft' ? -.15 : .15;
        this.requestRender();
      } else if (['+', '=', '-'].includes(event.key)) {
        event.preventDefault();
        this.zoom(event.key === '-' ? 1.1 : .9);
      }
    });
  }
}

customElements.define('aholo-gallery-viewer', AholoGalleryViewer);
