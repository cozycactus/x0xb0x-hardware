#!/bin/zsh
# Regenerate every revision-15 verification report, render and figure from the
# frozen saved scenes. Never saves a scene. Run from anywhere:
#   kicad-working/visualization/blender-case-revision-15/verification/run_verification.sh
# Set BLENDER to override the macOS application path.
set -euo pipefail
HERE=${0:A:h}
B=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
R14=$HERE/../../blender-case-revision-14/x0xb0x-populated-with-case.blend
R15=$HERE/../x0xb0x-populated-with-case.blend
LOGS=$(mktemp -d)

run() {
  local log=$1; shift
  if ! "$B" --background --factory-startup "$@" > "$LOGS/$log.log" 2>&1; then
    echo "FAILED $log"; tail -25 "$LOGS/$log.log"; exit 1
  fi
  echo "ok $log"
}

run saved-scene --python-exit-code 1 --python "$HERE/audit_saved_scene.py"
run portability "$R15" --python-exit-code 1 --python "$HERE/audit_portability.py"
run seating-14 "$R14" --python-exit-code 1 --python "$HERE/measure_rear_seating.py" -- rear-seating-revision-14.json
run seating-15 "$R15" --python-exit-code 1 --python "$HERE/measure_rear_seating.py" -- rear-seating-audit.json
run contacts-14 "$R14" --python-exit-code 1 --python "$HERE/screen_io_contacts.py" -- io-contacts-revision-14.json
run contacts-15 "$R15" --python-exit-code 1 --python "$HERE/screen_io_contacts.py" -- io-contacts.json
run sections-14 "$R14" --python-exit-code 1 --python "$HERE/extract_sections.py" -- sections-revision-14.json POWER0 USB0 CV0 HEADPHONE0
run sections-15 "$R15" --python-exit-code 1 --python "$HERE/extract_sections.py" -- sections.json POWER0 USB0 CV0 HEADPHONE0
python3 -I "$HERE/make_section_figure.py"
rsvg-convert -o "$HERE/../rear-height-sections.png" "$HERE/../rear-height-sections.svg"
rm -f "$HERE/../render-records.json"
run render "$R15" --python-exit-code 1 --python "$HERE/../render_scene.py" -- \
  --views=assembled,rear,exploded,control-side,wiring-study,rear-openings-closeup,rear-midi-detail
echo "all done (logs in $LOGS)"
