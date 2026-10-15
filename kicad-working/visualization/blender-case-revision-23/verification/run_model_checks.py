"""Replay the three shared current native checks without saving any scene."""
from pathlib import Path
import runpy
HERE=Path(__file__).resolve().parent
for name in ["audit_portability.py","audit_kicad_models.py","audit_terminal_joins.py"]:
    runpy.run_path(str(HERE/name))
