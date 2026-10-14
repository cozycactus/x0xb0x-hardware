#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Check snapshot integrity without requiring KiCad or Blender."""
import argparse
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                    help="Repository checkout to verify")
ROOT = parser.parse_args().root.resolve()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def matches(path, expected):
    return path.is_file() and sha(path) == expected

def metadata(name):
    try:
        return json.loads((ROOT / name).read_text())
    except (OSError, ValueError) as error:
        print(json.dumps({"passed": False, "failures": [name],
                          "error": str(error)}, indent=2))
        raise SystemExit(1)

required = ["docs/repository-content.json", "PROJECT.json"]
missing = [name for name in required if not (ROOT / name).is_file()]
if missing:
    print(json.dumps({"passed": False, "failures": missing,
                      "scope": "Required repository metadata is missing."}, indent=2))
    raise SystemExit(1)

project = metadata("PROJECT.json")
summary_path = "kicad-working/" + project.get(
    "validation_summary", "validation/working-validation-summary-revision-10.json")
manifest = metadata("docs/repository-content.json")
failures = []
for name, record in manifest["files"].items():
    path = ROOT / name
    if not path.is_file() or path.stat().st_size != record["bytes"] or sha(path) != record["sha256"]:
        failures.append(name)
summary = metadata(summary_path)
for name, expected in summary["outputs"].items():
    path = ROOT / "kicad-working" / name
    if not matches(path, expected):
        failures.append("KiCad: " + name)
for name, expected in project["original_Eagle_files"].items():
    path = ROOT / "original-eagle" / name
    if not matches(path, expected):
        failures.append("Eagle: " + name)
if not matches(ROOT / "kicad-working" / project["blender_scene"], project["blender_sha256"]):
    failures.append("Blender scene")
result = {"passed": not failures, "repository_files_checked": len(manifest["files"]),
          "KiCad_project_files_checked": len(summary["outputs"]),
          "original_Eagle_files_checked": len(project["original_Eagle_files"]),
          "Blender_scene_checked": True, "failures": failures,
          "scope": "File integrity only; no ERC, DRC or physical-fit certification."}
print(json.dumps(result, indent=2))
raise SystemExit(0 if not failures else 1)
