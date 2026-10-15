"""Compare USB triangle contacts against every visible mesh before/after correction."""
import hashlib,json
from pathlib import Path
import bpy
import numpy as np
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent
BASELINE=HERE.parents[1]/'blender-case-revision-22/x0xb0x-populated-with-case.blend'
FINAL=HERE.parent/'x0xb0x-populated-with-case.blend'
def screen(path):
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
    items=[]
    for inst in bpy.context.evaluated_depsgraph_get().object_instances:
        obj=inst.object
        if obj.type!='MESH' or obj.original.hide_render or (inst.parent and inst.parent.original.hide_render):continue
        data=obj.data
        if not data.polygons:continue
        co=np.empty(len(data.vertices)*3);data.vertices.foreach_get('co',co);co=co.reshape(-1,3)
        m=np.array(inst.matrix_world);world=co@m[:3,:3].T+m[:3,3]
        items.append(dict(name=obj.original.name,parent=inst.parent.original.name if inst.parent else '',world=world,polys=[tuple(p.vertices) for p in data.polygons],lo=world.min(0),hi=world.max(0)))
    targets=[i for i in items if i['name'].startswith(('MAINBOARD/R100A0/','MAINBOARD/R100B0/'))];assert len(targets)==14
    contacts=[];near_count=0
    for u in targets:
        tree=BVHTree.FromPolygons([tuple(v) for v in u['world']],u['polys']);own=u['name'].rsplit('/',1)[0]+'/'
        for item in items:
            if item is u or item['name'].startswith(own) or item['name'].startswith('MAINBOARD/PCB layers/'):continue
            if not(np.all(item['lo']<=u['hi']+.002) and np.all(item['hi']>=u['lo']-.002)):continue
            near_count+=1;other=BVHTree.FromPolygons([tuple(v) for v in item['world']],item['polys']);pairs=tree.overlap(other)
            if pairs:contacts.append(dict(target=u['name'],other=item['name'],parent=item['parent'],triangle_pairs=len(pairs)))
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
    return dict(scene_sha256=digest,visible_mesh_instances=len(items),nearby_meshes_tested=near_count,contacts=contacts)
before=screen(BASELINE);after=screen(FINAL)
key=lambda c:(c['target'].rsplit('/',1)[0],c['other'],c['parent'])
new=set(map(key,after['contacts']))-set(map(key,before['contacts']))
out=dict(passed=not new,baseline=before,current=after,new_contact_objects=[list(x) for x in sorted(new)],frame=1,read_only=True,physical_fit_qualified=False,method='Actual rendered PTC parts versus other component, panel and enclosure meshes within2mm bbox. Own reference geometry and expected PCB seating contacts excluded. Triangle-contact comparison, not a volume or tolerance qualification.')
(HERE/'ptc-neighbour-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2),flush=True);assert out['passed']
