import fs from 'node:fs/promises';
import validator from 'gltf-validator';
for (const name of ['burger','pasta','shrimp','salmon','dessert']) {
 const bytes=await fs.readFile(new URL('./assets/'+name+'.glb',import.meta.url));
 const report=await validator.validateBytes(new Uint8Array(bytes));
 console.log(name,JSON.stringify({errors:report.issues.numErrors,warnings:report.issues.numWarnings}));
 if(report.issues.numErrors)throw new Error('Invalid GLB: '+name);
}
