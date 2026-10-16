# SPDX-License-Identifier: CC0-1.0
"""Check every printed reference label against its Eagle smashed name record (revision 26).

Run with KiCad's bundled Python:  verify_name_labels.py <kicad-working> <eagle-staging-dir> <out.json>

For each part with a name record, exactly one visible silkscreen text prints the Eagle name,
on the record's layer, anchored at the record's position with its size and stroke. The
anchor corner of KiCad's text box (the nearest of its four corners, within 0.3 x the text
size, since the box also spans the descender) is checked against Eagle's own rule, written out
independently of the importer: text reads from the bottom or the right; text turned past
that (and mirrored text, read from below) grows from the opposite corner.
"""
import json
import math
import sys
import xml.etree.ElementTree as ET

import pcbnew

work, eagle, out = sys.argv[1:4]
mm = pcbnew.ToMM
LAYER = {21: 'F.SilkS', 25: 'F.SilkS', 22: 'B.SilkS', 26: 'B.SilkS'}
TOL = 0.3  # x text size: KiCad's box also spans the descender below the baseline


def expected_corner(rot):
    """Corner of the text box (x side, y side, in Gerber orientation) that sits on the Eagle anchor."""
    mirror, spin = 'M' in rot, 'S' in rot
    a = float(rot.replace('M', '').replace('S', '').replace('R', '')) % 360
    assert not spin
    if mirror:
        assert a in (0, 180), rot
        return ('right', 'bottom') if a == 0 else ('left', 'top')
    flipped = 90 < a <= 270
    a = (a - 180) % 360 if flipped else a
    assert a in (0, 90), rot
    corner = {0: ('left', 'bottom'), 90: ('right', 'bottom')}[a]
    if flipped:
        corner = ({'left': 'right', 'right': 'left'}[corner[0]], {'bottom': 'top', 'top': 'bottom'}[corner[1]])
    return corner


result = dict(passed=True, boards={})
for board in ('mainboard', 'ioboard'):
    records = {e.get('name'): e.find('name') for e in ET.parse(f'{eagle}/{board}.brd').getroot().iter('element')
               if e.find('name') is not None and e.find('name').get('layer') is not None}
    B = pcbnew.LoadBoard(f'{work}/{board}/{board}.kicad_pcb')
    failures, checked, worst = [], 0, 0.0
    for fp in B.GetFootprints():
        ref = fp.GetReference()
        name = ref if ref in records else None
        if name is None and ref.endswith('0') and ref[:-1] in records and not ref[-2].isdigit():
            name = ref[:-1]
        if name is None:
            continue
        n = records[name]
        texts = [t for t in [fp.Reference()] + [i for i in fp.GraphicalItems() if i.GetClass() == 'PCB_TEXT']
                 if t.IsVisible() and t.GetLayerName() in ('F.SilkS', 'B.SilkS', 'F.Silkscreen', 'B.Silkscreen')
                 and t.GetShownText(False) == name]
        if len(texts) != 1 or (name != ref and fp.Reference().IsVisible()):
            failures.append(dict(reference=ref, problem='printed label count', count=len(texts)))
            continue
        t = texts[0]
        size = 2 * float(n.get('size'))
        thickness = size * float(n.get('ratio')) / 100
        p = t.GetTextPos()
        anchor = (float(n.get('x')), float(n.get('y')))
        bb = t.GetBoundingBox()
        box = dict(left=mm(bb.GetLeft()), right=mm(bb.GetRight()), bottom=-mm(bb.GetBottom()), top=-mm(bb.GetTop()))
        cx, cy = expected_corner(n.get('rot'))
        corners = {(x, y): math.hypot(box[x] - anchor[0], box[y] - anchor[1])
                   for x in ('left', 'right') for y in ('bottom', 'top')}
        corner_error = corners[(cx, cy)]
        worst = max(worst, corner_error / size)
        problems = []
        if math.hypot(mm(p.x) - anchor[0], -mm(p.y) - anchor[1]) > 1e-6:
            problems.append('anchor')
        if t.GetLayerName() != LAYER[int(n.get('layer'))] and t.GetLayer() != B.GetLayerID(LAYER[int(n.get('layer'))]):
            problems.append('layer')
        if abs(mm(t.GetTextHeight()) + mm(t.GetTextThickness()) - size) > 1e-5 or abs(mm(t.GetTextThickness()) - thickness) > 1e-5:
            problems.append('size')
        if t.IsMirrored() != ('M' in n.get('rot')):
            problems.append('mirror')
        if corner_error > TOL * size or min(corners, key=corners.get) != (cx, cy):
            problems.append('corner')
        if problems:
            failures.append(dict(reference=ref, problems=problems, corner=[cx, cy], box=box, anchor=anchor))
        checked += 1
    result['boards'][board] = dict(records=len(records), labels_checked=checked, failures=failures,
                                   max_corner_error_per_text_size=round(worst, 4), corner_tolerance_per_text_size=TOL)
    result['passed'] &= not failures and checked == len(records)
json.dump(result, open(out, 'w'), indent=1)
