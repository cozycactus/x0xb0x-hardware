# SPDX-License-Identifier: CC0-1.0
"""Read pads, vias, tracks, zone fills, outline and footprints of one KiCad PCB (read-only).

Run with KiCad's bundled Python:  extract_board.py <board.kicad_pcb> <out.json>
Coordinates are returned in Gerber orientation (mm, y up), as kicad-cli plots them.
"""
import json
import sys

import pcbnew

mm = pcbnew.ToMM
pcb_path, out_path = sys.argv[1], sys.argv[2]
B = pcbnew.LoadBoard(pcb_path)
LAYERS = {'F.Cu': pcbnew.F_Cu, 'B.Cu': pcbnew.B_Cu, 'F.Mask': pcbnew.F_Mask, 'B.Mask': pcbnew.B_Mask,
          'F.Paste': pcbnew.F_Paste, 'B.Paste': pcbnew.B_Paste}
ATTR = {pcbnew.PAD_ATTRIB_PTH: 'PTH', pcbnew.PAD_ATTRIB_NPTH: 'NPTH', pcbnew.PAD_ATTRIB_SMD: 'SMD',
        pcbnew.PAD_ATTRIB_CONN: 'CONN'}


def xy(p):
    return [round(mm(p.x), 6), round(-mm(p.y), 6)]


pads, footprints = [], []
for fp in B.GetFootprints():
    kinds = set()
    for p in fp.Pads():
        attr = ATTR.get(p.GetAttribute(), str(p.GetAttribute()))
        kinds.add(attr)
        size = p.GetSize(pcbnew.F_Cu)
        drill = p.GetDrillSize()
        ring = None
        if attr == 'PTH':
            ring = min((mm(p.GetSize(L).x) - mm(drill.x)) / 2 for L in (pcbnew.F_Cu, pcbnew.B_Cu))
            ring = min(ring, min((mm(p.GetSize(L).y) - mm(drill.y)) / 2 for L in (pcbnew.F_Cu, pcbnew.B_Cu)))
        pads.append(dict(ref=fp.GetReference(), num=p.GetNumber(), pos=xy(p.GetPosition()), attr=attr,
                         net=p.GetNetname(), layers=sorted(n for n, L in LAYERS.items() if p.IsOnLayer(L)),
                         size=[mm(size.x), mm(size.y)], drill=[mm(drill.x), mm(drill.y)],
                         offset=[mm(p.GetOffset(pcbnew.F_Cu).x), mm(p.GetOffset(pcbnew.F_Cu).y)],
                         angle=p.GetOrientation().AsDegrees(), ring=ring))
    footprints.append(dict(ref=fp.GetReference(), value=fp.GetValue(), footprint=fp.GetFPIDAsString(),
                           side='bottom' if fp.IsFlipped() else 'top', pos=xy(fp.GetPosition()),
                           pad_kinds=sorted(kinds),
                           dnp=bool(fp.IsDNP()), exclude_from_bom=bool(fp.IsExcludedFromBOM()),
                           printed=[t.GetShownText(False) for t in fp.GraphicalItems()
                                    if t.GetClass() in ('PCB_TEXT', 'FP_TEXT') and t.IsVisible()
                                    and t.GetLayerName() in ('F.Silkscreen', 'B.Silkscreen', 'F.SilkS', 'B.SilkS')],
                           reference_visible=bool(fp.Reference().IsVisible())))

vias, tracks = [], []
for t in B.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        vias.append(dict(pos=xy(t.GetPosition()), width=mm(t.GetWidth(pcbnew.F_Cu)), drill=mm(t.GetDrillValue()),
                         net=t.GetNetname(),
                         mask=[n for n in ('F.Mask', 'B.Mask') if t.IsOnLayer(LAYERS[n])]))
        continue
    row = dict(layer=t.GetLayerName(), start=xy(t.GetStart()), end=xy(t.GetEnd()), width=mm(t.GetWidth()),
               net=t.GetNetname(), arc=t.GetClass() == 'PCB_ARC')
    if row['arc']:
        row['mid'] = xy(t.GetMid())
    tracks.append(row)

zones = []
for z in B.Zones():
    for L in z.GetLayerSet().Seq():
        name = B.GetLayerName(L)
        if name not in ('F.Cu', 'B.Cu'):
            continue
        polys = z.GetFilledPolysList(L)
        zones.append(dict(layer=name, net=z.GetNetname(), priority=z.GetAssignedPriority(),
                          outlines=polys.OutlineCount(), area_mm2=polys.Area() / 1e12))

edges = [d for d in B.GetDrawings() if d.GetLayerName() == 'Edge.Cuts']
bb = B.GetBoardEdgesBoundingBox()
ds = B.GetDesignSettings()
out = dict(
    pcb=pcb_path, thickness_mm=mm(ds.GetBoardThickness()), copper_layers=B.GetCopperLayerCount(),
    outline=dict(segments=len(edges), bbox=[mm(bb.GetLeft()), -mm(bb.GetBottom()), mm(bb.GetRight()), -mm(bb.GetTop())],
                 width=mm(bb.GetWidth()), height=mm(bb.GetHeight())),
    tenting=dict(front=bool(ds.m_TentViasFront) if hasattr(ds, 'm_TentViasFront') else None,
                 back=bool(ds.m_TentViasBack) if hasattr(ds, 'm_TentViasBack') else None),
    pads=pads, vias=vias, tracks=tracks, zones=zones, footprints=footprints)
with open(out_path, 'w') as f:
    json.dump(out, f)
