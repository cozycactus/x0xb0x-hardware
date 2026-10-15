#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Check that every drawing-derived terminal joins its component body.

Run with Blender (verified with 5.2.2) and KiCad's command-line tool:
  blender --background --factory-startup --python-exit-code 1 \
      --python scripts/verify_terminal_joins.py

Both KiCad PCBs are exported to glTF in a temporary directory with a private KiCad
configuration (`--no-board-body --user-origin 0x0mm`). The check covers every
placed reference whose 3D model is one of the project's drawing-derived terminal
models (`*_Terminals.step`). In the native mesh the terminals carry their own tin
material; each connected terminal piece must intersect or touch (within 0.005 mm)
the rest of the model. A terminal hanging next to its body fails. Set KICAD_CLI to
override the macOS default path. JSON is printed to stdout; the temporary directory
is removed and no repository file is written.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import bmesh
import bpy
from mathutils.bvhtree import BVHTree

BOARDS = ("mainboard", "ioboard")
DEFAULT_KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
TIN = (0.5071, 0.5225, 0.5382)          # sRGB 0.74/0.75/0.76 terminal colour as exported by KiCad
TOUCH_MM = 0.005
ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def terminal_references(pcb):
    sys.path.insert(0, str(ROOT / "kicad-import/validation"))
    from verify_native_projects import children, parse_sexpr, property_value
    refs = {}
    for fp in children(parse_sexpr(pcb.read_text(encoding="utf-8")), "footprint"):
        paths = [m[1] for m in children(fp, "model")]
        if any(p.endswith("_Terminals.step") for p in paths):
            refs[property_value(fp, "Reference", "reference")] = next(p for p in paths if p.endswith("_Terminals.step"))
    return refs


def is_tin(material):
    if material is None or not material.use_nodes:
        return False
    colour = material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value
    return max(abs(a - b) for a, b in zip(colour[:3], TIN)) < 2e-3


def split(root):
    """World-space (mm) bmesh of terminal faces and of all other faces under one reference."""
    tin, body = bmesh.new(), bmesh.new()
    for obj in [root, *root.children_recursive]:
        if obj.type != "MESH":
            continue
        for target, want in ((tin, True), (body, False)):
            part = bmesh.new()
            part.from_mesh(obj.data)
            part.transform(obj.matrix_world)
            drop = [f for f in part.faces
                    if is_tin(obj.data.materials[f.material_index] if obj.data.materials else None) != want]
            bmesh.ops.delete(part, geom=drop, context="FACES")
            scratch = bpy.data.meshes.new("scratch")
            part.to_mesh(scratch)
            target.from_mesh(scratch)
            bpy.data.meshes.remove(scratch)
            part.free()
    for b in (tin, body):
        bmesh.ops.scale(b, vec=(1000, 1000, 1000), verts=b.verts)
    # KiCad exports unwelded faces; weld coincident vertices so each terminal is one connected piece.
    bmesh.ops.remove_doubles(tin, verts=tin.verts, dist=1e-4)
    return tin, body


def pieces(b):
    """Connected face sets of a bmesh."""
    b.faces.ensure_lookup_table()
    seen, out = set(), []
    for start in b.faces:
        if start.index in seen:
            continue
        stack, group = [start], []
        seen.add(start.index)
        while stack:
            face = stack.pop()
            group.append(face)
            for vert in face.verts:
                for nxt in vert.link_faces:
                    if nxt.index not in seen:
                        seen.add(nxt.index)
                        stack.append(nxt)
        out.append(group)
    return out


def verify():
    kicad_cli = os.environ.get("KICAD_CLI", DEFAULT_KICAD_CLI)
    if not Path(kicad_cli).is_file():
        raise RuntimeError(f"KiCad CLI not found at {kicad_cli}; set KICAD_CLI")
    checks, detached, rows = [], [], {}

    def check(name, passed, **details):
        checks.append({"check": name, "passed": bool(passed), **details})

    work = Path(tempfile.mkdtemp(prefix="kicad-terminal-joins-"))
    environment = dict(os.environ, XDG_CONFIG_HOME=str(work / "config"),
                       XDG_CACHE_HOME=str(work / "cache"), KICAD_CONFIG_HOME=str(work / "config"))
    try:
        version = subprocess.run([kicad_cli, "version"], capture_output=True, text=True,
                                 env=environment, timeout=120).stdout.strip()
        for board in BOARDS:
            pcb = ROOT / "kicad-working" / board / f"{board}.kicad_pcb"
            before = sha256(pcb)
            refs = terminal_references(pcb)
            glb = work / f"{board}.glb"
            run = subprocess.run([kicad_cli, "pcb", "export", "glb", "--force", "--no-board-body",
                                  "--user-origin", "0x0mm", "-o", str(glb), str(pcb)],
                                 capture_output=True, text=True, env=environment, timeout=1800)
            if run.returncode != 0 or not glb.is_file():
                raise RuntimeError(f"KiCad export failed for {board}: {run.stderr.strip()[-400:]}")
            bpy.ops.wm.read_factory_settings(use_empty=True)
            bpy.ops.import_scene.gltf(filepath=str(glb))
            base = next(o for o in bpy.data.objects if o.parent is None)
            roots = {o.name: o for o in base.children}
            for ref, model in sorted(refs.items()):
                tin, body = split(roots[ref])
                body_tree = BVHTree.FromBMesh(body)
                groups = pieces(tin)
                gaps = []
                for group in groups:
                    piece = bmesh.new()
                    lookup = {}
                    for face in group:
                        verts = []
                        for v in face.verts:
                            if v.index not in lookup:
                                lookup[v.index] = piece.verts.new(v.co)
                            verts.append(lookup[v.index])
                        piece.faces.new(verts)
                    tree = BVHTree.FromBMesh(piece)
                    if tree.overlap(body_tree):
                        gaps.append(0.0)
                    else:
                        gaps.append(min(body_tree.find_nearest(v.co)[3] for v in piece.verts))
                    piece.free()
                tin.free()
                body.free()
                rows[f"{board}/{ref}"] = {"model": model.split("/")[-1], "terminal_pieces": len(groups),
                                          "largest_gap_mm": round(max(gaps), 4) if gaps else None}
                for i, gap in enumerate(gaps):
                    if gap > TOUCH_MM:
                        detached.append({"board": board, "reference": ref, "piece": i, "gap_mm": round(gap, 4)})
                if not groups:
                    detached.append({"board": board, "reference": ref, "problem": "no terminal geometry found"})
            check(f"{board}: KiCad export left the PCB bytes unchanged", sha256(pcb) == before)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    check("Drawing-derived terminal models are placed", len(rows) > 0, references=len(rows))
    check("Every terminal piece joins its body", not detached, detached=detached[:50], detached_count=len(detached))
    failures = [c for c in checks if not c["passed"]]
    return {"passed": not failures, "check_count": len(checks), "repository": str(ROOT),
            "kicad_version": version, "blender_version": bpy.app.version_string,
            "references_checked": len(rows), "terminal_pieces": sum(r["terminal_pieces"] for r in rows.values()),
            "references": rows, "failures": failures, "checks": checks, "read_only": True,
            "scope": "Drawing-derived terminal models only; their terminals are identified by the tin material."}


try:
    result = verify()
except Exception as error:
    result = {"passed": False, "read_only": True, "error": f"{type(error).__name__}: {error}"}
print(json.dumps(result, indent=2, allow_nan=False), flush=True)
if not result["passed"]:
    raise RuntimeError("Terminal join verification failed; see JSON output")
