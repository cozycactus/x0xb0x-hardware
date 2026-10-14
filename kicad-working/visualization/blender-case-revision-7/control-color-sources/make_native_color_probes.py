"""Create isolated one-reference KiCad probes; actual projects stay read-only."""
from pathlib import Path
import hashlib,json,re,sys
HERE=Path(__file__).resolve().parent
WORK=HERE.parents[2]
source=WORK/'mainboard/mainboard.kicad_pcb'
before=hashlib.sha256(source.read_bytes()).hexdigest()
text=source.read_text()
sys.path.insert(0,str(WORK.parent/'kicad-import/validation'))
from verify_native_projects import children,one,parse_sexpr,property_value
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
manifest=json.loads((HERE/'control-color-manifest.json').read_text())
out=HERE/'native-probes';out.mkdir(exist_ok=True)
rows=[]
for part in manifest['parts']:
    ref=part['references'][0]
    for kind,modelpath in [('original',part['original_step']),('colored',part['step'])]:
        target=next(block for _,_,r,block in ranges if r==ref)
        assert len(re.findall(r'\(model\s+"',target))==1
        replaced=re.sub(r'(\(model\s+)"[^"]*"',
            lambda m:m.group(1)+json.dumps(modelpath),target,count=1)
        pieces=[];cursor=0
        for start,end,r,block in ranges:
            pieces.append(text[cursor:start])
            if r==ref:pieces.append(replaced)
            cursor=end
        pieces.append(text[cursor:])
        path=out/(part['id']+'_'+kind+'.kicad_pcb')
        path.write_text(''.join(pieces))
        rf=children(parse_sexpr(path.read_text()),'footprint')
        assert len(rf)==1 and children(rf[0],'model')[0][1]==modelpath
        at=list(map(float,one(rf[0],'at')[1:]))
        glb=out/(part['id']+'_'+kind)/'native.glb'
        glb.parent.mkdir(exist_ok=True)
        rows.append({'id':part['id'],'reference':ref,'variant':kind,'board':str(path),
            'model':modelpath,'model_sha256':hashlib.sha256(Path(modelpath).read_bytes()).hexdigest(),
            'GLB':str(glb),'side':one(rf[0],'layer')[1],
            'original_board_xy_mm':at[:2],
            'original_board_angle_degrees':at[2] if len(at)>2 else 0})
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
(HERE/'native-probe-plan.json').write_text(json.dumps({'input_board':str(source),'input_board_sha256':before,'input_board_unchanged':True,'probes':rows},indent=2)+'\n')
print(json.dumps({'probes':len(rows),'families':6,'input_board_unchanged':True}))
