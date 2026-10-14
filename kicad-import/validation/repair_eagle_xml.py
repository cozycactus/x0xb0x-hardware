from pathlib import Path
from collections import defaultdict, Counter
import xml.etree.ElementTree as ET
import json
BASE=Path('/Users/ruslanmigirov/Downloads/hardware')
VAL=BASE/'kicad-import/validation';OUT=VAL/'repaired-eagle-xml';OUT.mkdir(exist_ok=True)
inventory=json.loads((VAL/'eagle-source-structure.json').read_text())
reports={}
for stem in ['mainboard','ioboard']:
    raw=(BASE/(stem+'.sch')).read_bytes();source=inventory['files'][stem+'.sch']
    root=ET.parse(VAL/'decoded-xml'/(stem+'.sch.restored-fields.xml')).getroot()
    byoff={int(n.get('_binary_offset')):n for n in root.iter() if n.get('_binary_offset')}
    parent={c:p for p in root.iter() for c in p}
    report={'input':stem+'.sch','method_source':'https://raw.githubusercontent.com/alexer/pyeagle/master/eagle.py','long_fields_restored':len(source['long_text_references']),'symbols_hoisted':[],'variants':[],'pinrefs':0,'bus':[],'zero_wire_segments':[],'checks':{}}
    # Preserve exact source library/symbol/device ordering and names, including misplaced nested records.
    for sl in source['raw_library_ordinals']:
        lib=byoff[sl['record_index']*24];lib.set('name',sl['name'])
        syms=lib.find('symbols');dslist=lib.find('devicesets')
        for ss in sl['symbols']:
            sym=byoff[ss['record_index']*24]
            if parent[sym] is not syms:report['symbols_hoisted'].append({'name':ss['name'],'record_index':ss['record_index']})
            parent[sym].remove(sym);syms.append(sym);sym.set('name',ss['name'])
            for sp in ss['pins']:
                pin=byoff[sp['record_index']*24];pin.set('name',sp['name'])
                if pin not in list(sym):
                    parent[pin].remove(pin);sym.append(pin)
        for sd in sl['devicesets']:
            ds=byoff[sd['record_index']*24];ds.set('name',sd['name']);ds.set('prefix',sd['prefix']);ds.set('desc',sd['desc'])
            for sg in sd['gates']:
                gate=byoff[sg['record_index']*24];gate.set('name',sg['name']);gate.set('symbol',sg['symbol'])
            for sv in sd['variants']:
                dv=byoff[sv['record_index']*24];dv.set('name',sv['name'])
                if sv['package']:dv.set('package',sv['package'])
                else:dv.attrib.pop('package',None)
                for old in list(dv):
                    if old.tag in ['variantconnections','connects']:dv.remove(old)
                grouped=defaultdict(list)
                for con in sv['connects']:grouped[(con['gate'],con['pin'])].append(con['pad'])
                if grouped:
                    connects=ET.SubElement(dv,'connects')
                    for (gate,pin),pads in grouped.items():ET.SubElement(connects,'connect',{'gate':gate,'pin':pin,'pad':' '.join(pads)})
                report['variants'].append({'library':sl['name'],'deviceset':sd['name'],'device':sv['name'],'package':sv['package'],'pin_index_bits':sd['pin_index_bits'],'record_index':sv['record_index'],'connections':sv['connects']})
        packages=lib.find('packages')
        if packages is not None:lib.remove(packages)
    # Correct part names, values and ordinal-derived device names before restoring pinrefs.
    for sp in source['parts']:
        part=byoff[sp['record_index']*24];sl=source['raw_library_ordinals'][sp['lib']-1];sd=sl['devicesets'][sp['device']-1];sv=sd['variants'][sp['variant']-1]
        part.set('name',sp['name']);part.set('value',sp['value']);part.set('library',sl['name']);part.set('deviceset',sd['name']);part.set('device',sv['name'])
    # Instances retain raw gateno, so resolve part and gate from their source parent parts.
    # Restored-field decoder has already assigned the exact source part names; verify all instances.
    parts={p.get('name'):p for p in root.findall('.//parts/part')}
    liblookup={l['name']:l for l in source['raw_library_ordinals']}
    for inst in root.findall('.//instances/instance'):
        part=parts[inst.get('part')];sl=liblookup[part.get('library')];sd=next(d for d in sl['devicesets'] if d['name']==part.get('deviceset'))
        inst.set('gate',sd['gates'][int(inst.get('gateno'))-1]['name'])
    for membership in source['source_schematic_pin_net_memberships']:
        node=byoff[membership['record_index']*24];assert node.tag=='UNKNOWN';assert raw[membership['record_index']*24]==0x3d
        node.tag='pinref';node.attrib={'part':membership['reference'],'gate':membership['gate'],'pin':membership['pin']};report['pinrefs']+=1
    for net in root.findall('.//nets/net'):
        for seg in net.findall('./segment'):
            if not seg.findall('./wire'):report['zero_wire_segments'].append({'net':net.get('name'),'pinrefs':[p.attrib for p in seg.findall('pinref')]})
    # Bus name and exact bounded path come from the independently decoded source span.
    longrefs={(r['index']*24,r['field']):r['sequential_text'] for r in source['long_text_references']}
    for bus in root.findall('.//busses/UNKNOWN'):
        o=int(bus.get('_binary_offset'));assert raw[o]==0x3a;nblocks=int.from_bytes(raw[o+2:o+4],'little')
        field=raw[o+4:o+24];name=longrefs[(o,'name')] if field[0]==0x7f else field.split(b'\0')[0].decode('utf8')
        bus.tag='bus';bus.set('name',name);adopted=[]
        for path in root.findall('.//plain/path'):
            po=int(path.get('_binary_offset'))
            if o<po<o+24*(nblocks+1):parent[path].remove(path);path.tag='segment';bus.append(path);adopted.append(po)
        report['bus'].append({'name':name,'record_index':o//24,'segments_adopted':adopted})
    # Assert preservation and all symbol pin/package references used by placed instances.
    for sl in source['raw_library_ordinals']:
        lib=byoff[sl['record_index']*24]
        assert [s.get('name') for s in lib.findall('./symbols/symbol')]==[s['name'] for s in sl['symbols']]
        for sd in sl['devicesets']:
            ds=byoff[sd['record_index']*24]
            for sv in sd['variants']:
                dv=byoff[sv['record_index']*24]
                for con in dv.findall('connects/connect'):
                    gate=next(g for g in sd['gates'] if g['name']==con.get('gate'))
                    symbol=sl['symbols'][gate['symbol_ordinal']-1]
                    assert con.get('pin') in [p['name'] for p in symbol['pins']]
    report['checks']={'parts':len(root.findall('.//parts/part')),'expected_parts':source['part_records'],'instances':len(root.findall('.//instances/instance')),'expected_instances':source['placed_gate_instances'],'symbols':len(root.findall('.//symbols/symbol')),'expected_symbols':source['library_symbol_definitions'],'pinrefs':report['pinrefs'],'expected_pinrefs':source['pin_connection_records'],'all_connects_have_valid_gate_and_pin':True}
    assert report['checks']['parts']==report['checks']['expected_parts']
    assert report['checks']['symbols']==report['checks']['expected_symbols']
    assert report['checks']['instances']==report['checks']['expected_instances']
    assert report['checks']['pinrefs']==report['checks']['expected_pinrefs']
    for n in root.iter():n.attrib.pop('_binary_offset',None)
    ET.indent(root,space='  ');ET.ElementTree(root).write(OUT/(stem+'.sch'),encoding='utf-8',xml_declaration=True)
    reports[stem]=report
(OUT/'correction-report.json').write_text(json.dumps(reports,indent=2)+'\n')
for stem,r in reports.items():print(stem,json.dumps({'checks':r['checks'],'hoisted':r['symbols_hoisted'],'longfields':r['long_fields_restored'],'bus':r['bus'],'zero_wire_segments':len(r['zero_wire_segments'])}))
