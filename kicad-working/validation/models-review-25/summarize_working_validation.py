#!/usr/bin/env python3
"""Record revision-25 file preservation, fresh ERC/DRC and the Eagle fabrication comparison."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
FAB = HERE / 'fabrication-comparison'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731
load = lambda p: json.loads(p.read_text())  # noqa: E731
old = load(WORK / 'validation/working-validation-summary-revision-24.json')
install = load(HERE / 'installation-audit.json')
functions = load(HERE / 'current-function-verification.json')
dependencies = load(HERE / 'local-dependencies.json')
gerbers = load(FAB / 'gerber-comparison.json')
gaps = load(FAB / 'connection-gap-review.json')
decode = load(FAB / 'source-decode-crosscheck.json')
assert install['passed'] and functions['passed'] and dependencies['passed']
assert all(b['passed'] for b in decode['boards'].values())
outputs = {name: sha(WORK / name) for name in old['outputs']}
changed = sorted(n for n in outputs if outputs[n] != old['outputs'][n])
assert changed == install['changed_previous_core_files'] and not install['new_core_files']
assert len(outputs) == 361
assert gerbers['inputs']['kicad_pcb_sha256'] == {b: outputs[f'{b}/{b}.kicad_pcb'] for b in ('mainboard', 'ioboard')}
baselines = {b: WORK / f'validation/models-review-24/{b}-drc.json' for b in ('mainboard', 'ioboard')}


def unconnected_nets(items):
    """Net of each unconnected pair; KiCad names varying representative pads/tracks of the same two islands."""
    return sorted(sorted({i['description'].split('[', 1)[1].split(']', 1)[0] for i in u['items']}) for u in items)


# The only intended DRC change: the mainboard +5V pair closed by the B3F strips (S19/S22 pads 1-2).
expected_nets = {'mainboard': [['GND']], 'ioboard': [['GND']]}
projects, comparisons, erc = {}, {}, {}
keys = ('erc_errors', 'erc_warnings', 'drc_violation_errors', 'drc_violation_warnings',
        'separate_schematic_parity_warnings', 'erc_ignored_checks', 'drc_ignored_checks',
        'erc_exclusions', 'drc_exclusions', 'model_instances')
for board in ('mainboard', 'ioboard'):
    fresh = load(HERE / f'{board}-drc.json')
    base = load(baselines[board])
    comparisons[board] = {k: fresh[k] == base[k] for k in ('violations', 'schematic_parity', 'ignored_checks')}
    comparisons[board]['unconnected_items_raw'] = fresh['unconnected_items'] == base['unconnected_items']
    comparisons[board]['unconnected_nets_previous'] = unconnected_nets(base['unconnected_items'])
    comparisons[board]['unconnected_nets_fresh'] = unconnected_nets(fresh['unconnected_items'])
    assert all(comparisons[board][k] for k in ('violations', 'schematic_parity', 'ignored_checks')), board
    assert comparisons[board]['unconnected_nets_fresh'] == expected_nets[board], comparisons[board]
    violations = [v for sheet in load(HERE / f'{board}-erc.json')['sheets'] for v in sheet['violations']]
    erc[board] = Counter(v['severity'] for v in violations)
    assert not violations
    projects[board] = {k: old['projects'][board][k] for k in keys}
    projects[board]['separate_unconnected_errors'] = len(fresh['unconnected_items'])
    projects[board]['remaining_connections'] = fresh['unconnected_items']
    projects[board].update(electrical_inputs_and_rules_preserved=True, fresh_native_ERC_DRC_this_revision=True,
                           electrical_evidence_basis=(
                               'Fresh KiCad10.0.7 reports for this revision; DRC violations, schematic parity and '
                               'ignored checks exactly equal the previous fresh report. ERC0 under retained project rules.'))
projects['mainboard']['unconnected_track_end_note'] = (
    'The +5V pair (S22 pad 1) is closed by the B3F-40XX jumper pad groups: the original switch strips 1-2 '
    'bridge S19 and S22, as the original Eagle symbol draws them. The remaining GND pair is the original '
    'analog/digital ground split (IC9 pad 8 side vs the digital B.Cu track), an unrouted airwire in the '
    'original Eagle board, joined through the J3-J7 board-to-board wiring. KiCad names varying representative '
    'pads or tracks of the same two islands between runs. Copper is unchanged.')
projects['ioboard']['unconnected_track_end_note'] = (
    'The GND pair (MIXOUT0 sleeve island vs the main ground track) is the original jack-ground island, an '
    'unrouted airwire in the original Eagle board, returned through J7 pin 2 to the mainboard analog ground. '
    'KiCad names varying representative pads or tracks of the same two islands between runs.')


def layer_summary(res):
    out = {}
    for k, v in res.items():
        if k == 'drills':
            out[k] = dict(eagle_plated=v['eagle_plated'], kicad_plated=v['kicad_plated'],
                          eagle_nonplated=v['eagle_nonplated'], kicad_nonplated=v['kicad_nonplated'],
                          unmatched=len(v['unmatched_eagle']) + len(v['unmatched_kicad']),
                          size_differences=len(v['size_differences']), max_position_error_mm=v['max_position_error_mm'])
        elif 'Silkscreen' in k:
            t = v['texts']
            out[k] = dict(lines_arcs=[v['lines_arcs']['matched'], v['lines_arcs']['eagle']],
                          circles=[v['circles']['matched'], v['circles']['eagle']],
                          filled_shapes=[v['filled_shapes']['matched'], v['filled_shapes']['expected']],
                          strokes_outside_texts=len(v['strokes_not_inside_any_text']),
                          texts=dict(eagle=t['eagle'], same_anchor=t['same_anchor'], moved=t['moved_count'],
                                     renamed=len(t['missing_in_kicad'])))
        elif 'matched' in v:
            out[k] = dict(matched=v['matched'], expected=v['expected'],
                          differences=dict(Counter(d['type'] for d in v['differences'])))
    return out


reports = ['installation-audit.json', 'native-run-records.json', 'local-dependencies.json',
           'current-function-verification.json', 'mainboard-drc.json', 'mainboard-erc.json', 'ioboard-drc.json',
           'ioboard-erc.json', 'fabrication-comparison/gerber-comparison.json',
           'fabrication-comparison/connection-gap-review.json', 'fabrication-comparison/source-decode-crosscheck.json']
out = dict(revision='Working revision25: fabrication comparison with the original Eagle boards; B3F switch strips declared',
           created_utc=datetime.now(timezone.utc).isoformat(), native_kicad_version='10.0.7',
           projects=projects, outputs=dict(sorted(outputs.items())),
           model_references=491, updated_model_references=[],
           updated_footprint_references=['mainboard:' + r for r in install['references']],
           previous_core_files=len(old['outputs']), changed_previous_core_files=changed,
           new_core_files=install['new_core_files'],
           fresh_DRC_comparison_to_previous=comparisons,
           fresh_ERC_errors={b: c.get('error', 0) for b, c in erc.items()},
           fresh_ERC_warnings={b: c.get('warning', 0) for b, c in erc.items()},
           lead_presence=old['lead_presence'], nominal_fit_findings=old['nominal_fit_findings'],
           model_evidence_basis='No model path, model transform or footprint placement changed; the revision-24 native '
                                'lead audit and nominal-fit findings apply unchanged.',
           fabrication_comparison=dict(method=('KiCad 10.0.7 Gerber/Excellon output compared object by object with the '
                                               'original Eagle 4.13 board geometry, read from the staging XML of the binary '
                                               'files and evaluated with Eagle 4.13 CAM rules (restring, elongation, stop frame); '
                                               'the XML was cross-checked against an independent read of original-eagle/.'),
                                       boards={b: layer_summary(r) for b, r in gerbers['boards'].items()},
                                       connection_gaps=dict(
                                           eagle_airwires={b: gaps[b]['eagle_stored_airwires'] for b in ('mainboard', 'ioboard')},
                                           system_ground_components=gaps['system_ground']['connected_components'],
                                           system_ground_loops=gaps['system_ground']['independent_loops_between_islands'],
                                           mainboard_plus5v=gaps['mainboard_plus5v'])),
           reports={n: sha(HERE / n) for n in reports},
           baseline_summary='validation/working-validation-summary-revision-24.json',
           baseline_summary_sha256=sha(WORK / 'validation/working-validation-summary-revision-24.json'),
           scope=('Jumper pad groups ("1" "2") and ("3" "4") on the 23 B3F-40XX switch placements and the project '
                  'library footprint; footprint metadata only. Copper, pads, drills, nets, zones, footprint poses, '
                  'models and the I/O project are unchanged. Adds the Gerber/drill comparison with the original Eagle '
                  'boards and the review of the three recorded connection gaps.'),
           limitations=old['limitations'][:-2] + [
               'Recorded DRC warnings (silkscreen overlaps and edge clearance, dangling track stubs carried from the '
               'Eagle source) and schematic-parity warnings remain unchanged.',
               'Two GND connection items remain by design: the original analog/digital mainboard ground split and the '
               'I/O jack-ground island, both unrouted airwires in the original Eagle boards and joined through the '
               'J3-J7 board-to-board wiring.',
               'The B3F-40XX internal strips (1-2, 3-4) follow the original Eagle symbol and the design\'s use of them; '
               'the Omron drawing itself was not retrieved.',
               'Gerber differences from the original Eagle CAM semantics are recorded, not corrected: SIP9 pad length, '
               'reference-label positions and names, NPTH stop frame, SMD mask corner radius and via tenting.',
               'Eagle polygon pours are compared by outline, settings and connectivity; Eagle 4.13 pour fill geometry '
               '(thermal spokes, isolation) was not regenerated.',
               'Nominal model checks and the Gerber comparison do not establish physical assembly; fabrication '
               'equivalence is to the original Eagle data, not to an inspected production board.'],
           physical_fit_qualified=False)
for name in ['working-validation-summary-revision-25.json', 'working-validation-summary.json']:
    (WORK / 'validation' / name).write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(dict(passed=True, core_files=len(outputs), changed_previous_core_files=changed,
                      fresh_ERC_errors=out['fresh_ERC_errors'],
                      unconnected={b: comparisons[b]['unconnected_nets_fresh'] for b in comparisons}), indent=2))
