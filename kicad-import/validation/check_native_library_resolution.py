#!/usr/bin/env python3
"""Read-only validation of project-local footprints and native symbol defaults."""
from pathlib import Path
import json
from resolve_native_footprint_fields import parse,prop,symbol_reference
BASE=Path('/Users/ruslanmigirov/Downloads/hardware/kicad-import');results={}
for stem in ['mainboard','ioboard']:
    project=BASE/stem;rows=parse((project/'fp-lib-table').read_text()).children('lib');libs={n.first('name').items[1].value:Path(n.first('uri').items[1].value.replace('${KIPRJMOD}',str(project.resolve())))for n in rows};root=parse((project/(stem+'.kicad_sch')).read_text());symbols=root.children('symbol');expected={};bad=[];physical=[]
    for s in symbols:
        fp=prop(s,'Footprint').value;ref=symbol_reference(s);libid=s.first('lib_id').items[1].value;expected.setdefault(libid,set()).add(fp)
        if fp:
            nick,name=fp.split(':',1);path=libs[nick]/(name+'.kicad_mod')
            if not path.is_file():bad.append({'reference':ref,'footprint':fp,'missing':str(path)})
            physical.append(ref)
    default_bad=[]
    for s in root.first('lib_symbols').children('symbol'):
        libid=s.items[1].value
        if libid in expected and {prop(s,'Footprint').value}!=expected[libid]:default_bad.append({'embedded':libid})
    for table in parse((project/'sym-lib-table').read_text()).children('lib'):
        nick=table.first('name').items[1].value;path=Path(table.first('uri').items[1].value.replace('${KIPRJMOD}',str(project.resolve())))
        for s in parse(path.read_text()).children('symbol'):
            libid=nick+':'+s.items[1].value
            if libid in expected and {prop(s,'Footprint').value}!=expected[libid]:default_bad.append({'cache':libid})
    results[stem]={'schematic_version':root.first('version').items[1].value,'placed_gate_instances':len(symbols),'instances_with_footprint':len(physical),'unique_physical_parts':len(set(physical)),'all_nonempty_footprints_resolve':not bad,'missing':bad,'embedded_and_cache_default_mismatches':default_bad,'local_footprint_libraries':{k:str(v)for k,v in libs.items()}}
path=BASE/'validation/native-library-resolution-checks.json';path.write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2));assert all(r['all_nonempty_footprints_resolve']and not r['embedded_and_cache_default_mismatches']for r in results.values())
