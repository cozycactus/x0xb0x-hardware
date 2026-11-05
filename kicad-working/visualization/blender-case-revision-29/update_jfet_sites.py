"""Bring the scene level with KiCad working revision 30 on the mainboard.

Adds the two SC-59 chips Q128 and Q139 at their footprint frames, removes the TO-92 JFETs Q28 and
Q39, which KiCad marks do-not-place, and replaces the eight mainboard layer meshes with a fresh
native export. The chips are the native export's own objects, moved into the mainboard source
collection: no model, pad or pose is scaled, reshaped or moved. Layer meshes keep the scene's layer
materials; the chips use three new materials copied from the native export, one per colour, shared
by both. The I/O board, every other object, pose, collection link and property are retained, and
materials left unused by the removed meshes are dropped on save.

Run from the repository root:
  Blender --background --factory-startup \
      kicad-working/visualization/blender-case-revision-28/x0xb0x-populated-with-case.blend \
      --python-exit-code 1 --python kicad-working/visualization/blender-case-revision-29/update_jfet_sites.py
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import bpy

H = Path(__file__).resolve().parent
WORK = H.parents[1]
REPO = H.parents[2]
sys.path.insert(0, str(H / 'verification'))
sys.path.insert(0, str(REPO / 'kicad-import/validation'))
sys.dont_write_bytecode = True
from scene_snapshot import sha, material_signature, mesh_signature, matrix  # noqa: E402
from verify_native_projects import children, one, parse_sexpr, property_value  # noqa: E402

BASE = H.parent / 'blender-case-revision-28/x0xb0x-populated-with-case.blend'
OUT = H / 'x0xb0x-populated-with-case.blend'
PCB = WORK / 'mainboard/mainboard.kicad_pcb'
assert Path(bpy.data.filepath).resolve() == BASE.resolve() and not OUT.exists()
CLI = os.environ.get('KICAD_CLI', '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
CHIPS = {'Q128': 'Q28', 'Q139': 'Q39'}
SITES = {ref: json.loads((REPO / 'docs/smd-sites.json').read_text())['chips'][ref] for ref in CHIPS}
assert {ref: row['replaces'] for ref, row in SITES.items()} == CHIPS
JFET = sorted(CHIPS.values())
COMPONENTS = ['--force', '--no-board-body', '--user-origin', '0x0mm', '--no-dnp']
LAYER_OPTIONS = ['--force', '--include-tracks', '--include-pads', '--include-zones', '--include-inner-copper',
                 '--include-silkscreen', '--include-soldermask', '--no-components', '--user-origin', '0x0mm']
# Scene layer object -> data name in the export, and which side of the board's mid-height it lies on.
LAYERS = {'MAINBOARD/PCB layers/mesh': ('mainboard_copper', None), 'MAINBOARD/PCB layers/mesh.001': ('mainboard_pad', None),
          'MAINBOARD/PCB layers/mesh.002': ('mainboard_via', None), 'MAINBOARD/PCB layers/mesh.003': ('mainboard_silkscreen', 'front'),
          'MAINBOARD/PCB layers/mesh.004': ('mainboard_silkscreen', 'back'), 'MAINBOARD/PCB layers/mesh.005': ('mainboard_soldermask', 'front'),
          'MAINBOARD/PCB layers/mesh.006': ('mainboard_soldermask', 'back'), 'MAINBOARD/PCB layers/mesh.007': ('mainboard_PCB', None)}
SLOT_ROLE = ('body', 'leads', 'pin-1 mark')
SOURCE_COLLECTION = 'SOURCE / mainboard / immutable native KiCad GLB — revision 10'
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
baseline = sha(BASE)
board_before = sha(PCB)
old_materials = {m.name: material_signature(m) for m in bpy.data.materials}
old_sets = {n: set(getattr(bpy.data, n)) for n in ('collections', 'meshes', 'materials', 'images', 'cameras', 'lights', 'actions')}
object_count = len(bpy.data.objects)
source = bpy.data.collections[SOURCE_COLLECTION]
board_root = bpy.data.objects['Node_0']
assert board_root.get('source_board') == 'mainboard'


def gap(a, b):
    return max(abs(v - w) for x, y in zip(a, b) for v, w in zip(x, y))


def rgb(material):
    return list(material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value)


def bounds(obj):
    points = [obj.matrix_world @ v.co for v in obj.data.vertices]
    return [[min(p[i] for p in points) for i in range(3)], [max(p[i] for p in points) for i in range(3)]]


def base(name):
    return name.rsplit('.', 1)[0] if name[-4:-3] == '.' and name[-3:].isdigit() else name


def footprint_at(reference):
    """Footprint position and rotation from the PCB file, in millimetres (KiCad Y down)."""
    tree = parse_sexpr(PCB.read_text(encoding='utf-8'))
    for fp in children(tree, 'footprint'):
        if property_value(fp, 'Reference', 'reference') == reference:
            at = [x for x in one(fp, 'at')[1:] if not isinstance(x, list)]
            return dict(x_mm=float(at[0]), y_mm=float(at[1]), rotation_deg=float(at[2]) if len(at) > 2 else 0.0)
    raise KeyError(reference)


def export(work, name, options, environment):
    glb = work / f'{name}.glb'
    command = [CLI, 'pcb', 'export', 'glb', *options, '-o', str(glb), str(PCB)]
    run = subprocess.run(command, capture_output=True, text=True, env=environment, timeout=1800)
    assert run.returncode == 0 and glb.is_file(), run.stderr[-400:]
    return glb, dict(options=options, glb_sha256=sha(glb), glb_bytes=glb.stat().st_size)


def imported_from(glb):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(glb))
    bpy.context.view_layer.update()
    return set(bpy.data.objects) - before


def references_to(names):
    """Anything else in the file that points at the objects about to be removed."""
    found = []
    for obj in bpy.data.objects:
        if obj.name in names:
            continue
        if obj.parent and obj.parent.name in names:
            found.append(obj.name)
        for owner in list(obj.constraints) + list(obj.modifiers):
            target = getattr(owner, 'target', None) or getattr(owner, 'object', None)
            if target and target.name in names:
                found.append(obj.name)
    return found


work = Path(tempfile.mkdtemp(prefix='blender-revision-29-'))
environment = dict(os.environ, XDG_CONFIG_HOME=str(work / 'config'), XDG_CACHE_HOME=str(work / 'cache'), KICAD_CONFIG_HOME=str(work / 'config'))
version = subprocess.run([CLI, 'version'], capture_output=True, text=True, env=environment, timeout=120).stdout.strip()
exports = {}
added, new_materials, previous_materials = {}, {}, set()
try:
    glb, exports['components'] = export(work, 'components', COMPONENTS, environment)
    imported = imported_from(glb)
    glb_base = next(o for o in imported if o.parent is None)
    native = {base(o.name): o for o in glb_base.children}
    assert len(native) == 409 and not set(JFET) & set(native), 'The do-not-place JFETs must be left out of this export'
    for ref in sorted(SITES):
        root, (mesh_object,) = native[ref], [o for o in native[ref].children_recursive if o.type == 'MESH']
        assert mesh_object.parent == root and len(root.children_recursive) == 1
        at = footprint_at(ref)
        frame = glb_base.matrix_world.inverted() @ root.matrix_world
        assert abs(frame[0][3] * 1000 - at['x_mm']) < 1e-3 and abs(frame[1][3] * 1000 + at['y_mm']) < 1e-3, ref
        assert abs(frame[2][3] * 1000 - 1.595) < 1e-3, ref
        mesh = mesh_object.data
        assert len(mesh.materials) == len(SLOT_ROLE)
        mapping = []
        for index, (material, role) in enumerate(zip(list(mesh.materials), SLOT_ROLE)):
            key = tuple(round(c, 6) for c in rgb(material)[:3])
            if key not in new_materials:
                copy = material.copy()
                copy.name = f'SC-59 {role} — revision 29 (native KiCad colour)'
                new_materials[key] = copy
            mesh.materials[index] = new_materials[key]
            mapping.append(dict(slot=index, role=role, native_colour=rgb(material), scene_material=new_materials[key].name))
        root.name, mesh_object.name, mesh.name = f'MAINBOARD/{ref}', f'MAINBOARD/{ref}/mesh', f'MAINBOARD/{ref}/revision29 native'
        for obj in (root, mesh_object):
            for collection in list(obj.users_collection):
                collection.objects.unlink(obj)
            source.objects.link(obj)
            obj['source_board'] = 'mainboard'
            obj['native_export_geometry_preserved'] = True
        root.parent = board_root
        root.empty_display_type, root.empty_display_size = 'PLAIN_AXES', bpy.data.objects['MAINBOARD/IC4'].empty_display_size
        assert gap(root.matrix_basis, frame) < 1e-9
        row = SITES[ref]
        root['source_reference'] = ref
        root['model_classification'] = 'generic package model; stock KiCad library SC-59, not manufacturer CAD'
        root['model_limitations'] = (f'Stock KiCad SC-59 model, unchanged; nominal package sizes, not CAD of the {row["part"]} to be bought. | '
                                     f'Stands in for do-not-place TO-92 JFET {row["replaces"]}; fit one or the other, never both. | '
                                     'Part marking omitted; the pin-1 mark is the library model\'s. | '
                                     'Lead seat is the library model\'s, without solder on the lengthened hand-soldering lands. | '
                                     'Nothing has been built or measured; physical fit is unqualified.')
        root['source_urls'] = ''
        root['detailed_model_revision'] = 30
        root['selected_native_source_glb_sha256'] = exports['components']['glb_sha256']
        root['source_geometry_basis'] = 'Native KiCad30: stock SC-59 model at the footprint; PCB placement and model transform as exported'
        root['fitted_part'] = row['part']
        root['replaces_do_not_place_reference'] = row['replaces']
        added[root.name] = dict(reference=ref, part=row['part'], replaces=row['replaces'], footprint=at, frame=matrix(root.matrix_basis),
                                mesh_object=mesh_object.name, mesh=mesh_signature(mesh), material_mapping=mapping)
    kept = {native[ref] for ref in SITES} | {o for ref in SITES for o in native[ref].children_recursive}
    for obj in imported - kept:
        bpy.data.objects.remove(obj, do_unlink=True)

    glb, exports['layers'] = export(work, 'layers', LAYER_OPTIONS, environment)
    imported = imported_from(glb)
    fresh = [o for o in imported if o.type == 'MESH']
    assert len(fresh) == len(LAYERS)
    layers = {}
    for name, (data_name, side) in LAYERS.items():
        target = bpy.data.objects[name]
        old_box = bounds(target)
        candidates = [o for o in fresh if base(o.data.name) == data_name]
        if side:
            mid = 0.755e-3
            candidates = [o for o in candidates if (bounds(o)[0][2] > mid) == (side == 'front')]
        (part,) = candidates
        new_box = bounds(part)
        assert abs(old_box[0][2] - new_box[0][2]) < 1e-6 and abs(old_box[1][2] - new_box[1][2]) < 1e-6, (name, 'height differs')
        local = target.matrix_world.inverted() @ part.matrix_world
        assert gap(local, ((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))) < 1e-9, (name, 'frame differs')
        assert len(target.data.materials) == len(part.data.materials) == 1
        keep = target.data.materials[0]
        mesh = part.data.copy()
        mesh.name = f'{name}/revision29 native'
        native_colour = rgb(mesh.materials[0])
        mesh.materials[0] = keep
        layers[name] = dict(kicad_mesh=data_name, side=side, old_mesh=mesh_signature(target.data), new_mesh=mesh_signature(mesh),
                            old_bounds_m=old_box, new_bounds_m=new_box, scene_material=keep.name, scene_colour=rgb(keep), native_colour=native_colour)
        previous = target.data
        target.data = mesh
        if previous.users == 0:
            bpy.data.meshes.remove(previous)
        target['selected_native_revision'] = 30
        target['selected_native_source_glb_sha256'] = exports['layers']['glb_sha256']
    for obj in imported:
        bpy.data.objects.remove(obj, do_unlink=True)
finally:
    shutil.rmtree(work, ignore_errors=True)
assert sha(PCB) == board_before

removed = {}
doomed = {o.name for ref in JFET for o in [bpy.data.objects[f'MAINBOARD/{ref}'], *bpy.data.objects[f'MAINBOARD/{ref}'].children_recursive]}
assert not references_to(doomed), references_to(doomed)
for ref in JFET:
    root = bpy.data.objects[f'MAINBOARD/{ref}']
    assert root['source_reference'] == ref and root.parent == board_root
    (mesh_object,) = root.children_recursive
    mesh = mesh_object.data
    previous_materials |= {m.name for m in mesh.materials}
    removed[root.name] = dict(reference=ref, frame=matrix(root.matrix_basis), mesh_object=mesh_object.name, mesh=mesh_signature(mesh))
    bpy.data.objects.remove(mesh_object, do_unlink=True)
    bpy.data.objects.remove(root, do_unlink=True)
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
for name in old_sets:
    block = getattr(bpy.data, name)
    for item in set(block) - old_sets[name]:
        if item.users == 0:
            block.remove(item)
assert len(bpy.data.objects) == object_count, (len(bpy.data.objects), object_count)
NEW = {m.name for m in new_materials.values()}
assert len(NEW) == 3
assert {m.name for m in bpy.data.materials} - set(old_materials) == NEW
assert {m.name: material_signature(m) for m in bpy.data.materials if m.name not in NEW} == {
    k: v for k, v in old_materials.items() if k in bpy.data.materials}
retired = sorted(m.name for m in bpy.data.materials if m.name in previous_materials and m.users == 0)
guide = bpy.data.texts.new('00 START HERE — revision29 assembly')
guide.write('''x0xb0x Blender29 / KiCad30
The mainboard shows the board as built with its SMD sites. Two SC-59 chips, Q128
and Q139, stand beside the empty holes of the rare TO-92 JFETs Q28 and Q39, which
KiCad marks do-not-place. An original JFET can still go in those holes in place
of a chip; Blender28 shows them. The four SOT-363 chips of Blender28 are unchanged.
The mainboard copper, pads, vias, silkscreen, mask and board body are a fresh
KiCad30 export in the scene's own materials. The I/O board layers are unchanged.
Q128's model clears C33's by 0.35 mm and standing resistor R105's by 0.42 mm, and its
gate land ends 0.08 mm from R105's model in plan; this is recorded, not corrected.
Nothing has been built or measured.
Frames 1 assembled, 80 exploded, 120 control-side, 160 wiring study.
''')
scene['visualization_revision'] = 29
scene['opening_notes_text'] = guide.name
scene['revision_29_baseline_scene_sha256'] = baseline
scene['revision_29_KiCad_revision'] = 30
scene['revision_29_added_reference_count'] = len(added)
scene['revision_29_removed_do_not_place_reference_count'] = len(removed)
scene['revision_29_replaced_mainboard_layer_mesh_count'] = len(layers)
scene['revision_29_unfitted_alternates'] = 'TO-92 JFETs Q28, Q39; each mutually exclusive with its fitted chip Q128, Q139'
scene.frame_set(1)
bpy.context.view_layer.update()
assert sha(BASE) == baseline
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), compress=True, check_existing=False)
assert sha(PCB) == board_before
record = dict(passed=True, visualization_revision=29, kicad_revision=30, baseline_sha256=baseline, stable_scene_sha256=sha(OUT),
              stable_scene_bytes=OUT.stat().st_size, kicad_version=version, blender_version=bpy.app.version_string,
              pcb=str(PCB.relative_to(REPO)), pcb_sha256=board_before, exports=exports, added_references=added,
              removed_do_not_place_references=removed, layer_changes=layers, added_materials=sorted(NEW), retired_materials=retired,
              native_reference_count=sum(bool(o.get('source_reference')) for o in bpy.data.objects), stored_object_count=len(bpy.data.objects),
              opening_guide=guide.name, opening_guide_sha256=hashlib.sha256(guide.as_string().encode()).hexdigest(), physical_fit_qualified=False)
assert record['native_reference_count'] == 491
(H / 'revision-29-change-record.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(dict(passed=True, added=sorted(added), removed=sorted(removed), layers=len(layers), added_materials=sorted(NEW), retired=retired,
                      scene_sha256=record['stable_scene_sha256'], objects=record['stored_object_count']), indent=2), flush=True)
