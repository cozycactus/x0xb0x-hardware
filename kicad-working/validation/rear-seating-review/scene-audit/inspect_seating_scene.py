import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update()
panel=bpy.data.objects['Rear panel — original DXF'];inv=panel.matrix_world.inverted()
out={'source_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'panel_parent_matrix':[list(r)for r in panel.matrix_world],'instances':[]}
for inst in bpy.context.evaluated_depsgraph_get().object_instances:
 o=inst.object
 if o.type!='MESH':continue
 parent=inst.parent.name if inst.parent else ''
 if parent not in ['Rear panel — original DXF','Case / bottom','Case / upper']and not o.name.startswith('IOBOARD/')and not any(o.name.startswith(r+' /')for r in ['HEADPHONE0','MIXIN0','MIXOUT0','CV0','GATE0']):continue
 if o.name.startswith('IOBOARD/')and not any(o.name.startswith('IOBOARD/'+r+'/')for r in ['POWER0','HEADPHONE0','MIXIN0','MIXOUT0','CV0','GATE0','USB0','DIN1','DIN2','DIN3','DIN4']):continue
 m=inv@inst.matrix_world
 p=[m@v.co*1000 for v in o.data.vertices]
 out['instances'].append(dict(name=o.name,parent=parent,vertex_count=len(p),matrix_panel_local=[list(r)for r in m],bounds_panel_local_mm=[min(v[i]for v in p)for i in range(3)]+[max(v[i]for v in p)for i in range(3)],materials=[m.name for m in o.data.materials]))
(HERE/'scene-inventory.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
