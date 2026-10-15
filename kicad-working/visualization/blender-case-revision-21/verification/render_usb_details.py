"""Render the saved USB mesh from two model views and in the actual enclosure."""
import hashlib,json,sys
from pathlib import Path
import bpy
from mathutils import Vector
HERE=Path(__file__).resolve().parent;REV=HERE.parent
SOURCE=Path(bpy.data.filepath);frozen=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
original=bpy.context.scene;original.frame_set(1);bpy.context.view_layer.update()
root=bpy.data.objects['IOBOARD/USB0'];native=bpy.data.objects['IOBOARD/USB0/mesh']
sc=bpy.data.scenes.new('TEMP USB source inspection');sc.render.engine=original.render.engine
sc.render.resolution_x=1400;sc.render.resolution_y=1000
sc.world=bpy.data.worlds.new('TEMP USB world');sc.world.use_nodes=True
sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.82,.84,.87,1)
sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.8
obj=bpy.data.objects.new('TEMP USB native aggregate',native.data);sc.collection.objects.link(obj)
obj.matrix_world=root.matrix_world.inverted()@native.matrix_world
for energy,direction in [(2.3,(.3,.8,-1)),(1.0,(-.5,-.2,.6))]:
    light=bpy.data.lights.new('TEMP USB light','SUN');light.energy=energy
    light.angle=.15;o=bpy.data.objects.new('TEMP USB light',light);sc.collection.objects.link(o)
    o.rotation_euler=Vector(direction).to_track_quat('-Z','Y').to_euler()
points=[obj.matrix_world@v.co for v in obj.data.vertices]
centre=Vector([(min(p[i] for p in points)+max(p[i] for p in points))/2 for i in range(3)])
records=[]
for label,offset in [('usb-front',Vector((.023,-.060,.018))),('usb-underside',Vector((.028,.040,-.036)))]:
    if '--case-only' in sys.argv:
        output=REV/(label+'.png');assert output.is_file()
        records.append(dict(view=label,image=output.name,sha256=hashlib.sha256(output.read_bytes()).hexdigest()))
        continue
    data=bpy.data.cameras.new('TEMP '+label);data.type='ORTHO';data.ortho_scale=.030;data.clip_start=.0001;data.clip_end=1
    cam=bpy.data.objects.new('TEMP '+label,data);sc.collection.objects.link(cam);cam.location=centre+offset
    cam.rotation_euler=(centre-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam
    output=REV/(label+'.png');sc.render.filepath=str(output)
    bpy.ops.render.render(write_still=True,scene=sc.name)
    records.append(dict(view=label,image=output.name,sha256=hashlib.sha256(output.read_bytes()).hexdigest()))
# The in-case camera uses the evaluated USB instance, including board placement.
instances=[i.matrix_world.copy() for i in bpy.context.evaluated_depsgraph_get().object_instances if i.object.original==native]
assert len(instances)==1
m=instances[0];face=m@Vector((0,0,.00569));out=(m.to_3x3()@Vector((0,-1,0))).normalized()
data=bpy.data.cameras.new('TEMP USB case');data.type='ORTHO';data.ortho_scale=.024;data.clip_start=.0001;data.clip_end=1
cam=bpy.data.objects.new('TEMP USB case',data);original.collection.objects.link(cam)
cam.location=face+out*.080+Vector((.006,0,.004));cam.rotation_euler=(face-out*.003-cam.location).to_track_quat('-Z','Y').to_euler()
for marker in original.timeline_markers:marker.camera=None
original.camera=cam;original.render.resolution_x=1400;original.render.resolution_y=1000;original.render.resolution_percentage=100
output=REV/'usb-in-case.png';original.render.filepath=str(output);bpy.ops.render.render(write_still=True,scene=original.name)
records.append(dict(view='usb-in-case',image=output.name,sha256=hashlib.sha256(output.read_bytes()).hexdigest()))
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==frozen
(HERE/'usb-detail-render.json').write_text(json.dumps(dict(passed=True,source_scene_sha256=frozen,views=records,saved_scene_unchanged=True,read_only=True),indent=2)+'\n')
print(json.dumps(dict(passed=True,view_count=len(records),read_only=True),indent=2),flush=True)
