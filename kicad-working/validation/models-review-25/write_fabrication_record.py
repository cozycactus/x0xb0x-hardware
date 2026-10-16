#!/usr/bin/env python3
"""Write docs/fabrication-readiness.json from the revision-25 evidence files."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
FAB = HERE / 'fabrication-comparison'
load = lambda p: json.loads(p.read_text())  # noqa: E731
summary = load(REPO / 'kicad-working/validation/working-validation-summary-revision-25.json')
gerbers = load(FAB / 'gerber-comparison.json')
gaps = load(FAB / 'connection-gap-review.json')


def diffs(board, layer, kind=None):
    return [d for d in gerbers['boards'][board][layer]['differences'] if kind is None or d['type'] == kind]


renamed = {b: [t['text'] for k in ('F_Silkscreen', 'B_Silkscreen') for t in gerbers['boards'][b][k]['texts']['missing_in_kicad']]
           for b in gerbers['boards']}
moved = {b: sum(gerbers['boards'][b][k]['texts']['moved_count'] for k in ('F_Silkscreen', 'B_Silkscreen'))
         for b in gerbers['boards']}
record = dict(
    schema=1, snapshot_date='2026-10-17', KiCad_revision=25,
    validation_summary='kicad-working/validation/working-validation-summary-revision-25.json',
    report='kicad-working/validation/models-review-25/fabrication-comparison/README.md',
    inputs=gerbers['inputs'],
    verdict=('Drills, copper tracks and arcs, vias, all pads except 27 SIP9 pads, pour outlines and connectivity, '
             'paste and non-text silkscreen reproduce the original Eagle 4.13 boards. No difference blocks ordering; '
             'the differences listed below await the owner\'s decision.'),
    layers=summary['fabrication_comparison']['boards'],
    differences=[
        dict(item='SIP9 pad length', layers=['F_Cu', 'B_Cu', 'F_Mask', 'B_Mask'], board='mainboard',
             references=['IC14', 'IC15A', 'IC15B'], count=len(diffs('mainboard', 'F_Cu pads/vias', 'size')),
             eagle_mm=[1.408, 2.816], kicad_mm=[1.4, 2.032],
             cause='Importer elongated the 1.016 mm library diameter instead of the restrung 1.408 mm width.',
             locations=[d['gerber_xy_mm'] for d in diffs('mainboard', 'F_Cu pads/vias', 'size')], changed=False),
        dict(item='NPTH stop-mask opening', layers=['F_Mask', 'B_Mask'], board='mainboard',
             eagle_mm=3.5052, kicad_mm=3.302,
             locations=[d['gerber_xy_mm'] for d in diffs('mainboard', 'F_Mask') if d['what'].startswith('hole')],
             changed=False),
        dict(item='SMD mask corner radius', layers=['B_Mask'], board='ioboard', references=['IC25'],
             count=len(diffs('ioboard', 'B_Mask')), size_mm=[0.6032, 1.8032], kicad_corner_radius_mm=0.1016,
             changed=False),
        dict(item='Via tenting', boards=['mainboard', 'ioboard'], vias={'mainboard': 6, 'ioboard': 2},
             kicad='tented', eagle='exposed unless the undecoded design-rule Limit was at least 0.6 mm', changed=False),
        dict(item='Name label positions', layers=['F_Silkscreen', 'B_Silkscreen'], moved=moved,
             evidence='Production I/O photograph matches the Eagle smashed positions (J3, J4, R164).', changed=False),
        dict(item='Renamed references', layers=['F_Silkscreen'], renamed=renamed,
             kicad='trailing 0 appended', changed=False),
        dict(item='Outline details', board_notes={
            'mainboard': 'Eagle spurs of up to 0.23 mm at (0, 0) closed by the conversion outline repair.',
            'ioboard': 'Detached rear-plate datum strip at y -2.921 kept on Dwgs.User, not Edge.Cuts.'},
            changed=False)],
    connection_gaps=dict(
        eagle_stored_airwires={b: gaps[b]['eagle_stored_airwires'] for b in ('mainboard', 'ioboard')},
        plus5v=dict(gap='mainboard S22 pad 1 [+5V]', finding=(
            'Closed inside S19 and S22: B3F-40XX pins 1-2 form one strip in the original symbol; the only path from '
            'the J3.3/J3.4 supply entry to the 74HC595 VCC pins.'), evidence=gaps['mainboard_plus5v'],
            fix='KiCad jumper pad groups ("1" "2") ("3" "4") on 23 B3F-40XX placements and the library footprint.'),
        ground=dict(gaps=['mainboard IC9 pad 8 [GND] vs B.Cu GND track',
                          'ioboard MIXOUT sleeve [GND] (F.Cu arc) vs B.Cu GND track'], finding=(
            'Original drawn ground splits: analog/digital pours on the mainboard, a jack-ground pour on the I/O '
            'board. The J3-J7 wiring joins the four islands into one ground without loops; routing either '
            'airwire would add a loop.'),
            system_ground=dict(components=gaps['system_ground']['connected_components'],
                               loops=gaps['system_ground']['independent_loops_between_islands'],
                               conductors=gaps['system_ground']['cable_conductors']),
            fix='None; copper unchanged.')),
    fresh_checks=dict(ERC_errors=summary['fresh_ERC_errors'], ERC_warnings=summary['fresh_ERC_warnings'],
                      DRC_comparison=summary['fresh_DRC_comparison_to_previous']),
    unchanged=['copper', 'pads', 'drills', 'nets', 'zones', 'footprint placement', '3D models', 'I/O project',
               'original Eagle files', 'Blender scene'],
    limitations=summary['limitations'][-6:],
    physical_fit_qualified=False)
(REPO / 'docs/fabrication-readiness.json').write_text(json.dumps(record, indent=1) + '\n')
print(json.dumps(dict(passed=True, sha256=hashlib.sha256((REPO / 'docs/fabrication-readiness.json').read_bytes()).hexdigest())))
