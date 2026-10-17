#!/usr/bin/env python3
"""Write docs/fabrication-readiness.json from the revision-27 evidence files."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
FAB = HERE / 'fabrication-comparison'
load = lambda p: json.loads(p.read_text())  # noqa: E731
summary = load(REPO / 'kicad-working/validation/working-validation-summary-revision-27.json')
install = load(HERE / 'installation-audit.json')
gerbers = load(FAB / 'gerber-comparison.json')
gaps = load(FAB / 'connection-gap-review.json')
previous = load(REPO / 'docs/fabrication-readiness.json')
assert previous['KiCad_revision'] in (26, 27)
before = {d['item']: d for d in previous['differences']}
assert not [d for k in ('F_Cu pads/vias', 'B_Cu pads/vias') for b in gerbers['boards'] for d in gerbers['boards'][b][k]['differences']]
checks = install['checks']
record = dict(
    schema=1, snapshot_date='2026-10-17', KiCad_revision=27,
    validation_summary='kicad-working/validation/working-validation-summary-revision-27.json',
    report='kicad-working/validation/models-review-27/README.md',
    packages='kicad-working/fabrication/revision-27/README.md',
    inputs=gerbers['inputs'],
    verdict=('Drills, copper tracks and arcs, vias, every pad, pour outlines and connectivity, paste, all silkscreen '
             'geometry and every name label reproduce the original Eagle 4.13 boards; the copper as saved and plotted '
             'passes DRC and each board has a single outline. No difference blocks ordering; the mask and tenting '
             'differences listed below are fab-note choices for the owner.'),
    layers=summary['fabrication_comparison']['boards'],
    differences=[
        before['SIP9 pad length'],
        dict(item='Saved pour fill', layers=['F_Cu', 'F_Mask'], board='mainboard',
             zones=[dict(priority=z['priority'], uuid=z['uuid']) for z in install['files'][0]['zones']],
             saved_copper_DRC_before=checks['mainboard_saved_copper_violations_before'],
             saved_copper_DRC_after=checks['mainboard_saved_copper_violations_after'],
             locations=[v['items'][0][1] for v in install['mainboard_saved_copper_violations_before']
                        if v['type'] == 'clearance'],
             cause=('Revision 26 lengthened the SIP9 pads without refilling the pours; its DRC refilled the zones '
                    'before checking, the plotter uses the saved fill.'),
             changed=True, revision=27),
        before['NPTH stop-mask opening'], before['SMD mask corner radius'], before['Via tenting'],
        before['Name label positions'], before['Renamed references'],
        dict(item='Outline details', board_notes=dict(
            mainboard=before['Outline details']['board_notes']['mainboard'],
            ioboard=('The rear-plate datum (four Eagle Dimension lines forming a 222.25 x 1.651 mm rectangle 0.508 mm '
                     'behind the rear edge, and the detached line at y -2.921) is on Dwgs.User; Edge.Cuts holds the '
                     f'single {checks["ioboard_board_outline_mm"][0]} x {checks["ioboard_board_outline_mm"][1]} mm '
                     'board outline. Until revision 26 the four lines were on Edge.Cuts as a second closed outline.')),
             changed=True, revision=27)],
    connection_gaps=previous['connection_gaps'],
    fresh_checks=dict(ERC_errors=summary['fresh_ERC_errors'], ERC_warnings=summary['fresh_ERC_warnings'],
                      DRC_without_zone_refill=True, DRC_comparison=summary['fresh_DRC_comparison_to_previous']),
    unchanged=['drills', 'tracks', 'vias', 'pads', 'nets', 'zone outlines and settings', 'footprint placement',
               '3D models', 'schematics', 'original Eagle files', 'Blender scene'],
    limitations=summary['limitations'][-8:],
    physical_fit_qualified=False)
assert record['connection_gaps']['eagle_stored_airwires'] == {b: gaps[b]['eagle_stored_airwires'] for b in ('mainboard', 'ioboard')}
(REPO / 'docs/fabrication-readiness.json').write_text(json.dumps(record, indent=1) + '\n')
print(json.dumps(dict(passed=True, sha256=hashlib.sha256((REPO / 'docs/fabrication-readiness.json').read_bytes()).hexdigest())))
