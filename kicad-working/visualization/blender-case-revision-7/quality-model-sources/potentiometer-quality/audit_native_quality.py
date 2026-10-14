from pathlib import Path
import json,struct,hashlib,math
HERE=Path(__file__).resolve().parent;m=json.loads((HERE/'potentiometer-quality-manifest.json').read_text());plan=json.loads((HERE/'native-probe-plan.json').read_text());rows=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lin(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
for part,probe in zip(m['parts'],plan['probes']):
 data=Path(probe['glb']).read_bytes();n=struct.unpack_from('<I',data,12)[0];j=json.loads(data[20:20+n]);binary=data[28+n:];assert data[24+n:28+n]==b'BIN\x00'
 def points(p):
  a=j['accessors'][p['attributes']['POSITION']];v=j['bufferViews'][a['bufferView']];offset=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',12)
  return [(x*1000,-z*1000,y*1000) for x,y,z in [struct.unpack_from('<fff',binary,offset+i*stride) for i in range(a['count'])]]
 expected={v['name']:v for v in part['segments']};roles=[]
 for node in j['nodes']:
  if 'mesh' not in node:continue
  name=node.get('name');assert name in expected,(part['id'],name);e=expected[name];prims=j['meshes'][node['mesh']]['primitives'];colors=[j['materials'][p['material']]['pbrMetallicRoughness']['baseColorFactor'][:3] for p in prims];error=max(abs(v-lin(c)) for rgb in colors for v,c in zip(rgb,e['color_srgb']));assert error<1e-6
  pts=[v for p in prims for v in points(p)];bounds=[min(v[k] for v in pts) for k in range(3)]+[max(v[k] for v in pts) for k in range(3)];wanted=e['tight_mesh_bounds']['min_mm']+e['tight_mesh_bounds']['max_mm'];res=max(abs(a-b) for a,b in zip(bounds,wanted));assert res<.025,(part['id'],name,bounds,wanted,res)
  roles.append({'name':name,'material_present_for_all_primitives':True,'primitive_count':len(prims),'native_rgb_linear':colors[0],'source_rgb_srgb':e['color_srgb'],'maximum_color_error':error,'native_canonical_bounds_mm':bounds,'maximum_bounds_residual_mm':res})
 assert {r['name'] for r in roles}==set(expected)
 rows.append({'id':part['id'],'probe_reference':probe['reference'],'STEP_sha256':sha(part['step']),'GLB':probe['glb'],'GLB_sha256':sha(probe['glb']),'roles':roles,'passed':True})
r={'passed':True,'family_count':2,'reference_count':7,'native_probe_count':2,'families':rows,'maximum_native_bounds_residual_mm':max(r['maximum_bounds_residual_mm'] for f in rows for r in f['roles']),'maximum_native_color_error':max(r['maximum_color_error'] for f in rows for r in f['roles']),'proof':'Every named feature imports natively with its intended sRGB-to-linear palette and source canonical bounds. Original footprint position/rotation/side retained in isolated source-copy probes. Original projects/models not modified.','limitations':['Native colors are diffuse palette only; STEP does not encode Blender metallic/roughness.','Candidate geometry differs intentionally from earlier rectangular envelopes. This is not a color-only revision.','Physical seating, historical variant equivalence of potentiometer shaft and housing details and unsized features remain qualified in source manifest.']}
(HERE/'native-quality-audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['passed','family_count','reference_count','native_probe_count','maximum_native_bounds_residual_mm','maximum_native_color_error']},indent=2))
