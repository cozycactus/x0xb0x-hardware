"""Verify current frozen STEP geometry/palette survives native KiCad export."""
from pathlib import Path
import hashlib,json,struct
H=Path(__file__).resolve().parent
manifest_path=H/'rear-connector-quality-corrected-manifest.json'
if not manifest_path.exists():manifest_path=H/'rear-connector-quality-manifest.json'
m=json.loads(manifest_path.read_text())
plan=json.loads((H/'native-probe-plan.json').read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
lin=lambda v:v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
checks=[];families=[]
def check(name,passed,**evidence):
    checks.append(dict(name=name,passed=bool(passed),**evidence));assert passed,(name,evidence)
def bb(points):
    return [min(p[k]for p in points)for k in range(3)]+[max(p[k]for p in points)for k in range(3)]
for part,probe in zip(m['parts'],plan['probes']):
    check(part['id']+':frozen-input',sha(part['step'])==part['source_sha256'])
    data=Path(probe['glb']).read_bytes();n=struct.unpack_from('<I',data,12)[0]
    j=json.loads(data[20:20+n]);binary=data[28+n:]
    check(part['id']+':binary-GLB',data[:4]==b'glTF'and data[24+n:28+n]==b'BIN\0')
    points_by_color={};maxcolor=0
    for mesh in j['meshes']:
        for p in mesh['primitives']:
            a=j['accessors'][p['attributes']['POSITION']]
            v=j['bufferViews'][a['bufferView']]
            off=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',12)
            pts=[struct.unpack_from('<fff',binary,off+i*stride)for i in range(a['count'])]
            pts=[(x*1000,-z*1000,y*1000)for x,y,z in pts]
            rgb=j['materials'][p['material']]['pbrMetallicRoughness']['baseColorFactor'][:3]
            wanted=min((f['color_rgb']for f in part['features']),key=lambda c:sum(abs(v-lin(c))for v,c in zip(rgb,c)))
            error=max(abs(v-lin(c))for v,c in zip(rgb,wanted));maxcolor=max(error,maxcolor)
            check(part['id']+':face-palette',error<1e-6,maximum_error=error)
            points_by_color.setdefault(tuple(wanted),[]).extend(pts)
    check(part['id']+':all-color-roles',set(points_by_color)=={tuple(f['color_rgb'])for f in part['features']})
    roles=[]
    for rgb,pts in points_by_color.items():
        expected_features=[f for f in part['features']if tuple(f['color_rgb'])==rgb]
        boxes=[f['exact_bounds_mm']for f in expected_features]
        wanted=[min(b[i]for b in boxes)for i in range(3)]+[max(b[i]for b in boxes)for i in range(3,6)]
        actual=bb(pts);error=max(abs(a-b)for a,b in zip(actual,wanted))
        check(part['id']+':role-bounds',error<.025,color_srgb=rgb,native_mm=actual,expected_mm=wanted,error_mm=error)
        roles.append(dict(color_srgb=rgb,feature_names=[f['name']for f in expected_features],native_bounds_mm=actual,maximum_residual_mm=error))
    whole=bb([p for pts in points_by_color.values()for p in pts])
    check(part['id']+':whole-bounds',max(abs(a-b)for a,b in zip(whole,part['exact_bounds_mm']))<.025)
    check(part['id']+':nothing-below-seat',whole[2]>=-1e-6)
    families.append(dict(id=part['id'],reference=probe['reference'],STEP_sha256=part['source_sha256'],GLB_sha256=sha(probe['glb']),native_canonical_bounds_mm=whole,color_roles=roles,maximum_color_error=maxcolor,passed=True))
r=dict(passed=True,checks_count=len(checks),checks=checks,families=families,
       maximum_bounds_residual_mm=max(r['maximum_residual_mm']for f in families for r in f['color_roles']),
       source_probe_plan='native-probe-plan.json',
       proof='Frozen colored STEP imports through native KiCad10 GLB with every color role and full canonical bounds. Actual source footprint placement/rotation retained in immutable isolated probes. No project/scene writes.',
       limitations=['Native surface tessellation is a visual export, not a physical fit test.','Below-seat terminals intentionally absent; no board-hole seating inference.','Contact stock and minor molding details remain explicitly unsized illustrations.'])
(H/'native-quality-audit.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:r[k]for k in ['passed','checks_count','maximum_bounds_residual_mm']},indent=2))
