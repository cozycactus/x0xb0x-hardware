# SPDX-License-Identifier: CC0-1.0
"""Check that the staging XML read by eagle_model.py carries the original binary's geometry.

Uses the repository's independent binary reader (kicad-import/validation/inspect_eagle_source.py)
on original-eagle/*.brd and compares raw 0.1 um record fields with the XML.
"""
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
import sys


def run(repo, eagle_xml_dir, parser_source):
    sys.path.insert(0, str(repo / 'kicad-import/validation'))
    import inspect_eagle_source as ies
    spec = ies.load_spec(Path(parser_source))
    out = {}
    for b in ('mainboard', 'ioboard'):
        e = ies.Eagle(repo / 'original-eagle' / f'{b}.brd', spec)
        X = ET.parse(Path(eagle_xml_dir) / f'{b}.brd').getroot()
        u = lambda v: round(float(v) * 10000)  # noqa: E731

        def raw_or_arc(w):
            # arc-type records keep their end points in the arc fields
            straight = (int(w.get('linetype_0_x1')), int(w.get('linetype_0_y1')),
                        int(w.get('linetype_0_x2')), int(w.get('linetype_0_y2')))
            xml = (u(w.get('x1')), u(w.get('y1')), u(w.get('x2')), u(w.get('y2')))
            arc = (int(w.get('arc_x1')), int(w.get('arc_y1')), int(w.get('arc_x2')), int(w.get('arc_y2')))
            return xml in (straight, arc)
        bw = Counter((r['attrs']['linetype_0_x1'], r['attrs']['linetype_0_y1'], r['attrs']['linetype_0_x2'],
                      r['attrs']['linetype_0_y2'], r['attrs'].get('half_width'))
                     for r in e.records if r['kind'] == 'wire' and 'linetype_0_x1' in r['attrs'])
        xw = Counter((int(w.get('linetype_0_x1')), int(w.get('linetype_0_y1')), int(w.get('linetype_0_x2')),
                      int(w.get('linetype_0_y2')), int(w.get('half_width'))) for w in X.iter('wire'))
        rec = lambda kind, keys: Counter(tuple(r['attrs'].get(k) for k in keys) for r in e.records if r['kind'] == kind)  # noqa: E731
        xml = lambda tag, keys: Counter(tuple(u(v.get(k)) if k in 'xy' else v.get(k) for k in keys) for v in X.iter(tag))  # noqa: E731
        res = dict(binary_wire_like_records=sum(bw.values()), xml_wires=sum(xw.values()),
                   polygon_vertex_records=sum(bw.values()) - sum(xw.values()),
                   wires_are_binary_records=not (xw - bw),
                   wire_coordinates_equal_binary_fields=all(raw_or_arc(w) for w in X.iter('wire')),
                   vias_equal=rec('via', ('x', 'y')) == xml('via', ('x', 'y')),
                   package_pads_equal=rec('pad', ('x', 'y', 'name')) == xml('pad', ('x', 'y', 'name')),
                   smds_equal=rec('smd', ('x', 'y')) == xml('smd', ('x', 'y')),
                   holes_equal=rec('hole', ('x', 'y')) == xml('hole', ('x', 'y')),
                   element_positions_equal=rec('element', ('x', 'y')) == xml('element', ('x', 'y')),
                   counts=dict(vias=sum(rec('via', ('x',)).values()), package_pads=sum(rec('pad', ('x',)).values()),
                               smds=sum(rec('smd', ('x',)).values()), holes=sum(rec('hole', ('x',)).values()),
                               elements=sum(rec('element', ('x',)).values())))
        res['passed'] = all(v for k, v in res.items() if k.endswith(('equal', 'records')) or k.startswith('wire'))
        out[b] = res
    return out
