"""Build photo-textured tabletop plaques as self-contained GLB and USDZ files."""
from pathlib import Path
from PIL import Image
import io,json,math,struct,zipfile
import numpy as np

A=Path(__file__).parent/'assets'
D=('burger','pasta','shrimp','salmon','dessert')

def texture(name):
    im=Image.open(A/f'{name}-photo.webp').convert('RGB');im.thumbnail((768,768),Image.Resampling.LANCZOS)
    b=io.BytesIO();im.save(b,'PNG',optimize=True);return b.getvalue()

def glb(name,png):
    w=h=.29;t=math.radians(12);yt=.018+math.cos(t)*h;zt=math.sin(t)*h
    p=np.array([[-w/2,.018,0],[w/2,.018,0],[w/2,yt,zt],[-w/2,yt,zt]],np.float32)
    n=np.tile(np.array([0,-math.sin(t),math.cos(t)],np.float32),(4,1));uv=np.array([[0,1],[1,1],[1,0],[0,0]],np.float32);ix=np.array([0,1,2,0,2,3],np.uint16)
    x,z=.1525,.0175;bp=np.array([[-x,0,-z],[x,0,-z],[x,.018,-z],[-x,.018,-z],[-x,0,z],[x,0,z],[x,.018,z],[-x,.018,z]],np.float32)
    bix=np.array([[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,4,7],[0,7,3],[1,2,6],[1,6,5],[3,7,6],[3,6,2],[0,1,5],[0,5,4]],np.uint16).reshape(-1)
    bn=np.zeros_like(bp)
    for tri in bix.reshape(-1,3):
        f=np.cross(bp[tri[1]]-bp[tri[0]],bp[tri[2]]-bp[tri[0]])
        for i in tri:bn[i]+=f
    bn/=np.maximum(np.linalg.norm(bn,axis=1,keepdims=True),1e-9)
    chunks=[];views=[];access=[];off=0
    def view(raw,target=None):
        nonlocal off
        raw+=b'\0'*(-len(raw)%4);d={'buffer':0,'byteOffset':off,'byteLength':len(raw)}
        if target:d['target']=target
        views.append(d);chunks.append(raw);off+=len(raw);return len(views)-1
    def acc(a,kind,comp,target=None,bounds=False):
        d={'bufferView':view(a.tobytes(),target),'componentType':comp,'count':len(a),'type':kind}
        if bounds:d.update(min=a.min(axis=0).tolist(),max=a.max(axis=0).tolist())
        access.append(d);return len(access)-1
    pa=acc(p,'VEC3',5126,34962,1);na=acc(n,'VEC3',5126,34962);ua=acc(uv,'VEC2',5126,34962);ia=acc(ix,'SCALAR',5123,34963)
    ba=acc(bp,'VEC3',5126,34962,1);bna=acc(bn,'VEC3',5126,34962);bia=acc(bix,'SCALAR',5123,34963);image=view(png)
    g={'asset':{'version':'2.0','generator':'SABOR photo AR'},'scene':0,'scenes':[{'nodes':[0,1]}],'nodes':[{'name':name.title()+' photo','mesh':0},{'name':'Tabletop base','mesh':1}],'meshes':[{'primitives':[{'attributes':{'POSITION':pa,'NORMAL':na,'TEXCOORD_0':ua},'indices':ia,'material':0}]},{'primitives':[{'attributes':{'POSITION':ba,'NORMAL':bna},'indices':bia,'material':1}]}],'materials':[{'name':'Dish photograph','pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicFactor':0,'roughnessFactor':.7},'doubleSided':True},{'name':'SABOR black','pbrMetallicRoughness':{'baseColorFactor':[.018,.026,.022,1],'metallicFactor':.15,'roughnessFactor':.44}}],'textures':[{'sampler':0,'source':0}],'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':33071}],'images':[{'bufferView':image,'mimeType':'image/png'}],'buffers':[{'byteLength':off}],'bufferViews':views,'accessors':access}
    js=json.dumps(g,separators=(',',':')).encode();js+=b' '*(-len(js)%4);raw=b''.join(chunks)
    return struct.pack('<III',0x46546c67,2,28+len(js)+len(raw))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(raw),0x004e4942)+raw

def usdz(name,png):
    from pxr import Usd, UsdGeom, UsdShade, Sdf, Gf, UsdUtils
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);(root/'textures').mkdir();(root/'textures'/f'{name}.png').write_bytes(png)
        stage=Usd.Stage.CreateNew(str(root/'scene.usdc'))
        UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.y);UsdGeom.SetStageMetersPerUnit(stage,1)
        model=UsdGeom.Xform.Define(stage,'/SABOR');stage.SetDefaultPrim(model.GetPrim())
        mesh=UsdGeom.Mesh.Define(stage,'/SABOR/DishPhoto')
        t=math.radians(12)
        mesh.CreatePointsAttr([(-.145,.018,0),(.145,.018,0),(.145,.018+math.cos(t)*.29,math.sin(t)*.29),(-.145,.018+math.cos(t)*.29,math.sin(t)*.29)])
        mesh.CreateFaceVertexCountsAttr([4]);mesh.CreateFaceVertexIndicesAttr([0,1,2,3])
        mesh.CreateSubdivisionSchemeAttr('none');mesh.CreateDoubleSidedAttr(True)
        UsdGeom.PrimvarsAPI(mesh).CreatePrimvar('st',Sdf.ValueTypeNames.TexCoord2fArray,'vertex').Set([(0,0),(1,0),(1,1),(0,1)])
        mat=UsdShade.Material.Define(stage,'/SABOR/PhotoMaterial')
        shader=UsdShade.Shader.Define(stage,'/SABOR/PhotoMaterial/PBR');shader.CreateIdAttr('UsdPreviewSurface')
        shader.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(.7)
        tex=UsdShade.Shader.Define(stage,'/SABOR/PhotoMaterial/Texture');tex.CreateIdAttr('UsdUVTexture')
        tex.CreateInput('file',Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath(f'textures/{name}.png'))
        tex.CreateInput('sourceColorSpace',Sdf.ValueTypeNames.Token).Set('sRGB')
        prim=UsdShade.Shader.Define(stage,'/SABOR/PhotoMaterial/UV');prim.CreateIdAttr('UsdPrimvarReader_float2')
        prim.CreateInput('varname',Sdf.ValueTypeNames.String).Set('st');prim.CreateOutput('result',Sdf.ValueTypeNames.Float2)
        tex.CreateInput('st',Sdf.ValueTypeNames.Float2).ConnectToSource(prim.ConnectableAPI(),'result')
        tex.CreateOutput('rgb',Sdf.ValueTypeNames.Float3)
        shader.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).ConnectToSource(tex.ConnectableAPI(),'rgb')
        shader.CreateOutput('surface',Sdf.ValueTypeNames.Token)
        mat.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(),'surface')
        UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(mat)
        base=UsdGeom.Cube.Define(stage,'/SABOR/Base');base.CreateSizeAttr(1)
        base.AddTranslateOp().Set(Gf.Vec3d(0,.009,0));base.AddScaleOp().Set(Gf.Vec3f(.305,.018,.035))
        bm=UsdShade.Material.Define(stage,'/SABOR/BaseMaterial');bs=UsdShade.Shader.Define(stage,'/SABOR/BaseMaterial/PBR');bs.CreateIdAttr('UsdPreviewSurface')
        bs.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(.018,.026,.022));bs.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(.44)
        bs.CreateOutput('surface',Sdf.ValueTypeNames.Token);bm.CreateSurfaceOutput().ConnectToSource(bs.ConnectableAPI(),'surface')
        UsdShade.MaterialBindingAPI.Apply(base.GetPrim()).Bind(bm)
        stage.GetRootLayer().Save()
        dest=root/f'{name}.usdz'
        assert UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(str(root/'scene.usdc')),str(dest))
        return dest.read_bytes()

for name in D:
    png=texture(name);(A/f'{name}.glb').write_bytes(glb(name,png));(A/f'{name}.usdz').write_bytes(usdz(name,png));print(name,len(png))
