"""Validate actual board interface positions against original panel DXFs."""
from pathlib import Path
import hashlib
import json
import math

BASE = Path(__file__).resolve().parent.parent
panels = json.loads((BASE / 'panels/original-panels.json').read_text())
boards = json.loads((BASE / 'panels/board-interface-positions.json').read_text())

def nearest_circle(panel, xy, allowed_radius=None):
    cs = [c for c in panel['circles']
          if allowed_radius is None or c['radius_in'] == allowed_radius]
    c = min(cs, key=lambda c: math.dist(c['center_mm'], xy))
    return c, math.dist(c['center_mm'], xy)

main = panels['mainpanel']
rows = []
controls = {'ALPHADUAL', 'EVU', 'PEC11-S', 'GH3074', 'NKKTOGGLE'}
for f in boards['mainboard']:
    if f['footprint'] not in controls | {'LED5MM', 'B3F-40XX', '1,3'}:
        continue
    xy = [234.95 - f['x'], -f['y'] - 12.7]
    kind = 'control'
    if f['footprint'] == 'LED5MM': kind = 'LED'
    if f['footprint'] == 'B3F-40XX': kind = 'button'
    if f['footprint'] == '1,3': kind = 'mount'
    if kind == 'button':
        r = min(main['rectangular_cutouts'], key=lambda r:
                math.dist([(a + b) / 2 for a, b in zip(*r['bounds_mm'])], xy))
        match = [(a + b) / 2 for a, b in zip(*r['bounds_mm'])]
        handles = r['source_handles']
        r['board_reference'] = f['ref']
        r['function'] = kind
    else:
        radius = .1 if kind == 'LED' else .068 if kind == 'mount' else None
        c, _ = nearest_circle(main, xy, radius)
        match = c['center_mm']
        handles = [c['source_handle']]
        c['board_reference'] = f['ref']
        c['function'] = kind
    rows.append({'ref': f['ref'], 'kind':kind, 'footprint':f['footprint'],
                 'board_pcb_xy_mm':[f['x'],f['y']],
                 'expected_panel_xy_mm':xy, 'dxf_panel_xy_mm':match,
                 'residual_mm':math.dist(xy,match), 'dxf_handles':handles})

rear = panels['iopanel']
io_rows = []
for f in boards['ioboard']:
    if f['footprint'] not in {'CP-2350', 'MJ-3536N', 'REAN_1_4STERO',
                              'PJ-202AH', 'PN61729'}:
        continue
    px = f['x'] + 2.286
    if f['footprint'] in {'PJ-202AH','PN61729'}:
        r = min(rear['rectangular_cutouts'], key=lambda r:
                abs((r['bounds_mm'][0][0]+r['bounds_mm'][1][0])/2-px))
        xy = [(a + b) / 2 for a, b in zip(*r['bounds_mm'])]
        r['board_reference'] = f['ref']
        r['function'] = f['footprint']
    else:
        radius = {'CP-2350':.3375,'MJ-3536N':.125,
                  'REAN_1_4STERO':.2325}[f['footprint']]
        c = min([c for c in rear['circles'] if c['radius_in']==radius],
                key=lambda c:abs(c['center_mm'][0]-px))
        xy = c['center_mm']
        c['board_reference'] = f['ref']
        c['function'] = f['footprint']
    io_rows.append({'ref':f['ref'],'footprint':f['footprint'],
                    'board_pcb_xy_mm':[f['x'],f['y']],
                    'dxf_panel_xz_mm':xy,'predicted_panel_x_mm':px,
                    'horizontal_residual_mm':abs(px-xy[0])})

out = {'native_board_mesh_frame': 'millimetres: (X,Y,Z)=(pcbX,-pcbY,KiCad STEP Z); Blender GLB values are metres',
       'mainboard': {
           'native_board_to_panel_local_2d': {
               'matrix':[[-1,0],[0,1]], 'translation_mm':[234.95,-12.7],
               'equations':['panelX=234.95-pcbX','panelY=-pcbY-12.7'],
               'basis_3d_before_panel_slope':[[-1,0,0],[0,1,0],[0,0,-1]],
               'reason':'180 degrees about native Y places B.Cu controls/LEDs outward and F.Cu components inward.'},
           'controls_and_LEDs_max_residual_mm':max(r['residual_mm'] for r in rows if r['kind'] in ['control','LED']),
           'buttons_max_residual_mm':max(r['residual_mm'] for r in rows if r['kind']=='button'),
           'mounts_max_residual_mm':max(r['residual_mm'] for r in rows if r['kind']=='mount'),
           'mount_note':'Four rear DXF mounts are 0.24548344 mm rearward of PCB centres. Preserve original geometry. Actual placed PCB drills are3.302 mm (radius1.651 mm), despite the stale local1,3 cache drill of2.6 mm. Panel radius1.7272 mm leaves only0.0762 mm radial difference; rear displacement0.24548344 mm exceeds that difference, so the PCB hole is not wholly inside the panel hole. Preserve both geometries. No physical-fit conclusion is made;4-40 fastener and fitted-part clearances require a separate check.',
           'correspondences':rows},
       'ioboard': {
           'horizontal_equation':'rearDrawingX=pcbX+2.286',
           'horizontal_max_residual_mm':max(r['horizontal_residual_mm'] for r in io_rows),
           'case_frame_orientation': {
               'native_to_case_basis':[[-1,0,0],[0,-1,0],[0,0,1]],
               'case_X_translation_mm_if_rear_panel_is_centered':217.932/2-2.286,
               'reason':'Rear drawing viewed from outside has its rightward X opposite top-panel rightward X; rotate board180 degrees about Z so jacks face rearward and components remain upward.'},
           'vertical_datum':{
               'status':'illustration assumption based on current manufacturer dimensions; historical fitted part heights are unmeasured',
               'reference':'Same Sky MJ-3536N manufacturer drawing 2024-09-12, page2 (locally retained validation/reference-pdfs/mj-3536n-page2.png)',
               'CV_GATE_center_height_above_seated_PCB_top_mm':5.5,
               'CV_GATE_panel_center_height_above_panel_bottom_mm':11.684,
               'suggested_PCB_top_height_above_rear_panel_bottom_mm':6.184,
               'alternative_NYS216_current_axis_height_mm':8.0,
               'alternative_NYS216_PCB_top_height_above_rear_panel_bottom_mm':6.351,
               'alternative_note':'Current REAN NYS216 primary drawing specifies an8.0mm front axis height above its housing bottom. DXF audio axis14.351mm implies PCBtop6.351mm,0.167mm higher than the MJ3536N estimate. The historical footprint body is about24mm deep while current NYS216 drawing is33mm; the historical fitted package/seating datum is unconfirmed.',
               'note':'Only horizontal alignment is established by original board/panel centres. The 5.5mm package datum assumes body seated against PCB. Current part drawing has revisions after2005; it does not prove the original assembly height.'},
           'depth_datum':{
               'status':'illustration assumption from original connector footprint front edges',
               'suggested_native_Y0_plane':'rear panel inner face',
               'note':'DIN and CV/GATE original footprint bodies begin at pcbY0. Their mating bushing artwork projects outside. No exact jack CAD is installed and connector shoulder/nut depths are unmeasured.'},
           'correspondences':io_rows},
       'board_source_hashes': {name:hashlib.sha256((BASE.parent.parent / name / (name+'.kicad_pcb')).read_bytes()).hexdigest() for name in ['mainboard','ioboard']}}
(BASE / 'panels/board-panel-alignment.json').write_text(json.dumps(out,indent=2)+'\n')
(BASE / 'panels/original-panels.json').write_text(json.dumps(panels,indent=2)+'\n')
print(json.dumps({name:{k:v for k,v in data.items() if 'residual' in k}
                  for name,data in out.items() if isinstance(data,dict)},indent=2))
