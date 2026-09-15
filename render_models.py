"""Render faithful static previews of the actual geometry for the fallback view."""
import trimesh, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from pathlib import Path
for name in ['burger','pasta','shrimp','salmon','dessert']:
    scene=trimesh.load('assets/'+name+'.glb');fig=plt.figure(figsize=(7,6),dpi=120);ax=fig.add_subplot(projection='3d',computed_zorder=False);fig.patch.set_alpha(0);ax.patch.set_alpha(0)
    for node in scene.graph.nodes_geometry:
        transform,key=scene.graph[node];mesh=scene.geometry[key].copy();mesh.apply_transform(transform)
        verts=mesh.vertices[:,[0,2,1]];tri=verts[mesh.faces]
        mat=mesh.visual.material;color=np.array(getattr(mat,'baseColorFactor',[180,180,180,255]),dtype=float)/255
        normal=mesh.face_normals[:,[0,2,1]];light=np.array([-.4,-.6,1]);light/=np.linalg.norm(light);shade=.5+.5*np.maximum(0,normal@light);colors=np.tile(color,(len(tri),1));colors[:,:3]*=shade[:,None];colors[:,3]=1
        ax.add_collection3d(Poly3DCollection(tri,facecolors=colors,edgecolors='none',zsort='average',zorder=1+mesh.vertices[:,1].mean()*10000))
    ax.set_xlim(-.18,.18);ax.set_ylim(-.18,.18);ax.set_zlim(0,.25);ax.set_box_aspect((.36,.36,.25));ax.view_init(27,-65);ax.set_axis_off();ax.set_position([0,0,1,1]);plt.savefig('assets/'+name+'.png',transparent=True,pad_inches=0);plt.close(fig)
    print('Rendered',name)
