#!/usr/bin/env python3
"""Resolve native schematic footprint fields through project-local imported caches.

This edits output artifacts only.  It preserves source SCH/BRD package differences,
keeps board-only mechanical footprints, and never substitutes a board package for a
schematic package with a different source name.  Without --apply it only reports.
"""
from pathlib import Path
from collections import defaultdict
import argparse, json, re, shutil, hashlib

class Atom:
    def __init__(self,value,start,end):self.value,self.start,self.end=value,start,end
class Node:
    def __init__(self,items,start,end):self.items,self.start,self.end=items,start,end
    @property
    def head(self):return self.items[0].value if self.items and isinstance(self.items[0],Atom) else None
    def children(self,head=None):return [n for n in self.items if isinstance(n,Node) and (head is None or n.head==head)]
    def first(self,head):return next(iter(self.children(head)),None)
def parse(text):
    tokens=[]
    for m in re.finditer(r'\s+|;[^\n]*|"(?:\\.|[^"\\])*"|[()]|[^\s()]+',text):
        s=m.group()
        if s.isspace() or s.startswith(';'):continue
        tokens.append((s,m.start(),m.end()))
    cursor=0
    def node():
        nonlocal cursor
        t,start,end=tokens[cursor];cursor+=1
        if t!='(':return Atom(json.loads(t) if t.startswith('"') else t,start,end)
        children=[]
        while tokens[cursor][0]!=')':children.append(node())
        _,_,end=tokens[cursor];cursor+=1;return Node(children,start,end)
    root=node();assert cursor==len(tokens);return root

def prop(node,name):
    for n in node.children('property'):
        if len(n.items)>=3 and n.items[1].value==name:return n.items[2]
    return None

def symbol_reference(node):
    instances=node.first('instances');references=set()
    if instances:
        for project in instances.children('project'):
            for path in project.children('path'):
                reference=path.first('reference')
                if reference:references.add(reference.items[1].value)
    if len(references)==1:return next(iter(references))
    reference=prop(node,'Reference')
    return reference.value if reference else None

def symbol_unit(node):
    instances=node.first('instances');units=set()
    if instances:
        for project in instances.children('project'):
            for path in project.children('path'):
                unit=path.first('unit')
                if unit:units.add(int(unit.items[1].value))
    if len(units)==1:return next(iter(units))
    unit=node.first('unit')
    return int(unit.items[1].value) if unit else 1

def footprint_ids(path):
    text=path.read_text();root=parse(text);result={}
    for fp in root.children('footprint'):
        ref=prop(fp,'Reference')
        if ref is None:
            for ft in fp.children('fp_text'):
                if ft.items[1].value=='reference':ref=ft.items[2];break
        assert ref is not None
        result[ref.value]=fp.items[1].value
    return result

def native_reference(ref,has_package):
    out=ref if has_package else '#'+ref
    if not out[-1:].isdigit():out+='0'
    if out[:1].isdigit():out='UNK'+out
    if ref.startswith('#'):out='UNK'+out
    return out

def patches(text,changes):
    for start,end,value in sorted(changes,reverse=True):text=text[:start]+json.dumps(value,ensure_ascii=False)+text[end:]
    return text

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def import_extra_libraries(extra_board,project_dir,needed_nicks,apply):
    source_dir=extra_board.parent;table_path=source_dir/'fp-lib-table';text=table_path.read_text();root=parse(text);rows=[];copied=[]
    for row in root.children('lib'):
        nick=row.first('name').items[1].value
        if nick not in needed_nicks:continue
        uri=row.first('uri').items[1].value;source_path=Path(uri.replace('${KIPRJMOD}',str(source_dir)))
        assert source_path.is_dir(),source_path
        dest=project_dir/source_path.name
        if dest.exists():
            assert {p.name:sha(p)for p in dest.glob('*.kicad_mod')}=={p.name:sha(p)for p in source_path.glob('*.kicad_mod')},dest
        elif apply:shutil.copytree(source_path,dest)
        row_text=text[row.start:row.end];old=row.first('uri').items[1];row_text=patches(row_text,[(old.start-row.start,old.end-row.start,'${KIPRJMOD}/'+dest.name)])
        rows.append((nick,row_text));copied.append({'nickname':nick,'source':str(source_path),'destination':str(dest)})
    assert {nick for nick,_ in rows}==needed_nicks
    target=project_dir/'fp-lib-table'
    current=target.read_text() if target.exists() else '(fp_lib_table\n)\n';r=parse(current)
    existing={n.first('name').items[1].value for n in r.children('lib')}
    additions=[row for nick,row in rows if nick not in existing]
    if apply and additions:target.write_text(current[:r.end-1]+'\n'+'\n'.join(additions)+'\n'+current[r.end-1:])
    return copied

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--project-stem',type=Path,required=True);ap.add_argument('--source-name',choices=['mainboard','ioboard'],required=True);ap.add_argument('--extra-board',type=Path);ap.add_argument('--inventory',type=Path,default=Path(__file__).with_name('eagle-source-structure.json'));ap.add_argument('--report',type=Path,required=True);ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    stem=args.project_stem.resolve();board=stem.with_suffix('.kicad_pcb');project_dir=stem.parent
    inv=json.loads(args.inventory.read_text());ss=inv['files'][args.source_name+'.sch'];bs=inv['files'][args.source_name+'.brd'];board_ids=footprint_ids(board);board_parts={e['reference']:e for e in bs['elements']}
    board_ids={ref:board_ids[native_reference(ref,True)] for ref in board_parts if native_reference(ref,True) in board_ids}
    expected={};by_package=defaultdict(set);by_lib_package=defaultdict(set)
    for ref,b in board_parts.items():
        if ref in board_ids:by_package[b['package']].add(board_ids[ref]);by_lib_package[(b['library'],b['package'])].add(board_ids[ref])
    extras={}
    if args.extra_board:
        extraction=footprint_ids(args.extra_board.resolve());extra_source=json.loads(Path(__file__).with_name('repaired-eagle-xml').joinpath('extra-footprint-inventory.json').read_text())[args.source_name]['schema_only_packages']
        for idx,p in enumerate(extra_source,1):extras[p['package']]=extraction['SCHEMAFP'+str(idx)]
    errors=[]
    for p in ss['parts']:
        lib=ss['raw_library_ordinals'][p['lib']-1];ds=lib['devicesets'][p['device']-1];variant=ds['variants'][p['variant']-1];package=variant['package'];ref=p['name'];nr=native_reference(ref,bool(package));target=''
        if package:
            if ref in board_parts and ref in board_ids and board_parts[ref]['package']==package:target=board_ids[ref]
            elif package in extras:target=extras[package]
            else:
                choices=by_lib_package[(lib['name'],package)] or by_package[package]
                if len(choices)==1:target=next(iter(choices))
                else:errors.append({'reference':ref,'package':package,'choices':sorted(choices)})
        expected[nr]={'source_reference':ref,'package':package,'target':target}
    changes=[];newfiles={};seen=set();default_targets=defaultdict(set);default_changes=[]
    for path in sorted(project_dir.glob('*.kicad_sch')):
        text=path.read_text();root=parse(text);edits=[]
        for sym in root.children('symbol'):
            ref=prop(sym,'Reference');fp=prop(sym,'Footprint')
            if ref:ref=Atom(symbol_reference(sym),ref.start,ref.end)
            if ref is None or fp is None:continue
            if ref.value not in expected:errors.append({'unknown_native_reference':ref.value,'path':str(path)});continue
            source=expected[ref.value];seen.add(ref.value)
            lib_id=sym.first('lib_id')
            if lib_id:default_targets[lib_id.items[1].value].add(source['target'])
            if fp.value!=source['target']:
                edits.append((fp.start,fp.end,source['target']));changes.append({'path':str(path),'reference':ref.value,'source_reference':source['source_reference'],'source_package':source['package'],'before':fp.value,'after':source['target']})
        newfiles[path]=patches(text,edits)
    # Align defaults only when every placed instance of the exact library item agrees.
    ambiguous_defaults={key:sorted(values) for key,values in default_targets.items() if len(values)!=1}
    defaults={key:next(iter(values)) for key,values in default_targets.items() if len(values)==1}
    for path,text in list(newfiles.items()):
        root=parse(text);lib_symbols=root.first('lib_symbols');edits=[]
        if lib_symbols:
            for sym in lib_symbols.children('symbol'):
                name=sym.items[1].value;fp=prop(sym,'Footprint')
                if name in defaults and fp is not None and fp.value!=defaults[name]:
                    edits.append((fp.start,fp.end,defaults[name]));default_changes.append({'path':str(path),'library_id':name,'before':fp.value,'after':defaults[name],'kind':'embedded'})
        newfiles[path]=patches(text,edits)
    symbol_table=project_dir/'sym-lib-table'
    if symbol_table.exists():
        for row in parse(symbol_table.read_text()).children('lib'):
            nick=row.first('name').items[1].value;uri=row.first('uri').items[1].value
            path=Path(uri.replace('${KIPRJMOD}',str(project_dir)));text=path.read_text();root=parse(text);edits=[]
            for sym in root.children('symbol'):
                name=nick+':'+sym.items[1].value;fp=prop(sym,'Footprint')
                if name in defaults and fp is not None and fp.value!=defaults[name]:
                    edits.append((fp.start,fp.end,defaults[name]));default_changes.append({'path':str(path),'library_id':name,'before':fp.value,'after':defaults[name],'kind':'project_cache'})
            newfiles[path]=patches(text,edits)
    absent=sorted(set(expected)-seen)
    if absent:errors.append({'missing_native_references':absent})
    needed={v.split(':',1)[0]for v in extras.values()};libraries=[]
    if not errors:
        if args.extra_board:libraries=import_extra_libraries(args.extra_board.resolve(),project_dir,needed,args.apply)
        if args.apply:
            for path,text in newfiles.items():path.write_text(text)
    report={'project_stem':str(stem),'applied':args.apply and not errors,'source_name':args.source_name,'source_parts':len(expected),'resolved_native_references':len(seen),'footprint_field_changes':changes,'symbol_default_changes':default_changes,'ambiguous_symbol_defaults_left_unchanged':ambiguous_defaults,'extra_libraries':libraries,'errors':errors,'preserved_source_schematic_package_differences':[{'reference':p['source_reference'],'schema_package':p['package'],'board_package':board_parts[p['source_reference']]['package']}for p in expected.values()if p['source_reference']in board_parts and p['package'] and p['package']!=board_parts[p['source_reference']]['package']]}
    args.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'applied':report['applied'],'changed_fields':len(changes),'changed_defaults':len(default_changes),'errors':errors,'report':str(args.report)},indent=2));return 1 if errors else 0
if __name__=='__main__':raise SystemExit(main())
