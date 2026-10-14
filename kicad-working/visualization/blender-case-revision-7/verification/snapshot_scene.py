import bpy,json,hashlib,struct,sys
from pathlib import Path
H=Path(__file__).resolve().parent
scene=bpy.context.scene;scene.frame_set(1)
def ancestor(o):
 while o:
  if o.get('source_reference'):return o['source_board']+'/'+o['source_reference']
  o=o.parent
 return None
def geometry(o):
 d=hashlib.sha256()
 for v in o.data.vertices:d.update(struct.pack('<3f',*v.co))
 for p in o.data.polygons:d.update(struct.pack('<I',len(p.vertices)));d.update(struct.pack('<'+str(len(p.vertices))+'I',*p.vertices))
 return {'hash':d.hexdigest(),'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'matrix':[list(r) for r in o.matrix_world]}
refs={};other={};poses={}
for o in bpy.data.objects:
 ref=ancestor(o)
 if o.get('source_reference'):poses[o['source_board']+'/'+o['source_reference']]=[list(r) for r in o.matrix_world]
 if o.type=='MESH':
  data=geometry(o)
  if ref:refs.setdefault(ref,[]).append(data)
  else:other[o.name]=data
for xs in refs.values():xs.sort(key=lambda x:x['hash'])
label=sys.argv[sys.argv.index('--')+1]
p=H/(label+'-scene-snapshot.json');p.write_text(json.dumps({'references':refs,'reference_poses':poses,'other_meshes':other,'instance_poses':{n:[list(r) for r in bpy.data.objects[n].matrix_world] for n in ['Mainboard — B.Cu outward in assembled view','I/O board — rear mounting approximation']}},indent=2)+'\n');print('Snapshot',label,'refs',len(poses),'meshes',sum(len(x) for x in refs.values())+len(other))
