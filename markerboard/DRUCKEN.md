# Markerboard – printing / Drucken

200 × 200 × 3 mm plate with 12 ArUco markers (DICT_4X4_50, ids 0–11, 20 mm). The black markers are 0.6 mm inlays.
Platte 200 × 200 × 3 mm mit 12 ArUco-Marken (DICT_4X4_50, IDs 0–11, 20 mm). Die schwarzen Marken sind 0,6 mm tiefe Einlagen.

| File | Use |
|---|---|
| `PLATTE.3mf` | two-colour project (base + black) |
| `PLATTE_grund.stl` + `PLATTE_schwarz.stl` | the same as two bodies, if your slicer prefers STL |
| `markerboard.json` | exact marker corners. The measuring tool needs this file, so do not change it |
| `WAND-LINKS/-HINTEN/-RECHTS` (3MF/STL) | optional walls with markers for taller parts. Not needed for keys. Print them lying down, marker side up |
| `generator/markerboard_kit.py` | generator (CadQuery), so you can change the clearances yourself |

**Walls, v5 kit version:**
- More clearance in the T-slots: per side 0.5 mm at the foot head and 0.35 mm at the web and tongue; above and below the head 0.2 mm each.
- Checked in CAD: even shifted ±0.3 mm sideways or 0.15 mm up, the wall does not touch the plate (0.000 mm³ overlap).
- Plate and all markers are identical to v4.
- Slide the walls in from the front.

- **Base colour:** light and matt (white, light grey, beige). Gloss causes reflections.
- **Black part:** a second filament, or a filament change at the layer where the inlays start (z 2.4 mm).
- **Our print:** [JÖRG: Material, Drucker (Kobra X?), Einstellungen eintragen]
- **Check after printing:** the plate must lie flat; a warped plate gives wrong values. The tool rejects photos whose markers deviate more than 0.5 mm.

**Photo tips:**
- Shoot from straight above, all 12 markers in the picture.
- Even light, no hard shadow over the key.
- Key in the middle of the plate, head and the first 3 cm of the shaft fully visible.
