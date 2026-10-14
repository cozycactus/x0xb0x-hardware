"""Create isolated Q22 native export probe with its actual angle and pads."""
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
manifest = json.loads((HERE/'legacy-quality-manifest.json').read_text())
part = manifest['parts'][0]
out = HERE/'native-probes'
out.mkdir(exist_ok=True)
text = '''(kicad_pcb (version 20260206) (generator pcbnew)
 (general (thickness 1.6)) (paper "A4")
 (layers (0 "F.Cu" signal) (31 "B.Cu" signal) (44 "Edge.Cuts" user))
 (setup (pad_to_mask_clearance 0))
 (gr_rect (start 10 10) (end 70 70) (stroke (width 0.05) (type default))
 (fill none) (layer "Edge.Cuts"))
 (footprint "SSIP5_Q22Probe" (layer "F.Cu") (at 40 40 180)
 (property "Reference" "Q22" (at 0 0) (layer "F.SilkS")
 (effects (font (size 1 1) (thickness 0.15))))
 (property "Value" "2SC2291" (at 0 0) (layer "F.Fab")
 (effects (font (size 1 1) (thickness 0.15))))
'''
for pad in manifest['actual_source_pads']:
    x,y = pad['canonical_xy_mm']
    text += f''' (pad "{pad['pin']}" thru_hole circle (at {x} {-y})
 (size 1.778 1.778) (drill {pad['drill_mm']}) (layers "*.Cu" "*.Mask"))
'''
text += f''' (model {json.dumps(part['step'])} (offset (xyz 0 0 0))
 (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))))
'''
(out/'2SC2291-Q22.kicad_pcb').write_text(text)
print('Prepared isolated Q22 probe with native F.Cu angle180; source untouched.')
