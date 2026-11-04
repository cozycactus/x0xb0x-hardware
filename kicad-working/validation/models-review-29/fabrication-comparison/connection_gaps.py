# SPDX-License-Identifier: CC0-1.0
"""Explain the DRC connection gaps from the original Eagle boards and the inter-board wiring."""
import json
import math
from pathlib import Path

import eagle_model
import eagle_islands

# Original jumper table (wiki.ladyada.net/x0x/jumpers, retained in
# visualization/blender-case-revision-7/harness-sources/primary-wiki-jumpers.md):
# J3-J7 join the mainboard and I/O board pin for pin.
CABLES = {'J3': 12, 'J4': 3, 'J5': 3, 'J6': 3, 'J7': 3}


def airwires(B):
    return [dict(signal=w['signal'], from_gerber_xy_mm=[round(v, 4) for v in w['p1']],
                 to_gerber_xy_mm=[round(v, 4) for v in w['p2']],
                 length_mm=round(math.dist(w['p1'], w['p2']), 4))
            for w in B.wires if w['layer'] == 19]


def island_of(islands, pad):
    for i, g in enumerate(islands):
        if pad in g['pads']:
            return i
    return None


def ground_tree(extract):
    """Islands of GND on both boards as graph nodes; cable conductors as edges."""
    nodes, edges = {}, []
    for b in ('mainboard', 'ioboard'):
        for i, g in enumerate(extract[b]['islands']['GND']):
            nodes[f'{b}#{i}'] = dict(items=g['items'], connector_pads=[p for p in g['pads'] if p.split('.')[0] in CABLES],
                                     zones=g['zones'])
    for j, n in CABLES.items():
        for pin in range(1, n + 1):
            a = island_of(extract['mainboard']['islands']['GND'], f'{j}.{pin}')
            c = island_of(extract['ioboard']['islands']['GND'], f'{j}.{pin}')
            if a is not None and c is not None:
                edges.append((f'mainboard#{a}', f'ioboard#{c}', f'{j}.{pin}'))
    # connected components and cycle count (graph cycles = E - V + C, parallel wires counted)
    parent = {k: k for k in nodes}

    def f(a):
        while parent[a] != a:
            a = parent[a]
        return a
    for a, c, _ in edges:
        parent[f(a)] = f(c)
    comps = len({f(k) for k in nodes})
    distinct = {tuple(sorted((a, c))) for a, c, _ in edges}
    return dict(nodes=nodes, cable_conductors=[dict(between=[a, c], conductor=n) for a, c, n in edges],
                connected_components=comps,
                independent_loops_between_islands=len(distinct) - len(nodes) + comps,
                note='Loops count distinct island pairs only; parallel conductors of one cable between the same two '
                     'islands are not counted as loops.')


def run(extract, eagle_dir, drc):
    out = {}
    for b in ('mainboard', 'ioboard'):
        B = eagle_model.Board(Path(eagle_dir) / f'{b}.brd')
        nets = ['GND', '+5V'] if b == 'mainboard' else ['GND']
        out[b] = dict(eagle_stored_airwires=airwires(B),
                      eagle_track_only_islands={n: [len(g) for g in eagle_islands.islands(B, n)] for n in nets},
                      eagle_islands_with_stored_airwires={n: [len(g) for g in eagle_islands.islands(B, n, True)] for n in nets},
                      kicad_islands={n: [dict(items=g['items'], zones=g['zones'], pad_count=len(g['pads']),
                                              connector_pads=[p for p in g['pads'] if p.split('.')[0] in CABLES])
                                         for g in extract[b]['islands'][n]] for n in nets},
                      kicad_drc_unconnected=[[i['description'] for i in u['items']] for u in drc[b]['unconnected_items']])
    out['system_ground'] = ground_tree(extract)
    # +5V: which Eagle copper island (tracks only, no part internals) holds each switch pad 1 and 2
    B = eagle_model.Board(Path(eagle_dir) / 'mainboard.brd')
    isl = eagle_islands.islands(B, '+5V')
    where = lambda pad: next((i for i, g in enumerate(isl) if pad in g), None)  # noqa: E731
    pads = {p['element'] + '.' + p['name'] for p in B.pads if p['signal'] == '+5V'}
    out['mainboard_plus5v'] = dict(
        eagle_track_only_island_sizes=[len(g) for g in isl],
        supply_entry=[dict(pad=p, island=where(p)) for p in ('J3.3', 'J3.4')],
        shift_register_vcc=[dict(pad=p, island=where(p)) for p in ('IC4.16', 'IC5.16', 'IC6.16', 'IC7.16', 'IC8.16')],
        switches_using_pads_1_and_2=[dict(switch=s, pad1_island=where(s + '.1'), pad2_island=where(s + '.2'))
                                     for s in sorted({p.split('.')[0] for p in pads if p.startswith('S')}, key=lambda r: int(r[1:]))
                                     if s + '.1' in pads and s + '.2' in pads],
        kicad_islands_with_jumper_groups=[g['items'] for g in extract['mainboard']['islands']['+5V']])
    return out
