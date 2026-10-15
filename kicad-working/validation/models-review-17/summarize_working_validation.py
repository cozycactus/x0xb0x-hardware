#!/usr/bin/env python3
"""Record revision-17 file preservation and fresh ERC/DRC evidence for both boards."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text())
old = load(WORK / 'validation/working-validation-summary-revision-16.json')
install = load(HERE / 'installation-audit.json')
terminals = load(HERE / 'tl1100-colour/tl1100-colour-audit.json')
native = load(HERE / 'native-terminal-audit.json')
functions = load(HERE / 'current-function-verification.json')
dependencies = load(HERE / 'local-dependencies.json')
assert install['passed'] and terminals['passed'] and native['passed'] and functions['passed'] and dependencies['passed']
outputs = {name: sha(WORK / name) for name in old['outputs']}
changed = sorted(n for n in outputs if outputs[n] != old['outputs'][n])
assert changed == install['changed_previous_core_files']
for name in install['new_core_files']:
    outputs[name] = sha(WORK / name)
assert len(outputs) == 289 + 2
baselines = {'mainboard': WORK / 'validation/models-review-16/mainboard-drc.json',
             'ioboard': WORK / 'validation/models-review-16/ioboard-drc.json'}


def unconnected_nets(items):
    """Net of each unconnected pair; KiCad names varying representative pads/tracks of the same two islands."""
    return sorted(sorted({i['description'].split('[', 1)[1].split(']', 1)[0] for i in u['items']}) for u in items)


projects, comparisons, erc = {}, {}, {}
keys = ('erc_errors', 'erc_warnings', 'drc_violation_errors', 'drc_violation_warnings',
        'separate_unconnected_errors', 'separate_schematic_parity_warnings',
        'remaining_connections', 'erc_ignored_checks', 'drc_ignored_checks',
        'erc_exclusions', 'drc_exclusions', 'model_instances')
for board in ('mainboard', 'ioboard'):
    fresh = load(HERE / f'{board}-drc.json')
    base = load(baselines[board])
    comparisons[board] = {k: fresh[k] == base[k] for k in ('violations', 'schematic_parity', 'ignored_checks')}
    comparisons[board]['unconnected_items_raw'] = fresh['unconnected_items'] == base['unconnected_items']
    comparisons[board]['unconnected_count_and_nets'] = unconnected_nets(fresh['unconnected_items']) == \
        unconnected_nets(base['unconnected_items'])
    assert all(v for k, v in comparisons[board].items() if k != 'unconnected_items_raw'), (board, comparisons[board])
    violations = [v for sheet in load(HERE / f'{board}-erc.json')['sheets'] for v in sheet['violations']]
    erc[board] = Counter(v['severity'] for v in violations)
    assert not violations
    projects[board] = {k: old['projects'][board][k] for k in keys}
    projects[board]['remaining_connections'] = fresh['unconnected_items']
    projects[board].update(electrical_inputs_and_rules_preserved=True, fresh_native_ERC_DRC_this_revision=True,
                           electrical_evidence_basis=(
                               'Fresh KiCad10.0.7 reports for this revision; DRC violations, schematic parity and '
                               'ignored checks exactly equal the previous fresh report; same unconnected gaps. ERC0 '
                               'under retained project rules.'))
projects['mainboard']['unconnected_track_end_note'] = (
    'S22 pad 1 [+5V] gap unchanged; KiCad names varying representative pads or tracks of the same two islands '
    'as its ends between runs. '
    'Copper is byte-identical apart from model paths.')
reports = ['installation-audit.json', 'combined-model-plan.json', 'tl1100-colour/tl1100-colour-audit.json',
           'tl1100-colour/tl1100-native-colour-check.json',
           'native-export-record.json', 'native-terminal-audit.json', 'native-run-records.json',
           'current-function-source-evidence.json', 'current-function-verification.json', 'local-dependencies.json',
           'mainboard-drc.json', 'mainboard-erc.json', 'ioboard-drc.json', 'ioboard-erc.json']
out = dict(revision='Working revision17: TL1100F terminal legs coloured as metal (geometry unchanged)',
           created_utc=datetime.now(timezone.utc).isoformat(), native_kicad_version='10.0.7',
           projects=projects, outputs=dict(sorted(outputs.items())),
           model_references=491, updated_model_references=sorted(r for v in install['references'].values() for r in v),
           previous_core_files=len(old['outputs']), changed_previous_core_files=changed,
           new_core_files=install['new_core_files'],
           fresh_DRC_comparison_to_previous=comparisons,
           fresh_ERC_errors={b: c.get('error', 0) for b, c in erc.items()},
           fresh_ERC_warnings={b: c.get('warning', 0) for b, c in erc.items()},
           lead_presence=native['boards'],
           nominal_fit_findings=native['nominal_fit_findings'],
           reports={n: sha(HERE / n) for n in reports},
           baseline_summary='validation/working-validation-summary-revision-16.json',
           baseline_summary_sha256=sha(WORK / 'validation/working-validation-summary-revision-16.json'),
           scope='Twenty-three PCB STEP paths and one corresponding footprint-cache path only (colour-only model update). Original Eagle '
                 'files, schematics, copper, pads, drills, nets, footprint poses, model transforms and rules are '
                 'preserved. Previous body solids are retained exactly; terminals follow drawing dimensions in each '
                 'model frame and were not moved to pads.',
           limitations=['Terminal thicknesses, bends and several widths are labelled assumptions in terminal_spec.py.',
                        'Nominal-fit findings record drawing/footprint disagreements; neither source was altered.',
                        'Grayhill MT bracket legs and SDS-50J locating pegs remain omitted (undimensioned or no hole).',
                        'Existing three PCB connection gaps and recorded DRC/parity warnings remain.',
                        'Nominal model checks do not establish physical assembly or fabrication readiness.'],
           physical_fit_qualified=False)
for name in ['working-validation-summary-revision-17.json', 'working-validation-summary.json']:
    (WORK / 'validation' / name).write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(dict(passed=True, core_files=len(outputs), changed_previous_core_files=len(changed),
                      fresh_ERC_errors=out['fresh_ERC_errors'], comparisons=comparisons,
                      nominal_fit_findings=len(out['nominal_fit_findings'])), indent=2))
