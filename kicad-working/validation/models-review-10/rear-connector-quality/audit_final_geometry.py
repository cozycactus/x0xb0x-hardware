"""Fresh saved-file geometry checks for the corrected active connector pair."""
from pathlib import Path
import json,hashlib,sys
sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part,Mesh
H=Path(__file__).resolve().parent
m=json.loads((H/'rear-connector-quality-corrected-manifest.json').read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[]
def check(name,passed,**evidence):
    checks.append(dict(name=name,passed=bool(passed),**evidence));assert passed,(name,evidence)
def bb(s):
    b=s.optimalBoundingBox(False,False)
    return [b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]
def inside(s,xyz):
    return any(t.isInside(App.Vector(*xyz),1e-7,True)for t in s.Solids)
rows=[]
for p in m['parts']:
    s=Part.Shape();s.read(p['step'])
    check(p['id']+':frozen-STEP-hash',sha(p['step'])==p['source_sha256'])
    check(p['id']+':STEP-valid',s.isValid())
    check(p['id']+':positive-solids',all(t.isValid()and t.Volume>0 for t in s.Solids))
    check(p['id']+':five-material-solids',len(s.Solids)==5)
    bounds=bb(s)
    check(p['id']+':saved-nominal-bounds',max(abs(a-b)for a,b in zip(bounds,p['exact_bounds_mm']))<1e-6,actual_mm=bounds,expected_mm=p['exact_bounds_mm'])
    check(p['id']+':zero-pose-unity',p['offset_mm']==[0,0,0]and p['rotation_deg']==[0,0,0]and p['scale']==[1,1,1])
    check(p['id']+':no-belowseat-body',bounds[2]>=-1e-7)
    check(p['id']+':union-STL-hash',sha(p['stl'])==p['stl_sha256'])
    mesh=Mesh.Mesh(p['stl'])
    check(p['id']+':union-STL-closed',mesh.isSolid(),facets=mesh.CountFacets)
    for f in p['features']:
        check(p['id']+':'+f['name']+':feature-STL-hash',sha(f['stl'])==f['sha256'])
        check(p['id']+':'+f['name']+':feature-STL-closed',Mesh.Mesh(f['stl']).isSolid())
    if p['id'].startswith('MJ'):
        check('MJ:full-aperture-clear',not inside(s,(0,-1.5,5.5)))
        check('MJ:full-bushing-annulus-present',inside(s,(2.65,-1.5,5.5)))
    else:
        check('PJ:unsupported-cover-hole-removed',inside(s,(0,-14.05,3)))
        check('PJ:nominal-mating-pin-full-diameter',inside(s,(.999,-5,6.5))and not inside(s,(1.001,-5,6.5)))
        check('PJ:nominal-mating-cavity-clear',not inside(s,(2.70,-4,6.5)))
    rows.append(dict(id=p['id'],source_sha256=p['source_sha256'],bounds_mm=bounds,solids=len(s.Solids),volume_mm3=s.Volume))
r=dict(passed=True,checks_count=len(checks),checks=checks,families=rows,
       manifest='rear-connector-quality-corrected-manifest.json',
       superseded_original_PJ_model='PJ202AH_DrawingDerived_DetailedBody.step',
       no_physical_fit_claim=True)
(H/'final-geometry-audit.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(dict(passed=True,checks_count=len(checks)),indent=2))
