---
name: printability
description: Check a CAD part for FDM 3D printing (orientation, overhangs, wall thickness, hole sizes, TPU hints) before the user prints it. Use after a part was built and before it is exported for printing, or when the user asks if something is printable.
---

# Printability check

These are general rules of thumb for a 0.4 mm nozzle. Only the TPU key cap was proven by us on a printer (Anycubic Kobra X, TPU 95A). Say that.

1. **Orientation.** Put the largest flat face on the bed. Say which face and why. A part that is mirror-symmetric still has one overhang.
2. **Overhangs and bridges.** Anything steeper than 45 degrees from vertical needs support or a chamfer. Bridges over 10 mm sag; say where they are. Prefer chamfers (0.15 to 0.5 mm) on bottom edges.
3. **Walls.** Minimum 1.2 mm (three lines) for stiff PLA/PETG, 1.5 mm or more for TPU. Report the thinnest wall you can find.
4. **Holes.** Printed holes come out about 0.1 to 0.2 mm smaller. For screws use clearance sizes (M3 3.4, M4 4.5, M5 5.5) and tell the user. Core holes for threads are not threads.
5. **Clearances for parts that slide into each other:** 0.3 mm per side as a start for FDM. For a press fit 0.1 mm, but test a small sample first.
6. **TPU 95A (our cap):** direct drive extruder, slow outer walls, little retraction, dry filament, cooling on for overhangs. These are starting points, not tested numbers. Ask the user for the slicer profile instead of inventing values.
7. **Report.** Give a short list: orientation, supports yes/no, thinnest wall, riskiest overhang, hole notes. Do not say a part "will print well" without these numbers.
