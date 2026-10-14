"""Read-only coarse sampling of board vertices in saved Blender assembly."""
import bpy, json, hashlib
from pathlib import Path
from mathutils import Vector
base=Path(__file__).resolve().parent.parent
bpy.context.scene.frame_set(1)
rows=[]
for key,name in [('mainboard','Mainboard — B.Cu outward in assembled view'),('ioboard','I/O board — rear mounting approximation')]:
    inst=bpy.data.objects[name]
    for o in inst.instance_collection.objects:
        if o.type!='MESH': continue
        ref=o.parent.get('source_reference') if o.parent else None
        ref=ref or o.get('source_reference') or 'PCB'
        mat=inst.matrix_world@o.matrix_world
        budget=1500 if ref=='PCB' else 100
        step=max(1,len(o.data.vertices)//budget)
        verts=[list((mat@v.co)*1000) for v in [o.data.vertices[i] for i in range(0,len(o.data.vertices),step)]]
        corners=[list((mat@Vector(v))*1000) for v in o.bound_box]
        rows.append({'board':key,'reference':ref,'object':o.name,'samples':verts,
                     'bounds':[[min(v[j] for v in corners) for j in range(3)],
                               [max(v[j] for v in corners) for j in range(3)]]})
(base/'case-model/scene-clearance-samples.json').write_text(json.dumps({'blend':bpy.data.filepath,'sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'rows':rows}))
print('Sampled',len(rows),'mesh objects;',sum(len(r['samples']) for r in rows),'vertices')
