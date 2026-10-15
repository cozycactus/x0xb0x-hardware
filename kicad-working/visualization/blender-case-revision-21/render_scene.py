import bpy,sys,json,hashlib,time
from mathutils import Vector
from pathlib import Path
HERE=Path(__file__).resolve().parent;scene=bpy.context.scene
SOURCE=Path(bpy.data.filepath);source_sha=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
draft='--draft' in sys.argv
rear_only='--rear-only' in sys.argv
requested=next((arg.split('=',1)[1].split(',') for arg in sys.argv if arg.startswith('--views=')), ['assembled','rear','rear-openings-closeup'])
scene.render.resolution_percentage=50 if draft else 100
if hasattr(scene,'eevee') and hasattr(scene.eevee,'taa_render_samples'):scene.eevee.taa_render_samples=32 if draft else 96
hero=bpy.data.objects['Camera / assembled and exploded'];rear=bpy.data.objects['Camera / rear connections']
jobs=[('preview-assembled',1,hero)] if draft else [('assembled',1,hero),('rear',1,rear),('exploded',80,hero)]
if not draft and 'Camera / control side inspection' in bpy.data.objects:jobs.append(('control-side',120,bpy.data.objects['Camera / control side inspection']))
if not draft and 'Camera / wiring routing study' in bpy.data.objects:jobs.append(('wiring-study',160,bpy.data.objects['Camera / wiring routing study']))
if rear_only:requested=['rear']
if draft:requested=['preview-assembled']
if 'rear-openings-closeup' in requested:
 camera_data=bpy.data.cameras.new('TEMP / rear openings diagnostic')
 diagnostic=bpy.data.objects.new('TEMP / rear openings diagnostic',camera_data)
 scene.collection.objects.link(diagnostic)
 diagnostic.location=(0,.420,.040)
 target=Vector((0,.198,.024))
 diagnostic.rotation_euler=(target-diagnostic.location).to_track_quat('-Z','Y').to_euler()
 camera_data.type='ORTHO';camera_data.ortho_scale=.245;camera_data.clip_start=.001;camera_data.clip_end=2.
 jobs.append(('rear-openings-closeup',1,diagnostic))
if 'rear-midi-detail' in requested:
 camera_data=bpy.data.cameras.new('TEMP / rear MIDI legends diagnostic')
 diagnostic=bpy.data.objects.new('TEMP / rear MIDI legends diagnostic',camera_data)
 scene.collection.objects.link(diagnostic)
 diagnostic.location=(-.028448,.325,.032)
 target=Vector((-.028448,.1985,.026))
 diagnostic.rotation_euler=(target-diagnostic.location).to_track_quat('-Z','Y').to_euler()
 camera_data.type='ORTHO';camera_data.ortho_scale=.078;camera_data.clip_start=.001;camera_data.clip_end=2.
 jobs.append(('rear-midi-detail',1,diagnostic))
UNDERSIDE={'io-terminals-detail':('ioboard',)}
if any(v in requested for v in UNDERSIDE):
 # Revision 16: view the solder sides from below. Each camera clips just below the lowest geometry of the boards
 # it frames, so the animated case floor, feet and ground drop out, and one shadowless upward light is added
 # only in memory for these views; the saved scene is never written.
 audit=json.loads((HERE.parents[1]/'validation/models-review-17/native-terminal-audit.json').read_text())
 scene.frame_set(1);bpy.context.view_layer.update()
 def bounds(boards):
  roots={('IOBOARD/' if v['board']=='ioboard' else 'MAINBOARD/')+ref for refs in audit['models'].values() for ref,v in refs.items() if v['board'] in boards};pts=[]
  for inst in bpy.context.evaluated_depsgraph_get().object_instances:
   o=inst.object.original;top=o
   while top.parent and top.name not in roots:top=top.parent
   if top.name in roots and inst.object.type=='MESH':pts+=[inst.matrix_world@v.co for v in inst.object.data.vertices]
  return [min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]
 for label,boards in UNDERSIDE.items():
  if label not in requested:continue
  lo,hi=bounds(boards);centre=Vector(((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]-.25))
  camera_data=bpy.data.cameras.new('TEMP / '+label);diagnostic=bpy.data.objects.new('TEMP / '+label,camera_data)
  scene.collection.objects.link(diagnostic);diagnostic.location=centre
  diagnostic.rotation_euler=Vector((0,0,1)).to_track_quat('-Z','Y').to_euler()
  aspect=1800/(750 if label=='io-terminals-detail' else 1400)
  camera_data.type='ORTHO';camera_data.ortho_scale=1.12*max(hi[0]-lo[0],(hi[1]-lo[1])*aspect);camera_data.clip_start=.25-.0005;camera_data.clip_end=2.
  jobs.append((label,1,diagnostic))
 light_data=bpy.data.lights.new('TEMP / underside light','SUN');light_data.energy=4.;light_data.use_shadow=False;underside_light=bpy.data.objects.new('TEMP / underside light',light_data)
 underside_light.rotation_euler=Vector((.35,-.45,1)).to_track_quat('-Z','Y').to_euler()
jobs=[job for job in jobs if job[0]in requested]
# Bound timeline cameras otherwise override an explicitly selected rear camera
# when rendering evaluates the same frame again. These changes stay in memory.
for marker in scene.timeline_markers:marker.camera=None
records=json.loads((HERE/'render-records.json').read_text()) if(HERE/'render-records.json').exists()else []
for label,frame,camera in jobs:
 under=label in UNDERSIDE
 if any(v in requested for v in UNDERSIDE):
  (scene.collection.objects.link(underside_light) if under and underside_light.name not in scene.collection.objects else None)
  (scene.collection.objects.unlink(underside_light) if not under and underside_light.name in scene.collection.objects else None)
 scene.render.resolution_x=1600 if label=='rear-midi-detail'else 1800;scene.render.resolution_y=900 if label=='rear-midi-detail'else(750 if label in('rear-openings-closeup','io-terminals-detail')else 1400);scene.frame_set(frame);scene.camera=camera;output=HERE/(label+'.png');scene.render.filepath=str(output);start=time.time();bpy.ops.render.render(write_still=True)
 records=[r for r in records if r['view']!=label]
 records.append(dict(source_scene_sha256=source_sha,view=label,frame=frame,camera=camera.name,image=output.name,sha256=hashlib.sha256(output.read_bytes()).hexdigest(),seconds=time.time()-start,resolution_percentage=scene.render.resolution_percentage,image_size=[scene.render.resolution_x,scene.render.resolution_y]))
scene.frame_set(1);scene.camera=hero;scene.render.resolution_percentage=100
# Rendering is read-only with respect to the saved scene. Do not overwrite inspection files.
(HERE/('preview-render-record.json' if draft else 'render-records.json')).write_text(json.dumps(records,indent=2)+'\n');print(json.dumps(records,indent=2))

assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_sha, 'Rendering changed the saved scene'
(HERE/'verification/render-readonly-verification.json').write_text(json.dumps(dict(passed=True,stable_scene_sha256=source_sha,view_count=len(records),views=[r['view']for r in records],saved_scene_unchanged=True),indent=2)+'\n')
