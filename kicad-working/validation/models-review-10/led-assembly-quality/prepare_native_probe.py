from pathlib import Path
import json
H=Path(__file__).resolve().parent;m=json.loads((H/'led-assembly-manifest.json').read_text());a=m['assignments'][0];out=H/'native-probes';out.mkdir(exist_ok=True)
t=f'''(kicad_pcb (version 20260206) (generator pcbnew)
(general (thickness 1.6)) (paper "A4")
(layers (0 "F.Cu" signal) (31 "B.Cu" signal) (44 "Edge.Cuts" user))
(setup (pad_to_mask_clearance 0))
(gr_rect (start 10 10) (end 70 70) (stroke (width .05) (type default)) (fill none) (layer "Edge.Cuts"))
(footprint "LED5MM" (layer "B.Cu") (at 40 40 180)
(property "Reference" "LEDprobe" (at 0 0) (layer "B.SilkS") (effects (font (size 1 1) (thickness .15))))
(property "Value" "Source-frame LED installation probe" (at 0 0) (layer "B.Fab") (effects (font (size 1 1) (thickness .15))))
(pad "K" thru_hole circle (at 1.27 0) (size 1.8 1.8) (drill 1) (layers "*.Cu" "*.Mask"))
(pad "A" thru_hole circle (at -1.27 0) (size 1.8 1.8) (drill 1) (layers "*.Cu" "*.Mask"))
(model {json.dumps(a['source_model'])} (offset (xyz 1.27 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 180)))))
'''
(out/'LED-installed.kicad_pcb').write_text(t)
