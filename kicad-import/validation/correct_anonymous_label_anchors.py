#!/usr/bin/env python3
"""Correct source-net label anchors using real native instance units/transforms.

KiCad 10 stores actual unit numbers in instances/path, while the top-level unit
can remain 1. Its parser mirrors after rotation. Only previously added global
label positions are changed; pins, wiring and PCB files remain untouched.
"""
from pathlib import Path
from collections import defaultdict
import math,json,hashlib,xml.etree.ElementTree as ET
from resolve_native_footprint_fields import parse,prop,symbol_reference,symbol_unit,native_reference
BASE=Path('/Users/ruslanmigirov/Downloads/hardware');VAL=BASE/'kicad-import/validation';source=json.loads((VAL/'eagle-source-structure.json').read_text());previous=json.loads((VAL/'source-anonymous-net-labels.json').read_text());reports={};errors=[];plans={}
for stem in ['mainboard','ioboard']:
    path=BASE/'kicad-import'/stem/(stem+'.kicad_sch');text=path.read_text();root=parse(text);embedded={s.items[1].value:s for s in root.first('lib_symbols').children('symbol')};pins=defaultdict(list);wireends=set()
    for wire in root.children('wire'):
        for xy in wire.first('pts').children('xy'):wireends.add(tuple(round(float(a.value),4)for a in xy.items[1:3]))
    for sym in root.children('symbol'):
        ref=symbol_reference(sym);unit=symbol_unit(sym);lib=embedded[sym.first('lib_id').items[1].value];sat=sym.first('at');a=math.radians(float(sat.items[3].value));mir=sym.first('mirror');mirrors=[x.value for x in mir.items[1:]]if mir else[]
        for group in lib.children('symbol'):
            bits=group.items[1].value.rsplit('_',2)
            if len(bits)!=3 or int(bits[1])not in[0,unit]or int(bits[2])not in[0,1]:continue
            for pin in group.children('pin'):
                at=pin.first('at');x=float(at.items[1].value);y=-float(at.items[2].value);xx=math.cos(a)*x+math.sin(a)*y;yy=-math.sin(a)*x+math.cos(a)*y
                if'x'in mirrors:yy=-yy
                if'y'in mirrors:xx=-xx
                point=(round(xx+float(sat.items[1].value),4),round(yy+float(sat.items[2].value),4));pad=pin.first('number').items[1].value
                p={'reference':ref,'pad':pad,'point':point,'actual_instance_unit':unit,'symbol_uuid':sym.first('uuid').items[1].value,'native_pin_type':pin.items[1].value,'on_existing_wire_endpoint':point in wireends,'instance_at':[v.value for v in sat.items[1:]],'library_pin_at':[v.value for v in at.items[1:]],'mirror':mirrors}
                if not any(q['point']==point and q['symbol_uuid']==p['symbol_uuid']for q in pins[(ref,pad)]):pins[(ref,pad)].append(p)
    native=ET.parse(VAL/stem/(stem+'.net')).getroot();groups=defaultdict(list)
    for n in native.findall('./nets/net'):groups[frozenset((p.get('ref'),p.get('pin'))for p in n.findall('node'))].append(n.get('name'))
    memberships=defaultdict(list)
    for m in source['files'][stem+'.sch']['source_schematic_pin_net_memberships']:
        if m['net'].startswith('N$')and m['has_package']:memberships[m['net']].append(m)
    labels={n.first('uuid').items[1].value:n for n in root.children('global_label')};edits=[];changes=[];still=[]
    for entry in previous['projects'][stem]['added_global_labels']:
        name=entry['source_net'];ms=memberships[name];expected=frozenset((native_reference(m['reference'],True),pad)for m in ms for pad in m['pads']);matches=groups[expected]
        if len(matches)!=1:errors.append({'project':stem,'net':name,'native_matches':matches});continue
        if matches[0]==name:continue
        label=labels[entry['label_uuid']];assert label.items[1].value==name;candidates=[]
        for m in ms:
            for pad in m['pads']:
                for p in pins[(native_reference(m['reference'],True),pad)]:
                    if p['native_pin_type']!='no_connect':candidates.append({'source_connection_record':m['record_index'],**p})
        if not candidates:errors.append({'project':stem,'net':name,'reason':'no actual-unit native pin'});continue
        candidates.sort(key=lambda p:(not p['on_existing_wire_endpoint'],p['reference'],p['pad'],p['symbol_uuid']));chosen=candidates[0];at=label.first('at');old=tuple(float(v.value)for v in at.items[1:3]);new=chosen['point'];moved=old!=new
        if moved:
            for token,value in zip(at.items[1:3],new):edits.append((token.start,token.end,f'{value:g}'))
            for propnode in label.children('property'):
                if propnode.items[1].value=='Intersheetrefs':
                    pat=propnode.first('at')
                    for token,value in zip(pat.items[1:3],new):edits.append((token.start,token.end,f'{value:g}'))
        changes.append({'source_net':name,'previous_native_group_name':matches[0],'old_point':old,'new_point':new,'position_changed':moved,'label_uuid':entry['label_uuid'],'chosen_actual_pin':chosen,'source_group_members':sorted(expected)})
    plans[stem]=(path,text,edits);reports[stem]={'file':str(path),'sha256_before':hashlib.sha256(path.read_bytes()).hexdigest(),'checked_added_labels':len(previous['projects'][stem]['added_global_labels']),'incorrect_group_names_considered':len(changes),'labels_moved':sum(x['position_changed']for x in changes),'changes':changes}
if not errors:
    for stem,(path,text,edits)in plans.items():
        for start,end,value in sorted(edits,reverse=True):text=text[:start]+value+text[end:]
        parse(text);path.write_text(text);reports[stem]['sha256_after']=hashlib.sha256(path.read_bytes()).hexdigest()
(VAL/'anonymous-label-anchor-corrections.json').write_text(json.dumps({'errors':errors,'transform':'Actual instances/path unit; local library Y negated; native rotation then native mirror.','projects':reports},indent=2)+'\n')
print(json.dumps({'errors':errors,'projects':{s:{'incorrect_group_names_considered':r['incorrect_group_names_considered'],'labels_moved':r['labels_moved'],'changes':[(c['source_net'],c['new_point'],c['chosen_actual_pin']['reference'],c['chosen_actual_pin']['pad'])for c in r['changes']]}for s,r in reports.items()}},indent=2));assert not errors
