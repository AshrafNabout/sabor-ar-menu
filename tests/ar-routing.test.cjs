const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
function boot(userAgent,search=''){
 const elements=new Map();
 function element(){return {hidden:false,dataset:{},attrs:{},listeners:{},classList:{add(){},remove(){}},setAttribute(k,v){this.attrs[k]=v},append(){},addEventListener(k,f){this.listeners[k]=f},querySelector(){return this.image||(this.image={})},scrollIntoView(){this.scrolled=true}}}
 const get=id=>{if(!elements.has(id))elements.set(id,element());return elements.get(id)};
 const context={navigator:{userAgent,platform:'',maxTouchPoints:0},URL,URLSearchParams,setTimeout:()=>1,clearTimeout(){},location:{href:'https://ashrafnabout.github.io/sabor-ar-menu/'+search,hash:'',search},history:{replaceState(){}},window:{addEventListener(){}},document:{getElementById:get,querySelectorAll:()=>[],querySelector:()=>get('qr'),createElement:tag=>tag==='canvas'?{getContext:()=>null}:element()}};
 vm.createContext(context);vm.runInContext(fs.readFileSync('app.js','utf8'),context);
 return {get,run:code=>vm.runInContext(code,context)};
}
test('iPhone launches the selected USDZ directly',()=>{
 const a=boot('iPhone');a.run("choose('salmon')");
 assert.equal(a.get('iosAR').hidden,false);assert.equal(a.get('androidAR').hidden,true);
 assert.match(a.get('iosAR').href,/salmon.usdz\?v=6/);
});
test('Android links to selected GLB and retains selection in fallback',()=>{
 const a=boot('Android');a.run("choose('dessert')");
 assert.equal(a.get('androidAR').hidden,false);assert.equal(a.get('ar').hidden,true);
 const uri=decodeURIComponent(a.get('androidAR').href);
 assert.match(uri,/assets\/dessert.glb\?v=6/);assert.match(uri,/mode=ar_preferred/);assert.match(uri,/ar=unavailable#dessert/);
});
test('desktop directs AR users to the QR code',()=>{
 const a=boot('Desktop');a.get('ar').listeners.click();assert.equal(a.get('qr').scrolled,true);
});
test('WebGL failure preserves the dish photo',async()=>{
 const a=boot('Desktop');await a.run('showModel()');
 assert.equal(a.get('dishPhoto').hidden,false);assert.equal(a.get('modelHost').hidden,true);
 assert.match(a.get('arHelp').textContent,/unavailable/);
});
test('native Android fallback has actionable guidance',()=>{
 const a=boot('Android','?ar=unavailable');assert.match(a.get('arHelp').textContent,/AR could not open/);
});
