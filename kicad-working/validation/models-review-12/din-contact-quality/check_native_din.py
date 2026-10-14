"""Verify the corrected STEP's actual native KiCad GLB, using Blender."""
from pathlib import Path
import hashlib,json,math,sys
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE=Path(__file__).resolve().parent
SOURCE=Path(next((s.split('=',1)[1] for s in sys.argv if s.startswith('--source=')),str(HERE/'native-probes/corrected-din.glb')))
OUTPUT=HERE/('native-final-geometry-audit.json' if '--final' in sys.argv else 'native-geometry-audit.json')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
bpy.context.view_layer.update()
checks=[]
def check(name,ok,**details):checks.append(dict(check=name,passed=bool(ok),**details))
centers=[(3.5,10.),(-3.5,10.),(-3.5/math.sqrt(2),10-3.5/math.sqrt(2)),(0.,6.5),(3.5/math.sqrt(2),10-3.5/math.sqrt(2))]
expected={'DIN1':.113538,'DIN2':.135128,'DIN3':.156718,'DIN4':.200914}
records=[]
for ref,x in expected.items():
    root=bpy.data.objects[ref]
    check(ref+' root remains at the original native footprint frame',
          (root.matrix_world.translation-Vector((x,0,.001595))).length<1e-7,
          actual_translation_m=list(root.matrix_world.translation))
    meshes=[o for o in root.children_recursive if o.type=='MESH']
    check(ref+' one native component mesh',len(meshes)==1)
    obj=meshes[0];transform=root.matrix_world.inverted()@obj.matrix_world
    points=[transform@v.co for v in obj.data.vertices]
    lo=[min(p[i] for p in points)*1000 for i in range(3)];hi=[max(p[i] for p in points)*1000 for i in range(3)]
    check(ref+' printed nominal envelope retained',max(abs(a-b) for a,b in zip(lo+hi,[-10,0,0,10,15.8,21.1]))<.0001,bounds_mm=lo+hi)
    tree=BVHTree.FromPolygons(points,[list(p.vertices) for p in obj.data.polygons])
    bores=[]
    for i,(cx,cz) in enumerate(centers):
        observations=[]
        for dx,dz in [(0,0),(.3,0),(-.3,0),(0,.3),(0,-.3)]:
            hit,normal,index,distance=tree.ray_cast(Vector(((cx+dx)/1000,-.00001,(cz+dz)/1000)),Vector((0,1,0)),.00736)
            observations.append(dict(offset_mm=[dx,dz],passed=hit is None,hit_y_mm=hit.y*1000 if hit else None))
        check(ref+' corrected contact bore '+str(i+1),all(o['passed'] for o in observations),center_mm=[cx,cz],observations=observations)
        bores.append(observations)
    records.append(dict(reference=ref,vertices=len(obj.data.vertices),triangles=len(obj.data.polygons),bounds_mm=lo+hi,source_mesh=obj.name))
result=dict(passed=all(c['passed'] for c in checks),check_count=len(checks),checks=checks,records=records,
    source_glb_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),read_only_source_export=True,
    physical_fit_qualified=False,scope='Native KiCad tessellation, unchanged canonical footprint frames, body envelopes and five corrected contact-mouth channels. No terminal or physical insertion qualification.')
OUTPUT.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['checks','records']},indent=2),flush=True)
assert result['passed'],[c for c in checks if not c['passed']]
