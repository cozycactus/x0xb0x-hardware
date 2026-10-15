"""Check actual KiCad USB tessellation, printed heights, insulation and drills."""
import ast,hashlib,json,math,sys
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent
REVIEW=HERE.parent;WORK=REVIEW.parents[1];REPO=WORK.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
exp=json.loads((REVIEW/'native-export-record.json').read_text())['boards']['ioboard']
source=REVIEW/exp['glb'];assert sha(source)==exp['glb_sha256']
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source))
root=bpy.data.objects['USB0'];inv=root.matrix_world.inverted()
parts={o.name:o for o in root.children_recursive if o.type=='MESH'}
get=lambda name:next(o for n,o in parts.items() if n==name or n.startswith(name+'.'))
shell=get('Shell');white=get('Insulator');tin=get('DrawingDerivedTerminals');gold=get('MatingContacts')
def points(obj):return [inv@obj.matrix_world@v.co*1000 for v in obj.data.vertices]
def bounds(ps):return [min(p[i] for p in ps) for i in range(3)]+[max(p[i] for p in ps) for i in range(3)]
checks=[]
def check(n,p,**d):checks.append(dict(check=n,passed=bool(p),**d))
check('Native four named parts present',len(parts)==4)
check('Native shell body0.38mm above PCB and printed envelope retained',max(abs(a-b) for a,b in zip(bounds(points(shell)),[-6.02,0,.38,6.02,16,11]))<.0001,bounds_mm=bounds(points(shell)))
sb=BVHTree.FromPolygons(points(shell),[list(p.vertices) for p in shell.data.polygons])
wb=BVHTree.FromPolygons(points(white),[list(p.vertices) for p in white.data.polygons])
bm=bmesh.new();bm.from_mesh(tin.data);bm.transform(inv@tin.matrix_world)
bmesh.ops.scale(bm,vec=(1000,)*3,verts=bm.verts)
bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=.0001)
bm.verts.ensure_lookup_table();remaining=set(bm.verts);components=[]
while remaining:
    start=remaining.pop();group={start};stack=[start]
    while stack:
        v=stack.pop()
        for e in v.link_edges:
            n=e.other_vert(v)
            if n in remaining:remaining.remove(n);group.add(n);stack.append(n)
    components.append(group)
check('Six native solder terminals retained',len(components)==6)
rows=[]
for group in components:
    ps=[v.co for v in group];bb=bounds(ps);cx=(bb[0]+bb[3])/2;cy=(bb[1]+bb[4])/2
    lock=abs(cx)>5.;expected=3.72 if lock else 2.91
    name=('lock' if lock else 'signal')+f'({cx:.2f},{cy:.2f})'
    check(name+' source projection',abs(bb[2]+expected)<.0001,bounds_mm=bb)
    if not lock:
        gap=min(sb.find_nearest(p)[3] for p in ps)
        touch=min(wb.find_nearest(p)[3] for p in ps)
        check(name+' insulated from shell and seated in white insert',gap>.20 and touch<.005,shell_gap_mm=gap,insulator_gap_mm=touch)
    rows.append(dict(name=name,bounds_mm=bb))
bm.free()
script=REPO/'scripts/verify_drill_fit.py';tree=ast.parse(script.read_text());nodes=[]
for node in tree.body:
    if isinstance(node,ast.Try):break
    nodes.append(node)
ns={'__file__':str(script)};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(script),'exec'),ns)
padmap,thickness=ns['drilled_pads'](WORK/'ioboard/ioboard.kicad_pcb')
worst,filled,stray=ns['measure'](ns['world_triangles'](root),padmap['USB0']['pads'],root.matrix_world.translation.z*1000,thickness)
check('All six original drilled holes contain leads at board mid-depth',filled=={p['number'] for p in padmap['USB0']['pads']},filled_pads=sorted(filled))
check('No USB geometry crosses PCB away from a hole',stray==0,stray_section_points=stray)
check('Only declared mounting-tab interferences remain',all(v<=0 if k not in {'M2','P$2'} else v<=.245 for k,v in worst.items()),nominal_wall_excess_mm=worst)
failures=[c for c in checks if not c['passed']]
out=dict(passed=not failures,check_count=len(checks),checks=checks,failures=failures,source_glb_sha256=sha(source),pcb_sha256=exp['pcb_sha256'],terminal_components=rows,drill_wall_excess_mm=worst,read_only=True,physical_fit_qualified=False,scope='Actual native KiCad tessellation of USB0; source heights, material separation and unchanged nominal drill exceptions. Not physical insertion or electrical certification.')
(HERE/'native-usb-audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['checks','terminal_components']},indent=2),flush=True)
assert not failures,'Native USB audit failed'
