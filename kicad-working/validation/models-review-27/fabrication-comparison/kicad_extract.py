# SPDX-License-Identifier: CC0-1.0
"""Read silkscreen texts, zones and copper islands from both KiCad PCBs (read-only).

Run with KiCad's bundled Python:  kicad_extract.py <kicad-working> <out.json>
Coordinates are returned in Gerber orientation (y up, = Eagle coordinates).
"""
import json
import sys
from collections import defaultdict

import pcbnew

mm = pcbnew.ToMM
work, out_path = sys.argv[1], sys.argv[2]
SILK = ('F.SilkS', 'B.SilkS', 'F.Silkscreen', 'B.Silkscreen')


def texts(B):
    rows = []

    def add(t, kind, ref):
        if t.GetLayerName() not in SILK or not t.IsVisible():
            return
        bb, p = t.GetBoundingBox(), t.GetTextPos()
        rows.append(dict(kind=kind, ref=ref, text=t.GetShownText(False), layer=t.GetLayerName(),
                         pos=[mm(p.x), -mm(p.y)], angle=t.GetTextAngleDegrees(), size=mm(t.GetTextHeight()),
                         bbox=[mm(bb.GetLeft()), -mm(bb.GetBottom()), mm(bb.GetRight()), -mm(bb.GetTop())]))
    for fp in B.GetFootprints():
        add(fp.Reference(), 'reference', fp.GetReference())
        add(fp.Value(), 'value', fp.GetReference())
        for it in fp.GraphicalItems():
            if it.GetClass() in ('PCB_TEXT', 'FP_TEXT'):
                add(it, 'fp_text', fp.GetReference())
    for it in B.GetDrawings():
        if it.GetClass() == 'PCB_TEXT':
            add(it, 'gr_text', None)
    return rows


def zones(B):
    zs = []
    for z in B.Zones():
        o = z.Outline()
        outline = []
        for i in range(o.OutlineCount()):
            ol = o.Outline(i)
            outline.append([(mm(ol.CPoint(k).x), -mm(ol.CPoint(k).y)) for k in range(ol.PointCount())])
        zs.append(dict(net=z.GetNetname(), layer=z.GetLayerName(), priority=z.GetAssignedPriority(),
                       clearance=mm(z.GetLocalClearance() or 0), min_width=mm(z.GetMinThickness()),
                       thermal_gap=mm(z.GetThermalReliefGap()), spoke=mm(z.GetThermalReliefSpokeWidth()),
                       island_mode=int(z.GetIslandRemovalMode()), fill_mode=int(z.GetFillMode()),
                       outline=outline, filled_area_mm2=round(z.GetFilledArea() / 1e12, 1)))
    return dict(zones=zs, board_clearance=mm(B.GetDesignSettings().m_MinClearance))


def islands(B, net):
    """Copper islands of one net from KiCad's connectivity (tracks, vias, pads, filled zones).

    Pads of one footprint jumper group are reported separately as 'jumper_links'."""
    items = []
    for fp in B.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() == net:
                items.append((f'{fp.GetReference()}.{p.GetNumber()}', p))
    for t in B.GetTracks():
        if t.GetNetname() == net:
            items.append(('via' if t.GetClass() == 'PCB_VIA' else 'track', t))
    for z in B.Zones():
        if z.GetNetname() == net:
            items.append((f'zone:{z.GetLayerName()}:priority{z.GetAssignedPriority()}', z))
    conn = B.GetConnectivity()
    index = {obj.m_Uuid.AsString(): k for k, (_, obj) in enumerate(items)}
    parent = list(range(len(items)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for k, (_, obj) in enumerate(items):
        for other in conn.GetConnectedItems(obj):
            j = index.get(other.m_Uuid.AsString())
            if j is not None:
                parent[find(k)] = find(j)
    groups = defaultdict(list)
    for k, (name, _) in enumerate(items):
        groups[find(k)].append(name)
    result = []
    for g in sorted(groups.values(), key=len, reverse=True):
        result.append(dict(items=len(g), pads=sorted(n for n in g if '.' in n and not n.startswith('zone')),
                           zones=sorted(n for n in g if n.startswith('zone')),
                           tracks=sum(1 for n in g if n == 'track'), vias=sum(1 for n in g if n == 'via')))
    return result


def jumper_groups(B):
    out = {}
    for fp in B.GetFootprints():
        try:
            groups = [sorted(list(g)) for g in fp.JumperPadGroups()]
        except TypeError:
            groups = None
        out[fp.GetReference()] = groups
    return out


report = {}
for b in ('mainboard', 'ioboard'):
    B = pcbnew.LoadBoard(f'{work}/{b}/{b}.kicad_pcb')
    report[b] = dict(texts=texts(B), zones=zones(B),
                     islands={net: islands(B, net) for net in (['GND', '+5V'] if b == 'mainboard' else ['GND'])})
json.dump(report, open(out_path, 'w'))
