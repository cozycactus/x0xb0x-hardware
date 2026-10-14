"""Export saved populated projects through native KiCad, with isolated outputs."""
from pathlib import Path
import argparse, concurrent.futures, datetime, hashlib, json, os, subprocess

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
DEST = WORK / 'visualization/blender-case-revision-8/board-meshes'
CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
parser = argparse.ArgumentParser()
parser.add_argument('--project-root', type=Path, default=WORK)
args = parser.parse_args()
env = dict(os.environ, XDG_CACHE_HOME=str(HERE / 'cache'), KICAD_CONFIG_HOME=str(HERE / 'config'))

def run(name):
    out = DEST / name
    out.mkdir(exist_ok=True)
    board = args.project_root / name / (name + '.kicad_pcb')
    result = out / (name + '.glb')
    cmd = [CLI, 'pcb', 'export', 'glb', '--force', '--include-tracks',
           '--include-pads', '--include-zones', '--include-inner-copper',
           '--include-silkscreen', '--include-soldermask', '-o', str(result), str(board)]
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    (out / 'export.stdout.log').write_text(p.stdout)
    (out / 'export.stderr.log').write_text(p.stderr)
    assert p.returncode == 0 and result.is_file(), (name, p.returncode, p.stdout, p.stderr)
    assert not any(s in (p.stdout + p.stderr).lower() for s in ['missing model', 'could not load', 'error:']), (p.stdout, p.stderr)
    final = DEST / (name + '.glb')
    final.write_bytes(result.read_bytes())
    return dict(board=name, timestamp_utc=start, command=cmd, exit_code=p.returncode,
                source_sha256=hashlib.sha256(board.read_bytes()).hexdigest(),
                output_sha256=hashlib.sha256(final.read_bytes()).hexdigest(),
                bytes=final.stat().st_size, stdout=p.stdout, stderr=p.stderr)

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    records = list(pool.map(run, ['mainboard', 'ioboard']))
(HERE / 'native-glb-exports.json').write_text(json.dumps(records, indent=2) + '\n')
print(json.dumps([{k: r[k] for k in ['board', 'exit_code', 'bytes', 'stderr']} for r in records], indent=2))
