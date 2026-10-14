"""Read-only source basis for rear-panel seating; no CAD or scene mutation.

SPDX-License-Identifier: CC0-1.0
Manufacturer documents and original design files retain their own notices.
Only JSON reports beside this script are written.
"""
from pathlib import Path
import hashlib
import html
import json
import math
import re
import sys

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
WORK=REPO/'kicad-working'
BASE=WORK/'visualization/blender-case-revision-7'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sys.path.insert(0,str(REPO/'kicad-import/validation'))
from verify_native_projects import children,one,parse_sexpr,property_value

source_specs=[
 ('original-download','kicad-working/visualization/blender-case-revision-7/source/original-download-page-mirror.html','https://www.ladyada.net/make/x0xb0x/download.html','Original author instruction: PT10 panels use0.062inch material.'),
 ('original-rear-panel','kicad-working/visualization/blender-case-revision-7/source/x0xb0x_iopanel_march2.dxf','https://www.ladyada.net/media/x0xb0x/x0xb0x_iopanel_march2.dxf','Original author geometry, inches; retained pinned mirror with source notice.'),
 ('original-finishing','kicad-working/validation/models-review-10/front-controls-review/sources/original-finishing.html','https://www.ladyada.net/make/x0xb0x/fab/finish/index.html','Original step5 attaches rearplate through3quarterinchjacks. No explicit numericalsetback or washer-side sequence.'),
 ('original-io-manual','kicad-working/visualization/blender-case-revision-7/source-review/original-ioboard-manual.md','https://www.ladyada.net/make/x0xb0x/fab/ioboard/','Original step9: DINfacesflushPCBedge; strongsoldermechanicalbond. No paneloffsetdimension.'),
 ('original-io-photo','kicad-working/validation/models-review-10/heatsink-fit-research/sources/ioboard_done.jpg','https://ladyada.net/make/x0xb0x/fab/images/ioboard_done.jpg','Visuallyreviewed: connectorfronts atPCBedge, no DINflangemountscrews, audio nuts/washerssuppliedonbareboard; photographnot dimensionalcalibration.'),
 ('pactec-pt10','kicad-working/visualization/blender-case-revision-7/source/pactec-pt10-manufacturer-drawing.pdf','https://www.farnell.com/datasheets/1483254.pdf','PacTec82232revC: rearplate8.580x2.070x.062inch. SectionC-C/detailDusedwithqualifiedtracedsetback.'),
 ('nys-older','kicad-working/visualization/blender-case-revision-7/quality-model-sources/rear-quality/source/nys-216-manufacturer.dxf','https://www.rean-connectors.com/media/12224/download/nys-216-1.dxf?v=1','2007revC: nose8.5, axis8, 3/8-32UNEF; existingnativebodyusescanonicalshoulderY0 as registrationassumption.'),
 ('nys-newer','kicad-working/visualization/blender-case-revision-7/quality-model-sources/rear-quality/source/nys216.pdf','https://www.rean-connectors.com/media/9014/download/nys-216.pdf?v=1','2015: M11x1.25, suppliednut/washerdimensions. Not proofofoldernosecompatibility orhistoricalfittedpart.'),
 ('sds50j','kicad-working/visualization/blender-case-revision-7/quality-model-sources/rear-quality/source/sds50j.pdf','https://www.sameskydevices.com/product/resource/sds-j.pdf','Page3: SDS50J20x15.8maxx21.1, flange1.8, axis10; doesnotgiveinstallationdepthfororiginalx0xb0xpanel.'),
 ('mj3536n','kicad-working/validation/models-review-10/rear-connector-quality/sources/mj-3536n-current.pdf','https://www.sameskydevices.com/product/resource/mj-3536n.pdf','Page2: nonthreadedØ6bushingprojection3, axis5.5, body10x15.8x10.'),
 ('pj202ah','kicad-working/validation/models-review-10/rear-connector-quality/sources/pj-202ah-current.pdf','https://www.sameskydevices.com/product/resource/pj-202ah.pdf','Page2: body9x14.4x11, axis6.5, frontbore6.5, pin2, insertion9; no panelclampingnut.'),
 ('usb-retained-extract','kicad-working/ioboard/3dmodels/Revision6/rear-body-illustrations/provenance/source/kc-301021-web-extract.json','https://www.mouser.com/catalog/specsheets/KC-301021.pdf','PreviousretainedBOMfamilyenvelopeextract; refreshedprimaryindexedtextbelowaddsPCB/panelrecommendation. No binaryPDFvisualreviewobtained.')
]
sources=[dict(id=i,path=p,url=u,evidence=e,sha256=sha(REPO/p),bytes=(REPO/p).stat().st_size)
         for i,p,u,e in source_specs]
derived_paths=[
 'kicad-working/visualization/blender-case-revision-7/panels/original-panels.json',
 'kicad-working/visualization/blender-case-revision-7/panels/board-panel-alignment.json',
 'kicad-working/visualization/blender-case-revision-7/case-model/pt10-datums.json',
 'kicad-working/visualization/blender-case-revision-7/source-review/io-depth-and-detached-outline-evidence.json',
 'kicad-working/validation/nys216-hardware-quality/hardware-parameters.json'
]
derived=[dict(path=p,sha256=sha(REPO/p),classification='previous reconstruction/evidence, not independent manufacturer dimension') for p in derived_paths]
checks=[]
def check(name,ok,**evidence):
    checks.append(dict(check=name,passed=bool(ok),**evidence))

download=html.unescape((REPO/source_specs[0][1]).read_text())
check('original author specifies.062inchsheet', '0.062" material' in download)
finish=html.unescape((REPO/source_specs[2][1]).read_text())
plain=re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',finish))
check('original rearplate usesquarterinchjacks','back panel is attached by threading the 1/4" jacks through the panel' in plain)
io=(REPO/source_specs[3][1]).read_text()
check('original DINfaceflushPCB instruction','face is flush with the PCB' in io)

panels=json.loads((BASE/'panels/original-panels.json').read_text())
panel=panels['iopanel']
t=.062*25.4
check('parsedpanelthicknessmatchesauthor',abs(panel['thickness_mm']-t)<1e-10,
      thickness_mm=t)
check('originalrearpanelninecirclestworectangles',len(panel['circles'])==9 and len(panel['rectangular_cutouts'])==2)
check('originalrearDXFcontainsnocontrolsilkscreenart',panel['silkscreen_text']==[])
check('originalDXFhashmatchesparsedpanel',sha(REPO/source_specs[1][1])==panel['source_sha256'])
lines=(REPO/source_specs[1][1]).read_text(errors='replace').splitlines()
pairs=[(int(lines[i]),lines[i+1].strip()) for i in range(0,len(lines)-1,2)]
chunks=[]
for code,value in pairs:
    if code==0:chunks.append([(code,value)])
    elif chunks:chunks[-1].append((code,value))
entities={dict(c).get(5):dict(c) for c in chunks if 5 in dict(c)}
origin=panel['origin_source_in']
for circle in panel['circles']:
    ent=entities[circle['source_handle']]
    actual=[(float(ent[10])-origin[0])*25.4,
            (float(ent[20])-origin[1])*25.4,float(ent[40])*25.4]
    expected=circle['center_mm']+[circle['radius_mm']]
    check(circle['board_reference']+':originalDXFcircleunchanged',
          ent[0]=='CIRCLE' and max(abs(a-b) for a,b in zip(actual,expected))<1e-8,
          handle=circle['source_handle'],actual_center_radius_mm=actual)
for rectangle in panel['rectangular_cutouts']:
    corners=rectangle['points_source_in']
    for handle in rectangle['source_handles']:
        ent=entities[handle]
        ends=[(float(ent[10]),float(ent[20])),(float(ent[11]),float(ent[21]))]
        ok=all(min(math.hypot(x-c[0],y-c[1]) for c in corners)<1e-9 for x,y in ends)
        check(rectangle['board_reference']+':originalDXFrectangleline:'+handle,ent[0]=='LINE' and ok)

families=[
 dict(family='NYS216',references=['HEADPHONE0','MIXIN0','MIXOUT0'],source_ids=['nys-older','nys-newer'],
      canonical_front_direction=[0,-1,0],canonical_body_shoulder_y_mm=0,
      canonical_mating_face_y_mm=-8.5,canonical_socket_axis_z_mm=8,
      nose_projection_from_body_shoulder_mm=8.5,
      mounting='ShoulderedthreadedPCBjack; originalrearplateisretainedbythesethreejacks.',
      source_registration_limit='CanonicalbodyshoulderY0 atoriginalfootprintorigin is currentmodelregistration, not historicalleadfitproof. OriginalfpKiCadY+.508anddetachedconstructionstripinnerY+.508suggestintendedpaneldatum, butstripidentity/historicalvariantunconfirmed.'),
 dict(family='SDS50J',references=['DIN1','DIN2','DIN3','DIN4'],source_ids=['sds50j','original-io-manual'],
      canonical_front_direction=[0,-1,0],canonical_flange_front_y_mm=0,
      canonical_flange_back_y_mm=1.8,canonical_mating_face_y_mm=0,canonical_socket_axis_z_mm=10,
      mounting='PCBsolderedDINjack. Manufacturerflangehas3holesbutoriginalpanelcontainsnocompanionflangemountingpattern; noaddedflangescrewsimplied.',
      source_registration_limit='DINfaceflushPCBedgeisoriginalinstruction. Itdoesnotrequirefaceflushpanelouterface; nominalrecesscanremain.'),
 dict(family='MJ3536N',references=['CV0','GATE0'],source_ids=['mj3536n'],
      canonical_front_direction=[0,-1,0],canonical_body_shoulder_y_mm=0,
      canonical_mating_face_y_mm=-3,canonical_socket_axis_z_mm=5.5,
      bushing_projection_from_body_shoulder_mm=3,bushing_diameter_mm=6,
      mounting='PCBsolderednonthreadedbushingjack. NoMJnut/washersorpanelclampareestablished.',
      source_registration_limit='Bodyseat againstPCBtop is nominalassumption; historicalcurrentmold/tailgauge notqualified.'),
 dict(family='PJ202AH',references=['POWER0'],source_ids=['pj202ah'],
      canonical_front_direction=[0,1,0],canonical_mating_face_y_mm=0,
      canonical_body_rear_y_mm=-14.4,canonical_socket_axis_z_mm=6.5,
      canonical_body_width_height_mm=[9,11],
      mounting='PCBsolderedrectangularpowerjackwithoutpanelnut. Frontmaypass throughoriginalrectangle; innerbodyneednotclampplate.',
      source_registration_limit='ActualPOWERfootprintrotation180isexternalmodelplacement. Exactterminalseatandhistoricalvariantnotqualified.'),
 dict(family='USB_TypeB',references=['USB0'],source_ids=['usb-retained-extract'],
      canonical_front_direction=[0,-1,0],canonical_mating_face_y_mm=0,
      canonical_body_rear_y_mm=16,canonical_socket_axis_z_mm=5.31,
      canonical_body_width_height_mm=[12.04,10.62],
      mounting='GenericBOM-familyPCBUSB-Bjackwithshell/insulator; noexternalnutorwasher.',
      source_registration_limit='5.31iscurrentillustrationhalf-height, notaprintedPCB-to-portaxis. OriginalBOMallowsdifferentthroughholeUSB-Bparts; PN61729footprintdoesnotprove154-2442-Eidentity. Frontlip/PCB-to-bodyseatingrequirebinarydrawingorrealpart.')
]
pcb=WORK/'ioboard/ioboard.kicad_pcb'
pcb_hash=sha(pcb)
fps={property_value(f,'Reference','reference'):f for f in children(parse_sexpr(pcb.read_text()),'footprint')}
for family in families:
    assignments=[]
    for ref in family['references']:
        fp=fps[ref]
        model=children(fp,'model')[0]
        path=Path(model[1].replace('${KIPRJMOD}',str(WORK/'ioboard')))
        transform={k:list(map(float,one(one(model,k),'xyz')[1:])) for k in ['offset','rotate','scale']}
        check(ref+':existingnativecanonicaltransform',transform==dict(offset=[0,0,0],rotate=[0,0,0],scale=[1,1,1]),transform=transform)
        assignments.append(dict(reference=ref,footprint_at=list(map(float,one(fp,'at')[1:])),
                                model_path=str(path.relative_to(REPO)),model_sha256=sha(path),transform=transform))
    family['current_native_assignments']=assignments

usb_primary=dict(
    source_url='https://www.mouser.com/catalog/specsheets/KC-301021.pdf',
    title='KC-301021, USB SeriesBConnector154-2442-E',drawing_date='2006-07-19',retrieved_date='2026-10-15',
    retrieval='PrimaryPDFindexedtextviaweb; no localbinary obtained ordiagramvisuallyverified.',
    confirmed_printed_text=dict(body_envelope_mm=[12.04,16,10.62],front_aperture_mm=[8.45,7.78],recommended_PCB_thickness_mm=1.57,recommended_panel_thickness_max_mm=2.67),
    download_attempts=[dict(protocol='defaultHTTP2',outcome='HTTP2INTERNAL_ERROR,0bytes'),dict(protocol='HTTP1.1',outcome='0bytesafterapproximately22seconds; stoppedboundedretry')],
    unresolved=['Dimensionorientation/PCBplane/frontlipnotvisuallyverifiedinnewbinary; no newaxis/seatingdatumasserted.','Source154-2442-EidentitynotproofactualhistoricalPN61729fittedpart.'])
(HERE/'usb-primary-retrieval.json').write_text(json.dumps(usb_primary,indent=2)+'\n')

result=dict(
    schema_version=1,review_date='2026-10-15',passed=all(c['passed'] for c in checks),checks_count=len(checks),checks=checks,
    scope='Read-onlysourceauditforBlender10rearconnector/panelseating; no correctionorphysicalfitcertification.',
    passed_meaning='Onlyretainedsource/geometrymapping/assignmentchecks pass. Knownassemblyintersectionsremain; passedisnotapanel-fitresult.',
    sources=sources,derived_evidence=derived,
    rear_panel=dict(thickness_mm=t,width_mm=217.932,height_mm=52.578,circles=panel['circles'],rectangular_cutouts=panel['rectangular_cutouts'],
                    original_cutout_counts=panel['counts'],no_DIN_flange_screw_pattern=True,
                    source_extent_basis='OriginalDXFinches; manufacturerPacTecagreesnominalsize. Sourceannotations/centerlinesare notcuts.',
                    case_placement_limit='ExistingouterfaceY198.4947wastracedfromPacTecC-Cnotprintedsetback;approximately±0.5mm. RearloweredgeZ6.2992usesdetailDandretainsconflictingundimensionedrear-silhouetteinterpretation.'),
    families=families,
    seating_interpretation=dict(
        axial_coordinate='qpositiveoutwardalongrearportaxis; q0isplateinnerface, plateoccupies0..1.5748mm.',
        audio_conventional_order=['bodyshoulder','panel','suppliedwasher','suppliednut'],
        audio_order_status='Assemblyinterpretation; originalfinishingtextdoesnotexplicitlystatewasher-sideorder. Notanextractedmanufacturerinstallationstack.',
        conditional_audio_stack_mm=dict(nose_from_shoulder=8.5,panel=t,washer=1.2,nut=5,tip_after_nut=8.5-t-1.2-5),
        conditional_audio_stack_limit='Onlyifbodyshoulderseatsatinnerplate;combinesoldernoseandnewerhardware, sodoesnotcertifythreadsorfit.',
        conditional_MJ_projection_past_outerface_mm=3-t,
        conditional_DIN_recess_from_outerface_mm=t,
        conditional_limits='Thesearearithmeticfromhypotheticalshoulder/frontseatatinnerplate, notmeasurementsorrequiredpositions.'),
    unresolved_datums=[
        'OriginaldocumentationdoesnotdimensionrearPCB-to-plate setbackorbodyseatinggaps.',
        'ThreeaudiofootprintsKiCadY+.508/body-frontconstructionstrip+.508differfromearlierPCBY0=plateinnerassumption; stripidentityandcurrentmodelregistrationarenotfactoryfitproof.',
        'EarlierMJheight5.5givesPCBtop6.184aboverearpanelbottom; audio8.0gives6.351;0.167disagreementremainswithhistoricalseatingunknown.',
        'NativeUSB5.31isgenericenvelope-centerchoice; actualPCB-to-aperturecenter/frontlipdatumunverified.'
    ],
    independent_scene_observations=dict(
        scene='kicad-working/visualization/blender-case-revision-10/x0xb0x-populated-with-case.blend',
        evidence_scope='Measurementscommunicatedbyindependentsceneauditor; exactsolidvolumes/finalchecksbelongtosibling scene-auditreport, notthissourcechecker.',
        audio=dict(references=['HEADPHONE0','MIXIN0','MIXOUT0'],body_shoulder_penetration_past_panel_inner_mm=.508,
                   classification='Actualcurrentmodel/panelintersection; nativebodyregistration/historicaldatumuncertaintypreventscertifyinguniversalphysicalcorrection.',
                   exterior_washer_nut_order='Washer0..1.2andnut1.2..6.2outwardofpanelouterface; exteriorstackalreadycorrectunderchosenillustration.'),
        rectangular_ports=dict(references=['POWER0','USB0'],body_bottom_overlap_below_original_rectangular_edge_mm=.081,
                               classification='Nominalcurrentmodel/cutoutintersection; exacthistoricalpackage/seatnotqualified, especiallygenericUSB. Quantifyindependentmeshintersectionseparatelyfromopenmatingpaths.'),
        MJ_DIN=dict(references=['CV0','GATE0','DIN1','DIN2','DIN3','DIN4'],front_or_shoulder='CanonicalY0mapsnominallytopanelinnerface inexistingdisplay.',
                    classification='Currentnominalposition; nohardware/PCBtranslationrecommendedfromthisalone.'),
        action='DocumentperportconflictswithoutmovingPCB,nativeconnector,case,panel,nutorwashergeometryinBlender11.'),
    rear_legends=dict(original_DXF_control_art_present=False,
                     current_text='Existingeditablepresentationlegends; not originalDXFart/font/layout.',
                     presentation_fix='Placeexistingglyphgeometryatpanelouterfaceplus.01mmalongoutwardnormal; keepx/z,textgeometry,fontandmaterial.',
                     offset_classification='.01mmisasmallrenderingoffset, notamanufacturingdimension.',
                     seating_effect='Nochange tonativeconnector/panel/case/hardwarepositionsorphysicalfit.'),
    source_supported_actions=[
        dict(action='Keeporiginalrearcutoutgeometryand1.5748panelthickness.',basis='OriginalauthorDXF/download+PacTecprintednominal.',ready=True),
        dict(action='PreserveoriginalDINfrontflushPCBedgeandPCB-solderretentiondepiction; do notinventDINscrewpattern.',basis='OriginalIOmanualandoriginalpanelholes.',ready=True),
        dict(action='Keepaudiohardwarecoaxialwithnativeportsandwashers/nutsonchosenexteriorstack.',basis='Existingqualifiedillustration; originalmountingmethodsupportsjackclampbutexactwasherorderisinterpretation.',ready=True),
        dict(action='Reportactualsceneaxialoverlap/gapsandapertureclearancebeforechoosingdisplayplacementcorrection.',basis='Incompletehistoricalsetback/bodyseatdata; requiresindependentcurrentgeometryaudit.',ready=True),
        dict(action='TranslatewholePCB,panelorindividualnativeconnectorstosuppressamismatch.',basis='No exactsource-supportedcorrection recovered; newchosenvisualseatwouldneedexplicitassumptionandendpoint/casechecks.',ready=False)
    ],
    current_PCB_sha256=pcb_hash,current_PCB_unchanged=sha(pcb)==pcb_hash,
    native_model_bytes_unchanged=all(sha(REPO/a['model_path'])==a['model_sha256'] for f in families for a in f['current_native_assignments']),
    geometry_changes_made=False,physical_fit_qualified=False,
    web_primary_sources_refreshed=['https://www.ladyada.net/make/x0xb0x/download.html','https://www.ladyada.net/make/x0xb0x/fab/finish/index.html','https://www.ladyada.net/make/x0xb0x/fab/ioboard/','https://www.mouser.com/catalog/specsheets/KC-301021.pdf'])
(HERE/'seating-source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(passed=result['passed'],checks_count=len(checks),families=len(families),references=sum(len(f['references']) for f in families),geometry_changes_made=False),indent=2))
