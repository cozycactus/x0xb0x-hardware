#!/usr/bin/env python3
"""Preserve five original Eagle nets across KiCad 10's connectivity interpretation.

Edits only the KiCad 10 primary mainboard copy. The validated development-native
copy is hash-checked and never opened for writing. Each adaptation adds source-net
labels to the isolated native pin and to one already connected native wire-end pin
from the same original source net. No geometry, pin types, or wiring are changed.
"""
from pathlib import Path
from collections import defaultdict
import math,json,uuid,hashlib,xml.etree.ElementTree as ET
from resolve_native_footprint_fields import parse,prop,native_reference,symbol_reference
BASE=Path('/Users/ruslanmigirov/Downloads/hardware');VAL=BASE/'kicad-import/validation';path=BASE/'kicad-import/mainboard/mainboard.kicad_sch';original=VAL/'development-native/mainboard/mainboard.kicad_sch';original_hash=hashlib.sha256(original.read_bytes()).hexdigest();text=path.read_text();root=parse(text);assert root.first('version').items[1].value=='20260306'
source=json.loads((VAL/'eagle-source-structure.json').read_text())['files']['mainboard.sch']['source_schematic_pin_net_memberships'];net=ET.parse(VAL/'mainboard/mainboard.net').getroot();native_nets={}
for n in net.findall('./nets/net'):
    members={(x.get('ref'),x.get('pin'))for x in n.findall('node')}
    for key in members:native_nets[key]={'name':n.get('name'),'members':members}
embedded={s.items[1].value:s for s in root.first('lib_symbols').children('symbol')};pins=defaultdict(list);wireends=set()
for wire in root.children('wire'):
    for xy in wire.first('pts').children('xy'):wireends.add(tuple(round(float(a.value),4)for a in xy.items[1:3]))
for sym in root.children('symbol'):
    ref=symbol_reference(sym);lib=embedded[sym.first('lib_id').items[1].value];unit=int(sym.first('unit').items[1].value);sat=sym.first('at');a=math.radians(float(sat.items[3].value));mir=sym.first('mirror');mirrors=[v.value for v in mir.items[1:]]if mir else[]
    for group in lib.children('symbol'):
        bits=group.items[1].value.rsplit('_',2)
        if len(bits)!=3 or int(bits[1])not in[0,unit]:continue
        for pin in group.children('pin'):
            at=pin.first('at');x=float(at.items[1].value);y=-float(at.items[2].value)
            if'x'in mirrors:y=-y
            if'y'in mirrors:x=-x
            point=(round(math.cos(a)*x+math.sin(a)*y+float(sat.items[1].value),4),round(-math.sin(a)*x+math.cos(a)*y+float(sat.items[2].value),4))
            pins[(ref,pin.first('number').items[1].value)].append({'point':point,'native_pin_type':pin.items[1].value,'instance_at':[v.value for v in sat.items[1:]],'library_pin_at':[v.value for v in at.items[1:]],'mirror':mirrors,'symbol_uuid':sym.first('uuid').items[1].value})
existing={(n.items[1].value,tuple(round(float(a.value),4)for a in n.first('at').items[1:3]))for n in root.children('global_label')};blocks=[];adaptations=[]
for source_net,splitkey in [('N$130',('Q18','3')),('N$147',('Q11','1')),('N$31',('R129','2')),('N$37',('C72','-')),('N$7',('C56','-'))]:
    original_members=[m for m in source if m['net']==source_net and m['has_package']];splitmember=next(m for m in original_members if native_reference(m['reference'],True)==splitkey[0]and splitkey[1]in m['pads']);assert len(pins[splitkey])==1
    splitpin=pins[splitkey][0];splitnet=native_nets[splitkey];anchors=[]
    for m in original_members:
        for pad in m['pads']:
            key=(native_reference(m['reference'],True),pad)
            if key==splitkey or key not in native_nets:continue
            if native_nets[key]['name']==splitnet['name']:continue
            for p in pins[key]:
                if p['point']in wireends:anchors.append((key,p,m,native_nets[key]['name']))
    assert anchors,(source_net,splitkey)
    key,anchor,sourceanchor,anchor_net=anchors[0];entries=[]
    for kind,k,p,m in [('isolated_pin',splitkey,splitpin,splitmember),('connected_wire_end',key,anchor,sourceanchor)]:
        x,y=p['point'];identity=f'kicad10-eagle-connectivity:{path}:{source_net}:{k[0]}:{k[1]}';uid=str(uuid.uuid5(uuid.NAMESPACE_URL,identity));added=(source_net,p['point'])not in existing
        if added:
            blocks.append(f'''\n\t(global_label {json.dumps(source_net)}
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
\t)\n''')
        entries.append({'role':kind,'reference':k[0],'pad':k[1],'source_connection_record':m['record_index'],'label_added':added,'label_uuid':uid,**p})
    adaptations.append({'original_net':source_net,'stock10_isolated_net':splitnet['name'],'stock10_connected_net':anchor_net,'labels':entries})
before=hashlib.sha256(path.read_bytes()).hexdigest();output=text[:root.end-1]+''.join(blocks)+text[root.end-1:];parse(output);path.write_text(output);assert hashlib.sha256(original.read_bytes()).hexdigest()==original_hash
report={'file':str(path),'target_format':'KiCad 10.0 / schematic version 20260306','reason':'Original source connection groups split when loaded by stock KiCad 10; source-net labels join only original group members.','sha256_before':before,'sha256_after':hashlib.sha256(path.read_bytes()).hexdigest(),'development_native_file':str(original),'development_native_sha256_unchanged':original_hash,'added_label_count':len(blocks),'adaptations':adaptations,'pins_wiring_geometry_unchanged':True}
(VAL/'kicad10-connection-adaptations.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'added_labels':len(blocks),'adaptations':[{'net':a['original_net'],'labels':[(p['reference'],p['pad'],p['point'])for p in a['labels']]}for a in adaptations]},indent=2))
