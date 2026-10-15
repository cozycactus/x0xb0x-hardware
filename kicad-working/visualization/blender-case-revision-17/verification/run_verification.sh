#!/bin/zsh
# Regenerate every revision-17 verification report and render from the frozen
# saved scenes. Never saves a scene. Run from anywhere:
#   kicad-working/visualization/blender-case-revision-17/verification/run_verification.sh
# Set BLENDER (and KICAD_CLI for the KiCad comparison) to override macOS paths.
set -euo pipefail
HERE=${0:A:h}
B=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
R17=$HERE/../x0xb0x-populated-with-case.blend
LOGS=$(mktemp -d)

run() {
  local log=$1; shift
  if ! "$B" --background --factory-startup "$@" > "$LOGS/$log.log" 2>&1; then
    echo "FAILED $log"; tail -25 "$LOGS/$log.log"; exit 1
  fi
  echo "ok $log"
}

run saved-scene --python-exit-code 1 --python "$HERE/audit_saved_scene.py"
run portability "$R17" --python-exit-code 1 --python "$HERE/audit_portability.py"
run kicad-models "$R17" --python-exit-code 1 --python "$HERE/audit_kicad_models.py"
run terminal-sheet "$R17" --python-exit-code 1 --python "$HERE/render_terminal_sheet.py"
rm -f "$HERE/../render-records.json"
run render "$R17" --python-exit-code 1 --python "$HERE/../render_scene.py" -- \
  --views=assembled,rear,exploded,control-side,io-terminals-detail
echo "all done (logs in $LOGS)"
