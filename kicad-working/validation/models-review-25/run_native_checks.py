#!/usr/bin/env python3
"""Fresh KiCad ERC/DRC for both boards (revision 25) with the revision 11 command lines.

Runs on a temporary copy of each project so the working files are never written;
the copied inputs are hash-checked against the working files.
"""
from pathlib import Path
import concurrent.futures, datetime, hashlib, json, os, shutil, subprocess, tempfile

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
CLI = os.environ.get('KICAD_CLI', '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
version = subprocess.check_output([CLI, '--version'], text=True).strip()
env = dict(os.environ, XDG_CACHE_HOME=str(HERE / 'native-probes/cache'),
           KICAD_CONFIG_HOME=str(HERE / 'native-probes/config'))
snapshot = Path(tempfile.mkdtemp(prefix='x0xb0x-rev25-checks-'))
for name in ('mainboard', 'ioboard'):
    shutil.copytree(WORK / name, snapshot / name, ignore=shutil.ignore_patterns(
        '3dmodels', '*.lck', '*.kicad_prl', '*-backups', '_autosave*', '~*', '.DS_Store'))


def run(task):
    name, check = task
    output = HERE / f'{name}-{check}.json'
    source = WORK / name / (name + ('.kicad_pcb' if check == 'drc' else '.kicad_sch'))
    copied = snapshot / name / source.name
    assert sha(copied) == sha(source)
    cmd = ([CLI, 'pcb', 'drc', '--refill-zones', '--schematic-parity', '--all-track-errors'] if check == 'drc'
           else [CLI, 'sch', 'erc'])
    cmd += ['--format', 'json', '--units', 'mm', '--severity-all', '--exit-code-violations', '-o', str(output),
            str(copied)]
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    json.loads(output.read_text())
    assert result.returncode in (0, 5), (name, check, result.returncode, result.stderr)
    return dict(project=name, check=check, timestamp_utc=stamp, version=version,
                command=[c.replace(str(snapshot), '<temporary-copy>') for c in cmd],
                exit_code=result.returncode, input=str(source.relative_to(WORK)), input_sha256=sha(source),
                output=output.name, report_parses=True)


with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    records = list(pool.map(run, [(n, c) for n in ('mainboard', 'ioboard') for c in ('drc', 'erc')]))
shutil.rmtree(snapshot)
(HERE / 'native-run-records.json').write_text(json.dumps(records, indent=2) + '\n')
print(json.dumps([{k: r[k] for k in ('project', 'check', 'version', 'exit_code')} for r in records], indent=2))
