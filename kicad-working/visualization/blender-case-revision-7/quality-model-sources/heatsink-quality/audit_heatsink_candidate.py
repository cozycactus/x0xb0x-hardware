"""Fresh independent exact BRep feature review; sources and candidate read only."""
from pathlib import Path
import hashlib
import json
import sys

sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part

HERE = Path(__file__).resolve().parent
manifest = json.loads((HERE/'heatsink-quality-manifest.json').read_text())
part = manifest['parts'][0]
path = Path(part['step'])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
before = sha(path)
shape = Part.read(str(path))
box = shape.BoundBox
bounds = [box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax]
expected = [-10.92, -1.27, 0, 10.92, 8.76, 19.05]
checks = []


def check(label, passed, detail=None):
    checks.append({'check': label, 'passed': bool(passed), 'detail': detail})


check('Fresh STEP shape is one valid positive-volume continuous solid',
      shape.isValid() and len(shape.Solids) == 1 and shape.Volume > 0,
      {'solids': len(shape.Solids), 'faces': len(shape.Faces),
       'volume_mm3': shape.Volume})
check('Exact published envelope at retained canonical datum',
      max(abs(a-b) for a,b in zip(bounds, expected)) < 1e-6,
      {'bounds_mm': bounds, 'published_dimensions_mm': [21.84, 10.03, 19.05]})
planes = []
for face in shape.Faces:
    if isinstance(face.Surface, Part.Plane):
        normal = face.normalAt(0, 0)
        if abs(normal.y) > .999:
            planes.append(face.CenterOfMass.y)
check('Published catalogue 0.63 mm sheet thickness at front return',
      any(abs(y + 1.27) < 1e-6 for y in planes)
      and any(abs(y + .64) < 1e-6 for y in planes),
      {'outer_y_mm': -1.27, 'inner_y_mm': -.64,
       'measured_thickness_mm': .63})
cylinders = [f.Surface for f in shape.Faces
             if isinstance(f.Surface, Part.Cylinder)]
hole = [surface for surface in cylinders
        if abs(surface.Radius - 1.905) < 1e-6
        and abs(surface.Axis.y) > .999
        and abs(surface.Center.x) < 1e-6
        and abs(surface.Center.z-11.81) < 1e-6]
check('Published 3.81 mm through hole at metric Z11.81', bool(hole))
finger_region = shape.common(Part.makeBox(4, 2.1, 9.8,
                                        App.Vector(-2, 3, 0)))
finger_top_y = finger_region.BoundBox.YMax
rear_inner_y = next(y for y in planes if abs(y-8.13) < 1e-6)
gap = rear_inner_y - finger_top_y
check('Published checking-gauge gap measured from candidate BRep',
      abs(gap-4.19) < 1e-6,
      {'rear_inner_y_mm': rear_inner_y, 'finger_edge_y_mm': finger_top_y,
       'gap_mm': gap, 'published_tolerance_mm': .13})
check('Explicit STEP millimetre units',
      'SI_UNIT(.MILLI.,.METRE.)' in path.read_text())
check('Black anodized AP214 appearance attached to every BRep face',
      path.read_text().count('STYLED_ITEM') == len(shape.Faces))
check('All original source files preserve their generator snapshot hashes',
      all(sha(Path(p)) == value for p, value
          in manifest['source_file_hashes'].items()))
check('Candidate frozen hash remains unchanged',
      before == sha(path) == part['source_sha256'])
assignment = manifest['assignments'][0]
check('KK1 assignment preserves original footprint and canonical transforms',
      assignment['board'] == 'ioboard' and assignment['references'] == ['KK1']
      and assignment['footprint'] == 'D03S'
      and assignment['offset_mm'] == [0,0,0]
      and assignment['rotation_deg'] == [0,0,0]
      and assignment['scale'] == [1,1,1])
native = json.loads((HERE/'native-probes/native-export-audit.json').read_text())
check('Fresh native KiCad export passes dimensional and palette checks',
      native['passed'])
contact = json.loads((HERE/'nominal-regulator-contact-audit.json').read_text())
check('Known nominal IC20 interference remains explicitly measurable',
      abs(contact['coarse_intersection_volume_mm3']-40.92) < 1e-6
      and contact['new_intersection_volume_mm3'] > 0,
      {'previous_mm3': contact['coarse_intersection_volume_mm3'],
       'candidate_mm3': contact['new_intersection_volume_mm3']})
result = {'scope': 'Fresh read-only source STEP/BRep feature audit; no generated '
                   'geometry or PCB edits during this check.',
          'source_step': str(path), 'source_sha256': before,
          'checks': checks, 'check_count': len(checks),
          'failures': [c for c in checks if not c['passed']],
          'limits': ['PASS verifies source-qualified geometry and export only. '
                     'The preserved nominal source pose has interference and '
                     'does not qualify clamping or installed fit.']}
result['passed'] = not result['failures']
(HERE/'independent-heatsink-audit.json').write_text(
    json.dumps(result, indent=2)+'\n')
print(json.dumps({'passed': result['passed'], 'check_count': len(checks),
                  'failures': result['failures']}, indent=2))
