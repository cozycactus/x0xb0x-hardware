#!/usr/bin/env python3
"""Record current file preservation and fresh I/O ERC/DRC evidence."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text())
old = load(WORK / 'validation/working-validation-summary-revision-11.json')
install = load(HERE / 'installation-audit.json')
assert install['passed']
outputs = {name: sha(WORK / name) for name in old['outputs']}
changed = sorted(n for n in outputs if outputs[n] != old['outputs'][n])
assert changed == install['changed_previous_core_files']
for name in install['new_core_files']:
    outputs[name] = sha(WORK / name)
assert len(outputs) == 259
fresh_drc = load(HERE / 'ioboard-drc.json')
old_drc = load(WORK / 'validation/models-review-11/ioboard-drc-final.json')
fresh_erc = load(HERE / 'ioboard-erc.json')
comparisons = {key: fresh_drc[key] == old_drc[key]
               for key in ('violations', 'unconnected_items', 'schematic_parity', 'ignored_checks')}
assert all(comparisons.values())
violations = [v for sheet in fresh_erc['sheets'] for v in sheet['violations']]
erc = Counter(v['severity'] for v in violations)
assert not violations
projects = {}
keys = ('erc_errors', 'erc_warnings', 'drc_violation_errors', 'drc_violation_warnings',
        'separate_unconnected_errors', 'separate_schematic_parity_warnings',
        'remaining_connections', 'erc_ignored_checks', 'drc_ignored_checks',
        'erc_exclusions', 'drc_exclusions', 'model_instances')
for board in ('mainboard', 'ioboard'):
    projects[board] = {k: old['projects'][board][k] for k in keys}
    projects[board]['electrical_inputs_and_rules_preserved'] = True
    projects[board]['fresh_native_ERC_DRC_this_revision'] = board == 'ioboard'
    projects[board]['electrical_evidence_basis'] = (
        'Fresh KiCad10.0.7 I/O reports; all DRC findings exactly equal revision11. ERC0 under retained project rules.'
        if board == 'ioboard' else
        'Revision11 native reports retained; every mainboard project file byte-identical. No mainboard electrical rerun this revision.')
reports = ['installation-audit.json', 'din-contact-quality/corrected-model-audit.json',
           'din-contact-quality/native-final-geometry-audit.json',
           'din-contact-quality/native-final-export-record.json',
           'current-function-verification.json', 'ioboard-drc.json', 'ioboard-erc.json']
out = dict(revision='Working revision12: corrected SDS-50J outer contact centers and independent slot tilts',
           created_utc=datetime.now(timezone.utc).isoformat(), native_kicad_version=fresh_drc['kicad_version'],
           projects=projects, outputs=dict(sorted(outputs.items())),
           model_references=491, updated_model_references=['DIN1', 'DIN2', 'DIN3', 'DIN4'],
           previous_core_files=257, changed_previous_core_files=changed, new_core_files=install['new_core_files'],
           fresh_ioboard_DRC_findings_identical_to_revision11=comparisons,
           fresh_ioboard_ERC_errors=erc.get('error', 0), fresh_ioboard_ERC_warnings=erc.get('warning', 0),
           reports={n: sha(HERE / n) for n in reports},
           baseline_summary='validation/working-validation-summary-revision-11.json',
           baseline_summary_sha256=sha(WORK / 'validation/working-validation-summary-revision-11.json'),
           scope='Four PCB STEP paths and one corresponding footprint cache path only. Original Eagle files, schematics, copper, pads, drills, nets, footprint poses and rules are preserved. Two original outer contact positions and their slot directions are corrected from the primary drawing.',
           limitations=['Drawing-derived model retains unsized illustrative details and omits solder terminals/locators.',
                        'Existing three PCB connection gaps and recorded DRC/parity warnings remain.',
                        'Nominal model checks and sampled rear passages do not establish physical assembly or fabrication readiness.'],
           physical_fit_qualified=False)
for name in ['working-validation-summary-revision-12.json', 'working-validation-summary.json']:
    (WORK / 'validation' / name).write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(dict(passed=True,core_files=len(outputs),changed_previous_core_files=changed,
                     fresh_ioboard_ERC_errors=0,fresh_ioboard_ERC_warnings=0,
                     fresh_ioboard_DRC_equivalent=True),indent=2))
