"""Read exact four-family source BRep bounds without meshing or saving CAD."""
from pathlib import Path
import hashlib
import json
import sys

sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD
import Part

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
sys.path.insert(0, str(WORK.parent / 'kicad-import/validation'))
from verify_native_projects import children, one, parse_sexpr, property_value
plan = json.loads((HERE / 'combined-model-plan.json').read_text())
actual_boards = {}
for board in {r['board'] for r in plan['updated_assignments']}:
    pcb = WORK / board / (board + '.kicad_pcb')
    text = pcb.read_text()
    actual_boards[board] = {
        'path': str(pcb),
        'sha256': hashlib.sha256(pcb.read_bytes()).hexdigest(),
        'footprints': {property_value(fp, 'Reference', 'reference'): fp
                       for fp in children(parse_sexpr(text), 'footprint')},
    }


def model_xyz(model, key, default):
    node = one(model, key)
    return list(map(float, one(node, 'xyz')[1:])) if node else default


records = []
for row in plan['updated_assignments']:
    path = Path(row['source_model'])
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    shape = Part.Shape()
    shape.read(str(path))
    box = shape.optimalBoundingBox()
    bounds = [box.XMin, box.YMin, box.ZMin,
              box.XMax, box.YMax, box.ZMax]
    after = hashlib.sha256(path.read_bytes()).hexdigest()
    native = []
    for ref in row['references']:
        footprint = actual_boards[row['board']]['footprints'][ref]
        models = children(footprint, 'model')
        assert len(models) == 1
        model = models[0]
        assigned = Path(model[1].replace('${KIPRJMOD}', str(WORK / row['board'])))
        actual = {
            'reference': ref,
            'actual_model': str(assigned),
            'actual_model_sha256': hashlib.sha256(assigned.read_bytes()).hexdigest(),
            'offset_mm': model_xyz(model, 'offset', [0,0,0]),
            'scale': model_xyz(model, 'scale', [1,1,1]),
            'rotation_deg': model_xyz(model, 'rotate', [0,0,0]),
        }
        actual['passed'] = (actual['actual_model_sha256'] == row['source_sha256']
                            and actual['offset_mm'] == row['offset_mm']
                            and actual['scale'] == row['scale']
                            and actual['rotation_deg'] == row['rotation_deg'])
        native.append(actual)
    records.append({
        'family': path.stem,
        'source_step': str(path),
        'source_sha256': before,
        'expected_sha256': row['source_sha256'],
        'source_hash_unchanged': before == after == row['source_sha256'],
        'board': row['board'],
        'references': row['references'],
        'exact_STEP_bounds_mm': bounds,
        'valid': shape.isValid(),
        'solid_count': len(shape.Solids),
        'face_count': len(shape.Faces),
        'volume_mm3': shape.Volume,
        'all_solids_valid_positive_volume': all(
            solid.isValid() and solid.Volume > 0 for solid in shape.Solids),
        'assignment_offset_mm': row['offset_mm'],
        'assignment_scale': row['scale'],
        'assignment_rotation_deg': row['rotation_deg'],
        'actual_native_assignments': native,
        'actual_PCB': actual_boards[row['board']]['path'],
        'actual_PCB_sha256': actual_boards[row['board']]['sha256'],
        'limitations': row['limitations'],
    })
result = {
    'method': 'Fresh read-only FreeCAD Part.Shape.read of frozen source STEP. '
              'Exact trimmed BRep bounds taken with optimalBoundingBox before tessellation; mm.',
    'records': records,
    'family_count': len({r['family'] for r in records}),
    'assignment_row_count': len(records),
    'reference_count': sum(len(r['references']) for r in records),
    'passed': bool(records) and all(
        r['source_hash_unchanged'] and r['valid']
        and all(a['passed'] for a in r['actual_native_assignments'])
        and r['all_solids_valid_positive_volume'] for r in records),
}
(HERE / 'full-scene-step-bounds-input.json').write_text(
    json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in
                  ('passed', 'family_count', 'reference_count')}, indent=2))
