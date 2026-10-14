from pathlib import Path
import xml.etree.ElementTree as E
import json,re,hashlib,math,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
actual=json.loads((HERE/'actual-board-endpoints.json').read_text());prior_path=ROOT/'validation/models-review-6/misc-body-illustrations/reference/ribbon-jumper-source-map.json';prior=json.loads(prior_path.read_text());wiki=(HERE/'primary-wiki-jumpers.md').read_text()
functions={}
for line in wiki.splitlines():
 cols=[c.strip() for c in line.strip().strip('|').split('|')]
 if len(cols)==4 and cols[0] in ['J4','J5','J6','J7']:functions[cols[0]]={i+1:s for i,s in enumerate(cols[1:])}
functions['J3']={int(a):b.strip() for a,b in re.findall(r'^\| (\d+) \| ([^|]+)\|$',wiki,re.M)}
assert [len(functions[x]) for x in ['J3','J4','J5','J6','J7']]==[12,3,3,3,3]
netlists={};source=[]
for board in ['mainboard','ioboard']:
 path=HERE/(board+'-current.net');r=E.parse(path).getroot();nets={};pinmap={}
 for net in r.findall('./nets/net'):
  nodes=[n.attrib for n in net.findall('node')];nets[net.get('name')]=nodes
  for n in nodes:
   if n['ref'] in functions:pinmap[(n['ref'],int(n['pin']))]={'name':net.get('name'),'node':n,'all_nodes':nodes}
 netlists[board]=pinmap
 for suffix in ['.kicad_pcb','.kicad_sch']:
  p=ROOT/board/(board+suffix);source.append({'path':str(p),'sha256':sha(p)})
 source.append({'path':str(path),'sha256':sha(path),'kind':'fresh native KiCad XML netlist exported read-only from the current schematic'})
checks=[];cables=[]
for ref in ['J3','J4','J5','J6','J7']:
 old=next(c for c in prior['cables'] if c['reference']==ref);count=len(functions[ref]);endpoints={b:actual[b]['footprints'][ref] for b in actual};pins=[]
 for pin in range(1,count+1):
  p={'main_pin':pin,'io_pin':pin,'documented_function':functions[ref][pin]}
  for b in actual:
   pad=next(v for v in endpoints[b]['pads'] if v['pin']==pin);net=netlists[b][(ref,pin)];oldpin=next(v for v in old['pins'] if v['number']==pin)
   checks.append({'check':b+'.'+ref+'.'+str(pin)+' PCB net equals fresh schematic net','passed':pad['net']==net['name']})
   checks.append({'check':b+'.'+ref+'.'+str(pin)+' prior map net retained','passed':pad['net']==oldpin[b+'_net_name']})
   checks.append({'check':b+'.'+ref+'.'+str(pin)+' prior local pad retained','passed':math.dist(pad['original_footprint_local_xy_mm'],oldpin[b+'_local_pad_mm'])<1e-7})
   p[b]={'net':pad['net'],'pad':pad,'schematic_connector_node':net['node'],'functional_endpoint_nodes':[v for v in net['all_nodes'] if (v['ref'].startswith('IC') or v['ref'] in ['MIXIN0','MIXOUT0','HEADPHONE0','CV0','GATE0']) and v['ref']!=ref]}
  pins.append(p)
 for b in actual:
  points=endpoints[b]['pads'];axis=[points[-1]['native_xy_mm'][k]-points[0]['native_xy_mm'][k] for k in range(2)];length=math.hypot(*axis);endpoints[b]['native_pin_number_increase_axis_xy']=[v/length for v in axis]
  for a,c in zip(points,points[1:]):checks.append({'check':b+'.'+ref+' pitch '+str(a['pin'])+'→'+str(c['pin']),'passed':abs(math.dist(a['native_xy_mm'],c['native_xy_mm'])-2.54)<1e-7})
  checks.append({'check':b+'.'+ref+' original pin1 silkscreen retained','passed':any(v['text']=='1' for v in endpoints[b]['pin_markers'])})
 cables.append({'reference':ref,'mapping':'mainboard.'+ref+'.n → ioboard.'+ref+'.n','electrical_conductor_count':count,'pitch_mm':2.54,'mapping_evidence':'Original jumper signal table plus finishing manual same pin1 stripe at both ends, corroborated by current schematic endpoint functions and actual PCB numbering.','endpoints':endpoints,'pins':pins})
usbpins=cables[0]['pins']
assert any(v['ref']=='IC25' and v['pin']=='25' and v['pinfunction']=='TXD_25' for v in usbpins[0]['ioboard']['functional_endpoint_nodes'])
assert any(v['ref']=='IC3' and v['pin']=='3' and v['pinfunction']=='(RXD1)PB2_3' for v in usbpins[0]['mainboard']['functional_endpoint_nodes'])
assert any(v['ref']=='IC25' and v['pin']=='24' and v['pinfunction']=='RXD_24' for v in usbpins[1]['ioboard']['functional_endpoint_nodes'])
assert any(v['ref']=='IC3' and v['pin']=='4' and v['pinfunction']=='(TXD1)PB3_4' for v in usbpins[1]['mainboard']['functional_endpoint_nodes'])
finish=ROOT/'visualization/blender-case/next-review/original-finish-mirror.html';shutil.copyfile(finish,HERE/'original-finishing-pinned-mirror.html')
report={'scope':'Independent source-grounded J3–J7 harness map for scene construction. No actual PCB/project/schematic changes.','passed':all(c['passed'] for c in checks),'electrical_group_count':5,'conductor_count':24,'endpoint_pad_count':48,'check_count':len(checks),'checks':checks,'cables':cables,'usb_name_resolution':{'pin1':'ioboard J3.1 USB_TX / IC25.25 TXD output → mainboard J3.1 USBRX / IC3.3 RXD1','pin2':'mainboard J3.2 USB_TX / IC3.4 TXD1 → ioboard J3.2 USB_RX / IC25.24 RXD input','interpretation':'The wiki USB TX/RX names correspond to the I/O USB bridge perspective. Pin1→pin1 and pin2→pin2 already connect transmitter to receiver. Do not cross physical pins by matching equal net strings across projects.','evidence_type':'Direction interpretation follows explicit current schematic device pin functions; no historical cable crossing inferred.'},'documented_orientation':{'pin1_stripe':'Original finishing manual explicitly says to match pin1 with the black stripe at both ends.','signal_pin_numbers':'Original wiki jumper table defines the24 conductor functions.','physical_stock_pieces':'Original finishing instructions specify four3-conductor pieces and two6-conductor pieces.','connector_bodies':'These are soldered jumper cables. MA03-1/MA12-1 are footprint names; no plastic header inferred.'},'assembly_interpretation':{'physical_piece_count':6,'piece_groups':[{'reference':'J3','pin_range':[1,6],'count':6},{'reference':'J3','pin_range':[7,12],'count':6}]+[{'reference':r,'pin_range':[1,3],'count':3} for r in ['J4','J5','J6','J7']],'basis':'Allocation of the two documented6-conductor pieces to the only12-pad group J3 follows the documented counts and actual row; this split assignment is a reconstruction inference, not an independently measured installed cable.','black_stripe_for_second_J3_half':'If rendering two adjacent6-conductor ribbons, mark the low-number edge of each corresponding half consistently at both ends. The second half begins at overallJ3.7; its exact historical ink placement is unmeasured.'},'scene_ambiguities':['Pin mapping and actual2.54mm pad row are established. Conductor diameter, insulation profile, stripped length, bend radius, slack,3D cable route and installed length are not established.','Source stock length152.4mm in the earlier distributor/BOM map must not be treated as measured installed board separation.','Native endpoint XY is PCB(X,-Y). Apply the actual board world matrix once; do not infer world left/right from a flat board drawing. Mainboard F.Cu points inside the assembled case after its side flip.','Actual jumper footprints are on F.Cu and have retained pin-number marks. Whether each wire is bent immediately after a pad or a short straight segment is a scene construction choice.','J3 power and ground are duplicated on pins3/4 and7/8. Preserve all12 conductors despite equivalent nets.','This review validates the source map and schematic/PCB agreement, not physical cable fit or electrical continuity on hardware.'],'primary_sources':[{'url':'https://wiki.ladyada.net/x0x/jumpers','local_file':'primary-wiki-jumpers.md','retrieval_metadata':'primary-wiki-retrieval.json','status':'Public primary page fetched successfully by Firecrawl basic proxy, HTTP200; also independently indexed by web search.','license':'CC BY-SA4.0 per wiki footer; retained as reference.'},{'url':'https://www.ladyada.net/make/x0xb0x/fab/finish/index.html','local_file':'original-finishing-pinned-mirror.html','mirror_url':'https://github.com/x0xb0x/x0xb0x.github.io/blob/1910f746d2d8758f2651596b00c08f76c847c926/pages/ladyada.net/make/x0xb0x/fab/finish/index.html','evidence':'Steps1–2: split stock to four3-conductor and two6-conductor pieces; solder jumpers with pin1 stripe at both ends. Live primary page read by web tool matches retained pinned mirror.'},{'url':'https://www.ladyada.net/make/x0xb0x/fab/vco.html','evidence':'Original VCO manual independently tells the builder to connect corresponding J4 pins, using the printed1 at both ends.'}],'input_map':{'path':str(prior_path),'sha256':sha(prior_path),'all48_endpoint_net_names_and_local_positions_reconfirmed':True},'source_files':source,'read_only_preservation':{b:actual[b]['unchanged_after_read'] for b in actual}}
report['retained_reference_hashes']={p.name:sha(p) for p in HERE.iterdir() if p.is_file() and p.name in ['primary-wiki-jumpers.md','primary-wiki-retrieval.json','original-finishing-pinned-mirror.html','actual-board-endpoints.json']}
(HERE/'verified-harness-map.json').write_text(json.dumps(report,indent=2)+'\n')
rows=['# Independently verified x0xb0x harness','','**Five electrical groups,24 conductors,48 endpoint pads.** Current PCB pads agree with fresh native schematic netlists for every endpoint. The earlier map matches every actual endpoint net and local pad position.','', 'The [original jumper table](https://wiki.ladyada.net/x0x/jumpers) gives signal functions. The [original finishing instructions](https://www.ladyada.net/make/x0xb0x/fab/finish/index.html) specify soldered ribbons, four3-conductor pieces plus two6-conductor pieces, and pin1 stripe alignment at both ends. The [VCO manual](https://www.ladyada.net/make/x0xb0x/fab/vco.html) independently confirms corresponding J4 pins.','','| Group/pin | Main net | I/O net | Function |','|---|---|---|---|']
for c in cables:
 for p in c['pins']:rows.append(f"| {c['reference']}.{p['main_pin']}→{c['reference']}.{p['io_pin']} | {p['mainboard']['net']} | {p['ioboard']['net']} | {p['documented_function']} |")
rows+=['','**USB needs no physical pin swap.** J3.1 connects FT232 IC25.25 TXD output (`USB_TX`) to MCU IC3.3 RXD1 (`USBRX`). J3.2 connects MCU IC3.4 TXD1 (`USB_TX`) to FT232 IC25.24 RXD input (`USB_RX`). The same net string appears on different directions in the two independent projects; pin numbers and device pin functions resolve the ambiguity.','','The two6-conductor pieces are allocated to J3.1–6 and J3.7–12 by the documented counts and the actual12-pad row. That allocation is a reconstruction inference. Bends, slack, wire sections, trimmed length and the3D route remain scene construction choices. Use actual endpoint pad positions and each board world matrix; no historical installed cable path or physical fit is certified.','','See [verified-harness-map.json](verified-harness-map.json) for all actual endpoint coordinates, orientations, silk pin markers, schematic endpoint evidence, source hashes and ambiguity notes. The primary wiki reference retains its CC BY-SA4.0 attribution. No KiCad/project files were edited.']
md='\n'.join(rows)+'\n'
for a,b in [('groups,24','groups, 24'),('conductors,48','conductors, 48'),('four3-','four 3-'),('two6-','two 6-'),('pin1','pin 1'),('actual12-','actual 12-'),('the3D','the 3D'),('SA4.0','SA 4.0')]:md=md.replace(a,b)
(HERE/'README.md').write_text(md)
assert report['passed'];print(json.dumps({'passed':report['passed'],'conductors':24,'endpoint_pads':48,'checks':len(checks),'manifest':str(HERE/'verified-harness-map.json')},indent=2))
