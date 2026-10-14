# Independent KK1 seating decision

**Reject the proposed installed offset (0, −8.78, +3.90) mm. Retain the unchanged zero/unity assignment as a qualified visualization datum, with seating unresolved.** No actual project, source/candidate geometry or saved scene was changed by this review.

The corrected pose is consistent with the isolated nominal regulator: the heatsink's rear inner plane atY8.13 maps to IC20's back atY−0.65, and the source11.81mm through-hole centre maps to the regulator's15.71mm hole. The primary14.99mm datum is the upper lance bottom, not the through-hole or a holding catch. Thus the earlier+0.72Z proposal had no valid hole-alignment basis.

Exact BRep intersection with IC20 falls from48.642693mm³ of rigid-return interference at zero to1.729422mm³ entirely inside the reconstructed spring-finger volumes at the corrected pose. Coplanar rear contact area is134.599mm². The checking gap is4.19±0.13mm versus nominal plasticdepth4.455mm, leaving0.265mm nominal excess. This is geometric evidence, not proof of elastic installation: finger dimensions are reconstructed and factory alloy, temper, spring force, deformation, tolerance and actual seating remain unknown.

The full populated-board screen is decisive. Fresh exact STEP comparisons at unchanged native component poses confirm these intersections with **rigid heatsink geometry outside the finger mask**:

| Unchanged I/O reference | Exact intersection, mm³ |
| --- | ---: |
| C3 | 125.417382 |
| C5 | 142.153138 |
| C4 | 1.051888 |

The saved-scene surface screen considered572 assembled mesh instances and refined15 relevant/case meshes. It found no case-shell, top-panel or main-PCB surface crossing at the proposed pose; the three capacitor contacts were then independently confirmed by exact BRep. Scene and frozen heatsink hashes stayed unchanged.

The unchanged zero pose also retains its known48.642693mm³ rigid interference with the nominal regulator and must not be presented as installed-fit evidence. The detailed full-size heatsink remains useful as a standalone/source-qualified assembly illustration. No body should be shrunk, trimmed or moved to conceal these conflicts.

Before any installed-fit claim, verify actual fitted heatsink identity, regulator orientation/body seat, capacitor package sizes and a mounted photograph or physical measurements. Nominal models reject this proposed modeled installation; they do not prove the original hardware cannot be assembled.

Detailed source hashes, both rejected offsets, exact volumes and qualifications are recorded in [independent-seating-decision.json](independent-seating-decision.json).
