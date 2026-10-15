#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Read the loaded repository scene without saving or relying on old exports.

Run with Blender (verified with 5.0.0):
  blender --background <checked-in .blend> --python-exit-code 1 \
      --python scripts/verify_blender_scene.py

The exit-code option is required: Blender can otherwise exit successfully after
a Python exception. JSON is printed to stdout; Blender also prints its own log.
The repository is located from the loaded .blend, so this script can inspect a
fresh clone even when the script itself is run from a different checkout.
"""

import hashlib
import json
from collections import Counter
from pathlib import Path

import bpy


BOARD_NAME = "Mainboard — B.Cu outward in assembled view"
CAP_NAMES = {f"S{i} / switch cap proxy" for i in range(5, 28)}
LED_REFERENCES = {f"LED{i}" for i in range(1, 41)}
MATRIX_TOLERANCE = 1e-7


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def matrix_error(first, second):
    return max(abs(a - b) for x, y in zip(first, second) for a, b in zip(x, y))


def bounds(points):
    return ([min(p[i] for p in points) for i in range(3)],
            [max(p[i] for p in points) for i in range(3)])


def verify():
    checks = []

    def check(name, passed, **details):
        checks.append({"check": name, "passed": bool(passed), **details})

    scene_path = Path(bpy.data.filepath).resolve()
    if not bpy.data.filepath or not scene_path.is_file():
        raise RuntimeError("Load the checked-in .blend before this script")
    original_hash = sha256(scene_path)
    root = next((p for p in scene_path.parents
                 if (p / "PROJECT.json").is_file()), None)
    if root is None:
        raise RuntimeError("The loaded scene has no repository PROJECT.json")
    project = json.loads((root / "PROJECT.json").read_text())
    expected_scene = root / "kicad-working" / project["blender_scene"]
    check("Loaded scene is the repository's declared Blender scene",
          scene_path == expected_scene.resolve())
    check("Scene bytes match the repository's declared revision",
          original_hash == project["blender_sha256"])

    roots = [o for o in bpy.data.objects if o.get("source_reference")]
    identities = [(o.get("source_board"), o["source_reference"]) for o in roots]
    counts = Counter(board for board, reference in identities)
    check("Exactly 491 unique fitted native reference roots",
          len(roots) == len(set(identities)) == 491)
    check("Native reference split is 409 mainboard and 82 ioboard",
          counts == {"mainboard": 409, "ioboard": 82}, counts=dict(counts))
    check("All fitted reference roots have embedded mesh geometry",
          all(any(o.type == "MESH" and len(o.data.vertices) > 0
                  for o in ref.children_recursive) for ref in roots))
    sources = [c for c in bpy.data.collections
               if "immutable native KiCad GLB" in c.name]
    source_roots = {o for c in sources for o in c.all_objects
                    if o.get("source_reference")}
    check("Both embedded native board collections retain all fitted roots",
          len(sources) == 2 and all(c.library is None and c.use_fake_user
                                   for c in sources)
          and source_roots == set(roots))

    duplicate_lenses = [o.name for o in bpy.data.objects
                        if o.name.endswith(" / visible lens proxy")]
    check("No old standalone LED lens proxies remain", not duplicate_lenses,
          objects=duplicate_lenses)
    leds = {ref["source_reference"]: ref for ref in roots
            if ref.get("source_board") == "mainboard"
            and ref["source_reference"].startswith("LED")}
    check("Exactly LED1 through LED40 are embedded PCB assemblies",
          set(leds) == LED_REFERENCES)
    for reference, ref in sorted(leds.items()):
        meshes = [o for o in ref.children_recursive if o.type == "MESH"]
        boxes = []
        spacers = [o for o in meshes if o.name == ref.name + "/STD240B spacer"]
        has_spacer = ref.get("detailed_model_revision", 0) >= 19
        spacer_valid = len(spacers) == (1 if has_spacer else 0)
        for mesh in meshes:
            transform = ref.matrix_world.inverted() @ mesh.matrix_world
            points = [transform @ v.co * 1000 for v in mesh.data.vertices]
            if points:
                box = bounds(points)
                if mesh in spacers:
                    expected = [-1.27, -2.54, 0, 3.81, 2.54, 6.096]
                    spacer_valid = spacer_valid and all(
                        abs(a - b) < .001
                        for a, b in zip(box[0] + box[1], expected))
                else:
                    boxes.append(box)
        leads = [(lo, hi) for lo, hi in boxes if lo[2] < 0]
        heads = [(lo, hi) for lo, hi in boxes if lo[2] > 0]
        lead_axes = sorted((lo[0] + hi[0]) / 2 for lo, hi in leads)
        full_leads = len(leads) == 2 and all(
            abs(lo[2] + 2.5) < .001 and abs(hi[2] - 6.096) < .001
            and abs(hi[0] - lo[0] - .4) < .001
            and abs(hi[1] - lo[1] - .4) < .001 for lo, hi in leads)
        check("Complete embedded head and full lead envelopes: " + reference,
              len(meshes) == (4 if has_spacer else 3) and spacer_valid
              and full_leads and len(heads) == 1
              and all(abs(a - b) < .001
                      for a, b in zip(lead_axes, [0, 2.54]))
              and abs(heads[0][0][2] - 6.096) < .001
              and abs(heads[0][1][2] - 14.696) < .001)

    board = bpy.data.objects.get(BOARD_NAME)
    caps = {n: bpy.data.objects.get(n) for n in CAP_NAMES}
    check("Exactly 23 named button caps are embedded",
          all(o is not None and o.type == "MESH" for o in caps.values()))
    if board is None or any(o is None for o in caps.values()):
        check("Mainboard and all caps exist for attachment checks", False)
    else:
        check("All 23 caps are directly parented to the PCB instance",
              all(o.parent == board for o in caps.values()))
        display_collections = {c for o in caps.values()
                               for c in o.users_collection}
        check("Caps use one ordinary, non-instanced scene collection",
              len(display_collections) == 1
              and all(c.name in bpy.context.scene.collection.children
                      for c in display_collections)
              and not any(o.instance_collection in display_collections
                          for o in bpy.data.objects))
        local_poses = {n: o.matrix_parent_inverse @ o.matrix_basis
                       for n, o in caps.items()}
        maximum_error = 0
        board_poses = []
        for frame in [1, 80, 120, 160]:
            bpy.context.scene.frame_set(frame)
            bpy.context.view_layer.update()
            displayed = {n: [] for n in caps}
            for instance in bpy.context.evaluated_depsgraph_get().object_instances:
                name = instance.object.original.name
                if name in displayed:
                    displayed[name].append(instance.matrix_world.copy())
            if frame in [1, 80]:
                board_poses.append(board.matrix_world.copy())
                for name, cap in sorted(caps.items()):
                    expected = board.matrix_world @ local_poses[name]
                    error = (matrix_error(displayed[name][0], expected)
                             if len(displayed[name]) == 1 else 1e30)
                    maximum_error = max(maximum_error, error)
                    check(f"One visible cap follows PCB at frame {frame}: {name}",
                          len(displayed[name]) == 1
                          and not cap.hide_viewport and not cap.hide_render
                          and error < MATRIX_TOLERANCE)
            else:
                # Hidden objects can retain stale matrix_world caches. Test
                # stored attachment and absence of displayed instances instead.
                check(f"Caps retain hidden inspection behavior at frame {frame}",
                      all(cap.hide_viewport and cap.hide_render
                          and not displayed[name]
                          and matrix_error(cap.matrix_parent_inverse
                                           @ cap.matrix_basis,
                                           local_poses[name]) < MATRIX_TOLERANCE
                          for name, cap in caps.items()))
        check("Exploded frame actually changes the board pose",
              matrix_error(*board_poses) > .01)
        check("Visible cap attachment error stays below tolerance",
              maximum_error < MATRIX_TOLERANCE,
              maximum_matrix_error=maximum_error)

    external_paths = bpy.utils.blend_paths(absolute=True, packed=False)
    check("Scene has no unpacked external file dependencies",
          not external_paths, paths=external_paths)
    check("Scene has no linked external Blender libraries",
          not bpy.data.libraries)
    check("All fonts are built in or packed into the scene",
          all(font.filepath == "<builtin>" or font.packed_file
              for font in bpy.data.fonts))
    check("All file-backed images are packed with their pixel data",
          all(image.source in {"GENERATED", "VIEWER"}
              or (image.packed_file and image.has_data)
              for image in bpy.data.images))
    check("Read-only inspection left the scene bytes unchanged",
          sha256(scene_path) == original_hash)
    failures = [c for c in checks if not c["passed"]]
    return {"passed": not failures, "check_count": len(checks),
            "repository": str(root), "scene": str(scene_path),
            "scene_sha256": original_hash, "blender_version": bpy.app.version_string,
            "fitted_native_reference_count": len(roots),
            "native_LED_count": len(leds), "button_cap_count": len(caps),
            "unpacked_external_dependency_count": len(external_paths),
            "failures": failures, "checks": checks,
            "read_only": True, "physical_fit_qualified": False,
            "scope": "Native scene portability, embedded geometry and cap animation; "
                     "no rendering, ERC, DRC or physical-fit certification."}


original_frame = bpy.context.scene.frame_current
try:
    result = verify()
except Exception as error:
    result = {"passed": False, "read_only": True,
              "error": f"{type(error).__name__}: {error}"}
finally:
    bpy.context.scene.frame_set(original_frame)
    bpy.context.view_layer.update()
print(json.dumps(result, indent=2, allow_nan=False), flush=True)
if not result["passed"]:
    raise RuntimeError("Blender scene verification failed; see JSON output")
