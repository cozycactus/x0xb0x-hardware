#!/usr/bin/env python3
"""Write docs/fabrication-readiness.json from the revision-26 evidence files."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
FAB = HERE / 'fabrication-comparison'
load = lambda p: json.loads(p.read_text())  # noqa: E731
summary = load(REPO / 'kicad-working/validation/working-validation-summary-revision-26.json')
install = load(HERE / 'installation-audit.json')
gerbers = load(FAB / 'gerber-comparison.json')
gaps = load(FAB / 'connection-gap-review.json')
previous = load(REPO / 'docs/fabrication-readiness.json')
assert previous['KiCad_revision'] in (25, 26)
before = {d['item']: d for d in previous['differences']}


def diffs(board, layer, kind=None):
    return [d for d in gerbers['boards'][board][layer]['differences'] if kind is None or d['type'] == kind]


texts = {b: {k: gerbers['boards'][b][k]['texts'] for k in ('F_Silkscreen', 'B_Silkscreen')} for b in gerbers['boards']}
assert not diffs('mainboard', 'F_Cu pads/vias') and not diffs('mainboard', 'B_Cu pads/vias')
assert all(t['moved_count'] == 0 and not t['missing_in_kicad'] for b in texts.values() for t in b.values())
labels = install['name_labels']
record = dict(
    schema=1, snapshot_date='2026-10-17', KiCad_revision=26,
    validation_summary='kicad-working/validation/working-validation-summary-revision-26.json',
    report='kicad-working/validation/models-review-26/README.md',
    inputs=gerbers['inputs'],
    verdict=('Drills, copper tracks and arcs, vias, every pad, pour outlines and connectivity, paste, all silkscreen '
             'geometry and every name label (position and printed name) reproduce the original Eagle 4.13 boards. '
             'No difference blocks ordering; the mask and tenting differences listed below await the owner\'s decision.'),
    layers=summary['fabrication_comparison']['boards'],
    differences=[
        dict(item='SIP9 pad length', layers=['F_Cu', 'B_Cu', 'F_Mask', 'B_Mask'], board='mainboard',
             references=install['sip9']['references'], count=install['sip9']['pads'], eagle_mm=[1.408, 2.816],
             kicad_mm_before=[1.4, 2.032], kicad_mm=[1.408, 2.816],
             cause='Importer elongated the 1.016 mm library diameter instead of the restrung 1.408 mm width.',
             locations=before['SIP9 pad length']['locations'], changed=True, revision=26),
        dict(before['NPTH stop-mask opening'], locations=[d['gerber_xy_mm'] for d in diffs('mainboard', 'F_Mask')
                                                          if d['what'].startswith('hole')]),
        dict(before['SMD mask corner radius'], count=len(diffs('ioboard', 'B_Mask'))),
        before['Via tenting'],
        dict(item='Name label positions', layers=['F_Silkscreen', 'B_Silkscreen'],
             restored={b: labels[b]['records'] for b in labels}, moved_before=before['Name label positions'].get('moved_before',
                                                                   before['Name label positions']['moved']),
             moved=0, evidence=('Eagle smashed name records (position, rotation, layer; size doubled from the stored half '
                                'size). The production I/O photograph matches (J3, J4, R164; J3 at the 1.27 mm height '
                                'of its package texts).'), changed=True, revision=26),
        dict(item='Renamed references', layers=['F_Silkscreen'], renamed=before['Renamed references']['renamed'],
             kicad=('Reference unchanged (trailing 0 kept) and hidden; a footprint text prints the Eagle name at the '
                    'smashed position.'), changed=True, revision=26),
        before['Outline details']],
    connection_gaps=previous['connection_gaps'],
    fresh_checks=dict(ERC_errors=summary['fresh_ERC_errors'], ERC_warnings=summary['fresh_ERC_warnings'],
                      DRC_comparison=summary['fresh_DRC_comparison_to_previous']),
    unchanged=['drills', 'tracks', 'vias', 'nets', 'zones', 'footprint placement', '3D models', 'schematics',
               'original Eagle files', 'Blender scene'],
    limitations=summary['limitations'][-7:],
    physical_fit_qualified=False)
assert record['connection_gaps']['eagle_stored_airwires'] == {b: gaps[b]['eagle_stored_airwires'] for b in ('mainboard', 'ioboard')}
(REPO / 'docs/fabrication-readiness.json').write_text(json.dumps(record, indent=1) + '\n')
print(json.dumps(dict(passed=True, sha256=hashlib.sha256((REPO / 'docs/fabrication-readiness.json').read_bytes()).hexdigest())))
