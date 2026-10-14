# Native control color audit

**Passed:** six corrected STEP families, 34 reusable reference assignments and 12 native KiCad10.0.7 probes. Original projects, delivered scenes and original STEP files were not edited.

| Family | References | Native materials | Probe | Appearance and unchanged geometry |
|---|---:|---:|---|---|
| ESwitch_TL1100F160Q | 23 | 2 | S5 / B.Cu | Pass |
| Panasonic_EVUF2LFL3 | 5 | 1 | VR2 / B.Cu | Pass |
| Alpha_RV112BCF40_25 | 2 | 1 | VR4 / B.Cu | Pass |
| CTS_290VAA5F201B2 | 1 | 2 | S2 / B.Cu | Pass |
| NKK_B12AB | 1 | 3 | S1 / B.Cu | Pass |
| Grayhill_25LB22H | 2 | 1 | S3 / B.Cu | Pass |

All original STEP geometry entities remain verbatim unchanged. Source and corrected files have identical exact reloaded BRep serialization, topology, volume and canonical bounds. All six original/colored native GLB pairs have byte-identical binary geometry, identical accessor/bufferView/primitive geometry metadata and identical node poses.

All corrected native faces carry explicit materials. The corresponding original faces omit material assignments and use glTF default appearance. Every expected material palette and role association passes; maximum linear RGB channel error is 1.05e-08.

Use `control-color-manifest.json` for integration. `control-color-audit-summary.json` is the compact machine record; `native-control-color-audit.json` and `control-color-geometry-audit.json` preserve detailed evidence. All original body-only qualifications and seating limits remain unchanged.
