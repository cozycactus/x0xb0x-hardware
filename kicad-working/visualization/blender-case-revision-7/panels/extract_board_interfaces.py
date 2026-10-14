"""Read placed KiCad footprints for original panel registration; never save PCB.

Run with the bundled KiCad Python interpreter, which supplies pcbnew.
"""
from pathlib import Path
import json
import pcbnew

BASE = Path(__file__).resolve().parent.parent
ROOT = BASE.parent.parent
INTERFACES = {'LED5MM', 'B3F-40XX', 'ALPHADUAL', 'EVU', 'NKKTOGGLE',
              'PEC11-S', 'GH3074', '1,3'}
out = {}
for name in ['mainboard', 'ioboard']:
    board = pcbnew.LoadBoard(str(ROOT / name / (name + '.kicad_pcb')))
    out[name] = []
    for footprint in board.GetFootprints():
        item = str(footprint.GetFPID().GetLibItemName())
        if name == 'mainboard' and item not in INTERFACES:
            continue
        pads = list(footprint.Pads())
        row = {'ref': footprint.GetReference(),
               'value': footprint.GetValue(), 'footprint': item,
               'x': pcbnew.ToMM(footprint.GetPosition().x),
               'y': pcbnew.ToMM(footprint.GetPosition().y),
               'rot': footprint.GetOrientationDegrees(),
               'layer': board.GetLayerName(footprint.GetLayer()),
               'pads': [[pad.GetNumber(), pcbnew.ToMM(pad.GetPosition().x),
                         pcbnew.ToMM(pad.GetPosition().y)] for pad in pads]}
        if any(pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH for pad in pads):
            row['actual_placed_drill_mm'] = [[pcbnew.ToMM(pad.GetDrillSize().x),
                                              pcbnew.ToMM(pad.GetDrillSize().y)]
                                             for pad in pads]
        out[name].append(row)
(BASE / 'panels/board-interface-positions.json').write_text(
    json.dumps(out, indent=2) + '\n')
print({name: len(rows) for name, rows in out.items()})
