"""Repair the recovered burger's exported all-grey PBR materials."""
import json,struct
from pathlib import Path
p=Path('assets/burger.glb');b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);binary=b[20+n:]
colors={'Brioche':[.67,.29,.065,1],'Cheddar':[1,.63,.055,1],'Fries':[.94,.58,.12,1],'Lettuce':[.13,.42,.035,1],'Plate':[.10,.15,.13,1],'Tomato':[.70,.035,.014,1],'Wagyu':[.16,.052,.02,1]}
for m in j['materials']:m['pbrMetallicRoughness']['baseColorFactor']=colors[m['name']]
raw=json.dumps(j,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4);p.write_bytes(struct.pack('<III',0x46546c67,2,20+len(raw)+len(binary))+struct.pack('<II',len(raw),0x4e4f534a)+raw+binary)
