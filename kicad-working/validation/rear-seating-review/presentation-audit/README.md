# Saved Blender10 rear presentation inspection

This is a read-only inspection of frozen scene `9c75786aa2ea7a551ef68ed0715c6ac8ef12455213dd24192e5a07f4d00f1d07`. `rear-presentation-inventory.json` records actual evaluated vertices and instance transforms, with the source hash checked again after inspection.

The remaining rear presentation collection contains **six meshes** (three audio nuts and three washers) and **eleven editable FONT legends**. USB, power, four DIN and two mini-jacks use their native component geometry without separate face meshes. No obsolete closing disk remains.

The highest-confidence visible defect is the rear legends' normal offset. Every legend object datum is 1.25 mm above the panel exterior. Their 0.006 mm two-sided extrusion yields actual glyph rear surfaces **1.243985–1.243998 mm** above that exterior and front surfaces **1.255996–1.256009 mm** above it. They are detached from the surface by over 1.24 mm and cast the ghosted shadows seen below letters in the rear render. Their ink shader is already nonmetallic, opaque and nonemissive, so changing the material is unnecessary.

Each legend has one original FONT object in one source collection, used by one collection instancer. The dependency graph exposes paired FONT and converted MESH records with identical transforms and evaluated geometry. These are two representations of the same original object; this inventory provides no evidence for an extra independent text object to remove.

The panel-normal slab thickness measured from actual mesh vertices is 1.574815 mm (nominal 1.5748 mm). The three washer rear faces sit on the panel exterior within 0.00003 mm, and their fronts meet the three nut rear planes within 0.00003 mm. Thus the exterior hardware stack has no meaningful axial gap. Small floating-point differences are not physical tolerances.

The concrete presentation correction is to translate only the eleven original legends along the panel normal until each actual rear-most glyph surface is 0.01 mm outside the panel. Preserve their content, FONT data, size, extrusion, ink material, in-plane position and all other geometry. Their instancer already follows the original panel in frames 1, 80, 120 and 160; no new ownership or animation is needed. The tiny remaining separation is a display choice to avoid coincident-surface artifacts, not an ink-thickness claim.

The native component seating review is separate. The inferred case/panel datums and historical connector variants do not justify forcing all native connector shoulders onto one plane from this presentation inspection. No scene, PCB, model or hardware change was made by this audit.
