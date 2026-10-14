"""Independent GLB canonical bounds and source asset hash check; no mutations."""
from pathlib import Path
import json,struct,hashlib,math
import numpy as np
H=Path(__file__).resolve().parent;m=json.loads((H/'control-quality-manifest.json').read_text());C=np.array([[1.,0,0],[0,0,1],[0,-1,0]])
def mat(n):
 if'matrix'in n:return np.array(n['matrix']).reshape((4,4),order='F')
 x,y,z,w=n.get('rotation',[0,0,0,1]);R=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]);a=np.eye(4);a[:3,:3]=R@np.diag(n.get('scale',[1,1,1]));a[:3,3]=n.get('translation',[0,0,0]);return a
records=[]
for p in m['parts']:
 path=H/'native-probes'/(p['id']+'.glb');raw=path.read_bytes();off=12;chunks={}
 while off<len(raw):
  count,typ=struct.unpack_from('<II',raw,off);chunks[typ]=raw[off+8:off+8+count];off+=8+count
 j=json.loads(chunks[0x4e4f534a]);binary=chunks[0x004e4942];node=next(i for i,n in enumerate(j['nodes'])if n.get('name')=='Probe0');vertices=[]
 def accessor(i):
  a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];assert a['componentType']==5126 and a['type']=='VEC3';return np.ndarray((a['count'],3),dtype='<f4',buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',12),4))
 def walk(i,parent):
  n=j['nodes'][i];M=parent@mat(n)
  if'mesh'in n:
   for prim in j['meshes'][n['mesh']]['primitives']:
    v=accessor(prim['attributes']['POSITION']);vertices.append((v@M[:3,:3].T+M[:3,3])@C*1000)
  for c in n.get('children',[]):walk(c,M)
 for c in j['nodes'][node].get('children',[]):walk(c,np.eye(4))
 v=np.concatenate(vertices);bounds=np.r_[v.min(axis=0),v.max(axis=0)];cad=np.array(p['bounds_mm']);err=max(abs(bounds-cad));tip=abs(bounds[5]-7.3);same=hashlib.sha256(Path(p['step']).read_bytes()).hexdigest()==p['source_sha256'];records.append(dict(id=p['id'],source_step=p['step'],source_sha256=p['source_sha256'],source_hash_unchanged=same,exact_reimported_STEP_bounds_mm=p['bounds_mm'],native_GLB_canonical_bounds_mm=bounds.tolist(),maximum_bound_chord_error_mm=float(err),actuator_tip_error_mm=float(tip),native_root_model_scale=j['nodes'][node].get('scale',[1,1,1]),passed=bool(err<.001 and tip<.00001 and same),native_GLB_sha256=hashlib.sha256(raw).hexdigest(),canonical_vertices=len(v)))
report=dict(passed=all(r['passed']for r in records),scope='Independent raw-nativeGLB buffer inspection, component placement excluded. ExactCADbounds recorded from separateFreeCADreimport; sourcehashes verified unchanged.',records=records,limits=['Curve chord extrema may differ by less than0.001mm from exactBRep bounds.','Nominal/free-state terminalgeometry remains physically unfitted; no deformation simulation or drill/tolerance qualification.'])
(H/'native-probes/native-canonical-bounds-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
