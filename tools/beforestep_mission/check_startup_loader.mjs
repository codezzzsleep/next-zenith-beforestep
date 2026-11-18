import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {StartupLoader} from '../../site/startup-loader.js';
const manifest=JSON.parse(fs.readFileSync(new URL('../../site/startup-assets.json',import.meta.url)));
// Build a stored ZIP fixture from the repository's unchanged runtime assets.
const table=Uint32Array.from({length:256},(_,n)=>{for(let i=0;i<8;i++)n=n&1?0xedb88320^(n>>>1):n>>>1;return n>>>0;});
const crc=bytes=>{let n=0xffffffff;for(const b of bytes)n=table[(n^b)&255]^(n>>>8);return (n^0xffffffff)>>>0;};
const local=[],central=[];let offset=0;
for(const file of manifest.files){
 const bytes=fs.readFileSync(new URL('../../site/'+file.path,import.meta.url)),name=Buffer.from(file.path),h=Buffer.alloc(30);
 h.writeUInt32LE(0x04034b50,0);h.writeUInt16LE(20,4);h.writeUInt32LE(crc(bytes),14);h.writeUInt32LE(bytes.length,18);h.writeUInt32LE(bytes.length,22);h.writeUInt16LE(name.length,26);
 assert.equal(offset+30+name.length,file.offset);local.push(h,name,bytes);
 const c=Buffer.alloc(46);c.writeUInt32LE(0x02014b50,0);c.writeUInt16LE(20,4);c.writeUInt16LE(20,6);c.writeUInt32LE(crc(bytes),16);c.writeUInt32LE(bytes.length,20);c.writeUInt32LE(bytes.length,24);c.writeUInt16LE(name.length,28);c.writeUInt32LE(offset,42);central.push(c,name);offset+=h.length+name.length+bytes.length;
}
const directory=Buffer.concat(central),end=Buffer.alloc(22);end.writeUInt32LE(0x06054b50);end.writeUInt16LE(manifest.files.length,8);end.writeUInt16LE(manifest.files.length,10);end.writeUInt32LE(directory.length,12);end.writeUInt32LE(offset,16);
const zip=Buffer.concat([...local,directory,end]);manifest.archive_bytes=zip.length;manifest.archive_sha256=createHash('sha256').update(zip).digest('hex');
const files=new Map(manifest.files.map(f=>[f.path,zip.subarray(f.offset,f.offset+f.bytes)]));
const store=new Map(),storage={async open(){return {async match(key){return store.get(key)?.clone();},async put(key,response){store.set(key,response.clone());},async delete(key){return store.delete(key);}};}};
let calls=[];
function fetcher(mode){return async(url,options)=>{
 calls.push({url,range:options.headers?.Range});
 if(url.startsWith('https://origin.example/'))return new Response(files.get(new URL(url).pathname.slice(1)));
 if(mode==='failure')throw new TypeError('CORS blocked');
 if(mode==='whole')return new Response(zip);
 const match=/bytes=(\d+)-(\d+)/.exec(options.headers.Range),start=+match[1],end=+match[2];
 const bytes=zip.subarray(start,end+1);
 if(mode==='corrupt'){const wrong=Buffer.from(bytes);wrong[0]^=1;return new Response(wrong,{status:206});}
 return new Response(bytes,{status:206});
};}
async function load(mode,cacheStorage=undefined){
 const loader=new StartupLoader(manifest,{fetcher:fetcher(mode),cacheStorage,base:'https://origin.example/'});
 const results=await Promise.all(manifest.files.map(async f=>[f.path,await loader.get(f.path)]));
 for(const [path,bytes]of results)assert(Buffer.from(bytes).equals(files.get(path)),path);
 assert.equal(loader.snapshot().loaded,loader.snapshot().total);return loader;
}
await load('range',storage);assert.equal(calls.length,5);assert(calls.every(c=>c.range));
calls=[];await load('failure',storage);assert.equal(calls.length,0,'verified persistent cache should require no network');
store.set([...store.keys()][0],new Response('bad cache'));calls=[];await load('range',storage);assert.equal(calls.length,1);
calls=[];await load('whole');assert.equal(calls.filter(c=>!c.range).length,1,'shared whole ZIP fallback downloaded once');
calls=[];await load('corrupt');assert.equal(calls.filter(c=>c.url.startsWith('https://origin.example/')).length,5);
calls=[];await load('failure');assert.equal(calls.filter(c=>c.url.startsWith('https://origin.example/')).length,5);
console.log(JSON.stringify({passed:true,checks:['exact original bytes from five ZIP ranges','persistent cache avoids network','corrupt cache is discarded','non-range server uses one shared full ZIP','corrupt CDN content falls back to original files','blocked CORS falls back without trusting bad data']}));
