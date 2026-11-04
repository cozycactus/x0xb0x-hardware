#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Check that the loaded assembly embeds exactly the current KiCad 3D models.

Run with Blender (verified with 5.2.2) and KiCad's command-line tool:
  blender --background <assembly.blend> --python-exit-code 1 \
      --python scripts/verify_kicad_blender_models.py

Both KiCad PCBs are exported to glTF in a temporary directory with a private
KiCad configuration, using the same options as the earlier native exports
(`--no-board-body --user-origin 0x0mm`) plus `--no-dnp`: the scene shows the
boards as built, so footprints marked do-not-place have no model in it. Every
placed model is then compared
with the scene's native reference root of the same board and designator:
footprint frame relative to the board root, and model geometry in that frame
(bounds, centroid, surface area, vertex and triangle counts). Set KICAD_CLI to
override the macOS default path. JSON is printed to stdout; the temporary
directory is removed and no repository file is written. The PCB bytes are
checked before and after the export.

Board substrate meshes and Blender-only presentation geometry (enclosure,
panels, caps, knobs, hardware, legends, wiring study) are outside its scope.
"""

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import bpy
import numpy as np


BOARDS = ("mainboard", "ioboard")
DEFAULT_KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
FRAME_TOLERANCE = 1e-6       # metres per unit of the 4x4 frame
LENGTH_TOLERANCE_MM = 1e-3
AREA_RELATIVE_TOLERANCE = 1e-4


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def signature(root):
    """Model geometry of every mesh under root, expressed in root's frame (mm)."""
    inverse = root.matrix_world.inverted()
    points, area, vertices, triangles = [], 0.0, 0, 0
    for obj in [root, *root.children_recursive]:
        if obj.type != "MESH" or not obj.data.polygons:
            continue
        matrix = np.array(inverse @ obj.matrix_world)
        co = np.empty(len(obj.data.vertices) * 3)
        obj.data.vertices.foreach_get("co", co)
        world = co.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]
        obj.data.calc_loop_triangles()
        tri = np.empty(len(obj.data.loop_triangles) * 3, dtype=np.int64)
        obj.data.loop_triangles.foreach_get("vertices", tri)
        tri = tri.reshape(-1, 3)
        cross = np.cross(world[tri[:, 1]] - world[tri[:, 0]],
                         world[tri[:, 2]] - world[tri[:, 0]])
        area += float(np.linalg.norm(cross, axis=1).sum() / 2)
        points.append(world)
        vertices += len(world)
        triangles += len(tri)
    if not points:
        return None
    mm = np.vstack(points) * 1000
    return {"bounds_mm": [*mm.min(0).tolist(), *mm.max(0).tolist()],
            "centroid_mm": mm.mean(0).tolist(), "area_mm2": area * 1e6,
            "vertices": vertices, "triangles": triangles}


def frame(root, base):
    return [list(row) for row in base.matrix_world.inverted() @ root.matrix_world]


def compare(scene_row, kicad_row):
    frame_diff = max(abs(a - b) for ra, rb in zip(scene_row["frame"], kicad_row["frame"])
                     for a, b in zip(ra, rb))
    result = {"frame_max_abs_diff": frame_diff}
    s, k = scene_row["signature"], kicad_row["signature"]
    if s is None or k is None:
        result["identical"] = s is None and k is None and frame_diff < FRAME_TOLERANCE
        result["missing_mesh"] = {"scene": s is None, "kicad": k is None}
        return result
    result.update(
        bounds_max_diff_mm=max(abs(a - b) for a, b in zip(s["bounds_mm"], k["bounds_mm"])),
        centroid_max_diff_mm=max(abs(a - b) for a, b in zip(s["centroid_mm"], k["centroid_mm"])),
        area_relative_diff=abs(s["area_mm2"] - k["area_mm2"]) / max(k["area_mm2"], 1e-12),
        vertices={"scene": s["vertices"], "kicad": k["vertices"]},
        triangles={"scene": s["triangles"], "kicad": k["triangles"]})
    result["identical"] = (frame_diff < FRAME_TOLERANCE
                           and result["bounds_max_diff_mm"] < LENGTH_TOLERANCE_MM
                           and result["centroid_max_diff_mm"] < LENGTH_TOLERANCE_MM
                           and result["area_relative_diff"] < AREA_RELATIVE_TOLERANCE
                           and s["triangles"] == k["triangles"])
    return result


def verify():
    scene_path = Path(bpy.data.filepath).resolve()
    if not bpy.data.filepath or not scene_path.is_file():
        raise RuntimeError("Load a saved assembly .blend before verification")
    root = next((p for p in scene_path.parents if (p / "PROJECT.json").is_file()), None)
    if root is None:
        raise RuntimeError("The loaded scene has no repository PROJECT.json")
    project = json.loads((root / "PROJECT.json").read_text())
    scene_hash = sha256(scene_path)
    kicad_cli = os.environ.get("KICAD_CLI", DEFAULT_KICAD_CLI)
    if not Path(kicad_cli).is_file():
        raise RuntimeError(f"KiCad CLI not found at {kicad_cli}; set KICAD_CLI")

    scene = {}
    for obj in bpy.data.objects:
        if obj.get("source_reference") and obj.get("source_board") in BOARDS:
            key = (obj["source_board"], obj["source_reference"])
            scene[key] = {"frame": frame(obj, obj.parent), "signature": signature(obj)}

    work = Path(tempfile.mkdtemp(prefix="kicad-blender-models-"))
    environment = dict(os.environ, XDG_CONFIG_HOME=str(work / "config"),
                       XDG_CACHE_HOME=str(work / "cache"), KICAD_CONFIG_HOME=str(work / "config"))
    kicad, exports = {}, {}
    try:
        version = subprocess.run([kicad_cli, "version"], capture_output=True, text=True,
                                 env=environment, timeout=120).stdout.strip()
        for board in BOARDS:
            pcb = root / "kicad-working" / board / f"{board}.kicad_pcb"
            before = sha256(pcb)
            glb = work / f"{board}.glb"
            run = subprocess.run([kicad_cli, "pcb", "export", "glb", "--force", "--no-board-body", "--no-dnp",
                                  "--user-origin", "0x0mm", "-o", str(glb), str(pcb)],
                                 capture_output=True, text=True, env=environment, timeout=1800)
            exports[board] = {"pcb": str(pcb.relative_to(root)), "pcb_sha256": before,
                              "pcb_unchanged": sha256(pcb) == before, "exit_code": run.returncode,
                              "glb_sha256": sha256(glb) if glb.is_file() else None}
            if run.returncode != 0 or not glb.is_file():
                raise RuntimeError(f"KiCad export failed for {board}: {run.stderr.strip()[-400:]}")
            bpy.ops.wm.read_factory_settings(use_empty=True)
            bpy.ops.import_scene.gltf(filepath=str(glb))
            base = next(o for o in bpy.data.objects if o.parent is None)
            for obj in base.children:
                kicad[(board, obj.name)] = {"frame": frame(obj, base), "signature": signature(obj)}
    finally:
        shutil.rmtree(work, ignore_errors=True)

    checks, differences = [], []

    def check(name, passed, **details):
        checks.append({"check": name, "passed": bool(passed), **details})

    for board in BOARDS:
        s = sorted(r for b, r in scene if b == board)
        k = sorted(r for b, r in kicad if b == board)
        check(f"{board}: scene and KiCad place the same designators", s == k,
              scene_count=len(s), kicad_count=len(k),
              only_in_scene=sorted(set(s) - set(k)), only_in_kicad=sorted(set(k) - set(s)))
        check(f"{board}: KiCad export left the PCB bytes unchanged", exports[board]["pcb_unchanged"])
    rows = {}
    for key in sorted(set(scene) & set(kicad)):
        rows[key] = compare(scene[key], kicad[key])
        if not rows[key]["identical"]:
            differences.append({"board": key[0], "reference": key[1], **rows[key]})
    for board in BOARDS:
        board_rows = [r for (b, _), r in rows.items() if b == board]
        check(f"{board}: every placed model frame and geometry matches the scene",
              board_rows and all(r["identical"] for r in board_rows), compared=len(board_rows),
              differing=sum(not r["identical"] for r in board_rows))
    check("Read-only verification left the scene bytes unchanged", sha256(scene_path) == scene_hash)

    numeric = lambda name: max((r.get(name, 0.0) for r in rows.values()), default=None)
    failures = [c for c in checks if not c["passed"]]
    return {"passed": not failures, "check_count": len(checks), "repository": str(root),
            "scene": str(scene_path), "scene_sha256": scene_hash,
            "declared_scene": scene_path == (root / "kicad-working" / project["blender_scene"]).resolve(),
            "blender_version": bpy.app.version_string, "kicad_version": version,
            "compared_references": len(rows), "identical_references": sum(r["identical"] for r in rows.values()),
            "total_triangles": sum(kicad[k]["signature"]["triangles"] for k in rows if kicad[k]["signature"]),
            "max_differences": {name: numeric(name) for name in
                                ("frame_max_abs_diff", "bounds_max_diff_mm", "centroid_max_diff_mm",
                                 "area_relative_diff")},
            "tolerances": {"frame": FRAME_TOLERANCE, "length_mm": LENGTH_TOLERANCE_MM,
                           "area_relative": AREA_RELATIVE_TOLERANCE, "triangle_count": "equal"},
            "exports": exports, "failures": failures, "checks": checks, "differences": differences,
            "read_only": True, "physical_fit_qualified": False,
            "scope": "Placed KiCad component models versus the scene's embedded native meshes; "
                     "do-not-place footprints, board substrate and Blender-only presentation "
                     "geometry are not compared."}


try:
    result = verify()
except Exception as error:
    result = {"passed": False, "read_only": True, "error": f"{type(error).__name__}: {error}"}
print(json.dumps(result, indent=2, allow_nan=False), flush=True)
if not result["passed"]:
    raise RuntimeError("KiCad/Blender model verification failed; see JSON output")
