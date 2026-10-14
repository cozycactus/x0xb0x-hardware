"""Read immutable baseline board; export isolated canonical-geometry probes."""
from pathlib import Path
import hashlib,json,re,subprocess,os,concurrent.futures
H=Path(__file__).resolve().parent
W=H.parents[2]
source=H.parent/'input-snapshot/ioboard/ioboard.kicad_pcb'
text=source.read_text()
before=hashlib.sha256(source.read_bytes()).hexdigest()

def end(start):
    depth=0;quoted=False;escaped=False
    for i in range(start,len(text)):
        c=text[i]
        if quoted:
            if escaped:escaped=False
            elif c=='\\':escaped=True
            elif c=='"':quoted=False
        elif c=='"':quoted=True
        elif c=='(':depth+=1
        elif c==')':
            depth-=1
            if not depth:return i+1
    raise ValueError('Unclosed source block')

ranges=[]
for m in re.finditer(r'^\t\(footprint ',text,re.M):
    a=m.start()+1;b=end(a);block=text[a:b]
    ref=re.search(r'\(property "Reference" "([^"]+)"',block).group(1)
    ranges.append((a,b,ref,block))
manifest_path=H/'rear-connector-quality-corrected-manifest.json'
if not manifest_path.exists():manifest_path=H/'rear-connector-quality-manifest.json'
manifest=json.loads(manifest_path.read_text())
rows=[]
for part in manifest['parts']:
    ref=part['references'][0]
    d=H/'native-probes'/part['id'];d.mkdir(parents=True,exist_ok=True)
    selected=next(b for _,_,r,b in ranges if r==ref)
    selected=re.sub(r'(\(model\s+)"[^"]*"',
                    lambda m:m.group(1)+json.dumps(part['source_model']),
                    selected,count=1)
    pieces=[];cursor=0
    for a,b,r,block in ranges:
        pieces.append(text[cursor:a])
        if r==ref:pieces.append(selected)
        cursor=b
    pieces.append(text[cursor:])
    pcb=d/(part['id']+'.kicad_pcb');pcb.write_text(''.join(pieces))
    glb=pcb.with_suffix('.glb')
    rows.append(dict(id=part['id'],reference=ref,pcb=str(pcb),glb=str(glb),
                     source_model_sha256=part['source_sha256'],
                     config_dir=str(d/'config'),log=str(d/'native-export.log')))

def run(row):
    env=os.environ.copy();env['XDG_CONFIG_HOME']=row['config_dir']
    args=['/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli',
          'pcb','export','glb','--force','--no-board-body',
          '--component-filter',row['reference'],'--user-origin','0x0mm',
          '-o',row['glb'],row['pcb']]
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=env)
    Path(row['log']).write_bytes(p.stdout)
    row.update(returncode=p.returncode,
               glb_sha256=hashlib.sha256(Path(row['glb']).read_bytes()).hexdigest()
               if Path(row['glb']).exists() else None)
    assert p.returncode==0 and row['glb_sha256'],row
    return row

with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
    rows=list(pool.map(run,rows))
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
report=dict(passed=True,source_board=str(source),source_sha256=before,
            immutable_source_unchanged=True,probes=rows)
(H/'native-probe-plan.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=True,probe_count=len(rows)),indent=2))
