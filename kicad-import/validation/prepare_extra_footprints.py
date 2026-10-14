from pathlib import Path
from collections import defaultdict
import xml.etree.ElementTree as ET
import json, copy
BASE=Path('/Users/ruslanmigirov/Downloads/hardware');VAL=BASE/'kicad-import/validation';OUT=VAL/'repaired-eagle-xml'
source=json.loads((VAL/'eagle-source-structure.json').read_text())
report={}
for stem in ['mainboard','ioboard']:
    schsrc=source['files'][stem+'.sch'];bsrc=source['files'][stem+'.brd'];boardnames={p['package'] for p in bsrc['elements']}
    sch=ET.parse(VAL/'decoded-xml'/(stem+'.sch.restored-fields.xml')).getroot();byoff={int(n.get('_binary_offset')):n for n in sch.iter() if n.get('_binary_offset')}
    needed=defaultdict(list)
    for p in schsrc['parts']:
        lib=schsrc['raw_library_ordinals'][p['lib']-1];ds=lib['devicesets'][p['device']-1];dv=ds['variants'][p['variant']-1]
        if dv['package']:needed[(lib['name'],dv['package'])].append(p['name'])
    missing={k:v for k,v in needed.items() if k[1] not in boardnames}
    report[stem]={'schema_only_packages':[{'library':k[0],'package':k[1],'references':v}for k,v in missing.items()],'all_used_schema_packages':sorted({k[1]for k in needed})}
    if not missing:continue
    root=ET.Element('eagle',{'version':'4.13'});drawing=ET.SubElement(root,'drawing');drawing.append(copy.deepcopy(sch.find('./drawing/layers')));board=ET.SubElement(drawing,'board');ET.SubElement(board,'plain');libs=ET.SubElement(board,'libraries');els=ET.SubElement(board,'elements');ET.SubElement(board,'signals');ET.SubElement(board,'designrules',{'name':'source-footprint-extraction'})
    addedlibs={}
    for index,((libname,pkgname),refs) in enumerate(missing.items(),1):
        sl=next(l for l in schsrc['raw_library_ordinals']if l['name']==libname);sp=next(p for p in sl['packages']if p['name']==pkgname);package=copy.deepcopy(byoff[sp['record_index']*24]);package.set('name',pkgname)
        # Schematic parser omits PCB pad normalization; apply the identical existing conversions.
        for n in package.iter():
            if n.tag in ['pad','hole','via']:
                for dim in ['drill','diameter']:
                    half=n.get('half_'+dim)
                    if half is not None:n.set(dim,f'{float(half)*2*0.0001:.4f}')
            if n.tag=='smd':
                for dim in ['dx','dy']:
                    half=n.get('half_'+dim)
                    if half is not None:n.set(dim,f'{float(half)*2*0.0001:.4f}')
            if n.tag=='pad' and n.get('shape') is not None:n.set('shape',{'0':'square','1':'round','2':'octagon','3':'long','4':'offset'}[n.get('shape')])
            n.attrib.pop('_binary_offset',None)
        if libname not in addedlibs:
            li=ET.SubElement(libs,'library',{'name':libname});addedlibs[libname]=ET.SubElement(li,'packages')
        addedlibs[libname].append(package)
        ET.SubElement(els,'element',{'name':f'SCHEMAFP{index}','library':libname,'package':pkgname,'value':pkgname,'x':str((index-1)*20),'y':'0','rot':'R0'})
    for n in root.iter():n.attrib.pop('_binary_offset',None)
    ET.indent(root,space='  ');path=OUT/(stem+'-schema-extra-footprints.brd');ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True);report[stem]['extraction_board']=str(path)
(OUT/'extra-footprint-inventory.json').write_text(json.dumps(report,indent=2)+'\n')
for stem,r in report.items():print(stem,r['schema_only_packages'])
