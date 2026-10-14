#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Read-only DIN function evidence; print JSON without touching source designs.

Default verifies the portable frozen source extract against source hashes,
original schematic record bytes and current PCB nets. To reproduce the full
original binary interpretation, add --parser-source <eagle_bin_parser.cpp>.
Use --refresh-source-extract with that argument to rewrite only the JSON
extract beside this script. The manufacturer drawing/CAD search is separate.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
sys.path.insert(0,str(REPO/'kicad-import/validation'))
from verify_native_projects import children,one,parse_sexpr,property_value

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
FUNCTIONS={'DIN1':'MIDI OUT','DIN2':'MIDI THRU','DIN3':'MIDI IN','DIN4':'DIN SYNC'}
DISPLAY12={'DIN1':'MIDI OUT','DIN2':'THRU','DIN3':'MIDI IN','DIN4':'SYNC'}
DISPLAY11={'DIN1':'MIDI IN','DIN2':'MIDI OUT','DIN3':'THRU','DIN4':'SYNC'}
# Connectivity anchors are read from the original source, not from the scene
# updater or the display-label mapping. They distinguish output, buffered
# receive/thru, isolated input and all four DIN-sync signal lines.
EXPECTED={
 'DIN1.5':'N$295','R13.2':'N$295','R13.1':'MIDI_OUT','J3.6':'MIDI_OUT',
 'DIN1.4':'N$296','R14.1':'N$296','R14.2':'+5V',
 'DIN2.5':'N$293','R15.1':'N$293','R15.2':'MIDI_IN','Q50.2':'MIDI_IN','J3.5':'MIDI_IN',
 'DIN2.4':'N$294','R18.1':'N$294','R18.2':'+5V',
 'DIN3.4':'N$234','R19.1':'N$234','R19.2':'N$90','IC24.1':'N$90','D48.C':'N$90',
 'DIN3.5':'N$87','IC24.2':'N$87','D48.A':'N$87',
 'IC24.4':'N$18','Q50.1':'N$18','R16.2':'N$18','Q50.3':'GND',
 'DIN4.1':'N$24','R24.2':'N$24','R24.1':'DINSYNC1','J3.12':'DINSYNC1',
 'DIN4.2':'N$78','R20.1':'N$78','R20.2':'GND',
 'DIN4.3':'N$22','R21.1':'N$22','R21.2':'DINSYNC4','J3.9':'DINSYNC4',
 'DIN4.4':'N$25','R23.1':'N$25','R23.2':'DINSYNC2','J3.11':'DINSYNC2',
 'DIN4.5':'N$23','R22.2':'N$23','R22.1':'DINSYNC3','J3.10':'DINSYNC3',
}
CORE=['original-eagle/ioboard.sch','original-eagle/ioboard.brd',
      'kicad-working/ioboard/ioboard.kicad_pcb','kicad-working/ioboard/ioboard.kicad_sch']

def current_pcb():
    nodes={}
    pcb=parse_sexpr((REPO/CORE[2]).read_text())
    for footprint in children(pcb,'footprint'):
        ref=property_value(footprint,'Reference','reference')
        for pad in children(footprint,'pad'):
            net=one(pad,'net')
            if net:nodes[ref+'.'+pad[1]]=net[-1]
    return nodes

def decode_original(parser_source):
    from inspect_eagle_source import Eagle,load_spec
    spec=load_spec(parser_source)
    schematic=Eagle(REPO/CORE[0],spec)
    sr=schematic.schematic()
    board=Eagle(REPO/CORE[1],spec).board()
    refs={node.rsplit('.',1)[0] for node in EXPECTED}
    sm=[r for r in sr['source_schematic_pin_net_memberships'] if r['reference'] in refs]
    bm=[r for r in board['pad_net_memberships'] if r['reference'] in refs]
    records={r['index']:dict(record_index=r['index'],record_id_hex=hex(r['id']),
                            original_24bytes_hex=r['raw'].hex(),decoded_attributes=r['attrs'])
             for r in schematic.records if r['index'] in {m['record_index'] for m in sm}}
    visual=[]
    for record in schematic.records:
        if record['id']==0x3100 and record['attrs'].get('textfield') in ['MIDI OUT','MIDI THRU','MIDI IN','DINSYNC']:
            visual.append(dict(record_index=record['index'],text=record['attrs']['textfield'],
                               xy_mm=[record['attrs']['x']/10000,record['attrs']['y']/10000]))
            records[record['index']]=dict(record_index=record['index'],record_id_hex=hex(record['id']),
                                         original_24bytes_hex=record['raw'].hex(),decoded_attributes=record['attrs'])
    gates=[]
    for part in schematic.by_id(0x3800):
        if part['attrs'].get('name') not in FUNCTIONS:continue
        for gate in part['children']:
            if gate['id']==0x3000 and gate['attrs'].get('gateno')==1:
                gates.append(dict(reference=part['attrs']['name'],record_index=gate['index'],
                                  xy_mm=[gate['attrs']['x']/10000,gate['attrs']['y']/10000]))
                records[gate['index']]=dict(record_index=gate['index'],record_id_hex=hex(gate['id']),
                                           original_24bytes_hex=gate['raw'].hex(),decoded_attributes=gate['attrs'])
    return dict(schema_version=1,review_date='2026-10-15',
                method='Read-only original Eagle4.13 fixed24-byte schematic/board records through existing Python inspector and recorded fork table; not derived from Blender labels.',
                core_inputs=[dict(path=p,sha256=sha(REPO/p),bytes=(REPO/p).stat().st_size) for p in CORE],
                decoder=dict(inspector_path='kicad-import/validation/inspect_eagle_source.py',
                             inspector_sha256=sha(REPO/'kicad-import/validation/inspect_eagle_source.py'),
                             parser_source_name=parser_source.name,parser_source_sha256=sha(parser_source),
                             full_redecode_requires='Pass local fork common/io/eagle/eagle_bin_parser.cpp with--parser-source; not bundled again.'),
                functions=FUNCTIONS,revision11_display_text=DISPLAY11,revision12_display_text=DISPLAY12,
                abbreviation_meaning={'THRU':'MIDI THRU','SYNC':'DIN SYNC'},
                schematic_pin_net_subset=sm,board_pad_net_subset=bm,
                original_schematic_text=visual,original_main_gate_positions=gates,
                original_schematic_records=sorted(records.values(),key=lambda r:r['record_index']),
                binary_limit='The fixed-record inspector shares the documented fork recordtable. Default portable replay verifies frozen original bytes/hash and PCB graph; full semantic binary re-decode requires that table.',
                original_Eagle_DIN_elements=[r for r in board['elements'] if r['reference'] in FUNCTIONS],
                physical_or_electrical_hardware_test_performed=False,source_designs_modified=False)

def verify(evidence):
    checks=[]
    def check(name,passed,**details):checks.append(dict(check=name,passed=bool(passed),**details))
    for row in evidence['core_inputs']:
        check('input unchanged:'+row['path'],sha(REPO/row['path'])==row['sha256'])
    original=(REPO/CORE[0]).read_bytes()
    for row in evidence['original_schematic_records']:
        at=row['record_index']*24
        check('original schematic record:'+str(row['record_index']),
              original[at:at+24].hex()==row['original_24bytes_hex'])
    graphs={'current PCB':current_pcb(),
            'original Eagle board':{r['reference']+'.'+r['pad']:r['net'] for r in evidence['board_pad_net_subset']},
            'original Eagle schematic':{r['reference']+'.'+p:r['net'] for r in evidence['schematic_pin_net_subset'] for p in r['pads']}}
    for source,graph in graphs.items():
        for node,net in EXPECTED.items():check(source+':'+node,graph.get(node)==net,actual_net=graph.get(node),expected_net=net)
    for ref,function in FUNCTIONS.items():
        text='DINSYNC' if ref=='DIN4' else function
        gate=next(r for r in evidence['original_main_gate_positions'] if r['reference']==ref)
        label=next(r for r in evidence['original_schematic_text'] if r['text']==text)
        delta=[a-b for a,b in zip(label['xy_mm'],gate['xy_mm'])]
        check(ref+':original named schematic block',abs(delta[1]+12.7)<1e-7 and abs(delta[0])<6,
              original_text=text,label_minus_main_gate_mm=delta)
    return dict(passed=all(r['passed'] for r in checks),checks_count=len(checks),checks=checks,
                functions=FUNCTIONS,revision12_display_text=DISPLAY12,read_only=True,
                scope='Function/source evidence only; no physical fit or hardware playback test.')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parser-source',type=Path)
    parser.add_argument('--refresh-source-extract',action='store_true')
    args=parser.parse_args()
    path=HERE/'function-source-evidence.json'
    if args.refresh_source_extract and not args.parser_source:parser.error('--refresh-source-extract requires--parser-source')
    evidence=decode_original(args.parser_source) if args.parser_source else json.loads(path.read_text())
    if args.refresh_source_extract:path.write_text(json.dumps(evidence,indent=2)+'\n')
    result=verify(evidence)
    result['full_original_binary_redecoded']=bool(args.parser_source)
    print(json.dumps(result,indent=2))
    return 0 if result['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
