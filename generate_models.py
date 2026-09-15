"""Generate original, metre-scale SABOR concept dishes as self-contained GLB files."""
import json, struct, math, random
from pathlib import Path
import numpy as np
random.seed(27)
OUT=Path(__file__).parent/'assets'
class Dish:
    def __init__(self): self.parts=[]
    def mesh(self,v,f,color): self.parts.append((np.array(v,dtype=np.float32),np.array(f,dtype=np.uint32),color))
    def sphere(self,p,s,c):
        v=[];f=[];n=24;m=12
        for i in range(m+1):
            a=math.pi*i/m
            for k in range(n):
                b=2*math.pi*k/n;v.append([p[0]+s[0]*math.sin(a)*math.cos(b),p[1]+s[1]*math.cos(a),p[2]+s[2]*math.sin(a)*math.sin(b)])
        for i in range(m):
            for k in range(n):
                a=i*n+k;b=i*n+(k+1)%n;f.extend([[a,b,a+n],[b,b+n,a+n]])
        self.mesh(v,f,c)
    def cylinder(self,p,r,h,c,top=None):
        top=r if top is None else top;v=[];f=[];n=48
        for y,rr in [(p[1]-h/2,r),(p[1]+h/2,top)]:
            v.extend([[p[0]+rr*math.cos(2*math.pi*k/n),y,p[2]+rr*math.sin(2*math.pi*k/n)] for k in range(n)])
        v.extend([[p[0],p[1]-h/2,p[2]],[p[0],p[1]+h/2,p[2]]])
        for k in range(n):
            j=(k+1)%n;f.extend([[k,k+n,j],[j,k+n,j+n],[2*n,k,j],[2*n+1,j+n,k+n]])
        self.mesh(v,f,c)
    def tube(self,points,r,c):
        v=[];f=[];n=8;points=np.array(points)
        for i,p in enumerate(points):
            t=points[min(i+1,len(points)-1)]-points[max(i-1,0)];t=t/np.linalg.norm(t)
            a=np.cross(t,[0,1,0]);a=a/np.linalg.norm(a);b=np.cross(t,a)
            for k in range(n):v.append(p+r*(math.cos(k*2*math.pi/n)*a+math.sin(k*2*math.pi/n)*b))
        for i in range(len(points)-1):
            for k in range(n):
                a=i*n+k;b=i*n+(k+1)%n;f.extend([[a,b,a+n],[b,b+n,a+n]])
        self.mesh(v,f,c)
    def plate(self):
        self.cylinder((0,.006,0),.145,.008,[.12,.15,.16]);self.cylinder((0,.011,0),.128,.004,[.19,.23,.24]);
    def garnish(self):
        for i in range(14):
            a=random.random()*6.28;r=random.uniform(.05,.11);self.sphere((r*math.cos(a),.025,r*math.sin(a)),(.006,.002,.003),[.14,.38,.07])
    def save(self,name):
        chunks=[];views=[];access=[];meshes=[];mats=[];offset=0
        def add(data,typ,component,values):
            nonlocal offset
            raw=data.tobytes();raw+=b'\0'*((-len(raw))%4);views.append({'buffer':0,'byteOffset':offset,'byteLength':len(raw)});chunks.append(raw);offset+=len(raw)
            item={'bufferView':len(views)-1,'componentType':component,'count':len(data),'type':typ}
            if values:item.update(min=data.min(axis=0).tolist(),max=data.max(axis=0).tolist())
            access.append(item);return len(access)-1
        for v,f,c in self.parts:
            norm=np.zeros_like(v);face=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]])
            for k in range(3):np.add.at(norm,f[:,k],face)
            lengths=np.linalg.norm(norm,axis=1,keepdims=True);norm/=np.maximum(lengths,1e-12);norm[lengths[:,0]<1e-10]=[0,1,0]
            pos=add(v,'VEC3',5126,True);normal=add(norm,'VEC3',5126,False);indices=add(f.reshape(-1),'SCALAR',5125,False)
            mats.append({'pbrMetallicRoughness':{'baseColorFactor':c+[1],'metallicFactor':0,'roughnessFactor':.65},'doubleSided':True})
            meshes.append({'primitives':[{'attributes':{'POSITION':pos,'NORMAL':normal},'indices':indices,'material':len(mats)-1}]})
        j={'asset':{'version':'2.0','generator':'SABOR original concept dishes'},'scene':0,'scenes':[{'nodes':list(range(len(meshes)))}],'nodes':[{'mesh':i} for i in range(len(meshes))],'meshes':meshes,'materials':mats,'buffers':[{'byteLength':offset}],'bufferViews':views,'accessors':access}
        raw=json.dumps(j,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4);binary=b''.join(chunks)
        (OUT/(name+'.glb')).write_bytes(struct.pack('<III',0x46546c67,2,28+len(raw)+len(binary))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(binary),0x004e4942)+binary)

d=Dish();d.plate()
for i in range(24):
    a=i*.74;rad=.028+(i%6)*.005
    points=[]
    for k in range(70):
        t=k/69*math.pi*3.5+a;r=rad*(.75+.25*math.sin(k*.2));points.append((r*math.cos(t),.024+.00038*k+(i%3)*.003,r*math.sin(t)))
    d.tube(points,.002,[.88,.69+.005*(i%4),.37])
for i in range(18):
    a=random.random()*6.28;r=random.random()*.055;d.sphere((r*math.cos(a),.055,r*math.sin(a)),(.004,.001,.005),[.19,.12,.07])
d.garnish();d.save('pasta')
d=Dish();d.plate()
for i in range(7):
    a=i*6.28/7;cx=.061*math.cos(a);cz=.061*math.sin(a)
    points=[(cx+.021*math.cos(k/28*4.5+a),.035+.006*math.sin(k/28*math.pi),cz+.021*math.sin(k/28*4.5+a)) for k in range(29)]
    d.tube(points,.0085,[.92,.41,.19]);p=points[-1];d.sphere(p,(.013,.003,.008),[.76,.23,.10])
d.garnish();d.save('shrimp')
d=Dish();d.plate();d.sphere((-.025,.036,0),(.074,.022,.044),[.93,.39,.23])
for i in range(6):
    x=-.08+i*.021;d.tube([(x,.050,-.032),(x+.009,.058,0),(x+.017,.049,.031)],.0016,[.43,.20,.12])
for i in range(5):
    x=.066+i*.008;d.tube([(x,.025,-.072),(x-.012,.026,.06)],.0035,[.18,.38,.09]);d.sphere((x-.012,.026,.06),(.005,.004,.009),[.23,.43,.12])
d.cylinder((.058,.021,-.08),.022,.006,[.96,.81,.20]);d.cylinder((.058,.025,-.08),.018,.001,[1,.93,.52]);d.garnish();d.save('salmon')
d=Dish();d.plate();d.cylinder((-.032,.039,0),.038,.052,[.20,.075,.03],.034);d.cylinder((-.032,.066,0),.027,.003,[.11,.03,.015]);d.sphere((.06,.039,.015),(.03,.029,.029),[.95,.87,.68])
for i in range(8):
    a=i*6.28/8;d.sphere((-.032+.031*math.cos(a),.062,.031*math.sin(a)),(.006,.008,.006),[.26,.10,.04])
d.tube([(-.032,.069,0),(-.023,.063,.032),(-.014,.038,.04),(.004,.016,.052),(.02,.016,.06)],.006,[.16,.05,.02]);d.garnish();d.save('dessert')
print('Generated four original GLB dishes')
