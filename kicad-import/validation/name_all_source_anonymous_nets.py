#!/usr/bin/env python3
"""Give every anonymous original Eagle N$ net a stable explicit native name.

Only primary schematic files are edited. Every label is placed at an exact native
pin terminal after matching the entire source package-pad membership group to one
exported native net. Existing labels and wiring are preserved. Global labels avoid
sheet-path and multi-unit naming differences between stock KiCad export and DRC.
"""
from pathlib import Path
from collections import defaultdict
import math,json,uuid,hashlib,xml.etree.ElementTree as ET
from resolve_native_footprint_fields import parse,prop,symbol_reference,symbol_unit,native_reference
BASE=Path('/Users/ruslanmigirov/Downloads/hardware');VAL=BASE/'kicad-import/validation';inventory=json.loads((VAL/'eagle-source-structure.json').read_text());plans={};errors=[]
for stem in ['mainboard','ioboard']:
    path=BASE/'kicad-import'/stem/(stem+'.kicad_sch');text=path.read_text();root=parse(text);source=inventory['files'][stem+'.sch'];embedded={s.items[1].value:s for s in root.first('lib_symbols').children('symbol')};pins=defaultdict(list);wireends=set()
    for wire in root.children('wire'):
        for xy in wire.first('pts').children('xy'):wireends.add(tuple(round(float(a.value),4)for a in xy.items[1:3]))
    for sym in root.children('symbol'):
        ref=symbol_reference(sym);unit=symbol_unit(sym);lib=embedded[sym.first('lib_id').items[1].value];sat=sym.first('at');angle=math.radians(float(sat.items[3].value));mir=sym.first('mirror');mirrors=[a.value for a in mir.items[1:]]if mir else[]
        for group in lib.children('symbol'):
            bits=group.items[1].value.rsplit('_',2)
            if len(bits)!=3 or int(bits[1])not in[0,unit]:continue
            for pin in group.children('pin'):
                at=pin.first('at');x=float(at.items[1].value);y=-float(at.items[2].value)
                xx=math.cos(angle)*x+math.sin(angle)*y;yy=-math.sin(angle)*x+math.cos(angle)*y
                if'x'in mirrors:yy=-yy
                if'y'in mirrors:xx=-xx
                point=(round(xx+float(sat.items[1].value),4),round(yy+float(sat.items[2].value),4));num=pin.first('number').items[1].value
                pins[(ref,num)].append({'point':point,'reference':ref,'pad':num,'native_pin_type':pin.items[1].value,'symbol_uuid':sym.first('uuid').items[1].value,'instance_at':[a.value for a in sat.items[1:]],'library_pin_at':[a.value for a in at.items[1:]],'mirror':mirrors,'on_existing_wire_endpoint':point in wireends})
    native=ET.parse(VAL/stem/(stem+'.net')).getroot();groups=defaultdict(list)
    for net in native.findall('./nets/net'):
        key=frozenset((n.get('ref'),n.get('pin'))for n in net.findall('node'));groups[key].append(net.get('name'))
    memberships=defaultdict(list)
    for m in source['source_schematic_pin_net_memberships']:
        if m['net'].startswith('N$')and m['has_package']:memberships[m['net']].append(m)
    labels={n.items[1].value for tag in ['global_label','label']for n in root.children(tag)};added=[];already=[]
    for name in source['net_names']:
        if not name.startswith('N$'):continue
        source_members=memberships[name];expected=frozenset((native_reference(m['reference'],True),pad)for m in source_members for pad in m['pads']);matches=groups[expected]
        if len(matches)!=1:
            errors.append({'project':stem,'net':name,'reason':'Source membership does not match exactly one native group','native_matches':matches,'source_members':sorted(expected)});continue
        if name in labels:
            if matches[0]!=name:errors.append({'project':stem,'net':name,'reason':'Existing explicit label does not determine native name','native_name':matches[0]})
            already.append({'source_net':name,'native_name':matches[0]});continue
        candidates=[]
        for m in source_members:
            for pad in m['pads']:
                key=(native_reference(m['reference'],True),pad)
                for p in pins[key]:
                    if p['native_pin_type']=='no_connect':continue
                    candidates.append({'source_net':name,'previous_native_net':matches[0],'source_connection_record':m['record_index'],'source_group_members':sorted(expected),**p})
        if not candidates:
            errors.append({'project':stem,'net':name,'reason':'No unambiguous connectable native pin terminal'});continue
        candidates.sort(key=lambda p:(not p['on_existing_wire_endpoint'],p['reference'],p['pad'],p['symbol_uuid']));chosen=candidates[0]
        # The chosen pad is explicitly in the exact native net and exact source group.
        assert (chosen['reference'],chosen['pad'])in expected
        added.append(chosen)
    development=VAL/'development-native'/stem/(stem+'.kicad_sch');plans[stem]={'file':str(path),'text':text,'root_end':root.end,'sha256_before':hashlib.sha256(path.read_bytes()).hexdigest(),'development_file':str(development),'development_sha256':hashlib.sha256(development.read_bytes()).hexdigest(),'source_anonymous_nets':len([n for n in source['net_names']if n.startswith('N$')]),'existing_explicit_nets':already,'added_global_labels':added}
report={'method':'Exact source package-pad group match to exported stock KiCad 10 net, then global label at an existing native pin terminal.','source':'eagle-source-structure.json','errors':errors,'projects':{}}
if not errors:
    for stem,plan in plans.items():
        path=Path(plan['file']);blocks=[]
        for p in plan['added_global_labels']:
            name=p['source_net'];x,y=p['point'];uid=str(uuid.uuid5(uuid.NAMESPACE_URL,f'eagle-source-anonymous-net:{path}:{name}'));p['label_uuid']=uid
            blocks.append(f'''\n\t(global_label {json.dumps(name)}
\t\t(shape bidirectional)
\t\t(at {x:g} {y:g} 0)
\t\t(fields_autoplaced yes)
\t\t(effects (font (size 0.762 0.762)) (justify left))
\t\t(uuid "{uid}")
\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}"
\t\t\t(at {x:g} {y:g} 0)
\t\t\t(hide yes)
\t\t\t(effects (font (size 0.762 0.762)) (justify left))
\t\t)
\t)\n''')
        text=plan['text'];end=plan['root_end'];output=text[:end-1]+''.join(blocks)+text[end-1:];parse(output);path.write_text(output)
        assert hashlib.sha256(Path(plan['development_file']).read_bytes()).hexdigest()==plan['development_sha256']
        plan['sha256_after']=hashlib.sha256(path.read_bytes()).hexdigest();plan['geometry_wiring_and_pin_types_unchanged']=True
for stem,plan in plans.items():
    report['projects'][stem]={k:v for k,v in plan.items()if k not in['text','root_end']}
(VAL/'source-anonymous-net-labels.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'errors':errors,'projects':{s:{'source_anonymous_nets':p['source_anonymous_nets'],'existing_explicit_nets':len(p['existing_explicit_nets']),'added_global_labels':len(p['added_global_labels'])}for s,p in plans.items()}},indent=2));assert not errors
