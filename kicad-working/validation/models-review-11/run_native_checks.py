#!/usr/bin/env python3
from pathlib import Path
import argparse,concurrent.futures,datetime,hashlib,json,os,shutil,subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
a=argparse.ArgumentParser();a.add_argument('phase');a.add_argument('--project-root',type=Path);args=a.parse_args()
source=args.project_root or (HERE/'input-snapshot' if args.phase=='baseline' else ROOT)
snapshot=HERE/(args.phase+'-check-snapshot')
assert not snapshot.exists()
for name in ['mainboard','ioboard']:shutil.copytree(source/name,snapshot/name,ignore=shutil.ignore_patterns('*.lck','*.kicad_prl','*-backups','_autosave*','~*','.DS_Store'))
CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
version=subprocess.check_output([CLI,'--version'],text=True).strip()
env=dict(os.environ,XDG_CACHE_HOME=str(HERE/'cache'),KICAD_CONFIG_HOME=str(HERE/'config'))
def run(task):
 name,check=task;output=HERE/f'{name}-{check}-{args.phase}.json';input=snapshot/name/(name+('.kicad_pcb' if check=='drc' else '.kicad_sch'))
 cmd=[CLI,'pcb','drc','--refill-zones','--schematic-parity','--all-track-errors'] if check=='drc' else [CLI,'sch','erc']
 cmd+=['--format','json','--units','mm','--severity-all','--exit-code-violations','-o',str(output),str(input)]
 timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat();result=subprocess.run(cmd,capture_output=True,text=True,env=env)
 (HERE/f'{name}-{check}-{args.phase}.stdout.log').write_text(result.stdout);(HERE/f'{name}-{check}-{args.phase}.stderr.log').write_text(result.stderr)
 data=json.loads(output.read_text());assert result.returncode in [0,5]
 return dict(project=name,check=check,timestamp_utc=timestamp,version=version,command=cmd,exit_code=result.returncode,input_sha256=hashlib.sha256(input.read_bytes()).hexdigest(),output=str(output),report_parses=True,environment_overrides={k:env[k] for k in ['XDG_CACHE_HOME','KICAD_CONFIG_HOME']})
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(run,[(n,c) for n in ['mainboard','ioboard'] for c in ['drc','erc']]))
(HERE/(args.phase+'-run-records.json')).write_text(json.dumps(records,indent=2)+'\n');print(json.dumps([dict(project=x['project'],check=x['check'],version=x['version'],exit_code=x['exit_code']) for x in records],indent=2))
