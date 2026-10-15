"""Export both revision-20 PCBs to glTF and record every pad, with KiCad's own Python.

The GLB files (native-probes/, not tracked) feed the Blender revision-23 PTC update and
native terminal audit. The same kicad-cli options as the earlier native exports
and scripts/verify_kicad_blender_models.py are used; the PCB bytes are checked
before and after.

Run with KiCad's bundled Python from the repository root:
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
      kicad-working/validation/models-review-20/export_native_boards.py
"""
from pathlib import Path
import hashlib, json, os, subprocess

import pcbnew

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
PROBES = HERE / 'native-probes'
CLI = os.environ.get('KICAD_CLI', '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
ATTR = {pcbnew.PAD_ATTRIB_PTH: 'PTH', pcbnew.PAD_ATTRIB_NPTH: 'NPTH',
        pcbnew.PAD_ATTRIB_SMD: 'SMD', pcbnew.PAD_ATTRIB_CONN: 'CONN'}
env = dict(os.environ, XDG_CACHE_HOME=str(PROBES / 'cache'), KICAD_CONFIG_HOME=str(PROBES / 'config'))
PROBES.mkdir(exist_ok=True)
records, pads = {}, {}
for board in ('ioboard', 'mainboard'):
    pcb = WORK / board / f'{board}.kicad_pcb'
    before = sha(pcb)
    glb = PROBES / f'{board}.glb'
    cmd = [CLI, 'pcb', 'export', 'glb', '--force', '--no-board-body', '--user-origin', '0x0mm', '-o', str(glb), str(pcb)]
    run = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert run.returncode == 0 and glb.is_file(), run.stderr[-400:]
    b = pcbnew.LoadBoard(str(pcb))
    footprints = []
    for fp in b.GetFootprints():
        rows = []
        for p in fp.Pads():
            pos, drill = p.GetPosition(), p.GetDrillSize()
            rows.append(dict(number=p.GetNumber(), attribute=ATTR.get(p.GetAttribute(), str(p.GetAttribute())),
                             x_mm=pcbnew.ToMM(pos.x), y_mm=pcbnew.ToMM(pos.y),
                             drill_mm=[pcbnew.ToMM(drill.x), pcbnew.ToMM(drill.y)],
                             orientation_deg=p.GetOrientation().AsDegrees()))
        footprints.append(dict(reference=fp.GetReference(), flipped=bool(fp.IsFlipped()),
                               models=[m.m_Filename for m in fp.Models() if m.m_Show], pads=rows))
    after = sha(pcb)
    assert before == after
    pads[board] = dict(pcb_sha256=before, thickness_mm=pcbnew.ToMM(b.GetDesignSettings().GetBoardThickness()),
                       footprints=footprints)
    records[board] = dict(pcb=str(pcb.relative_to(WORK)), pcb_sha256=before, pcb_unchanged=True,
                          command=[c.replace(str(WORK), '<kicad-working>') for c in cmd],
                          glb=str(glb.relative_to(HERE)), glb_sha256=sha(glb), glb_bytes=glb.stat().st_size)
(PROBES / 'pads.json').write_text(json.dumps(pads, indent=1))
record = dict(passed=True, kicad_version=subprocess.check_output([CLI, '--version'], text=True).strip(),
              boards=records, pads_sha256=sha(PROBES / 'pads.json'), exports_tracked=False,
              note='GLB exports are regenerated from the tracked PCBs; only their hashes are recorded.')
(HERE / 'native-export-record.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
