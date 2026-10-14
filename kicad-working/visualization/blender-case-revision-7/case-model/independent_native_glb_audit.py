#!/usr/bin/env python3
"""Read-only native GLB preservation and newly assigned footprint-pose audit.

Reads original GLB buffers directly, without Blender importing/resaving geometry.
The report distinguishes native graphical transforms from physical terminal fit.
"""
from pathlib import Path
import argparse,collections,hashlib,json,math,struct,subprocess,sys,tempfile
import numpy as np
HERE=Path(__file__).resolve().parent
WORK=HERE.parents[2]
BASE=WORK.parent
sys.path.insert(0,str(BASE/'kicad-import/validation'))
from resolve_native_footprint_fields import parse,prop

C=np.array([[1.,0,0],[0,0,1],[0,-1,0]]) # CAD/Blender Z-up -> glTF Y-up
TYPES={5120:np.int8,5121:np.uint8,5122:np.int16,5123:np.uint16,5125:np.uint32,5126:np.float32}
SIZES={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stable(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def quat(q):
 x,y,z,w=q
 return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                  [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                  [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def matrix(n):
 if 'matrix' in n:return np.array(n['matrix'],float).reshape((4,4),order='F')
 m=np.eye(4);m[:3,:3]=quat(n.get('rotation',[0,0,0,1]))@np.diag(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0]);return m
class GLB:
 def __init__(self,p,refs):
  self.path=Path(p);raw=self.path.read_bytes();assert raw[:4]==b'glTF' and struct.unpack_from('<I',raw,4)[0]==2
  offset=12;chunks={}
  while offset<len(raw):
   n,t=struct.unpack_from('<II',raw,offset);chunks[t]=raw[offset+8:offset+8+n];offset+=8+n
  self.j=json.loads(chunks[0x4e4f534a]);self.binary=chunks[0x004e4942]
  self.refs={n['name']:i for i,n in enumerate(self.j['nodes']) if n.get('name') in refs}
  assert len(self.refs)==sum(n.get('name') in refs for n in self.j['nodes']), 'Duplicate reference nodes'
  self.ah={};self.mh={};self.ch={}
 def array(self,i):
  a=self.j['accessors'][i];v=self.j['bufferViews'][a['bufferView']];dt=np.dtype(TYPES[a['componentType']]).newbyteorder('<');n=SIZES[a['type']];stride=v.get('byteStride',dt.itemsize*n)
  return np.ndarray((a['count'],n),dtype=dt,buffer=self.binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(stride,dt.itemsize))
 def accessor_hash(self,i):
  if i not in self.ah:
   a=self.j['accessors'][i];h=hashlib.sha256(stable({k:a[k] for k in ('componentType','count','type')}));h.update(self.array(i).tobytes());self.ah[i]=h.hexdigest()
  return self.ah[i]
 def mesh_hash(self,i,colors=False):
  cache=self.ch if colors else self.mh
  if i not in cache:
   prim=[]
   for p in self.j['meshes'][i]['primitives']:
    q={'mode':p.get('mode',4),'attributes':{k:self.accessor_hash(a) for k,a in sorted(p['attributes'].items())},'indices':self.accessor_hash(p['indices']) if 'indices'in p else None}
    if colors:q['material']={k:v for k,v in self.j.get('materials',[])[p['material']].items() if k!='name'} if 'material'in p else None
    prim.append(q)
   cache[i]=hashlib.sha256(stable(prim)).hexdigest()
  return cache[i]
 def fingerprint(self,i,colors=False):
  n=self.j['nodes'][i]
  return {'matrix':matrix(n).round(14).tolist(),'mesh':self.mesh_hash(n['mesh'],colors) if 'mesh'in n else None,'children':[self.fingerprint(c,colors) for c in n.get('children',[])]}
 def vertices(self,i,acc=None):
  n=self.j['nodes'][i];w=(np.eye(4) if acc is None else acc)@matrix(n);out=[]
  if 'mesh'in n:
   for p in self.j['meshes'][n['mesh']]['primitives']:
    v=self.array(p['attributes']['POSITION']);out.append(v@w[:3,:3].T+w[:3,3])
  for c in n.get('children',[]):out.extend(self.vertices(c,w))
  return out
 def noncomponent_meshes(self):
  excluded=set()
  def mark(i):
   excluded.add(i)
   for c in self.j['nodes'][i].get('children',[]):mark(c)
  for i in self.refs.values():mark(i)
  return collections.Counter(self.mesh_hash(n['mesh']) for i,n in enumerate(self.j['nodes']) if i not in excluded and 'mesh'in n)
 def totals(self):
  mesh_ids=[n['mesh'] for n in self.j['nodes'] if 'mesh'in n];verts=tri=0
  for i in mesh_ids:
   for p in self.j['meshes'][i]['primitives']:
    verts+=self.j['accessors'][p['attributes']['POSITION']]['count']
    if p.get('mode',4)==4:tri+=(self.j['accessors'][p['indices']]['count']//3 if 'indices'in p else self.j['accessors'][p['attributes']['POSITION']]['count']//3)
  return dict(component_references=len(self.refs),mesh_nodes=len(mesh_ids),primitive_vertices=verts,triangles=tri)
def fpdata(board):
 root=parse(board.read_text());out={}
 for fp in root.children('footprint'):
  ref=prop(fp,'Reference').value;at=[float(x.value) for x in fp.first('at').items[1:]];at=at+[0.]*(3-len(at));layer=fp.first('layer').items[1].value
  ms=[]
  for m in fp.children('model'):
   vals=lambda key:[float(x.value) for x in m.first(key).first('xyz').items[1:]]
   ms.append(dict(path=m.items[1].value,offset=vals('offset'),rotation=vals('rotate'),scale=vals('scale')))
  out[ref]=dict(at=at,layer=layer,models=ms)
 return out

a=argparse.ArgumentParser();a.add_argument('--skip-step-bounds',action='store_true');args=a.parse_args()
planpath=WORK/'validation/models-review-6/combined-model-plan.json';plan=json.loads(planpath.read_text());newmap={(r['board'],ref):r for r in plan['new_assignments'] for ref in r['references']}
checks=[];records=[];assets={};newrecords=[]
def check(name,ok,**details):checks.append(dict(check=name,passed=bool(ok),**details))
for b,expected_old,expected_new in [('mainboard',362,409),('ioboard',63,82)]:
 board=WORK/b/(b+'.kicad_pcb');fps=fpdata(board);old=GLB(WORK/'visualization/blender-case-revision-2/board-meshes'/(b+'.glb'),fps);new=GLB(WORK/'visualization/blender-case-revision-3/board-meshes'/(b+'.glb'),fps)
 check(b+' previous reference count',len(old.refs)==expected_old,actual=len(old.refs));check(b+' current reference count',len(new.refs)==expected_new,actual=len(new.refs));check(b+' old reference set retained',old.refs.keys()<=new.refs.keys())
 added=new.refs.keys()-old.refs.keys();planned={ref for (bb,ref)in newmap if bb==b};check(b+' exactly planned new references',added==planned,actual=sorted(added),planned=sorted(planned))
 unchanged=[];materialsame=[]
 for ref in sorted(old.refs):
  same=old.fingerprint(old.refs[ref])==new.fingerprint(new.refs[ref]);unchanged.append(ref if same else None)
  check(b+'/'+ref+' original geometry topology and transforms byte-equivalent',same)
  samecolor=old.fingerprint(old.refs[ref],True)==new.fingerprint(new.refs[ref],True);materialsame.append(ref if samecolor else None);check(b+'/'+ref+' original material definitions equivalent',samecolor)
 check(b+' all noncomponent board mesh geometry/topology preserved',old.noncomponent_meshes()==new.noncomponent_meshes(),old_mesh_count=sum(old.noncomponent_meshes().values()),new_mesh_count=sum(new.noncomponent_meshes().values()))
 for ref in sorted(added):
  f=fps[ref];r=newmap[(b,ref)];ms=f['models'];check(b+'/'+ref+' exactly one native model',len(ms)==1)
  if len(ms)!=1:continue
  m=ms[0];check(b+'/'+ref+' source canonical unity model transform',m['offset']==[0,0,0] and m['rotation']==[0,0,0] and m['scale']==[1,1,1],actual=m)
  x,y,angle=f['at'];rad=math.radians(angle);rot=np.array([[math.cos(rad),-math.sin(rad),0],[math.sin(rad),math.cos(rad),0],[0,0,1.]])
  if f['layer']=='B.Cu':rot=rot@np.diag([1.,-1.,-1.])
  expected=np.eye(4);expected[:3,:3]=C@rot@C.T;expected[:3,3]=C@np.array([x,-y,1.595 if f['layer']=='F.Cu' else -.085])/1000
  actual=matrix(new.j['nodes'][new.refs[ref]]);err=float(np.max(abs(actual-expected)));check(b+'/'+ref+' native footprint pose and side flip',err<1e-11,max_matrix_error=err,side=f['layer'])
  # Exclude the component placement node to measure the unplaced source model.
  vertices=[]
  for i in new.j['nodes'][new.refs[ref]].get('children',[]):vertices.extend(new.vertices(i))
  v=np.concatenate(vertices)@C*1000;bounds=np.stack([v.min(axis=0),v.max(axis=0)]).tolist();source=Path(r['source_model']);resolved=Path(m['path'].replace('${KIPRJMOD}',str(board.parent)))
  check(b+'/'+ref+' assigned STEP asset matches manifest',sha(resolved)==r['source_sha256']==sha(source))
  assets[str(source)]=r['source_sha256']
  newrecords.append(dict(board=b,reference=ref,footprint_at=f['at'],side=f['layer'],actual_gltf_matrix=actual.tolist(),expected_gltf_matrix=expected.tolist(),canonical_mesh_bounds_mm=bounds,source_model=str(source),classification=r['classification'],limitations=r.get('limitations',[])))
 records.append(dict(board=b,source_pcb_sha256=sha(board),previous_glb_sha256=sha(old.path),current_glb_sha256=sha(new.path),previous=old.totals(),current=new.totals(),old_geometry_preserved=sum(x is not None for x in unchanged),old_material_preserved=sum(x is not None for x in materialsame)))
if not args.skip_step_bounds:
 helper=HERE/'read_source_step_bounds.py';payload=HERE/'source-step-audit-input.json';output=HERE/'source-step-bounds.json';payload.write_text(json.dumps(assets,indent=2)+'\n')
 helper.write_text('from pathlib import Path\nimport json,FreeCAD,Part\np=Path(__file__).resolve().parent\nrows={}\nfor name,h in json.loads((p/"source-step-audit-input.json").read_text()).items():\n s=Part.Shape();s.read(name);b=s.BoundBox\n rows[name]={"sha256":h,"valid":s.isValid(),"solid_count":len(s.Solids),"bounds_mm":[[b.XMin,b.YMin,b.ZMin],[b.XMax,b.YMax,b.ZMax]]}\n(p/"source-step-bounds.json").write_text(json.dumps(rows,indent=2)+"\\n")\n')
 import os
 env=dict(os.environ,PYTHONPATH='/Applications/FreeCAD.app/Contents/Resources/lib')
 p=subprocess.run(['/Applications/FreeCAD.app/Contents/Resources/bin/python',str(helper)],env=env,capture_output=True,text=True)
 check('Independent source STEP re-import completed',p.returncode==0,stderr=p.stderr[-2000:],returncode=p.returncode)
 if p.returncode==0:
  dims=json.loads(output.read_text())
  for r in newrecords:
   s=dims[r['source_model']];err=float(np.max(abs(np.array(r['canonical_mesh_bounds_mm'])-np.array(s['bounds_mm']))));check(r['board']+'/'+r['reference']+' source nominal CAD bounds retained',s['valid'] and err<.025,max_bound_error_mm=err,step_bounds_mm=s['bounds_mm']);r['source_STEP_bounds']=s
report=dict(passed=all(c['passed'] for c in checks),check_count=len(checks),failure_count=sum(not c['passed'] for c in checks),failures=[c for c in checks if not c['passed']],read_only_inputs=True,boards=records,new_instance_count=len(newrecords),new_instances=newrecords,checks=checks,limits=['Native graphical geometry, topology, model source hashes and transforms checked. No PCB/source asset or Blender scene was modified.','GLB graphical planes at F.Cu +1.595 mm and B.Cu -0.085 mm are KiCad export datums used for graphical placement, not independently measured physical seating heights.','New model body outlines include sourced dimensions and documented source-outline approximations. Terminals/locators omitted where unconfirmed; no terminal-to-drill or complete enclosure fit is certified.','Triangulated bounds may differ by less than 0.025 mm from exact CAD bounds due to tessellation.'])
(HERE/'revision-3-independent-native-glb-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('checks','new_instances','failures')},indent=2));sys.exit(0 if report['passed'] else 1)
