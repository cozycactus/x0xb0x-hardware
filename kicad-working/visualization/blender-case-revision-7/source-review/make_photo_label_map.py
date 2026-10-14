"""Own editable text layout from original-photo facts and approximate calibration.

No photograph is traced, embedded or used as a texture. Font and metric label
positions are documented approximations; raw original mechanical paths remain
untouched. The source photograph remains All rights reserved.
"""
from pathlib import Path
import json,math,hashlib,html
import numpy as np

BASE=Path(__file__).resolve().parent
PANELS=json.loads((BASE.parent/'panels/original-panels.json').read_text())['mainpanel']
# Approximate manual readings of the flat sheet corners in the original
#1499x1114-pixel photo. Knobs stand above this plane and are not calibration
#features. Source-DXF outer profile supplies the metric coordinates.
metric=np.array([[0,163.2712],[232.41,163.2712],[232.41,0],[0,0]],float)
pixels=np.array([[299,133],[1315,207],[1280,934],[216,846]],float)
a=[];b=[]
for (x,y),(u,v) in zip(metric,pixels):
    a.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]])
    b.extend([u,v])
H=np.r_[np.linalg.solve(a,b),1].reshape(3,3)
INV=np.linalg.inv(H)
def to_mm(uv):
    q=INV@np.r_[uv,1]
    return [round(float(v),4) for v in q[:2]/q[2]]
def to_px(xy):
    q=H@np.r_[xy,1]
    return [float(v) for v in q[:2]/q[2]]
byref={c['board_reference']:c for c in PANELS['circles']}
rects={c['board_reference']:c for c in PANELS['rectangular_cutouts']}
labels=[]
def add(id,text,xy,ref=None,size=2.2,confidence='photo text clear; position approximate',method='relative to DXF feature',pixel=None):
    row={'id':id,'text':text,'anchor_mm':xy,'anchor_mode':'text center','font_height_mm':size,
         'font_family':'Arial, Helvetica, sans-serif (presentation approximation)',
         'letter_spacing_mm':.25 if size>=2 else .1,'alignment':'center',
         'confidence':confidence,'position_method':method}
    if ref:row['reference']=ref
    if pixel:row['manual_photo_anchor_px']=pixel
    labels.append(row)
def photo_label(id,text,pixel,ref=None,size=2.2):
    add(id,text,to_mm(pixel),ref,size,method='inverse planar homography of manually read photo text centre',pixel=pixel)

for ref,text,pixel in [('S1','SAW',(383,197)),('S1','SQR',(377,246)),
                       ('S2','TEMPO',(355,420)),('VR2','TUNE',(522,276)),
                       ('VR3','CUTOFF',(660,286)),('VR4','RESONANCE',(796,297)),
                       ('VR5','ENV MOD',(937,308)),('VR6','DECAY',(1068,320)),
                       ('VR7','ACCENT',(1203,331)),('VR8','VOLUME',(1213,486))]:
    photo_label(ref+'-'+text.replace(' ','-'),text,pixel,ref)
# Original photo has no BANK or MODE word. The bank selector uses numbers.
# Most of16positions are visible;1and16sit behind the elevated knob. Those
#two labels and their equal angular layout are sequence-based approximations.
s3=byref['S3']['center_mm']
for number in range(1,17):
    ang=math.radians((number-1)*22.5)
    xy=[round(s3[0]+15.3*math.sin(ang),4),round(s3[1]+15.3*math.cos(ang),4)]
    confidence='Visible numeric sequence; regular16-position ring is an approximate layout'
    if number in [1,16]:confidence='Label occluded in source photo; inferred from visible sequence and16-position selector'
    add('S3-position-'+str(number),str(number),xy,'S3',1.65,confidence,
        'regular16-position22.5degree ring around DXF centre;15.3mm radius approximated from visible photo labels')
# These are visible original legends; stacked text centres are hand-read.
modes=[('PATTERN (SYNC OUT)',(796,333)),('PATTERN (DINSYNC)',(913,361)),
       ('PATTERN (MIDISYNC)',(911,378)),('PATTERN EDIT',(900,394)),
       ('TRACK (SYNC OUT)',(908,410)),('TRACK (DINSYNC)',(909,427)),
       ('TRACK (MIDISYNC)',(911,444)),('TRACK EDIT',(890,460)),
       ('COMPUTER CONTROL',(789,471)),('BOOTLOAD',(683,445)),
       ('USER C',(704,429)),('USER B',(704,412)),('USER A',(702,395)),
       ('KEYBOARD',(690,378)),('RANDOM',(693,363)),('MIDI PLAY',(682,346))]
for index,(text,pixel) in enumerate(modes):
    photo_label('S4-mode-'+str(index+1),text,pixel,'S4',1.55)
# Note names are printed adjacent to LEDs; number and function labels lie
# below their switchcaps. Offsets below are informed by planar photo reads,
# then expressed relative to the exact original DXF feature centres.
notes={'LED20':'C#','LED21':'D#','LED22':'F#','LED23':'G#','LED24':'A#',
       'LED30':'C','LED31':'D','LED32':'E','LED33':'F','LED34':'G','LED35':'A','LED36':'B','LED37':"C'"}
for ref,text in notes.items():
    x,y=byref[ref]['center_mm'];add(ref+'-note',text,[x,y+4.5],ref,2.0)
for i in range(1,17):
    ref='LED'+str(i+1);x,y=byref[ref]['center_mm'];add('step-LED-'+str(i),str(i),[x,y-4.5],ref,1.9)
button_labels={'S5':'PREV','S6':'NEXT','S12':'D','S13':'U','S14':'DONE','S15':'R/S','S16':'CHAIN','S25':'R','S26':'A','S27':'S'}
for ref,text in button_labels.items():
    cut=rects[ref];lo,hi=cut['bounds_mm'];x,y=[(a+b)/2 for a,b in zip(lo,hi)]
    add(ref+'-function',text,[x,y-(7.5 if hi[1]-lo[1]<10 else 9.3)],ref,2.0)
for i in range(1,9):
    ref='S'+str(i+16);lo,hi=rects[ref]['bounds_mm'];x,y=[(a+b)/2 for a,b in zip(lo,hi)]
    add(ref+'-step',str(i),[x,y-9.3],ref,2.0)
# Rear-port names were printed along the front panel top edge in the source.
for i,(text,pixel) in enumerate([('DINSYNC',(390,152)),('MIX IN',(485,161)),
                                ('MIDI IN',(581,168)),('MIDI THRU',(682,176)),
                                ('MIDI OUT',(784,182)),('MIX OUT',(876,190)),
                                ('USB',(961,197)),('CV',(1018,202)),
                                ('GATE',(1075,207)),('PHONE',(1165,213)),
                                ('9VAC',(1251,219))]):
    photo_label('top-port-label-'+str(i+1),text,pixel,None,2.0)
# Independent check features are screw centres manually read from the photo,
#excluded from the4-corner homography fit. Chrome highlights limit precision.
check_pixels={'U$23':(326,173),'U$24':(1286,241),'U$2':(252,808),'U$25':(1254,894),'U$27':(750,854)}
checks=[]
for ref,pixel in check_pixels.items():
    predicted=to_px(byref[ref]['center_mm']);observed=to_mm(pixel)
    checks.append({'reference':ref,'photo_anchor_px':pixel,'predicted_photo_px':predicted,
                   'error_pixels':math.dist(pixel,predicted),
                   'metric_error_mm':math.dist(observed,byref[ref]['center_mm'])})
lines=[{'id':'sequence-separator','start_mm':to_mm((309,516)),'end_mm':to_mm((1243,588)),
        'width_mm':.18,'status':'approximate manually read printed line'}]
photo=BASE/'ladyada-panel-original-388576688.jpg'
out={'artifact':'Editable approximate text layout from original Ladyada panel photograph',
     'source_photo_url':'https://www.flickr.com/photos/ladyada/388576688',
     'source_photo_sha256':hashlib.sha256(photo.read_bytes()).hexdigest(),
     'source_photograph_license':'All rights reserved; photograph is reference only and is not embedded or traced as a texture.',
     'vector_derivation':'Original short functional text transcribed; new editable text placements and generic presentation font. No original glyph outlines or silkscreen vector file recovered.',
     'units':'mm','frame':'Original DXF local panelXY: lower-left0,0;Xright;Yup',
     'calibration':{'method':'4-corner planar homography; manually read flat-sheet corners',
                    'source_metric_corners_mm':metric.tolist(),'photo_corners_px':pixels.tolist(),
                    'panel_to_photo_homography':H.tolist(),
                    'independent_screw_checks':checks,
                    'independent_max_error_mm':max(r['metric_error_mm'] for r in checks),
                    'position_uncertainty_mm':1.5,
                    'note':'Approximate photographic registration, not manufacturing artwork; lens distortion and manual corner/text readings are uncorrected.'},
     'omit_presentation_additions':['x0xb0x title','SYNTHESIZER / SEQUENCER subtitle','WAVEFORM generic label','BANK generic label','MODE generic label'],
     'cap_color_map':{'white':[f'S{i}' for i in range(17,25)],'black':[f'S{i}' for i in list(range(5,17))+list(range(25,28))]},
     'labels':labels,'lines':lines,'total_editable_text_objects':len(labels)}
(BASE/'original-photo-label-map.json').write_text(json.dumps(out,indent=2)+'\n')
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="232.41mm" height="163.2712mm" viewBox="0 0 232.41 163.2712">',
     '<title>Own editable approximate original-photo label layout</title>',
     '<desc>Text transcription and approximate planar-photo registration. Generic font; original silkscreen artwork was not recovered. No photo embedded.</desc>',
     '<g id="editable-labels" fill="#111111">']
for label in labels:
    x,y=label['anchor_mm'];svg.append(f'<text id="{label["id"]}" x="{x}" y="{163.2712-y:.4f}" font-family="Arial, Helvetica, sans-serif" font-size="{label["font_height_mm"]}" letter-spacing="{label["letter_spacing_mm"]}" text-anchor="middle" dominant-baseline="central">{html.escape(label["text"])}</text>')
svg.append('</g><g id="approximate-printed-lines" stroke="#111111" fill="none">')
for line in lines:
    x1,y1=line['start_mm'];x2,y2=line['end_mm'];svg.append(f'<line id="{line["id"]}" x1="{x1}" y1="{163.2712-y1}" x2="{x2}" y2="{163.2712-y2}" stroke-width="{line["width_mm"]}"/>')
svg.append('</g></svg>')
(BASE/'original-photo-label-layout.svg').write_text('\n'.join(svg)+'\n')
print(json.dumps({'text_objects':len(labels),'independent_screw_calibration_max_error_mm':out['calibration']['independent_max_error_mm']},indent=2))
out['new_vector_license']='CC0-1.0 for the newly authored approximate text layout and factual mapping; no rights in the source photograph or trademarks are conveyed.'
out['editable_vector_file']='original-photo-label-layout.svg'
out['editable_vector_sha256']=hashlib.sha256((BASE/'original-photo-label-layout.svg').read_bytes()).hexdigest()
out['diagnostic_preview_file']='original-photo-label-diagnostic.png'
(BASE/'original-photo-label-map.json').write_text(json.dumps(out,indent=2)+'\n')
