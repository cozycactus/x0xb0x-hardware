import bpy,json,hashlib,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent
SOURCE=Path(bpy.data.filepath);before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
refs=['POWER0','HEADPHONE0','MIXIN0','MIXOUT0','CV0','GATE0','USB0','DIN1','DIN2','DIN3','DIN4']
spec={r:dict(z=8.,front=-8.5,radius=3.175,expected='open audio socket')for r in ['HEADPHONE0','MIXIN0','MIXOUT0']}
spec.update({r:dict(z=5.5,front=-3.,radius=1.8,expected='open 3.5mm socket')for r in ['CV0','GATE0']})
spec.update({r:dict(z=10.,front=0.,radius=7.1,expected='recessed five-contact DIN insert')for r in ['DIN1','DIN2','DIN3','DIN4']})
spec['POWER0']=dict(z=6.5,front=0.,radius=3.25,expected='open annulus around 2mm center pin')
spec['USB0']=dict(z=5.31,front=0.,radius=3.0,expected='open Type-B aperture around insulating tongue')
cache={};items=[];native={}
for inst in dg.object_instances:
 o=inst.object
 if o.type!='MESH' or o.hide_render:continue
 key=o.original.as_pointer()
 if key not in cache:
  me=o.to_mesh();cache[key]=BVHTree.FromPolygons([v.co.copy()for v in me.vertices],[list(p.vertices)for p in me.polygons],all_triangles=False);o.to_mesh_clear()
 pts=[inst.matrix_world@Vector(p)for p in o.bound_box];bb=[min(p[i]for p in pts)for i in range(3)]+[max(p[i]for p in pts)for i in range(3)]
 item=dict(name=o.name,matrix=inst.matrix_world.copy(),inverse=inst.matrix_world.inverted(),tree=cache[key],bounds=bb)
 items.append(item)
 for r in refs:
  if o.name=='IOBOARD/'+r+'/mesh':native[r]=item

def trace(x,z,omit_proxies=False,omit_hardware=False):
 origin=Vector((x,.230,z));direction=Vector((0,-1,0));out=[]
 for it in items:
  b=it['bounds']
  if not(b[0]-1e-8<=x<=b[3]+1e-8 and b[2]-1e-8<=z<=b[5]+1e-8 and b[4]>.165 and b[1]<.23):continue
  if omit_proxies and it['name'].endswith('/ jack recess proxy'):continue
  if omit_hardware and (it['name'].endswith('/ black PA6 nut proxy') or it['name'].endswith('/ black ABS washer proxy')):continue
  inv=it['inverse'];loc=inv@origin;direc=(inv.to_3x3()@direction).normalized()
  for _ in range(16):
   hit,normal,index,dist=it['tree'].ray_cast(loc,direc,.100)
   if hit is None:break
   world=it['matrix']@hit
   if world.y<.165:break
   out.append(dict(object=it['name'],world_mm=[round(c*1000,6)for c in world],face=index))
   loc=hit+direc*1e-7
 out.sort(key=lambda h:-h['world_mm'][1]);return out

report=dict(source_scene=str(SOURCE),source_scene_sha256=before,method='Frame1 evaluated depsgraph collection-instance matrices; per-instance BVH multi-hit rays from external +worldY toward -worldY. Center plus aperture samples; blind socket backs, DIN insert and USB tongue classified separately.',ports=[],source_bytes_unchanged=None)
for r in refs:
 sp=spec[r];it=native[r];m=it['matrix'];front=m@Vector((0,sp['front']/1000,sp['z']/1000));axis=(m.to_3x3()@Vector((0,-1 if r!='POWER0' else 1,0))).normalized()
 samples=[('center',0,0)]
 for angle in range(0,360,45):
  a=math.radians(angle);rad=sp['radius']*.65;samples.append(('aperture-'+str(angle),rad*math.cos(a),rad*math.sin(a)))
 if r.startswith('DIN'):
  for angle in [25,155,225,270,315]:
   a=math.radians(angle);samples.append(('contact-'+str(angle),-3.5*math.cos(a),3.5*math.sin(a)))
 row=dict(reference=r,expected=sp['expected'],native_front_axis_point_mm=[c*1000 for c in front],outward_axis=list(axis),rays=[])
 for label,dx,dz in samples:
  x,z=front.x+dx/1000,front.z+dz/1000
  hits=trace(x,z);without=trace(x,z,True);native_only=trace(x,z,True,True)
  row['rays'].append(dict(label=label,x_mm=x*1000,z_mm=z*1000,ordered_hits=hits,without_recess_proxies=without,without_recess_proxies_or_exterior_audio_hardware=native_only))
 row['erroneous_recess_proxies']=sorted(set(h['object']for ray in row['rays']for h in ray['ordered_hits']if h['object'].endswith('/ jack recess proxy')))
 row['exterior_audio_hardware_across_bore']=sorted(set(h['object']for ray in row['rays']for h in ray['ordered_hits']if h['object'].endswith(('/ black PA6 nut proxy','/ black ABS washer proxy'))))
 row['panel_or_case_before_native_front']=sorted(set(h['object']for ray in row['rays']for h in ray['ordered_hits']if (h['object'].startswith('Case /')or 'panel' in h['object'].lower())and h['world_mm'][1]>=front.y*1000-.001))
 row['diagnosis']='Erroneous separate solid recess disk closes mating aperture'if row['erroneous_recess_proxies']else'No separate cap found; intended cavity/contacts/insert remain'
 if row['exterior_audio_hardware_across_bore']:row['diagnosis']+='; exterior nut and washer illustrations also lack mating bores'
 first=row['rays'][0]['without_recess_proxies_or_exterior_audio_hardware']
 row['native_center_first_hit_depth_mm_ignoring_erroneous_presentation_blockers']=front.y*1000-first[0]['world_mm'][1] if first else None
 row['mating_axis_faces_outward']=axis.y>.99999
 row['sampled_panel_or_case_obstruction']=bool(row['panel_or_case_before_native_front'])
 row['ray_count']=len(row['rays'])
 report['ports'].append(row)
report['source_bytes_unchanged']=hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
report['summary']=dict(port_count=len(report['ports']),ray_count=sum(p['ray_count']for p in report['ports']),erroneous_recess_disks=len(set(n for p in report['ports']for n in p['erroneous_recess_proxies'])),solid_audio_hardware_pieces=len(set(n for p in report['ports']for n in p['exterior_audio_hardware_across_bore'])),case_panel_blockers_detected=sum(p['sampled_panel_or_case_obstruction']for p in report['ports']),scope='Sampled visual mating apertures in assembled scene; not toleranced installed fit or plug compatibility.')
output=next((a.split('=',1)[1]for a in sys.argv if a.startswith('--audit-output=')),'rear-ray-audit.json')
(HERE/output).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(source_bytes_unchanged=report['source_bytes_unchanged'],ports=[dict(reference=p['reference'],front=p['native_front_axis_point_mm'],proxies=p['erroneous_recess_proxies'],panel=p['panel_or_case_before_native_front'],center=p['rays'][0]['ordered_hits'][:6],center_no_proxy=p['rays'][0]['without_recess_proxies'][:3])for p in report['ports']]),indent=2))
