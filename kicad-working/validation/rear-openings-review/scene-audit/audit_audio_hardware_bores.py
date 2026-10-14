"""Read-only dense rays through the nominal NYS216 bushing envelope.

The tests isolate the six exterior hardware illustrations so that the native
socket's expected bore wall does not appear as an erroneous hardware blocker.
"""
import bpy,json,hashlib,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent
source=Path(bpy.data.filepath);digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.context.scene.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
refs=['HEADPHONE0','MIXIN0','MIXOUT0'];native={};hardware={}
for inst in dg.object_instances:
 o=inst.object
 if o.type!='MESH' or o.hide_render:continue
 for ref in refs:
  if o.name=='IOBOARD/'+ref+'/mesh':native[ref]=inst.matrix_world.copy()
  if o.name in [ref+' / black ABS washer proxy',ref+' / black PA6 nut proxy']:
   me=o.to_mesh();tree=BVHTree.FromPolygons([v.co.copy()for v in me.vertices],[list(p.vertices)for p in me.polygons],all_triangles=False);o.to_mesh_clear()
   hardware[o.name]=(inst.matrix_world.copy(),tree)
checks=[]
for ref in refs:
 center=native[ref]@Vector((0,0,.008))
 samples=[('center',0.,0.)]
 for radial_fraction in [.25,.70,.999]:
  radius=(9.525/2)*radial_fraction
  for angle in range(0,360,11):
   a=math.radians(angle);samples.append((f'r{radial_fraction}-a{angle}',radius*math.cos(a)/1000,radius*math.sin(a)/1000))
 for suffix in ['black ABS washer proxy','black PA6 nut proxy']:
  name=ref+' / '+suffix;m,tree=hardware[name];inv=m.inverted();direction=(inv.to_3x3()@Vector((0,-1,0))).normalized();blocked=[]
  for label,dx,dz in samples:
   origin=inv@Vector((center.x+dx,.230,center.z+dz));hit,normal,index,dist=tree.ray_cast(origin,direction,.100)
   if hit is not None:blocked.append(dict(sample=label,hit_world_mm=[c*1000 for c in m@hit],face=index))
  checks.append(dict(object=name,passed=not blocked,ray_count=len(samples),native_axis_mm=[center.x*1000,center.z*1000],native_bushing_nominal_diameter_mm=9.525,max_sample_diameter_mm=9.525*.999,blocked_rays=blocked))
out=dict(source_scene=str(source),source_scene_sha256=digest,method='Frame1 evaluated collection-instance matrices, isolated per-hardware BVH rays; center plus three rings up to99.9percent of native9.525mm threadednose diameter.',passed=all(c['passed']for c in checks),hardware_count=len(checks),ray_count=sum(c['ray_count']for c in checks),checks=checks,source_bytes_unchanged=hashlib.sha256(source.read_bytes()).hexdigest()==digest,scope='Sampled geometric clearance around nominal body envelope; not a thread tolerance or assembly-fit certification.')
output=next((a.split('=',1)[1]for a in sys.argv if a.startswith('--audit-output=')),'audio-hardware-bore-audit.json')
(HERE/output).write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items()if k!='checks'},indent=2))
