#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Check snapshot integrity without requiring KiCad or Blender."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

manifest = json.loads((ROOT / "docs/repository-content.json").read_text())
failures = []
for name, record in manifest["files"].items():
    path = ROOT / name
    if not path.is_file() or path.stat().st_size != record["bytes"] or sha(path) != record["sha256"]:
        failures.append(name)
summary = json.loads((ROOT / "kicad-working/validation/working-validation-summary-revision-10.json").read_text())
for name, expected in summary["outputs"].items():
    path = ROOT / "kicad-working" / name
    if not path.is_file() or sha(path) != expected:
        failures.append("KiCad: " + name)
project = json.loads((ROOT / "PROJECT.json").read_text())
for name, expected in project["original_Eagle_files"].items():
    path = ROOT / "original-eagle" / name
    if not path.is_file() or sha(path) != expected:
        failures.append("Eagle: " + name)
if sha(ROOT / "kicad-working" / project["blender_scene"]) != project["blender_sha256"]:
    failures.append("Blender scene")
result = {"passed": not failures, "repository_files_checked": len(manifest["files"]),
          "KiCad_project_files_checked": len(summary["outputs"]),
          "original_Eagle_files_checked": len(project["original_Eagle_files"]),
          "Blender_scene_checked": True, "failures": failures,
          "scope": "File integrity only; no ERC, DRC or physical-fit certification."}
print(json.dumps(result, indent=2))
raise SystemExit(0 if not failures else 1)
