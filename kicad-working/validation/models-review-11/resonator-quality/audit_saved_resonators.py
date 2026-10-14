#!/usr/bin/env python3
"""Read-only independent STEP reimport audit; writes only its report here.

SPDX-License-Identifier: CC0-1.0
"""
import hashlib
import json
import math
from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[2]
sha=lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
manifest=json.loads((HERE/'resonator-quality-manifest.json').read_text())
checks=[]


def check(name, passed, **evidence):
    checks.append(dict(name=name, passed=bool(passed), **evidence))


def bounds(shape):
    b=shape.optimalBoundingBox(False,False)
    return [b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]


models=[]
for row in manifest['parts']:
    path=HERE/Path(row['source_model']).name
    oldpath=WORK/row['board']/'3dmodels/Revision5/integrated-models'/Path(row['baseline_model']).name
    check(row['id']+':frozen-STEP-hash', sha(path)==row['source_sha256'])
    check(row['id']+':frozen-baseline-hash', sha(oldpath)==row['baseline_sha256'])
    shape=Part.read(str(path))
    old=Part.read(str(oldpath))
    check(row['id']+':four-valid-material-solids', shape.isValid() and len(shape.Solids)==4 and
          all(s.isValid() and s.Volume>0 for s in shape.Solids))
    body=max(shape.Solids,key=lambda s:s.Volume)
    oldbody=max(old.Solids,key=lambda s:s.Volume)
    leads=sorted([s for s in shape.Solids if s.Volume<1], key=lambda s:s.CenterOfMass.x)
    oldleads=sorted([s for s in old.Solids if s.Volume<1], key=lambda s:s.CenterOfMass.x)
    check(row['id']+':same-body-max-envelope',
          max(abs(a-b) for a,b in zip(bounds(body),bounds(oldbody)))<1e-6,
          refined_mm=bounds(body), baseline_mm=bounds(oldbody))
    check(row['id']+':same-full-max-envelope',
          max(abs(a-b) for a,b in zip(bounds(shape),bounds(old)))<1e-6)
    check(row['id']+':refined-body-within-prior-envelope', body.cut(oldbody).Volume<1e-6,
          outside_baseline_body_volume_mm3=body.cut(oldbody).Volume)
    check(row['id']+':taper-removes-box-volume', body.Volume<oldbody.Volume*.9,
          baseline_body_volume_mm3=oldbody.Volume, refined_body_volume_mm3=body.Volume)
    check(row['id']+':three-complete-leads',len(leads)==len(oldleads)==3)
    centers=[]
    for index,(lead,previous) in enumerate(zip(leads,oldleads)):
        difference=lead.cut(previous).Volume+previous.cut(lead).Volume
        check(row['id']+f':lead-{index+1}-same-exact-solid',difference<1e-8,
              symmetric_difference_volume_mm3=difference)
        check(row['id']+f':lead-{index+1}-same-six-bounds',
              max(abs(a-b) for a,b in zip(bounds(lead),bounds(previous)))<1e-7)
        check(row['id']+f':lead-{index+1}-full-section',abs(lead.Volume-.6237)<1e-8)
        contact=body.common(lead).Volume
        check(row['id']+f':lead-{index+1}-body-continuity',contact>0,
              overlapping_body_volume_mm3=contact)
        centers.append([lead.CenterOfMass.x,lead.CenterOfMass.y])
    check(row['id']+':exact-2p54-pitch',
          all(math.dist(center,[x,0])<1e-7 for center,x in zip(centers,[-2.54,0,2.54])),
          centers_mm=centers)
    plane=Part.makePlane(30,30,App.Vector(-15,-15,-1))
    section=shape.section(plane)
    wires=[Part.Wire(edges) for edges in Part.sortEdges(section.Edges)]
    check(row['id']+':three-lead-sections-at-z-minus1',len(wires)==3)
    for i,wire in enumerate(sorted(wires,key=lambda s:s.CenterOfMass.x)):
        b=wire.BoundBox
        check(row['id']+f':section-{i+1}-exact-width-thickness',
              abs(b.XLength-.6)<1e-7 and abs(b.YLength-.35)<1e-7,
              section_mm=[b.XLength,b.YLength])
    union=body
    for lead in leads:union=union.fuse(lead)
    check(row['id']+':connected-valid-STEP-union',union.isValid() and len(union.Solids)==1)
    stl=HERE/Path(row['stl']).name
    check(row['id']+':frozen-exterior-STL-hash',sha(stl)==row['stl_sha256'])
    for feature in row['features']:
        check(row['id']+':feature-'+feature['name']+':frozen-STL-hash',
              sha(HERE/Path(feature['stl']).name)==feature['sha256'])
    check(row['id']+':placement-diff-zero-recorded', row['placement_diff_zero'] and
          row['offset_mm']==[0,0,0] and row['scale']==[1,1,1] and
          row['rotation_deg']==([0,0,180] if row['board']=='mainboard' else [0,0,0]))
    check(row['id']+':source-polarity-preserved',row['source_face_and_pin_order']==['3','2/GND','1'])
    models.append(dict(id=row['id'],sha256=sha(path),body_bounds_mm=bounds(body),
                       full_bounds_mm=bounds(shape),lead_centers_mm=centers,
                       body_volume_mm3=body.Volume,physical_fit_qualified=False))
for original_path,expected in manifest['source_project_hashes'].items():
    path=WORK/Path(original_path).parent.name/Path(original_path).name
    check('source-PCB-unchanged:'+path.parent.name,sha(path)==expected)
failures=[c for c in checks if not c['passed']]
report=dict(passed=not failures,check_count=len(checks),failure_count=len(failures),
            failures=failures,models=models,checks=checks,
            generator_imported=False,independent_algorithm='Fresh STEP reimport; prior STEP comparison, boolean differences and z=-1 section measurement',
            physical_fit_qualified=False)
(HERE/'resonator-quality-saved-geometry-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['checks','models']},indent=2),flush=True)
raise SystemExit(0 if report['passed'] else 1)
