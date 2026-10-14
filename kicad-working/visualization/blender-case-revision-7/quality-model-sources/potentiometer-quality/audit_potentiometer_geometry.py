"""Fresh read-only native STEP and published-datum audit."""
from pathlib import Path
import sys, json, hashlib
sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part, Import
H = Path(__file__).resolve().parent
m = json.loads((H/'potentiometer-quality-manifest.json').read_text())
checks, models = [], []
def check(name, passed, detail=None):
    r = {'check':name,'passed':bool(passed)}
    if detail is not None:r['detail'] = detail
    checks.append(r)
def bounds(s):
    b=s.BoundBox
    return [b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]
for p in m['parts']:
    path=Path(p['step']); s=Part.read(str(path)); pan=p['id'].startswith('Panasonic')
    expected=[-4.85,-6.5,0,4.85,6,30] if pan else [-6.8,-8.7,0,6.8,6.7,25]
    check(p['id']+' valid STEP',s.isValid() and all(v.isValid() and v.Volume>0 for v in s.Solids))
    check(p['id']+' frozen source hash',hashlib.sha256(path.read_bytes()).hexdigest()==p['source_sha256'])
    check(p['id']+' full published nominal bounds',max(abs(a-b) for a,b in zip(bounds(s),expected))<1e-5,bounds(s))
    check(p['id']+' no below-seat geometry',s.BoundBox.ZMin>-1e-7)
    check(p['id']+' millimetre SI units',"SI_UNIT(.MILLI.,.METRE.)" in path.read_text())
    check(p['id']+' zero-unity assignment',p['offset_mm']==[0,0,0] and p['rotation_deg']==[0,0,0] and p['scale']==[1,1,1])
    doc=App.newDocument('PotIndependent');Import.insert(str(path),doc.Name)
    features={o.Label:o.Shape for o in doc.Objects if hasattr(o,'Shape') and o.Shape.Solids}
    shaft=features['FL3_FlattedInsulatedShaft' if pan else 'OpaqueFlattedShaft']
    sleeve=features['UnthreadedSleeve']
    target=[-4.5,-4.5,8.5,4.5,4.5,13.5] if pan else [-3.6,-3.6,6.9,3.6,3.6,11.9]
    check(p['id']+' sleeve diameter/projection',max(abs(a-b) for a,b in zip(bounds(sleeve),target))<1e-5,bounds(sleeve))
    top=30 if pan else 25;length=12 if pan else 7
    inside=lambda x,y,z:shaft.isInside(App.Vector(x,y,z),1e-7,True)
    check(p['id']+' D6 lower round shaft',inside(2.99,0,15) and not inside(3.01,0,15))
    check(p['id']+' negativeY flat across4.5',not inside(0,-1.51,top-2) and inside(0,-1.49,top-2))
    check(p['id']+' selected flat length',inside(0,-2.0,top-length-.01) and not inside(0,-2.0,top-length+.01))
    check(p['id']+' shaft tip Z',abs(shaft.BoundBox.ZMax-top)<1e-6)
    models.append({'id':p['id'],'step_sha256':p['source_sha256'],'bounds_mm':bounds(s),
                   'solids':len(s.Solids),'faces':len(s.Faces),'volume_mm3':s.Volume,
                   'feature_bounds_mm':{k:bounds(v) for k,v in features.items()}})
    App.closeDocument(doc.Name)
check('All original input assets unchanged',{str(p):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in m['input_hashes']}==m['input_hashes'])
out={'passed':all(c['passed'] for c in checks),'scope':'Fresh native FreeCAD read-only imports and source-qualified published datums; no installed-fit claim.',
     'check_count':len(checks),'checks':checks,'models':models,'failure_count':sum(not c['passed'] for c in checks)}
(H/'geometry-quality-audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'passed':out['passed'],'check_count':len(checks),'failures':[c for c in checks if not c['passed']]},indent=2))
assert out['passed']
