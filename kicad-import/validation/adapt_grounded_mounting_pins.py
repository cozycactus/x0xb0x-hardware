#!/usr/bin/env python3
"""Adapt four explicitly grounded Eagle mechanical pins to KiCad connectivity.

Eagle's original no-connect type hint coexists with explicit GND membership on
S1.M1-M4. KiCad suppresses electrical connection for that pin type even when a
GND label touches the terminal. Preserve the explicit source pad connectivity by
changing only these four native library pins to passive in both embedded and
project-cache symbol definitions. No PCB geometry, pin numbers or coordinates,
placements, or wiring are changed.
"""
from pathlib import Path
import json,hashlib
from resolve_native_footprint_fields import parse
BASE=Path('/Users/ruslanmigirov/Downloads/hardware');VAL=BASE/'kicad-import/validation';project=BASE/'kicad-import/mainboard';targets=[(project/'mainboard.kicad_sch',True),(project/'mainboard-eagle-import.kicad_sym',False)];report=[]
source=json.loads((VAL/'eagle-source-structure.json').read_text())['files']['mainboard.sch']['source_schematic_pin_net_memberships']
for number in ['M1','M2','M3','M4']:
    assert any(m['reference']=='S1'and number in m['pads']and m['net']=='GND'for m in source)
for path,embedded in targets:
    text=path.read_text();root=parse(text);container=root.first('lib_symbols')if embedded else root;name="mainboard-eagle-import:SWITCH_GND''"if embedded else"SWITCH_GND''";symbol=next(s for s in container.children('symbol')if s.items[1].value==name);changes=[];seen=set();pins=[]
    for group in symbol.children('symbol'):
        for pin in group.children('pin'):
            number=pin.first('number').items[1].value
            if number not in ['M1','M2','M3','M4']:continue
            assert number not in seen;seen.add(number);old=pin.items[1];assert old.value in ['no_connect','passive']
            if old.value!='passive':changes.append((old.start,old.end,'passive'))
            pins.append({'number':number,'before':old.value,'after':'passive','local_at':[a.value for a in pin.first('at').items[1:]],'source_net':'GND'})
    assert seen=={'M1','M2','M3','M4'};before=hashlib.sha256(path.read_bytes()).hexdigest()
    for start,end,value in sorted(changes,reverse=True):text=text[:start]+value+text[end:]
    parse(text);path.write_text(text);report.append({'file':str(path),'sha256_before':before,'sha256_after':hashlib.sha256(path.read_bytes()).hexdigest(),'changed_pin_types':len(changes),'pins':pins})
(VAL/'grounded-mounting-pin-adaptation.json').write_text(json.dumps({'reason':'Native KiCad no_connect suppresses electrical connection; preserve original explicit grounded mechanical pad membership using passive native pin type.','scope':'S1 M1-M4 only, embedded and project cache. No source file or PCB geometry edits.','files':report},indent=2)+'\n')
print(json.dumps([{'file':r['file'],'changed_pin_types':r['changed_pin_types']}for r in report],indent=2))
