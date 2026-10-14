"""Pin all completed independent/delegated evidence to the frozen scene bytes."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p / 'PROJECT.json').is_file())
SCENE = HERE.parent / 'x0xb0x-populated-with-case.blend'
BASELINE = HERE.parent.parent / 'blender-case-revision-11/x0xb0x-populated-with-case.blend'
EXPECTED = '517da1343de66a3e3b5c4848c182bcd263cccca419d3601e5805e0d3402228e1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


reports = {}
for name in ['final-saved-scene-audit.json', 'midi-legends-audit.json',
             'rear-legend-plane-audit.json', 'rear-openings-audit.json',
             'portable-scene-audit.json', 'final-render-review.json',
             'render-readonly-verification.json']:
    report = json.loads((HERE / name).read_text())
    assert report['passed'], name
    assert report.get('scene_sha256', report.get('stable_scene_sha256')) == EXPECTED, name
    reports[name] = dict(passed=True, sha256=sha(HERE / name),
                         check_count=report.get('check_count'),
                         view_count=report.get('view_count'))
assert sha(SCENE) == EXPECTED
preservation = json.loads((HERE / 'final-saved-scene-audit.json').read_text())
assert sha(BASELINE) == preservation['baseline_scene_sha256']
negative = json.loads((HERE / 'baseline-midi-legends-audit.json').read_text())
assert not negative['passed'] and {r['reference'] for r in negative['failures']} == {'DIN1', 'DIN2', 'DIN3'}
assert negative['scene_sha256'] == sha(BASELINE)
source = json.loads((HERE / 'midi-connectivity-evidence.json').read_text())
for name, expected in [(source['pcb'], source['pcb_sha256']),
                       (source['original_eagle'], source['eagle_sha256'])]:
    assert sha(REPO / name) == expected
files = sorted(p for p in HERE.iterdir() if p.suffix in {'.json', '.py', '.md', '.gz'}
               and p.name != 'independent-validation-summary.json')
result = dict(
    passed=True, scene_sha256=sha(SCENE), scene_bytes=SCENE.stat().st_size,
    baseline_scene_sha256=sha(BASELINE), blender_version='5.0.0',
    corrected_font_objects=preservation['changed_objects'],
    derived_display_mapping={ref: row['expected_legend'] for ref, row in source['functions'].items()},
    independent_original_connected_pad_memberships=62,
    baseline_regression=dict(passed=True, baseline_mapping_passed=False,
                             expected_failure_references=['DIN1', 'DIN2', 'DIN3']),
    native_reference_count=491, native_LED_count=40, button_cap_count=23,
    rear_port_count=11, rear_opening_check_count=44, rear_opening_ray_count=974,
    evaluated_rear_glyph_pose_count=44, inspection_frame_count=4,
    reports=reports,
    evidence_files=[dict(path=str(p.relative_to(REPO)), sha256=sha(p), bytes=p.stat().st_size)
                    for p in files],
    unchanged_repository_verifiers=[dict(path=str(p.relative_to(REPO)), sha256=sha(p))
        for p in [REPO / 'scripts/verify_blender_scene.py', REPO / 'scripts/verify_rear_openings.py']],
    source_inputs=[dict(path=source['pcb'], sha256=source['pcb_sha256']),
                   dict(path=source['original_eagle'], sha256=source['eagle_sha256'])],
    source_review=dict(path='kicad-working/validation/din-midi-review/function-verification.json',
        sha256=sha(REPO / 'kicad-working/validation/din-midi-review/function-verification.json'),
        ownership='Separate source reviewer; broader original schematic/board checks.'),
    snapshot_scope='All 1661 stored objects, geometry/data signatures, font resources/settings, materials, hierarchy, collections, animation, cameras and actual instance matrices in frames1/80/120/160.',
    automatic_font_cache_qualification='The three regenerated glyphs update automatic texture-space XY bounds with use_auto_texspace retained true; native glyph measurements confirm those caches. All editable font/style/material fields and normal cache components remain exact.',
    render_review_ownership='Delegated scene renderer owns only final-render-review.json and render-readonly-verification.json.',
    read_only=True, source_designs_modified=False, physical_fit_qualified=False,
    qualifications=[
        'Three editable presentation legend strings are corrected; original printed typography is not recovered.',
        'The preserved .01mm rear glyph display offset is a rendering choice, not physical ink thickness.',
        'Previously measured three audio .508mm panel intersections and nominal power/USB .081mm lower clipping remain unchanged model/datum conflicts; seating is not certified.',
        'Rear rays qualify sampled visual apertures only; no physical insertion/thread, hardware electrical, ERC, DRC or fabrication certification.'])
(HERE / 'independent-validation-summary.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in {'reports', 'evidence_files', 'qualifications'}}, indent=2))
