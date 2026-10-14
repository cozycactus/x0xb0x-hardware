#!/usr/bin/env python3
"""Restore explicit original net membership/names lost by geometry-only Eagle import.

Adds labels only at native pin terminals, after proving the intended net from
original Eagle connection records. Pin shapes/types, placement, and wiring stay
unchanged. Manual net-name labels must land on an existing wire endpoint.
"""
from pathlib import Path
from collections import defaultdict
import math,json,uuid,hashlib
from resolve_native_footprint_fields import parse,prop,native_reference
BASE=Path('/Users/ruslanmigirov/Downloads/hardware');VAL=BASE/'kicad-import/validation';source=json.loads((VAL/'eagle-source-structure.json').read_text());reports={}

def descendants(node,head):
    out=[]
    for child in node.children():
        if child.head==head:out.append(child)
        out+=descendants(child,head)
    return out

def terminal(sym,pin):
    at=sym.first('at');px=float(pin.first('at').items[1].value);py=-float(pin.first('at').items[2].value)
    mir=sym.first('mirror')
    if mir:
        if 'x' in [a.value for a in mir.items[1:]]:py=-py
        if 'y' in [a.value for a in mir.items[1:]]:px=-px
    a=math.radians(float(at.items[3].value));x=math.cos(a)*px+math.sin(a)*py+float(at.items[1].value);y=-math.sin(a)*px+math.cos(a)*py+float(at.items[2].value)
    return (round(x,4),round(y,4))

def label_text(net,x,y,identity):
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,identity))
    return f'''\n\t(global_label {json.dumps(net)}
\t\t(shape bidirectional)
\t\t(at {x:g} {y:g} 0)
\t\t(fields_autoplaced yes)
\t\t(effects (font (size 1.016 1.016)) (justify left))
\t\t(uuid "{uid}")
\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}"
\t\t\t(at {x:g} {y:g} 0)
\t\t\t(hide yes)
\t\t\t(effects (font (size 1.016 1.016)) (justify left))
\t\t)
\t)\n'''

for stem in ['mainboard','ioboard']:
    path=BASE/'kicad-import'/stem/(stem+'.kicad_sch');text=path.read_text();root=parse(text);embedded={s.items[1].value:s for s in root.first('lib_symbols').children('symbol')};pins=defaultdict(list);wireends=set()
    for wire in root.children('wire'):
        pts=wire.first('pts')
        for xy in pts.children('xy'):wireends.add(tuple(round(float(a.value),4)for a in xy.items[1:3]))
    for sym in root.children('symbol'):
        ref=prop(sym,'Reference').value;lib=embedded[sym.first('lib_id').items[1].value];unit=int(sym.first('unit').items[1].value)
        for group in lib.children('symbol'):
            bits=group.items[1].value.rsplit('_',2)
            if len(bits)!=3 or int(bits[1]) not in [0,unit]:continue
            for pin in group.children('pin'):
                num=pin.first('number').items[1].value;point=terminal(sym,pin);pins[(ref,num)].append({'point':point,'pin_type':pin.items[1].value,'library_pin':pin.first('name').items[1].value,'unit':unit,'symbol_uuid':sym.first('uuid').items[1].value,'instance_at':[a.value for a in sym.first('at').items[1:]],'library_at':[a.value for a in pin.first('at').items[1:]],'mirror':[a.value for a in sym.first('mirror').items[1:]] if sym.first('mirror') else []})
    ss=source['files'][stem+'.sch'];members=ss['source_schematic_pin_net_memberships'];wanted=[]
    if stem=='mainboard':
        for pad in ['M1','M2','M3','M4']:
            m=next(m for m in members if m['reference']=='S1' and pad in m['pads']);assert m['net']=='GND';candidates=pins[('S1',pad)];assert len(candidates)==1;wanted.append({'net':'GND','reference':'S1','pad':pad,'source_record':m['record_index'],'reason':'Restore original explicit mounting-pad GND membership',**candidates[0]})
    for name in (['C48','Q17','XTL1']if stem=='mainboard'else['HP_OUT']):
        candidates=[]
        for m in members:
            if m['net']!=name or not m['has_package']:continue
            ref=native_reference(m['reference'],True)
            for pad in m['pads']:
                for pin in pins[(ref,pad)]:
                    if pin['point'] in wireends:candidates.append({'net':name,'reference':ref,'pad':pad,'source_record':m['record_index'],'reason':'Preserve original manually named net',**pin})
        assert candidates,(stem,name)
        wanted.append(candidates[0])
    existing={(n.items[1].value,tuple(round(float(a.value),4)for a in n.first('at').items[1:3]))for n in root.children('global_label')};added=[];blocks=[]
    for w in wanted:
        point=w['point']
        if (w['net'],point) in existing:continue
        identity='eagle-net-recovery:'+str(path)+':'+w['reference']+':'+w['pad']+':'+w['net'];blocks.append(label_text(w['net'],*point,identity));added.append(w)
    before=hashlib.sha256(path.read_bytes()).hexdigest()
    if blocks:
        output=text[:root.end-1]+''.join(blocks)+text[root.end-1:];parse(output);path.write_text(output)
    reports[stem]={'file':str(path),'sha256_before':before,'sha256_after':hashlib.sha256(path.read_bytes()).hexdigest(),'added_labels':added,'pins_and_wiring_unchanged':True,'source_evidence':'eagle-source-structure.json source_schematic_pin_net_memberships','coordinate_rule':'Native library Y is negated; mirror is applied to local coordinates before native symbol rotation, matching SCH_SYMBOL SetOrientation and serializer.'}
    print(stem,'added',len(added),'labels',[(w['net'],w['reference'],w['pad'],w['point'])for w in added])
(VAL/'native-net-label-recovery.json').write_text(json.dumps(reports,indent=2)+'\n')
