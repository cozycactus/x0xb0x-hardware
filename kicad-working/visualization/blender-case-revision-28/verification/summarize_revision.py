"""Write the revision-28 render review, validation summary and docs/blender-smd-sites.json.

Every number comes from a report in this folder or from the KiCad revision-29 records. Asserts the outcomes
that the README files state.

Run:  python3 -I kicad-working/visualization/blender-case-revision-28/verification/summarize_revision.py
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REV = HERE.parent
REPO = HERE.parents[3]
WORK = REPO / 'kicad-working'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
load = lambda p: json.loads(Path(p).read_text())  # noqa: E731
rel = lambda p: str(Path(p).resolve().relative_to(REPO))  # noqa: E731


def report(path, **extra):
    data = load(path)
    row = dict(report=rel(path), sha256=sha(path))
    for key in ('passed', 'check_count', 'ray_count'):
        if key in data:
            row[key] = data[key]
    row.update(extra)
    return row


project = load(REPO / 'PROJECT.json')
change = load(REV / 'revision-28-change-record.json')
scene = REV / 'x0xb0x-populated-with-case.blend'
assert sha(scene) == change['stable_scene_sha256'] == project['blender_sha256']
assert project['kicad_working_revision'] == 29 and project['blender_revision'] == 28 and project['fitted_model_references'] == 491
saved, portable = load(HERE / 'final-saved-scene-audit.json'), load(HERE / 'portable-scene-audit.json')
openings, models = load(HERE / 'rear-openings-audit.json'), load(HERE / 'kicad-blender-models-audit.json')
joins, drill = load(HERE / 'terminal-join-audit.json'), load(HERE / 'drill-fit-audit.json')
layers, neighbours = load(HERE / 'board-layer-audit.json'), load(HERE / 'chip-neighbour-audit.json')
renders, readonly, details = load(REV / 'render-records.json'), load(HERE / 'render-readonly-verification.json'), load(HERE / 'chip-detail-render.json')
fit = load(WORK / 'smd-sites/fit-check.json')
for r in (saved, portable, openings, models, joins, drill, layers, neighbours, details, readonly):
    assert r['passed']
assert saved['check_count'] == 16 and portable['check_count'] == 106 and openings['check_count'] == 44 and openings['ray_count'] == 974
assert models['compared_references'] == models['identical_references'] == 491
assert joins['references_checked'] == 25 and joins['terminal_pieces'] == 133 and drill['measured_models'] == 489
assert layers['check_count'] == 5 and layers['via_count'] == 13
assert len(change['added_references']) == len(change['removed_do_not_place_references']) == 4 and len(change['layer_changes']) == 8
assert change['stored_object_count'] == 1721 and change['native_reference_count'] == 491 and len(change['added_materials']) == 3
assert neighbours['chip_contacts'] == [] and fit['touching_in_the_models'] == ['Q126-R100A0']
assert neighbours['q126_r100a0_mesh_gap_mm'] == 0.07 and neighbours['q126_r100a0_triangle_pairs'] == 0
images = {r['view']: dict(path=r['image'], sha256=sha(REV / r['image'])) for r in renders}
images.update({Path(r['image']).stem: dict(path=r['image'], sha256=sha(REV / r['image'])) for r in details['images']})
review = dict(passed=True, review='Visual inspection of all eleven current PNGs', scene_sha256=change['stable_scene_sha256'], images=images,
              observations=load(HERE / 'render-observations.json'), physical_fit_qualified=False)
(HERE / 'final-render-review.json').write_text(json.dumps(review, indent=2) + '\n')
verification = dict(
    saved_scene_preservation=report(HERE / 'final-saved-scene-audit.json'),
    kicad_blender_models=report(HERE / 'kicad-blender-models-audit.json'),
    board_layers=report(HERE / 'board-layer-audit.json'),
    drill_fit=report(HERE / 'drill-fit-audit.json'),
    terminal_joins=report(HERE / 'terminal-join-audit.json'),
    rear_openings=report(HERE / 'rear-openings-audit.json'),
    scene_portability=report(HERE / 'portable-scene-audit.json'),
    chip_neighbours=report(HERE / 'chip-neighbour-audit.json'),
    detail_renders=report(HERE / 'chip-detail-render.json'),
    render_readonly=report(HERE / 'render-readonly-verification.json'),
    render_review=report(HERE / 'final-render-review.json'))
chips = {v['reference']: dict(part=v['part'], replaces=v['replaces'], footprint=v['footprint']) for v in change['added_references'].values()}
position = {c['check']: c for c in saved['checks']}['All 4 chips stand at their KiCad positions and rotations']['positions']
summary = dict(
    schema=1, snapshot_date='2026-11-04', Blender_revision=28, KiCad_revision=29,
    scene=rel(scene), scene_sha256=change['stable_scene_sha256'], scene_bytes=scene.stat().st_size, baseline_scene_sha256=change['baseline_sha256'],
    correction='The mainboard shows the board as built with its SMD sites: the four SOT-363 chips stand at their KiCad footprints, the do-not-place '
               'SIP pairs they replace are out of the scene, and the eight mainboard layer meshes are a fresh KiCad 29 export.',
    do_not_place=dict(
        kicad_cli='kicad-cli pcb export glb keeps do-not-place footprints unless given --no-dnp: 413 mainboard models without it, 409 with it, the chips in and the SIP pairs out.',
        decision='The owner chose to take the pairs out of the scene, which holds fitted references. Fit a chip or its pair, never both, as IC15A0 and IC15B0.',
        verifier_change='scripts/verify_kicad_blender_models.py now exports with --no-dnp. verify_blender_scene.py still expects 491 = 409 + 82, unchanged.',
        unaffected='verify_drill_fit.py and verify_terminal_joins.py read KiCad, not the scene, and still export the pairs, so the pairs\' leads stay checked against their holes. '
                   'verify_kicad_dependencies.py still resolves all 495 model files.',
        fallback='The holes and pads stay, and an original pair or an adapter can still go in. Blender 27 still shows the pairs.'),
    chips=chips, chip_positions=position,
    contacts=dict(chip_contacts=neighbours['chip_contacts'], removed_with_the_sip_pairs=neighbours['removed_with_the_sip_pairs'],
                  smallest_gap_per_chip=neighbours['smallest_gap_per_chip'], headroom_above_chip_mm=neighbours['headroom_above_chip_mm'],
                  q126_r100a0_mesh_gap_mm=neighbours['q126_r100a0_mesh_gap_mm'], fit_check_touching_the_chip_box=fit['touching_in_the_models'],
                  fit_check_difference=neighbours['fit_check_difference'], fit_check=rel(WORK / 'smd-sites/fit-check.json')),
    blender=dict(added_objects=8, removed_objects=8, stored_objects=change['stored_object_count'], replaced_layer_meshes=sorted(change['layer_changes']),
                 layer_vertex_counts={k: dict(old=v['old_mesh']['vertices'], new=v['new_mesh']['vertices']) for k, v in change['layer_changes'].items()},
                 added_materials=change['added_materials'], retired_materials=change['retired_materials']),
    kicad=dict(pcb_sha256=change['pcb_sha256'], pcb_changed=False, kicad_version=change['kicad_version'], exports=change['exports']),
    verification=verification,
    unchanged=['Original Eagle files', 'Both KiCad projects, boards and libraries', 'The 487 other model references',
               'I/O board layers, all poses, case, LEDs, spacers, caps, hardware, wiring study, previous materials, cameras and animation'],
    limitations=['The chip model is KiCad\'s stock SOT-363_SC-70-6: nominal sizes, no part marking, no solder, not CAD of the part to be bought.',
                 'Layer meshes keep the scene\'s own materials, so pads stay grey although the export colours them gold.',
                 'The I/O board layers were not refreshed. A fresh export has the same copper, pads, vias and main board body, but differs in both silkscreens and both masks and no longer has the detached datum strip.',
                 'Nothing has been built or measured. These checks do not qualify physical fit or circuit operation.'],
    physical_fit_qualified=False)
(HERE / 'independent-validation-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
docs = dict(summary)
docs['validation_summary'] = dict(report=rel(HERE / 'independent-validation-summary.json'), sha256=sha(HERE / 'independent-validation-summary.json'))
(REPO / 'docs/blender-smd-sites.json').write_text(json.dumps(docs, indent=2) + '\n')
print(json.dumps(dict(passed=True, verification={k: v.get('passed') for k, v in verification.items()}), indent=2))
