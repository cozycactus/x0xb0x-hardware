#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Check every placed KiCad 3D model's leads against the real PCB drills.

Run with Blender (verified with 5.2.2) and KiCad's command-line tool:
  blender --background --factory-startup --python-exit-code 1 \
      --python scripts/verify_drill_fit.py

Both KiCad PCBs are exported to glTF in a temporary directory with a private
KiCad configuration (`--no-board-body --user-origin 0x0mm`, the options of the
native exports). Drilled pads are read from the PCB files themselves. Each model
is cut at both board faces (0.02 mm inside) and at mid-depth, in the board frame:

* every drilled hole must contain lead geometry at mid-depth;
* every section point belongs to the pad with the nearest drill wall; the largest
  distance beyond that wall is the pad's nominal interference;
* points more than 1 mm outside every wall are geometry crossing the board away
  from a hole.

docs/drill-fit-allowances.json declares the known exceptions with their source
reasons: holes that are empty by design, and nominal interferences up to a
recorded depth. Anything else fails, as does an allowance exceeded by more than
0.005 mm. Allowances that are no longer needed are reported, not failed. Set
KICAD_CLI to override the macOS default path. JSON is printed to stdout; the
temporary directory is removed and no repository file is written. Nominal
geometry only: tolerances, elastic leads and assembly are outside its scope.
"""

import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import bpy
import numpy as np


BOARDS = ("mainboard", "ioboard")
DEFAULT_KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
FACE_INSET_MM = 0.02
NEAR_WALL_MM = 1.0
ALLOWANCE_SLACK_MM = 0.005
ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def drilled_pads(pcb):
    """Drilled pads per reference in board millimetres (KiCad Y down) and the board thickness, from the PCB."""
    sys.path.insert(0, str(ROOT / "kicad-import/validation"))
    from verify_native_projects import children, one, parse_sexpr, property_value
    atoms = lambda node: [x for x in node[1:] if not isinstance(x, list)]  # noqa: E731
    tree = parse_sexpr(pcb.read_text(encoding="utf-8"))
    result = {}
    for fp in children(tree, "footprint"):
        at = atoms(one(fp, "at"))
        fx, fy = float(at[0]), float(at[1])
        angle = math.radians(float(at[2]) if len(at) > 2 else 0.0)
        pads = []
        for pad in children(fp, "pad"):
            if pad[2] not in ("thru_hole", "np_thru_hole"):
                continue
            pa = atoms(one(pad, "at"))
            px, py = float(pa[0]), float(pa[1])
            drill = [float(v) for v in atoms(one(pad, "drill")) if v != "oval"]
            pads.append({"number": str(pad[1]), "drill_mm": drill * 2 if len(drill) == 1 else drill,
                         "x_mm": fx + px * math.cos(angle) + py * math.sin(angle),
                         "y_mm": fy - px * math.sin(angle) + py * math.cos(angle),
                         "orientation_deg": float(pa[2]) if len(pa) > 2 else 0.0})
        result[property_value(fp, "Reference", "reference")] = {
            "flipped": atoms(one(fp, "layer"))[0] == "B.Cu", "pads": pads}
    return result, float(atoms(one(one(tree, "general"), "thickness"))[0])


def world_triangles(root):
    out = []
    for obj in [root, *root.children_recursive]:
        if obj.type != "MESH" or not obj.data.polygons:
            continue
        matrix = np.array(obj.matrix_world)
        co = np.empty(len(obj.data.vertices) * 3)
        obj.data.vertices.foreach_get("co", co)
        world = (co.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]) * 1000
        obj.data.calc_loop_triangles()
        tri = np.empty(len(obj.data.loop_triangles) * 3, dtype=np.int64)
        obj.data.loop_triangles.foreach_get("vertices", tri)
        out.append(world[tri.reshape(-1, 3)])
    return np.vstack(out) if out else np.zeros((0, 3, 3))


def section(triangles, z):
    s = triangles[:, :, 2] - z
    crossing = (s.min(1) < 0) & (s.max(1) > 0)
    points = []
    for tri, ss in zip(triangles[crossing], s[crossing]):
        for a, b in ((0, 1), (1, 2), (2, 0)):
            if (ss[a] < 0) != (ss[b] < 0):
                points.append((tri[a] + (tri[b] - tri[a]) * (ss[a] / (ss[a] - ss[b])))[:2])
    return np.array(points) if points else np.zeros((0, 2))


def beyond_wall(points, pad):
    """Distance of each point beyond the drill wall (negative inside), slots included."""
    dx, dy = pad["drill_mm"]
    radius = min(dx, dy) / 2
    half = max(dx, dy) / 2 - radius
    angle = math.radians(pad["orientation_deg"])
    axis = np.array((math.cos(angle), math.sin(angle)) if dx >= dy else (-math.sin(angle), math.cos(angle)))
    relative = points - np.array([pad["x_mm"], -pad["y_mm"]])
    t = np.clip(relative @ axis, -half, half)
    return np.linalg.norm(relative - np.outer(t, axis), axis=1) - radius


def measure(triangles, pads, top, thickness):
    heights = {"top": top - FACE_INSET_MM, "mid": top - thickness / 2,
               "bottom": top - thickness + FACE_INSET_MM}
    worst, filled, stray = {}, set(), 0
    for name, z in heights.items():
        points = section(triangles, z)
        if not len(points):
            continue
        excess = np.array([beyond_wall(points, pad) for pad in pads])
        owner, assigned = excess.argmin(0), excess.min(0) < NEAR_WALL_MM
        stray += int((~assigned).sum())
        for i, pad in enumerate(pads):
            mine = assigned & (owner == i)
            if not mine.any():
                continue
            worst[pad["number"]] = max(worst.get(pad["number"], -1e9), float(excess[i][mine].max()))
            if name == "mid" and (excess[i][mine] < 0).any():
                filled.add(pad["number"])
    return worst, filled, stray


def verify():
    allowances = json.loads((ROOT / "docs/drill-fit-allowances.json").read_text())
    empty = {(e["board"], e["reference"], e["pad"]): e["reason"] for e in allowances["empty_by_design"]}
    allowed = {(a["board"], a["reference"], a["pad"]): a for group in allowances["nominal_interference"]
               for a in ({"board": group["board"], "reference": r, "pad": p,
                          "max_interference_mm": group["max_interference_mm"], "reason": group["reason"]}
                         for r in group["references"] for p in group["pads"])}
    kicad_cli = os.environ.get("KICAD_CLI", DEFAULT_KICAD_CLI)
    if not Path(kicad_cli).is_file():
        raise RuntimeError(f"KiCad CLI not found at {kicad_cli}; set KICAD_CLI")
    checks, findings, exports, seen = [], [], {}, set()

    def check(name, passed, **details):
        checks.append({"check": name, "passed": bool(passed), **details})

    work = Path(tempfile.mkdtemp(prefix="kicad-drill-fit-"))
    environment = dict(os.environ, XDG_CONFIG_HOME=str(work / "config"),
                       XDG_CACHE_HOME=str(work / "cache"), KICAD_CONFIG_HOME=str(work / "config"))
    models = 0
    try:
        version = subprocess.run([kicad_cli, "version"], capture_output=True, text=True,
                                 env=environment, timeout=120).stdout.strip()
        for board in BOARDS:
            pcb = ROOT / "kicad-working" / board / f"{board}.kicad_pcb"
            before = sha256(pcb)
            pads, thickness = drilled_pads(pcb)
            glb = work / f"{board}.glb"
            run = subprocess.run([kicad_cli, "pcb", "export", "glb", "--force", "--no-board-body",
                                  "--user-origin", "0x0mm", "-o", str(glb), str(pcb)],
                                 capture_output=True, text=True, env=environment, timeout=1800)
            if run.returncode != 0 or not glb.is_file():
                raise RuntimeError(f"KiCad export failed for {board}: {run.stderr.strip()[-400:]}")
            exports[board] = {"pcb": str(pcb.relative_to(ROOT)), "pcb_sha256": before, "glb_sha256": sha256(glb)}
            bpy.ops.wm.read_factory_settings(use_empty=True)
            bpy.ops.import_scene.gltf(filepath=str(glb))
            base = next(o for o in bpy.data.objects if o.parent is None)
            roots = {o.name: o for o in base.children}
            tops = {round(o.matrix_world.translation.z * 1000, 4) for r, o in roots.items()
                    if r in pads and not pads[r]["flipped"]}
            check(f"{board}: top-side models share one seating plane", len(tops) == 1, planes_mm=sorted(tops))
            top = max(tops)
            for reference, root in sorted(roots.items()):
                drilled = pads.get(reference, {}).get("pads", [])
                if not drilled:
                    continue
                models += 1
                worst, filled, stray = measure(world_triangles(root), drilled, top, thickness)
                if stray:
                    findings.append({"board": board, "reference": reference, "problem": "geometry crosses the board "
                                     "away from every hole", "section_points": stray})
                for pad in drilled:
                    key = (board, reference, pad["number"])
                    if key in empty:
                        seen.add(key)
                        if pad["number"] in filled:
                            findings.append({"board": board, "reference": reference, "pad": pad["number"],
                                             "problem": "declared empty hole now has a lead"})
                        continue
                    if pad["number"] not in filled:
                        findings.append({"board": board, "reference": reference, "pad": pad["number"],
                                         "problem": "no lead in drilled hole"})
                    depth = worst.get(pad["number"], -1.0)
                    if depth <= 0:
                        continue
                    seen.add(key)
                    limit = allowed.get(key, {}).get("max_interference_mm")
                    if limit is None or depth > limit + ALLOWANCE_SLACK_MM:
                        findings.append({"board": board, "reference": reference, "pad": pad["number"],
                                         "problem": "undeclared or increased nominal interference",
                                         "interference_mm": round(depth, 4), "allowance_mm": limit})
            check(f"{board}: KiCad export and pad read left the PCB bytes unchanged", sha256(pcb) == before)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    check("Every fitted model with drilled holes was measured", models > 0, models=models)
    check("No lead, interference or crossing outside the declared allowances", not findings,
          findings=findings[:50], finding_count=len(findings))
    resolved = sorted("/".join(k) for k in set(allowed) | set(empty) if k not in seen)
    failures = [c for c in checks if not c["passed"]]
    return {"passed": not failures, "check_count": len(checks), "repository": str(ROOT),
            "kicad_version": version, "blender_version": bpy.app.version_string,
            "measured_models": models, "declared_interference_pads": len(allowed),
            "declared_empty_holes": len(empty), "allowances_no_longer_needed": resolved,
            "exports": exports, "failures": failures, "checks": checks,
            "read_only": True, "physical_fit_qualified": False,
            "scope": "Nominal native-model sections against nominal drills; tolerances, elastic leads, solder "
                     "and assembly are not modelled."}


try:
    result = verify()
except Exception as error:
    result = {"passed": False, "read_only": True, "error": f"{type(error).__name__}: {error}"}
print(json.dumps(result, indent=2, allow_nan=False), flush=True)
if not result["passed"]:
    raise RuntimeError("Drill-fit verification failed; see JSON output")
