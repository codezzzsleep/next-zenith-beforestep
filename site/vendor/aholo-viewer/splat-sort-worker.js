var __defProp = Object.defineProperty;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __esm = (fn, res, err) => function __init() {
  if (err) throw err[0];
  try {
    return fn && (res = (0, fn[__getOwnPropNames(fn)[0]])(fn = 0)), res;
  } catch (e) {
    throw err = [e], e;
  }
};
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};

// ../../external/egs-core/packages/utils/splat-utils/simd/sort.wasm.js
var sort_wasm_exports = {};
__export(sort_wasm_exports, {
  default: () => sort_wasm_default
});
var buffer, sort_wasm_default;
var init_sort_wasm = __esm({
  "../../external/egs-core/packages/utils/splat-utils/simd/sort.wasm.js"() {
    buffer = (function(base64Data) {
      const binary = globalThis.atob(base64Data);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; ++i) {
        bytes[i] = binary.charCodeAt(i);
      }
      return bytes.buffer;
    })("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");
    sort_wasm_default = buffer;
  }
});

// ../../external/egs-core/packages/utils/splat-utils/simd/sort-module.js
var sort_module_exports = {};
__export(sort_module_exports, {
  default: () => sort_module_default
});
async function Module(moduleArg = {}) {
  var Module2 = moduleArg;
  var ENVIRONMENT_IS_WEB = !!globalThis.window;
  var ENVIRONMENT_IS_WORKER = !!globalThis.WorkerGlobalScope;
  globalThis.process?.versions?.node && globalThis.process;
  var _scriptName = import.meta.url;
  var scriptDirectory = "";
  function locateFile(path) {
    return scriptDirectory + path;
  }
  var readAsync, readBinary;
  if (ENVIRONMENT_IS_WEB || ENVIRONMENT_IS_WORKER) {
    try {
      scriptDirectory = new URL(".", _scriptName).href;
    } catch {
    }
    if (ENVIRONMENT_IS_WORKER) readBinary = (url) => {
      var xhr = new XMLHttpRequest();
      xhr.open("GET", url, false);
      xhr.responseType = "arraybuffer";
      xhr.send(null);
      return new Uint8Array(xhr.response);
    };
    readAsync = async (url) => {
      var response = await fetch(url, { credentials: "same-origin" });
      if (response.ok) return response.arrayBuffer();
      throw new Error(response.status + " : " + response.url);
    };
  }
  console.log.bind(console);
  var err = console.error.bind(console);
  var ABORT = false;
  function getMemoryBuffer() {
    return wasmMemory.buffer;
  }
  function updateMemoryViews() {
    if (HEAP8?.buffer?.resizable) return;
    var b = getMemoryBuffer();
    HEAP8 = new Int8Array(b);
    HEAPU8 = new Uint8Array(b);
    Module2["HEAPU32"] = new Uint32Array(b);
    Module2["HEAPF32"] = new Float32Array(b);
  }
  function preRun() {
  }
  function initRuntime() {
    0;
    wasmExports["c"]();
  }
  function postRun() {
  }
  function abort(what) {
    what = `Aborted(${what})`;
    err(what);
    ABORT = true;
    what += ". Build with -sASSERTIONS for more info.";
    throw new WebAssembly.RuntimeError(what);
  }
  var wasmBinaryFile;
  function findWasmBinary() {
    if (Module2["locateFile"]) return locateFile("sort-module.wasm");
    return new URL("sort-module.wasm", import.meta.url).href;
  }
  function getBinarySync(file) {
    if (readBinary) return readBinary(file);
    throw "both async and sync fetching of the wasm failed";
  }
  async function getWasmBinary(binaryFile) {
    if (true) try {
      return await readAsync(binaryFile);
    } catch {
    }
    return getBinarySync(binaryFile);
  }
  async function instantiateArrayBuffer(binaryFile, imports) {
    try {
      var binary = await getWasmBinary(binaryFile);
      var instance = await WebAssembly.instantiate(binary, imports);
      return instance;
    } catch (reason) {
      err(`failed to asynchronously prepare wasm: ${reason}`);
      abort(reason);
    }
  }
  async function instantiateAsync(binary, binaryFile, imports) {
    if (!binary) try {
      var response = fetch(binaryFile, { credentials: "same-origin" });
      var instantiationResult = await WebAssembly.instantiateStreaming(response, imports);
      return instantiationResult;
    } catch (reason) {
      err(`wasm streaming compile failed: ${reason}`);
      err("falling back to ArrayBuffer instantiation");
    }
    return instantiateArrayBuffer(binaryFile, imports);
  }
  function getWasmImports() {
    var imports = { a: wasmImports };
    return imports;
  }
  var HEAP8;
  var HEAPU8;
  var alignMemory = (size, alignment) => Math.ceil(size / alignment) * alignment;
  var getHeapMax = () => 2147483648;
  var growMemory = (size) => {
    var oldHeapSize = wasmMemory.buffer.byteLength;
    var pages = (size - oldHeapSize + 65535) / 65536 | 0;
    try {
      wasmMemory.grow(pages);
      updateMemoryViews();
      return 1;
    } catch (e) {
    }
  };
  var wasmMemory;
  function assignWasmExports(wasmExports2) {
    Module2["_reset_buckets"] = wasmExports2["d"];
    Module2["_project_chunk"] = wasmExports2["e"];
    Module2["_write_order"] = wasmExports2["f"];
    Module2["_malloc"] = wasmExports2["g"];
    Module2["_realloc"] = wasmExports2["h"];
    wasmMemory = wasmExports2["b"];
    wasmExports2["__indirect_function_table"];
  }
  var wasmImports = { a: (requestedSize) => {
    var oldSize = HEAPU8.length;
    requestedSize >>>= 0;
    var maxHeapSize = getHeapMax();
    if (requestedSize > maxHeapSize) return false;
    for (var cutDown = 1; cutDown <= 4; cutDown *= 2) {
      var overGrownHeapSize = oldSize * (1 + 0.2 / cutDown);
      overGrownHeapSize = Math.min(overGrownHeapSize, requestedSize + 100663296);
      var newSize = Math.min(maxHeapSize, alignMemory(Math.max(requestedSize, overGrownHeapSize), 65536));
      var replacement = growMemory(newSize);
      if (replacement) return true;
    }
    return false;
  } };
  var wasmExports;
  wasmExports = await (async function() {
    function receiveInstance(instance) {
      wasmExports = instance.exports;
      assignWasmExports(wasmExports);
      updateMemoryViews();
      return wasmExports;
    }
    var info = getWasmImports();
    var instantiateWasm = Module2["instantiateWasm"];
    if (instantiateWasm) return new Promise((resolve) => {
      instantiateWasm(info, (inst) => resolve(receiveInstance(inst)));
    });
    wasmBinaryFile ?? (wasmBinaryFile = findWasmBinary());
    var result = await instantiateAsync(void 0, wasmBinaryFile, info);
    var exports = (function(result2) {
      return receiveInstance(result2["instance"]);
    })(result);
    return exports;
  })();
  await (async function() {
    preRun();
    if (ABORT) return;
    initRuntime();
    postRun();
  })();
  ;
  return Module2;
}
var sort_module_default;
var init_sort_module = __esm({
  "../../external/egs-core/packages/utils/splat-utils/simd/sort-module.js"() {
    sort_module_default = Module;
  }
});

// ../../external/egs-core/packages/utils/splat-utils/simd/sort.ts
var CHUNK_SIZE = 4096;
var CHUNK_BYTES = CHUNK_SIZE * 4 * Float32Array.BYTES_PER_ELEMENT;
var SIMD_ALIGNMENT = 16;
async function createSimdSort() {
  const [binary, loader] = await Promise.all([Promise.resolve().then(() => (init_sort_wasm(), sort_wasm_exports)), Promise.resolve().then(() => (init_sort_module(), sort_module_exports))]);
  const wasm = await loader.default({
    async instantiateWasm(imports, receiveInstance) {
      const module = await WebAssembly.compile(binary.default);
      const instance = new WebAssembly.Instance(module, imports);
      receiveInstance(instance, module);
    }
  });
  let dataPtr = wasm._malloc(CHUNK_BYTES + SIMD_ALIGNMENT - 1);
  if (!dataPtr) {
    throw new Error("Failed to allocate the SIMD sort buffer.");
  }
  let dataBytes = CHUNK_BYTES;
  return (request) => {
    const { count, sorting, ordering, cameraPosition, cameraDirection, depthBias, radial } = request;
    const keysBytes = Math.ceil(count / 4) * 4 * Uint32Array.BYTES_PER_ELEMENT;
    const bytes = CHUNK_BYTES + keysBytes + count * Uint32Array.BYTES_PER_ELEMENT;
    if (bytes > dataBytes) {
      const nextPtr = wasm._realloc(dataPtr, bytes + SIMD_ALIGNMENT - 1);
      if (!nextPtr) {
        throw new Error(`Failed to allocate ${bytes} bytes for SIMD sorting.`);
      }
      dataPtr = nextPtr;
      dataBytes = bytes;
    }
    const centersPtr = Math.ceil(dataPtr / SIMD_ALIGNMENT) * SIMD_ALIGNMENT;
    const keysPtr = centersPtr + CHUNK_BYTES;
    const orderPtr = keysPtr + keysBytes;
    const chunk = wasm.HEAPF32.subarray(centersPtr >>> 2, (centersPtr >>> 2) + CHUNK_SIZE * 4);
    const [cx, cy, cz] = cameraPosition;
    const [dx, dy, dz] = cameraDirection;
    wasm._reset_buckets();
    for (let start = 0; start < count; start += CHUNK_SIZE) {
      const end = Math.min(start + CHUNK_SIZE, count);
      chunk.set(sorting.subarray(start * 4, end * 4));
      wasm._project_chunk(
        centersPtr,
        keysPtr + start * 4,
        end - start,
        cx,
        cy,
        cz,
        dx,
        dy,
        dz,
        depthBias,
        +radial
      );
    }
    const activeCount = wasm._write_order(keysPtr, count, orderPtr);
    ordering.set(wasm.HEAPU32.subarray(orderPtr >>> 2, (orderPtr >>> 2) + activeCount));
    return { activeCount, sorting, ordering };
  };
}

// ../../external/egs-core/packages/utils/splat-utils/worker.ts
var DEPTH_INFINITY_F32 = 2139095040 - 1;
var KEY_SHIFT = 8;
var depthBuckets;
function countingSort(count, depthBits2, order) {
  const buckets = depthBuckets ?? (depthBuckets = new Uint32Array(1 << 31 - KEY_SHIFT));
  buckets.fill(0);
  let minBucket = buckets.length;
  let maxBucket = -1;
  for (let i = 0; i < count; i++) {
    const key = depthBits2[i];
    if (key < DEPTH_INFINITY_F32) {
      const bucket = key >>> KEY_SHIFT;
      buckets[bucket]++;
      if (bucket < minBucket) {
        minBucket = bucket;
      }
      if (bucket > maxBucket) {
        maxBucket = bucket;
      }
    }
  }
  let activeCount = 0;
  for (let bucket = maxBucket; bucket >= minBucket; bucket--) {
    const size = buckets[bucket];
    buckets[bucket] = activeCount;
    activeCount += size;
  }
  for (let i = 0; i < count; i++) {
    const key = depthBits2[i];
    if (key < DEPTH_INFINITY_F32) {
      order[buckets[key >>> KEY_SHIFT]++] = i;
    }
  }
  return activeCount;
}
var depths = new Float32Array(0);
var depthBits = new Uint32Array(depths.buffer);
function sortSplats(request) {
  const { count, sorting, ordering, cameraPosition, cameraDirection, radial, depthBias } = request;
  if (depths.length < count) {
    depths = new Float32Array(count);
    depthBits = new Uint32Array(depths.buffer);
  }
  const [cx, cy, cz] = cameraPosition;
  const [dx, dy, dz] = cameraDirection;
  for (let i = 0; i < count; i++) {
    const p = i * 4;
    let depth = Infinity;
    if (sorting[p + 3] > 0) {
      const x = sorting[p] - cx;
      const y = sorting[p + 1] - cy;
      const z = sorting[p + 2] - cz;
      const biasedDepth = x * dx + y * dy + z * dz + depthBias;
      if (biasedDepth > 0) {
        depth = radial ? Math.sqrt(x * x + y * y + z * z) : biasedDepth;
      }
    }
    depths[i] = depth;
  }
  const activeCount = countingSort(count, depthBits, ordering);
  return { activeCount, sorting, ordering };
}
var sorter = createSimdSort().catch((error) => {
  console.warn("Splat sort WASM initialization failed; using JavaScript.", error);
  return sortSplats;
});
self.onmessage = async ({ data }) => {
  try {
    if (data.taskType !== "SortSplats" /* SortSplats */) {
      throw new Error(`Unsupported task type: ${data.taskType}.`);
    }
    const payload = (await sorter)(data.payload);
    postMessage({ status: 0 /* Success */, payload }, [
      payload.sorting.buffer,
      payload.ordering.buffer
    ]);
  } catch (error) {
    postMessage({ status: 1 /* Fail */, payload: String(error) });
  }
};
//# sourceMappingURL=splat-sort-worker.js.map
