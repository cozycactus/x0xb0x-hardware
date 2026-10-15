"""Render saved LED/spacer geometry read-only, isolated and in the assembly."""
import bpy,hashlib,json,sys
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent;R=H.parent;source=Path(bpy.data.filepath);digest=hashlib.sha256(source.read_bytes()).hexdigest();original=bpy.context.scene
root=bpy.data.objects['MAINBOARD/LED1'];parts=[o for o in root.children_recursive if o.type=='MESH'];assert len(parts)==4
sc=bpy.data.scenes.new('TEMP LED spacer inspection');sc.render.engine='CYCLES';sc.cycles.samples=64;sc.render.resolution_x=1400;sc.render.resolution_y=1200;sc.render.resolution_percentage=100
sc.world=bpy.data.worlds.new('TEMP neutral world');sc.world.color=(.25,.25,.25)
for p in parts:
 o=bpy.data.objects.new('TEMP '+p.name,p.data);sc.collection.objects.link(o);o.matrix_world=root.matrix_world.inverted()@p.matrix_world
for pos,energy,size in [((-.02,-.02,.04),.07,.025),((.02,.01,.03),.04,.02),((0,.03,.01),.03,.02)]:
 d=bpy.data.lights.new('TEMP studio light','AREA');d.energy=energy;d.shape='DISK';d.size=size;o=bpy.data.objects.new(d.name,d);sc.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((.00127,0,.007))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('TEMP LED camera');d.type='ORTHO';d.ortho_scale=.023;d.clip_start=.0001;d.clip_end=1
c=bpy.data.objects.new('TEMP LED camera',d);sc.collection.objects.link(c);target=Vector((.00127,0,.006));c.location=(.018,-.03,.017);c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler();sc.camera=c
records=[];out=R/'led-spacer-detail.png';sc.render.filepath=str(out)
if '--installed-only' not in sys.argv:bpy.ops.render.render(write_still=True,scene=sc.name)
records.append(dict(image=out.name,sha256=hashlib.sha256(out.read_bytes()).hexdigest()))
original.frame_set(80);bpy.context.view_layer.update();spacer=bpy.data.objects['MAINBOARD/LED1/STD240B spacer']
matrices=[i.matrix_world.copy() for i in bpy.context.evaluated_depsgraph_get().object_instances if i.object.original==spacer];assert len(matrices)==1;m=matrices[0]
d=bpy.data.cameras.new('TEMP installed LED camera');d.type='ORTHO';d.ortho_scale=.027;d.clip_start=.0001;d.clip_end=1
c=bpy.data.objects.new(d.name,d);original.collection.objects.link(c);target=m@Vector((.00127,0,.007));c.location=m@Vector((.018,-.03,.018));c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler()
for marker in original.timeline_markers:marker.camera=None
light=bpy.data.lights.new('TEMP installed inspection light','AREA');light.energy=.06;light.shape='DISK';light.size=.025
l=bpy.data.objects.new(light.name,light);original.collection.objects.link(l);l.location=c.location;l.rotation_euler=c.rotation_euler
original.camera=c;original.render.resolution_x=1400;original.render.resolution_y=1200;original.render.resolution_percentage=100
out=R/'led-spacer-installed.png';original.render.filepath=str(out);bpy.ops.render.render(write_still=True,scene=original.name);records.append(dict(image=out.name,sha256=hashlib.sha256(out.read_bytes()).hexdigest()))
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(H/'led-detail-render.json').write_text(json.dumps(dict(passed=True,source_scene_sha256=digest,images=records,saved_scene_unchanged=True,read_only=True),indent=2)+'\n')
