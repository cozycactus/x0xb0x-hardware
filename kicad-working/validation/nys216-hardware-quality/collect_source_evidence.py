"""Freeze retained NYS216 hardware evidence and qualified illustration choices.

SPDX-License-Identifier: CC0-1.0
Reads retained sources only; writes JSON solely beside this script. It neither
builds nor changes geometry. Manufacturer source documents retain their rights.
"""
from pathlib import Path
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
sources = [
    dict(id='official-dxf-2007',
         path='kicad-working/visualization/blender-case-revision-7/quality-model-sources/rear-quality/source/nys-216-manufacturer.dxf',
         url='https://www.rean-connectors.com/media/12224/download/nys-216-1.dxf?v=1',
         drawing='3102 ST 22 01',revision='C,2007-06-14;original2004',
         drawing_to_physical_scale=.5,
         review='Assembled front has six-flat hardware and SW15 label. Thread3/8-32UNEF. Separate nut component dimensions not supplied in this DXF.'),
    dict(id='official-pdf-2015',
         path='kicad-working/visualization/blender-case-revision-7/quality-model-sources/rear-quality/source/nys216.pdf',
         url='https://www.rean-connectors.com/media/9014/download/nys-216.pdf?v=1',
         drawing='3102 ST 22 01',revision='2015-05-27',page=1,
         review='Assembled frontSW15; separate Nut flangeØ17.5/total5/flange1.5; WasherØ11.3ID/Ø15.3OD/t1.2. ThreadM11x1.25. Raster PDF visually reviewed; no extractable text.'),
    dict(id='official-photo-current',
         path='kicad-working/validation/rear-openings-review/source-audit/nys216-official-current.jpg',
         url='https://www.rean-connectors.com/uploads/media/400x/02/15142-NYS216.jpg?v=1-0',
         product_url='https://www.rean-connectors.com/en/product/nys216',
         review='Visible six-flat external nut with rounded front rim. Does not establish exact historical hardware or rounding dimensions.'),
    dict(id='pdf-nut-detail-render',
         path='kicad-working/validation/rear-openings-review/source-audit/nys216-nut-detail.png',
         derived_from='official-pdf-2015',
         review='Enlarged PDF region verifies flange section, nut dimension callouts and nine radial rear-face features.'),
]
for source in sources:
    path=REPO/source['path']
    source.update(sha256=sha(path),bytes=path.stat().st_size)

# Preserve relevant raw manufacturer entities without claiming that every
# unprinted coordinate overrides a printed nominal dimension.
path=REPO/sources[0]['path']
lines=path.read_text(errors='replace').splitlines()
pairs=[(int(lines[i]),lines[i+1].strip()) for i in range(0,len(lines)-1,2)]
chunks=[]
for code,value in pairs:
    if code==0:
        chunks.append([(code,value)])
    elif chunks:
        chunks[-1].append((code,value))
handles={'138F','1397','138E','1BE9','12B7','12BF','12A5','12A7','12A6','114F'}
entities=[]
for chunk in chunks:
    fields=dict(chunk)
    if fields.get(5) in handles:
        entities.append(dict(handle=fields[5],type=fields[0],
                             layer=fields.get(8),raw_groups=chunk))
assert len(entities)==len(handles)
assert any(e['handle']=='1BE9' and dict(e['raw_groups']).get(1)=='SW15'
           for e in entities)

evidence=dict(
    schema_version=1,review_date='2026-10-14',sources=sources,
    visual_findings=[
        'DXF assembled front and official photograph independently confirm six exterior wrench flats; this is a real removable nut, not the20mm-wide connector body.',
        'PDF circular nut view contains nine radial features. Its side section supports interpreting them as rear mounting-face ribs; exact function is not stated.',
        'Rounded/beveled circular front is visible. No printed front fillet radius, chamfer depth, circle diameter, rear-rib size or rib datum was recovered.',
        'Source revisions differ in thread designation: olderDXF3/8-32UNEF versus newerPDFM11x1.25. They do not certify hardware interchangeability.'
    ],raw_DXF_entities=entities,
    raw_DXF_limits='Drawing is2:1, with unsized coordinates that differ from printednominals. SW15 governs wrenchsize; do not promote rawfrontcircle/hex coordinates to toleranced dimensions.',
    geometry_changes_made=False,manufacturer_sources_rights_retained=True)

parameters=dict(
    schema_version=1,scope='Blender10 exterior mounting-nut refinement only; three retained audio nuts, no native connector/washer/PCB changes.',
    references=['HEADPHONE0','MIXIN0','MIXOUT0'],
    object_names=[f'{r} / black PA6 nut proxy' for r in ['HEADPHONE0','MIXIN0','MIXOUT0']],
    source_evidence='source-evidence.json',units='mm',
    local_frame=dict(axis='existing nut localZ',front='+Z',back='-Z',
                     origin='preserve existing objectorigin halfway through5mm nut',
                     profile_center_xy='actual native mating-axis intersection expressed in existing nutobject localXY; same center as retained bore, not assumed local(0,0)',
                     geometry_center_refinement=True,
                     previous_outer_axis_residual_mm_approx=.082,
                     expected_profile_center_local_xy_mm_approx=[0,-.082],
                     center_value_requirement='Compute exact center perreference from nativeaxis; approximation is descriptive, not a placementoverride.',
                     center_refinement_scope='Center only the new nutmesh profile and its plainbore on actual nativeaxis; objectorigin/matrix,parenting,PCBcomponentpose and all nativegeometry remain unchanged.',
                     rear_plane_z_mm=-2.5,front_plane_z_mm=2.5,
                     previous_source_absolute_rear_z_mm=1.2,
                     previous_source_absolute_front_z_mm=6.2,
                     note='Preserve objectmatrix/material/axis; sourcepositions quoted for interpretation only. Use actual native-axis bore from revision9 and center complete new exteriorprofile coaxially on it.'),
    printed_nominal_dimensions=dict(
        wrench_across_flats_mm=dict(value=15.,evidence=['official-dxf-2007','official-pdf-2015'],classification='printed SW15'),
        circular_flange_diameter_mm=dict(value=17.5,evidence=['official-pdf-2015'],classification='printed nut detail'),
        total_axial_depth_mm=dict(value=5.,evidence=['official-pdf-2015'],classification='printed nut detail'),
        rear_flange_depth_mm=dict(value=1.5,evidence=['official-pdf-2015'],classification='printed nut detail')),
    build_profile=dict(
        center_xy='shared actual native-axis center in existing nutobject localXY, derived independently for each reference',
        flange=dict(shape='cylinder',diameter_mm=17.5,z_min_mm=-2.5,z_max_mm=-1.0),
        wrench=dict(shape='regular six-flat prism, phase inherited from previousnut',
                    across_flats_mm=15.,circumscribed_diameter_mm=15/math.cos(math.pi/6),
                    z_min_mm=-1.,z_max_mm=2.5),
        front_treatment=dict(operation='intersect wrenchprism with sampled quarter-ellipse radial envelope to round corners near front',
                             cap_start_z_mm=1.95,cap_end_z_mm=2.5,
                             back_diameter_mm=15/math.cos(math.pi/6),
                             front_diameter_mm=15.,axial_depth_mm=.55,
                             curve_profile='quarter-ellipse',
                             parameter_theta_range_rad=[0,math.pi/2],
                             parameter_z_formula='z(theta)=1.95+0.55*sin(theta)',
                             parameter_radius_formula='r(theta)=7.5+(8.660254037844386-7.5)*cos(theta)',
                             quarter_arc_segments=64,
                             classification='explicit visual approximation',
                             evidence=['official-dxf-2007','official-photo-current'],
                             limitation='Circular front face and rounding visible;15mm frontcircle,0.55mm depth and quarter-ellipse curve are modeling choices, not printeddimensions.64segmentsisrenderingresolutiononly. No physical thread/contact assertion.'),
        bore=dict(diameter_mm=9.6,through=True,classification='retained revision9 nominal visual clearance',
                  installed_native_nose_major_diameter_mm=9.525,
                  nominal_radial_clearance_mm=(9.6-9.525)/2,
                  thread_geometry='omitted; plain cylindrical bore',
                  limitation='Older3/8-32source cannot be qualified by newerM11nut drawing; historicalsuppliednutidentity/fitunverified.'),
        rear_features=dict(include=False,observed_count=9,observed_angular_pitch_deg=40,
                           classification='inferred rear mounting-face details; deliberately omitted',
                           reason='Rib width/height/radii/angular datum are unprinted; adding them could alter seat or total axial depth. No new seating claim.')),
    retained_washer=dict(inner_diameter_mm=11.3,outer_diameter_mm=15.3,thickness_mm=1.2,
                         source='official-pdf-2015',change=False,
                         note='NewerPDFwasherdimensionsalreadyretained; do notchange to9.6 orconflate with6.35plugaperture.'),
    preservation=dict(retain_object_pose=True,retain_parenting=True,retain_material=True,
                      retain_native_model_bytes=True,retain_washer_mesh_bytes=True,
                      retain_plain_bore_axis=True,
                      refine_mesh_profile_center_to_native_axis=True,
                      note='Flange converts prior fullhex silhouette into circularrearflange. AxisalignedXYboundsmayexpand toward17.5 whilecircumscribedmaximumdiameterstays17.5.'),
    physical_fit_qualified=False,
    limitations=['Printed hardware envelope from2015drawing is combined witholdernativeconnector. Historicalidentity/threadcompatibilityunqualified.',
                 'Frontcapshape/depth and source-rearfeatureinterpretation are illustrative; no moldtol/truefemale thread.',
                 'No solderterminals,PCBplacement,routing,enclosureorconnectorbody changes are authorized by this source note.'])

(HERE/'source-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
(HERE/'hardware-parameters.json').write_text(json.dumps(parameters,indent=2)+'\n')
print(json.dumps(dict(passed=True,sources=len(sources),DXF_entities=len(entities),
                     references=len(parameters['references']),geometry_changes_made=False),indent=2))
