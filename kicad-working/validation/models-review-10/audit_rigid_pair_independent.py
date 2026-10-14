"""Independently compare the photo-qualified pair with original full solids."""
from pathlib import Path
import hashlib
import json
import sys

sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
SOURCE = HERE / 'heatsink-fit-research'
plan = json.loads((HERE / 'combined-model-plan.json').read_text())
pose_file = HERE.parent / 'models-review-9/heatsink-quality/independent-io-pose-input.json'
poses = {r['ref']: r for r in json.loads(pose_file.read_text())}
rows = {(r['board'], ref): r for r in plan['assignments'] for ref in r['references']}
manifest = json.loads((SOURCE / 'bent-pair-manifest.json').read_text())
checks = []
records = []


def check(name, ok, details=None):
    checks.append({'check': name, 'passed': bool(ok), 'details': details})


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


parts = {}
for part in manifest['parts']:
    ref = part['references'][0]
    original = Part.read(part['rigid_source'])
    actual = Part.read(part['step'])
    expected = original.copy()
    if ref == 'KK1':
        # Native footprint KK1 is 1.27 mm beyond IC20 in outward Y.
        # Align the source 11.81 mm hole and rear contact plane first.
        expected.translate(App.Vector(0, -7.51, 3.90))
    expected.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), -90)
    expected.translate(App.Vector(0, -1.27 if ref == 'KK1' else 0, 2.0))
    overlap = expected.common(actual).Volume
    delta = max(abs(expected.Volume - overlap), abs(actual.Volume - overlap))
    check(ref + ' original and frozen replacement hashes',
          sha(part['rigid_source']) == part['rigid_source_sha256']
          and sha(part['step']) == part['source_sha256'])
    check(ref + ' valid positive-volume replacement', actual.isValid()
          and all(s.isValid() and s.Volume > 0 for s in actual.Solids))
    check(ref + ' full original rigid geometry retained', delta < 1e-5,
          {'expected_volume_mm3': expected.Volume, 'actual_volume_mm3': actual.Volume,
           'common_volume_mm3': overlap, 'maximum_volume_difference_mm3': delta})
    check(ref + ' canonical geometry above board seat',
          actual.optimalBoundingBox().ZMin > 0)
    parts[ref] = actual
    records.append({'reference': ref, 'maximum_rigid_volume_difference_mm3': delta})

# Compare exact source BReps in the unchanged native footprint frame.
heat = parts['KK1'].copy()
heat.translate(App.Vector(poses['KK1']['x'], poses['KK1']['y'], 0))
reg = parts['IC20'].copy()
reg.translate(App.Vector(poses['IC20']['x'], poses['IC20']['y'], 0))
pair_overlap = heat.common(reg).Volume
check('Previously documented free-state spring overlap retained',
      abs(pair_overlap - 1.729422) < 1e-5, {'overlap_mm3': pair_overlap})
neighbors = []
for ref in ['C3', 'C4', 'C5']:
    row = rows['ioboard', ref]
    check(ref + ' existing model canonical assignment', row['offset_mm'] == [0, 0, 0]
          and row['rotation_deg'] == [0, 0, 0] and row['scale'] == [1, 1, 1])
    shape = Part.read(row['source_model'])
    shape.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), poses[ref]['angle'])
    shape.translate(App.Vector(poses[ref]['x'], poses[ref]['y'], 0))
    volumes = {'heatsink_mm3': heat.common(shape).Volume,
               'regulator_mm3': reg.common(shape).Volume}
    check(ref + ' exact package bodies clear of bent pair',
          max(volumes.values()) < 1e-7, volumes)
    neighbors.append({'reference': ref, 'intersections': volumes})

report = {'passed': all(c['passed'] for c in checks), 'check_count': len(checks),
          'checks': checks, 'failures': [c for c in checks if not c['passed']],
          'rigid_geometry_records': records, 'neighbor_records': neighbors,
          'pair_free_state_overlap_mm3': pair_overlap,
          'scope': 'Fresh independent exact BRep rigid-transform and nearby body review; no project or geometry edits.',
          'limits': ['The 90 degree bend and 2 mm vertical datum are illustrations supported qualitatively by original photos, not measured forming specifications.',
                     'Free-state spring overlap is not elastic clamping or thermal-contact certification.',
                     'IC20 leads remain omitted; actual original vendor, lead dimensions and fitted tolerances are unresolved.',
                     'Case and full populated-board surface screens are recorded separately.']}
(HERE / 'independent-rigid-pair-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ['passed', 'check_count', 'failures', 'pair_free_state_overlap_mm3']}, indent=2))
raise SystemExit(0 if report['passed'] else 1)
