# Separate-terminal BRep review

The current KiCad19 models for12 terminal-completed families, at25 references, were freshly loaded into FreeCAD. All151 pairs of separately specified solder-terminal solids were checked for common volume and nearest distance. No pair overlaps or touches. Each file hash and pair result is recorded in `terminal-pair-audit.json`; the replay script is read-only.

The corrected USB model contains shell, insulator, six solder terminals and four gold mating strips; this audit explicitly selects its six solder terminals and verifies their below-board extents. Other families retain their documented appended-terminal ordering.

This examines separate solder-lead geometry only. It excludes intentional lead-to-body embedding and does not test internal switch/jack contacts, insulation materials, voltage ratings, tolerance, or actual electrical isolation. No model, PCB, project rule or Blender scene was changed. Current native outputs remain KiCad19 / Blender22.
