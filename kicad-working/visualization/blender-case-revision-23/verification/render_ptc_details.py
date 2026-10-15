"""Read-only same-scale before/after PTC and installed detail renders."""
import bpy,hashlib,json,sys,math
from mathutils.bvhtree import BVHTree
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent;R=H.parent;baseline=R.parent/'blender-case-revision-22/x0xb0x-populated-with-case.blend';current=R/'x0xb0x-populated-with-case.blend'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();guards={str(p):sha(p) for p in [baseline,current]};records=[]
for path,label in [(baseline,'ptc-before'),(current,'ptc-after')]:
 bpy.ops.wm.open_mainfile(filepath=str(path));original=bpy.context.scene;original.frame_set(1);bpy.context.view_layer.update();root=bpy.data.objects['MAINBOARD/R100A0'];parts=[o for o in root.children_recursive if o.type=='MESH'];assert len(parts)==7
 sc=bpy.data.scenes.new('TEMP PTC '+label);sc.render.engine='CYCLES';sc.cycles.samples=64;sc.render.resolution_x=1500;sc.render.resolution_y=1000;sc.render.resolution_percentage=100;sc.world=bpy.data.worlds.new('TEMP neutral world');sc.world.color=(.25,.25,.25)
 for p in parts:
  o=bpy.data.objects.new('TEMP '+p.name,p.data);sc.collection.objects.link(o);o.matrix_world=root.matrix_world.inverted()@p.matrix_world
 for pos,energy,size in [((-.015,-.018,.030),.04,.02),((.02,.01,.02),.03,.015),((0,.02,.01),.02,.015)]:
  d=bpy.data.lights.new('TEMP studio light','AREA');d.energy=energy;d.shape='DISK';d.size=size;o=bpy.data.objects.new(d.name,d);sc.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
 d=bpy.data.cameras.new('TEMP PTC camera');d.type='ORTHO';d.ortho_scale=.016;d.clip_start=.0001;d.clip_end=1;c=bpy.data.objects.new(d.name,d);sc.collection.objects.link(c);c.location=(.008,-.023,.012);c.rotation_euler=(-c.location).to_track_quat('-Z','Y').to_euler();sc.camera=c
 out=R/(label+'.png');sc.render.filepath=str(out)
 if '--installed-only' not in sys.argv:bpy.ops.render.render(write_still=True,scene=sc.name)
 records.append(dict(image=out.name,sha256=sha(out),source_scene_sha256=sha(path)))
# Current scene, actual displayed reference pose in exploded view.
original.frame_set(80);bpy.context.view_layer.update();target_object=bpy.data.objects['MAINBOARD/R100A0/mesh.005'];matrices=[i.matrix_world.copy() for i in bpy.context.evaluated_depsgraph_get().object_instances if i.object.original==target_object];assert len(matrices)==1;m=matrices[0]
d=bpy.data.cameras.new('TEMP installed PTC camera');d.type='ORTHO';d.ortho_scale=.023;d.clip_start=.0001;d.clip_end=1;c=bpy.data.objects.new(d.name,d);original.collection.objects.link(c);pts=[m@v.co for v in target_object.data.vertices];target=Vector([(min(p[i] for p in pts)+max(p[i] for p in pts))/2 for i in range(3)]);trees=[]
for inst in bpy.context.evaluated_depsgraph_get().object_instances:
 obj=inst.object
 if obj.type!='MESH' or obj.original.hide_render or (inst.parent and inst.parent.original.hide_render):continue
 if not obj.data.polygons:continue
 points=[inst.matrix_world@v.co for v in obj.data.vertices]
 trees.append((obj.original.name,BVHTree.FromPolygons(points,[tuple(p.vertices) for p in obj.data.polygons])))
selected=None;screen=[]
for elevation in [75,60,45,30,15]:
 for azimuth in range(0,360,30):
  e,a=math.radians(elevation),math.radians(azimuth)
  direction=(m.to_quaternion()@Vector((math.cos(e)*math.cos(a),math.cos(e)*math.sin(a),math.sin(e)))).normalized()
  origin=target+direction*.030;hits=[]
  for name,tree in trees:
   point,normal,index,distance=tree.ray_cast(origin,-direction,.035)
   if point is not None:hits.append((distance,name))
  first=min(hits) if hits else None
  screen.append(dict(elevation=elevation,azimuth=azimuth,first=first))
  if first and first[1].startswith('MAINBOARD/R100A0/'):
   selected=origin;break
 if selected is not None:break
print('PTC CAMERA SCREEN',json.dumps(screen),flush=True)
assert selected is not None,'PTC is occluded from all screened inspection directions'
c.location=selected;c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler()
light=bpy.data.lights.new('TEMP installed light','AREA');light.energy=.06;light.shape='DISK';light.size=.025;l=bpy.data.objects.new(light.name,light);original.collection.objects.link(l);l.location=c.location;l.rotation_euler=c.rotation_euler
for marker in original.timeline_markers:marker.camera=None
original.camera=c;original.render.resolution_x=1500;original.render.resolution_y=1000;original.render.resolution_percentage=100;out=R/'ptc-installed.png';original.render.filepath=str(out);bpy.ops.render.render(write_still=True,scene=original.name);records.append(dict(image=out.name,sha256=sha(out),source_scene_sha256=sha(current)))
assert guards=={str(p):sha(p) for p in [baseline,current]}
(H/'ptc-detail-render.json').write_text(json.dumps(dict(passed=True,images=records,same_scale_before_after=True,read_only=True,saved_scenes_unchanged=True),indent=2)+'\n')
