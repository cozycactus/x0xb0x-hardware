# SPDX-License-Identifier: CC0-1.0
"""Set each reference label from the Eagle smashed name record (KiCad revision 26 helper).

Run with KiCad's bundled Python on a temporary copy of one board:
  apply_name_records.py <board.kicad_pcb> <eagle-staging.brd> <out.kicad_pcb> <rows.json>

Position, rotation, size, ratio, mirror and layer come from the element's <name> record.
Rotation and justification follow KiCad's own Eagle importer (EaglePcbTextToKiCadAlignment
for a smashed attribute): text that Eagle turns to stay readable (90 < angle <= 270, or
90 <= angle < 270 when mirrored, no spin) is drawn 180 degrees back and anchored at its
top-right corner. The record stores half the text size, like Eagle's text record, so the
size is doubled; the production I/O photograph shows J3 at the 1.27 mm of its "1"/"12".
Thickness is size x ratio, and KiCad's font size excludes it (Eagle's includes it).

References that KiCad had to end with "0" (Eagle "MIXOUT" -> KiCad "MIXOUT0") keep their
reference; the Reference field is hidden and a footprint text with the Eagle name is
printed instead, with the same geometry.
"""
import json
import sys
import xml.etree.ElementTree as ET

import pcbnew

src, xml_path, out, report = sys.argv[1:5]
LAYER = {21: 'F.SilkS', 25: 'F.SilkS', 22: 'B.SilkS', 26: 'B.SilkS'}
JUSTIFY = {'left': pcbnew.GR_TEXT_H_ALIGN_LEFT, 'right': pcbnew.GR_TEXT_H_ALIGN_RIGHT,
           'bottom': pcbnew.GR_TEXT_V_ALIGN_BOTTOM, 'top': pcbnew.GR_TEXT_V_ALIGN_TOP}


def nm(v):
    return int(round(float(v) * 1e6))


def rot(s):
    s = s or 'R0'
    return 'M' in s, 'S' in s, float(s.replace('M', '').replace('S', '').replace('R', '') or 0)


def kicad_alignment(degrees, mirror, spin):
    """EaglePcbTextToKiCadAlignment with the element defaults (0 degrees, no mirror, no spin)."""
    d = ((-1.0 if mirror else 1.0) * (degrees % 360.0)) % 360.0
    if not spin and ((not mirror and 90 < d <= 270) or (mirror and 90 <= d < 270)):
        return (d - 180) % 360.0, ('right', 'top')
    return d, ('left', 'bottom')


records = {e.get('name'): e.find('name') for e in ET.parse(xml_path).getroot().iter('element')
           if e.find('name') is not None and e.find('name').get('layer') is not None}
B = pcbnew.LoadBoard(src)
rows = []
for fp in B.GetFootprints():
    ref = fp.GetReference()
    name = ref if ref in records else None
    if name is None and ref.endswith('0') and ref[:-1] in records and not ref[-2].isdigit():
        name = ref[:-1]
    if name is None:
        continue
    n = records[name]
    mirror, spin, degrees = rot(n.get('rot'))
    assert (n.get('mirrored') == '1') == mirror and (n.get('spin') == '1') == spin, name
    size = 2 * nm(n.get('size'))
    thickness = int(round(size * float(n.get('ratio')) / 100.0))
    angle, (h, v) = kicad_alignment(degrees, mirror, spin)
    field = fp.Reference()
    p = field.GetTextPos()
    before = dict(pos_mm=[pcbnew.ToMM(p.x), -pcbnew.ToMM(p.y)], angle=field.GetTextAngleDegrees(),
                  layer=field.GetLayerName(), size_mm=pcbnew.ToMM(field.GetTextHeight()),
                  thickness_mm=pcbnew.ToMM(field.GetTextThickness()), mirrored=field.IsMirrored())
    texts = [field]
    if name != ref:
        user = pcbnew.PCB_TEXT(fp)
        user.SetText(name)
        fp.Add(user)
        texts.append(user)
    for t in texts:
        t.SetLayer(B.GetLayerID(LAYER[int(n.get('layer'))]))
        t.SetTextPos(pcbnew.VECTOR2I(nm(n.get('x')), -nm(n.get('y'))))
        t.SetTextSize(pcbnew.VECTOR2I(size - thickness, size - thickness))
        t.SetTextThickness(thickness)
        t.SetTextAngleDegrees(angle)
        t.SetMirrored(mirror)
        t.SetKeepUpright(False)
        t.SetHorizJustify(JUSTIFY[h])
        t.SetVertJustify(JUSTIFY[v])
    field.SetVisible(name == ref)
    rows.append(dict(reference=ref, printed=name, eagle_record=dict(n.attrib), eagle_size_mm=size / 1e6,
                     layer=LAYER[int(n.get('layer'))], anchor_mm=[nm(n.get('x')) / 1e6, nm(n.get('y')) / 1e6],
                     kicad_angle=angle, mirrored=mirror, justify=[h, v],
                     font_mm=(size - thickness) / 1e6, thickness_mm=thickness / 1e6, before=before))
pcbnew.SaveBoard(out, B)
json.dump(rows, open(report, 'w'), indent=1)
