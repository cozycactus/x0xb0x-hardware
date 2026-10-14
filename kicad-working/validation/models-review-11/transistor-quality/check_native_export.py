#!/usr/bin/env python3
"""Isolated original-footprint native KiCad STEP-to-GLB geometry audit.
SPDX-License-Identifier: CC0-1.0
"""
from pathlib import Path
import concurrent.futures
import hashlib
import json
import os
import re
import struct
import subprocess

H = Path(__file__).resolve().parent
W = H.parents[2]
M = json.loads((H/'transistor-quality-manifest.json').read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
text = (W/'mainboard/mainboard.kicad_pcb').read_text()
source_hash = sha(W/'mainboard/mainboard.kicad_pcb')


def end(start):
    depth = 0; quoted = False; escaped = False
    for i in range(start, len(text)):
        c = text[i]
        if quoted:
            if escaped: escaped=False
            elif c=='\\': escaped=True
            elif c=='"': quoted=False
        elif c=='"': quoted=True
        elif c=='(': depth+=1
        elif c==')':
            depth-=1
            if not depth: return i+1
    raise ValueError('Unclosed source footprint')


ranges=[]
for m in re.finditer(r'^\t\(footprint ',text,re.M):
    a=m.start()+1;b=end(a);block=text[a:b]
    ref=re.search(r'\(property "Reference" "([^"]+)"',block).group(1)
    ranges.append((a,b,ref,block))
probes=[]
for part,ref in zip(M['parts'],['Q3','Q17']):
    d=H/'native-probes'/part['id'];d.mkdir(parents=True,exist_ok=True)
    selected=next(b for _,_,r,b in ranges if r==ref)
    selected=re.sub(r'(\(model\s+)"[^"]*"',
                    lambda m:m.group(1)+json.dumps(part['step']),selected,count=1)
    pieces=[];cursor=0
    for a,b,r,block in ranges:
        pieces.append(text[cursor:a])
        if r==ref: pieces.append(selected)
        cursor=b
    pieces.append(text[cursor:])
    pcb=d/(part['id']+'.kicad_pcb');pcb.write_text(''.join(pieces))
    probes.append(dict(id=part['id'],reference=ref,pcb=str(pcb),
                       glb=str(pcb.with_suffix('.glb')),config_dir=str(d/'config')))


def run(row):
    env=os.environ.copy();env['XDG_CONFIG_HOME']=row['config_dir']
    args=['/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli',
          'pcb','export','glb','--force','--no-board-body',
          '--component-filter',row['reference'],'--user-origin','0x0mm',
          '-o',row['glb'],row['pcb']]
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=env)
    Path(row['glb']).with_suffix('.log').write_bytes(p.stdout)
    assert p.returncode==0 and Path(row['glb']).exists(),p.stdout.decode()
    row['glb_sha256']=sha(row['glb']);row['returncode']=p.returncode
    return row


with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    probes=list(pool.map(run,probes))

lin=lambda v:v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
checks=[];families=[]


def check(name,passed,**evidence):
    checks.append(dict(name=name,passed=bool(passed),**evidence))
    assert passed,(name,evidence)


def bb(points):
    return [min(p[k]for p in points)for k in range(3)]+[max(p[k]for p in points)for k in range(3)]


for part,probe in zip(M['parts'],probes):
    check(part['id']+':frozen-source-STEP',sha(part['step'])==part['source_sha256'])
    data=Path(probe['glb']).read_bytes();n=struct.unpack_from('<I',data,12)[0]
    j=json.loads(data[20:20+n]);binary=data[28+n:]
    check(part['id']+':binary-GLB',data[:4]==b'glTF'and data[24+n:28+n]==b'BIN\0')
    points_by_color={};mesh_count=0
    for mesh in j['meshes']:
        for primitive in mesh['primitives']:
            mesh_count+=1
            a=j['accessors'][primitive['attributes']['POSITION']]
            v=j['bufferViews'][a['bufferView']]
            off=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',12)
            pts=[struct.unpack_from('<fff',binary,off+i*stride)for i in range(a['count'])]
            pts=[(x*1000,-z*1000,y*1000)for x,y,z in pts]
            rgb=j['materials'][primitive['material']]['pbrMetallicRoughness']['baseColorFactor'][:3]
            wanted=min((f['color_rgb']for f in part['segments']),key=lambda c:sum(abs(v-lin(c))for v,c in zip(rgb,c)))
            error=max(abs(v-lin(c))for v,c in zip(rgb,wanted))
            check(part['id']+':native-face-palette',error<1e-6,maximum_error=error)
            points_by_color.setdefault(tuple(wanted),[]).extend(pts)
    check(part['id']+':all-color-roles',set(points_by_color)=={tuple(f['color_rgb'])for f in part['segments']})
    roles=[]
    for rgb,pts in points_by_color.items():
        boxes=[f['exact_bounds_mm']for f in part['segments']if tuple(f['color_rgb'])==rgb]
        wanted=[min(b[i]for b in boxes)for i in range(3)]+[max(b[i]for b in boxes)for i in range(3,6)]
        actual=bb(pts);error=max(abs(a-b)for a,b in zip(actual,wanted))
        check(part['id']+':native-role-bounds',error<.001,expected_mm=wanted,native_mm=actual,residual_mm=error)
        roles.append(dict(color_srgb=rgb,native_bounds_mm=actual,expected_bounds_mm=wanted,maximum_residual_mm=error))
    whole=bb([p for pts in points_by_color.values()for p in pts]);expected=part['geometry']['exact_bounds_mm']
    check(part['id']+':whole-geometry-bounds',max(abs(a-b)for a,b in zip(whole,expected))<.001,
          native_mm=whole,expected_mm=expected)
    families.append(dict(id=part['id'],reference=probe['reference'],STEP_sha256=part['source_sha256'],
                         GLB_sha256=probe['glb_sha256'],mesh_primitives=mesh_count,color_roles=roles,
                         native_canonical_bounds_mm=whole,passed=True))

check('immutable-source-board',sha(W/'mainboard/mainboard.kicad_pcb')==source_hash)
r=dict(passed=True,check_count=len(checks),checks=checks,families=families,probes=probes,
       maximum_bounds_residual_mm=max(r['maximum_residual_mm']for f in families for r in f['color_roles']),
       physical_fit_qualified=False,source_board_unchanged=True,
       proof='Frozen colored STEP imports through native KiCad GLB with all four feature solids, two material roles and full canonical bounds. Original board footprint transforms retained in isolated probes.')
(H/'native-export-audit.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:r[k]for k in ['passed','check_count','maximum_bounds_residual_mm']},indent=2))
