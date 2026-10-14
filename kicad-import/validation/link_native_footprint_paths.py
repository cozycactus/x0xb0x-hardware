#!/usr/bin/env python3
"""Link existing native footprints to exported schematic identities by exact reference.

No placement, pads, copper, references, or nets are changed. Board-only footprints
remain untouched. Paths come from the native exported netlist, never from a guessed
root UUID or from an arbitrary unit of a multi-unit schematic symbol.
"""
from pathlib import Path
import argparse,json,xml.etree.ElementTree as ET
from resolve_native_footprint_fields import parse,prop

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--netlist',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);ap.add_argument('--apply',action='store_true');a=ap.parse_args()
    net=ET.parse(a.netlist).getroot();comps={};errors=[]
    for comp in net.findall('./components/comp'):
        ref=comp.get('ref');path=comp.find('sheetpath');uuids=comp.findtext('tstamps','').split()
        if ref in comps:errors.append({'duplicate_component_reference':ref});continue
        if path is None or not uuids:errors.append({'missing_native_identity':ref});continue
        comps[ref]={'path':path.get('tstamps').rstrip('/')+'/'+uuids[0],'sheetname':path.get('names'),'all_symbol_uuids':uuids}
    text=a.board.read_text();root=parse(text);edits=[];links=[];board_only=[]
    for fp in root.children('footprint'):
        ref=prop(fp,'Reference').value
        if ref not in comps:board_only.append(ref);continue
        identity=comps[ref];old=fp.first('path');value=identity['path']
        if old:
            if old.items[1].value!=value:edits.append((old.items[1].start,old.items[1].end,json.dumps(value)))
        else:edits.append((fp.end-1,fp.end-1,'\n\t\t(path '+json.dumps(value)+')\n\t'))
        links.append({'reference':ref,**identity,'before':old.items[1].value if old else None})
    if a.apply and not errors:
        for start,end,replacement in sorted(edits,reverse=True):text=text[:start]+replacement+text[end:]
        a.board.write_text(text)
    report={'board':str(a.board.resolve()),'netlist':str(a.netlist.resolve()),'applied':a.apply and not errors,'linked_footprints':len(links),'paths_changed':len(edits),'links':links,'board_only_footprints_left_unchanged':board_only,'errors':errors}
    a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['applied','linked_footprints','paths_changed','board_only_footprints_left_unchanged','errors']},indent=2));return 1 if errors else 0
if __name__=='__main__':raise SystemExit(main())
