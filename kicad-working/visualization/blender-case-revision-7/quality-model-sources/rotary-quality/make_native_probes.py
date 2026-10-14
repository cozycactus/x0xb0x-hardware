from pathlib import Path
import json,hashlib,re,sys,subprocess,os
HERE=Path(__file__).resolve().parent;WORK=HERE.parents[2]
source=WORK/'mainboard/mainboard.kicad_pcb';before=hashlib.sha256(source.read_bytes()).hexdigest();text=source.read_text()
def end_of_block(start):
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
            if depth==0:return i+1
    raise ValueError('Unclosed footprint block')
ranges=[]
for m in re.finditer(r'^\t\(footprint ',text,re.M):
    start=m.start()+1;end=end_of_block(start)
    block=text[start:end]
    ref=re.search(r'\(property "Reference" "([^"]+)"',block).group(1)
    ranges.append((start,end,ref,block))
assert len(ranges)==417
manifest=json.loads((HERE/'rotary-quality-manifest.json').read_text());out=HERE/'native-probes';out.mkdir(exist_ok=True);rows=[]
for part in manifest['parts']:
 ref=part['references'][0];target=next(block for _,_,r,block in ranges if r==ref);replaced=re.sub(r'(\(model\s+)"[^"]*"',lambda m:m.group(1)+json.dumps(part['step']),target,count=1)
 pieces=[];cursor=0
 for start,end,r,block in ranges:
  pieces.append(text[cursor:start])
  if r==ref:pieces.append(replaced)
  cursor=end
 pieces.append(text[cursor:]);path=out/(part['id']+'.kicad_pcb');path.write_text(''.join(pieces));rows.append({'id':part['id'],'reference':ref,'pcb':str(path),'glb':str(path.with_suffix('.glb')),'step_sha256':part['source_sha256']})
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
(HERE/'native-probe-plan.json').write_text(json.dumps({'source_board':str(source),'sha256':before,'unchanged_after_read':True,'probes':rows},indent=2)+'\n')
print(json.dumps(rows,indent=2))
