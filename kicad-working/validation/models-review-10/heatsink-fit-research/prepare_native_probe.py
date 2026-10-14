from pathlib import Path
import json
H=Path(__file__).resolve().parent
m=json.loads((H/'bent-pair-manifest.json').read_text());out=H/'native-probes';out.mkdir(exist_ok=True)
t='''(kicad_pcb (version 20260206) (generator pcbnew)
(general (thickness 1.6)) (paper "A4")
(layers (0 "F.Cu" signal) (31 "B.Cu" signal) (44 "Edge.Cuts" user))
(setup (pad_to_mask_clearance 0))
(gr_rect (start 10 10) (end 70 70) (stroke (width 0.05) (type default)) (fill none) (layer "Edge.Cuts"))
'''
for part in m['parts']:
 ref=part['references'][0];y=41.27 if ref=='IC20' else 40
 t+=f'''(footprint "ReadOnlyProbe" (layer "F.Cu") (at 40 {y})
(property "Reference" "{ref}" (at 0 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness .15))))
(property "Value" "Isolated photo-qualified model probe" (at 0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness .15))))
(model {json.dumps(part['step'])} (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0))))
'''
t+=')\n';(out/'bent-pair.kicad_pcb').write_text(t)
