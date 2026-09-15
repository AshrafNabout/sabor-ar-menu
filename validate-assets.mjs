import fs from 'node:fs/promises';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { USDZExporter } from 'three/examples/jsm/exporters/USDZExporter.js';
import validator from 'gltf-validator';
for (const name of ['burger','pasta','shrimp','salmon','dessert']) {
 const bytes=await fs.readFile(new URL('./assets/'+name+'.glb',import.meta.url));
 const report=await validator.validateBytes(new Uint8Array(bytes));
 console.log(name,JSON.stringify({errors:report.issues.numErrors,warnings:report.issues.numWarnings,messages:report.issues.messages.filter(m=>m.severity<2).slice(0,3)}));
 if(report.issues.numErrors)throw new Error('Invalid GLB: '+name);
 const gltf=await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
 gltf.scene.traverse(obj=>{if(obj.isMesh){obj.material.side=0}});
 const usdz=await new USDZExporter().parseAsync(gltf.scene);
 await fs.writeFile(new URL('./assets/'+name+'.usdz',import.meta.url),usdz);
 console.log(name,'USDZ bytes',usdz.length);
}
