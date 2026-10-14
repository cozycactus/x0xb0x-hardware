"""Extract original DXF model-space manufacturing lines in mm.

The design DXFs contain model-space and duplicate paper-space geometry;
only model-space continuous lines and circles are manufacturing features.
Construction centrelines and dimensions are retained only in raw source.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json

BASE = Path(__file__).resolve().parent.parent

def parse_dxf(file):
    lines = file.read_text(encoding='cp1252').splitlines()
    pairs = [(int(lines[i]), lines[i + 1].strip())
             for i in range(0, len(lines) - 1, 2)]
    entities = []
    in_entities = False
    for i, (code, value) in enumerate(pairs):
        if code == 0 and value == 'SECTION':
            in_entities = pairs[i + 1][1] == 'ENTITIES'
            continue
        if code == 0 and value == 'ENDSEC':
            in_entities = False
        if in_entities and code == 0:
            entities.append((value, []))
        elif in_entities and entities:
            entities[-1][1].append((code, value))
    model = [(typ, dict(p)) for typ, p in entities
             if dict(p).get(67, '0') != '1']
    circles = []
    segments = []
    for typ, d in model:
        if typ == 'CIRCLE':
            circles.append({'source_handle': d[5],
                            'center_source_in': [float(d[10]), float(d[20])],
                            'radius_in': float(d[40])})
        if typ == 'LINE' and d.get(6) == 'Continuous':
            segments.append({'source_handle': d[5],
                             'start_in': [float(d[10]), float(d[20])],
                             'end_in': [float(d[11]), float(d[21])]})
    # Connected groups are the closed physical profile and cutouts. They
    # have disjoint endpoints; the long dashed centrelines were excluded.
    key = lambda p: tuple(round(v, 8) for v in p)
    remaining = list(segments)
    loops = []
    open_lines = []
    while remaining:
        s = remaining.pop(0)
        points = [s['start_in'], s['end_in']]
        handles = [s['source_handle']]
        while key(points[-1]) != key(points[0]):
            for i, candidate in enumerate(remaining):
                a, b = candidate['start_in'], candidate['end_in']
                if key(a) == key(points[-1]):
                    points.append(b)
                elif key(b) == key(points[-1]):
                    points.append(a)
                else:
                    continue
                handles.append(candidate['source_handle'])
                remaining.pop(i)
                break
            else:
                open_lines.append({'source_handles': handles, 'points_source_in': points})
                break
        if key(points[-1]) == key(points[0]):
            loops.append({'source_handles': handles, 'points_source_in': points[:-1]})
    def area(loop):
        p = loop['points_source_in']
        return abs(sum(a[0] * b[1] - b[0] * a[1]
                       for a, b in zip(p, p[1:] + p[:1])) / 2)
    loops.sort(key=area, reverse=True)
    outer = loops[0]
    origin = [min(p[i] for p in outer['points_source_in']) for i in [0, 1]]
    def mm(p):
        return [round((p[i] - origin[i]) * 25.4, 8) for i in [0, 1]]
    for c in circles:
        c['center_mm'] = mm(c['center_source_in'])
        c['radius_mm'] = round(c['radius_in'] * 25.4, 8)
    for loop in open_lines:
        loop['points_mm'] = [mm(p) for p in loop['points_source_in']]
        loop['note'] = 'Open source line; retained as drawing data, not used as a zero-width physical cut.'
    for loop in loops:
        loop['points_mm'] = [mm(p) for p in loop['points_source_in']]
        loop['bounds_mm'] = [[min(p[i] for p in loop['points_mm']) for i in [0, 1]],
                             [max(p[i] for p in loop['points_mm']) for i in [0, 1]]]
    return {'source_filename': file.name,
            'source_sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
            'source_units': 'inches (explicit original drawing annotation)',
            'mm_per_source_unit': 25.4,
            'local_frame': 'X right, Y up on original drawing; origin lower-left outer profile corner',
            'origin_source_in': origin,
            'geometry_filter': 'ENTITIES model space, all CIRCLE and Continuous LINE only; duplicate paper space and construction centrelines excluded',
            'outer_profile': outer,
            'rectangular_cutouts': loops[1:],
            'open_source_lines': open_lines,
            'circles': circles,
            'counts': {'circles':len(circles),'rectangular_cutouts':len(loops)-1},
            'thickness_mm': 0.062 * 25.4,
            'silkscreen_text': [],
            'silkscreen_note': 'The source DXF contains manufacturing annotations but no control legends or silkscreen artwork.'}

out = {}
for name, filename in [('mainpanel', 'x0xbox_mainpanel_march2.dxf'),
                       ('iopanel', 'x0xb0x_iopanel_march2.dxf')]:
    out[name] = parse_dxf(BASE / 'source' / filename)
    print(name, out[name]['counts'], out[name]['outer_profile']['bounds_mm'])
(BASE / 'panels' / 'original-panels.json').write_text(json.dumps(out, indent=2) + '\n')
