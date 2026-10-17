#!/usr/bin/env python3
"""Record revision-27 file preservation, fresh ERC/DRC (saved copper, no refill) and the Eagle fabrication comparison."""
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
old = load(WORK / 'validation/working-validation-summary-revision-26.json')
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
baselines = {b: WORK / f'validation/models-review-26/{b}-drc.json' for b in ('mainboard', 'ioboard')}
ERROR_LIMIT = 199  # KiCad 10 drc_engine.cpp reports at most 199 items of one violation type


def unconnected_nets(items):
    """Net of each unconnected pair; KiCad names varying representative pads/tracks of the same two islands."""
    return sorted(sorted({i['description'].split('[', 1)[1].split(']', 1)[0] for i in u['items']}) for u in items)


def located(v):
    return (v['type'], v['severity'],
            tuple(sorted((i['description'], round(i['pos']['x'], 4), round(i['pos']['y'], 4)) for i in v['items'])))


def described(v):
    return (v['type'], v['severity'], tuple(sorted(i['description'] for i in v['items'])))


# Revision 26's DRC refilled the zones; revision 27's checks the saved copper, whose fill now equals that refill.
# Intended DRC change: I/O silkscreen-to-edge warnings against the removed datum outline. Every other violation must
# be identical item by item, including position; parity, ignored checks and the two GND splits are unchanged.
expected_nets = {'mainboard': [['GND']], 'ioboard': [['GND']]}
projects, comparisons, erc = {}, {}, {}
keys = ('erc_errors', 'erc_warnings', 'separate_schematic_parity_warnings', 'erc_ignored_checks', 'drc_ignored_checks',
        'erc_exclusions', 'drc_exclusions', 'model_instances')
for board in ('mainboard', 'ioboard'):
    fresh = load(HERE / f'{board}-drc.json')
    base = load(baselines[board])
    silk = lambda v: v['type'].startswith('silk')  # noqa: E731
    other_base = Counter(located(v) for v in base['violations'] if not silk(v))
    other_fresh = Counter(located(v) for v in fresh['violations'] if not silk(v))
    by_type = lambda d: dict(sorted(Counter(v['type'] for v in d['violations'] if silk(v)).items()))  # noqa: E731
    types = set(by_type(base)) | set(by_type(fresh))
    complete = {t for t in types if max(by_type(base).get(t, 0), by_type(fresh).get(t, 0)) < ERROR_LIMIT}
    added = Counter(described(v) for v in fresh['violations'] if v['type'] in complete) - \
        Counter(described(v) for v in base['violations'] if v['type'] in complete)
    comparisons[board] = dict(
        non_silkscreen_violations_identical=other_base == other_fresh, non_silkscreen_violations=sum(other_fresh.values()),
        schematic_parity=fresh['schematic_parity'] == base['schematic_parity'],
        ignored_checks=fresh['ignored_checks'] == base['ignored_checks'],
        silkscreen_warnings_previous=by_type(base), silkscreen_warnings_fresh=by_type(fresh),
        silkscreen_types_truncated_at_report_limit=sorted(types - complete),
        silkscreen_pairs_new_in_complete_types=[dict(type=k[0], items=list(k[2])) for k in sorted(added.elements())],
        unconnected_items_raw=fresh['unconnected_items'] == base['unconnected_items'],
        unconnected_nets_previous=unconnected_nets(base['unconnected_items']),
        unconnected_nets_fresh=unconnected_nets(fresh['unconnected_items']))
    c = comparisons[board]
    assert c['non_silkscreen_violations_identical'] and c['schematic_parity'] and c['ignored_checks'], board
    assert c['unconnected_nets_fresh'] == expected_nets[board], c
    assert all(n <= c['silkscreen_warnings_previous'].get(t, 0) for t, n in c['silkscreen_warnings_fresh'].items()), c
    violations = [v for sheet in load(HERE / f'{board}-erc.json')['sheets'] for v in sheet['violations']]
    erc[board] = Counter(v['severity'] for v in violations)
    assert not violations
    severities = Counter(v['severity'] for v in fresh['violations'])
    projects[board] = {k: old['projects'][board][k] for k in keys}
    projects[board].update(drc_violation_errors=severities.get('error', 0),
                           drc_violation_warnings=severities.get('warning', 0))
    projects[board]['separate_unconnected_errors'] = len(fresh['unconnected_items'])
    projects[board]['remaining_connections'] = fresh['unconnected_items']
    projects[board]['unconnected_track_end_note'] = old['projects'][board]['unconnected_track_end_note']
    projects[board].update(electrical_inputs_and_rules_preserved=True, fresh_native_ERC_DRC_this_revision=True,
                           electrical_evidence_basis=(
                               'Fresh KiCad10.0.7 reports for this revision; DRC checks the copper as saved (no zone refill). '
                               'Every non-silkscreen DRC violation, schematic parity and ignored checks exactly equal the '
                               'previous fresh report, which refilled the zones. I/O silkscreen-to-edge warnings decrease with '
                               'the datum outline removed. ERC0 under retained project rules.'))


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


boards = {b: layer_summary(r) for b, r in gerbers['boards'].items()}
for b in boards:
    for k in ('F_Silkscreen', 'B_Silkscreen'):
        t = boards[b][k]['texts']
        assert t['moved'] == 0 and t['renamed'] == 0 and t['same_anchor'] == t['eagle'], (b, k)
for k in ('F_Cu pads/vias', 'B_Cu pads/vias'):
    assert boards['mainboard'][k]['matched'] == boards['mainboard'][k]['expected'], k
edge = gerbers['boards']['ioboard']['Edge_Cuts']['differences']
datum = sorted([d['gerber_xy_mm'], d['p2']] for d in edge if d['type'] == 'missing_in_kicad' and d['width'] == 0.0254)
assert len(datum) == 5 and gerbers['boards']['ioboard']['Edge_Cuts']['kicad_draws'] == 4, edge
assert all(install['checks'][k] == {} for k in ('mainboard_saved_copper_violations_after',
                                                'ioboard_saved_copper_violations_after'))
assert install['checks']['mainboard_refill_of_installed_fill_identical']
reports = ['installation-audit.json', 'native-run-records.json', 'local-dependencies.json',
           'current-function-source-evidence.json', 'current-function-verification.json', 'mainboard-drc.json',
           'mainboard-erc.json', 'ioboard-drc.json', 'ioboard-erc.json', 'fabrication-comparison/gerber-comparison.json',
           'fabrication-comparison/connection-gap-review.json', 'fabrication-comparison/source-decode-crosscheck.json']
out = dict(revision='Working revision27: mainboard pour fill refilled, I/O rear-plate datum off Edge.Cuts',
           created_utc=datetime.now(timezone.utc).isoformat(), native_kicad_version='10.0.7',
           projects=projects, outputs=dict(sorted(outputs.items())),
           model_references=491, updated_model_references=[],
           updated_footprint_references=[], updated_reference_labels={},
           printed_with_eagle_name=old['printed_with_eagle_name'],
           updated_zone_fills={'mainboard': [dict(priority=z['priority'], uuid=z['uuid']) for z in
                                             install['files'][0]['zones']]},
           saved_copper_DRC_before_install={'mainboard': install['checks']['mainboard_saved_copper_violations_before']},
           datum_lines_moved_to_Dwgs_User={'ioboard': [r['uuid'] for r in install['files'][1]['lines_moved']]},
           previous_core_files=len(old['outputs']), changed_previous_core_files=changed,
           new_core_files=install['new_core_files'],
           fresh_DRC_comparison_to_previous=comparisons,
           fresh_ERC_errors={b: c.get('error', 0) for b, c in erc.items()},
           fresh_ERC_warnings={b: c.get('warning', 0) for b, c in erc.items()},
           lead_presence=old['lead_presence'], nominal_fit_findings=old['nominal_fit_findings'],
           model_evidence_basis='No model path, model transform or footprint placement changed; the revision-24 native '
                                'lead audit and nominal-fit findings apply unchanged.',
           fabrication_comparison=dict(method=old['fabrication_comparison']['method'], boards=boards,
                                       connection_gaps=dict(
                                           eagle_airwires={b: gaps[b]['eagle_stored_airwires'] for b in ('mainboard', 'ioboard')},
                                           system_ground_components=gaps['system_ground']['connected_components'],
                                           system_ground_loops=gaps['system_ground']['independent_loops_between_islands'],
                                           mainboard_plus5v=gaps['mainboard_plus5v'])),
           reports={n: sha(HERE / n) for n in reports},
           baseline_summary='validation/working-validation-summary-revision-26.json',
           baseline_summary_sha256=sha(WORK / 'validation/working-validation-summary-revision-26.json'),
           scope=('Mainboard: the filled polygons of the two F.Cu GND zones replaced by KiCad\'s refill, which clears the '
                  'revision-26 SIP9 pads (the saved fill touched 23 of them). I/O board: the four rear-plate datum lines '
                  'moved from Edge.Cuts to Dwgs.User, leaving one 213.36 x 44.45 mm board outline. Zone outlines and '
                  'settings, drills, tracks, vias, pads, nets, footprint poses, models and the schematics are unchanged.'),
           limitations=old['limitations'][:-7] + [
               'DRC now checks the copper as saved and plotted (revisions 11-26 refilled the zones first). KiCad reports '
               'at most 199 items of one type, so truncated silkscreen types are compared by count only. Other recorded '
               'DRC warnings (dangling track stubs carried from the Eagle source) and schematic-parity warnings are '
               'unchanged.',
               old['limitations'][-6], old['limitations'][-5], old['limitations'][-4], old['limitations'][-3],
               'The I/O saved pour fill differs slightly from a fresh refill (about 1.9 mm2 in two places) and passes DRC; '
               'it was left as saved. The rear-plate datum lines stay in the board on Dwgs.User for the Blender datum.',
               old['limitations'][-2], old['limitations'][-1]],
           physical_fit_qualified=False)
for name in ['working-validation-summary-revision-27.json', 'working-validation-summary.json']:
    (WORK / 'validation' / name).write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(dict(passed=True, core_files=len(outputs), changed_previous_core_files=changed,
                      fresh_ERC_errors=out['fresh_ERC_errors'],
                      drc_warnings={b: [old['projects'][b]['drc_violation_warnings'], projects[b]['drc_violation_warnings']]
                                    for b in projects},
                      new_silkscreen_pairs={b: len(comparisons[b]['silkscreen_pairs_new_in_complete_types'])
                                            for b in comparisons},
                      unconnected={b: comparisons[b]['unconnected_nets_fresh'] for b in comparisons}), indent=2))
