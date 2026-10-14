"""Prepare an isolated native export probe; actual source PCB is read only."""
from pathlib import Path
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
sys.path.insert(0, str(WORK.parent/'kicad-import/validation'))
from verify_native_projects import children, one, parse_sexpr, property_value

manifest = json.loads((HERE/'heatsink-quality-manifest.json').read_text())
pcb = WORK/'ioboard/ioboard.kicad_pcb'
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
before = digest(pcb)
tree = parse_sexpr(pcb.read_text())
fps = {property_value(fp, 'Reference', 'reference'): fp
       for fp in children(tree, 'footprint')}
poses = {}
for ref in ['KK1', 'IC20']:
    fp = fps[ref]
    at = list(map(float, one(fp, 'at')[1:]))
    poses[ref] = {'pcb_at_mm_deg': at, 'layer': one(fp, 'layer')[1]}
    assert poses[ref]['layer'] == 'F.Cu'
    assert at[2] == 0 if len(at) > 2 else True
delta = [poses['IC20']['pcb_at_mm_deg'][i]
         - poses['KK1']['pcb_at_mm_deg'][i] for i in range(2)]
assert max(abs(a-b) for a, b in zip(delta, [0, 1.27])) < 1e-6
out = HERE/'native-probes'
out.mkdir(exist_ok=True)
parts = [
    ('KK1', manifest['parts'][0]['step'], 40, 40),
    ('IC20', json.loads((HERE/'nominal-regulator-contact-audit.json').read_text())
     ['IC20_source_step'], 40+delta[0], 40+delta[1]),
]
text = '''(kicad_pcb (version 20260206) (generator pcbnew)
 (general (thickness 1.6)) (paper "A4")
 (layers (0 "F.Cu" signal) (31 "B.Cu" signal) (44 "Edge.Cuts" user))
 (setup (pad_to_mask_clearance 0))
 (gr_rect (start 10 10) (end 70 70) (stroke (width 0.05) (type default))
 (fill none) (layer "Edge.Cuts"))
'''
for ref, path, x, y in parts:
    text += f''' (footprint "ReadOnlyProbe" (layer "F.Cu") (at {x} {y})
 (property "Reference" "{ref}" (at 0 0) (layer "F.SilkS")
 (effects (font (size 1 1) (thickness 0.15))))
 (property "Value" "Read-only native probe" (at 0 0) (layer "F.Fab")
 (effects (font (size 1 1) (thickness 0.15))))
 (model {json.dumps(path)} (offset (xyz 0 0 0))
 (scale (xyz 1 1 1)) (rotate (xyz 0 0 0))))
'''
text += ')\n'
(out/'heatsink-with-regulator.kicad_pcb').write_text(text)
assert before == digest(pcb)
(out/'native-probe-plan.json').write_text(json.dumps({
    'source_board': str(pcb), 'source_board_sha256': before,
    'source_board_unchanged': True, 'actual_source_poses': poses,
    'probe_KK1_pcb_at_mm': [40, 40],
    'probe_IC20_pcb_at_mm': [40+delta[0], 40+delta[1]],
    'original_relative_native_translation_mm': [delta[0], -delta[1], 0],
    'model_transforms': 'Zero offsets/rotations, unity scales for both models.',
}, indent=2)+'\n')
print('Prepared isolated native probe; source PCB hash unchanged:', before)
