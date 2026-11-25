---
name: key-cap
description: Design and check a printable TPU key cap (ring with groove, two closed lips and a shaft passage) for a round-headed key. Use when the user wants a cap, cover or marker ring for a key head, after the key was measured with a caliper.
---

# Key cap

Use the parametric builder instead of free-form modelling: it reproduced our printed cap to 0.001 mm3 and it has a self-check.

## Inputs you need (use already supplied measurements; ask only for missing values)
- head diameter (caliper), head thickness (caliper)
- shoulder edges across the shaft: `shoulder_lo`, `shoulder_hi` in mm. Take them from `photo-measure.measure_key` (`schulter_quer_min_mm`, `schulter_quer_max_mm`), then ask the user to confirm the shoulder width with a caliper. The shoulder can be asymmetric, so the opening is placed by the two edges, not only by the width.
- shaft direction in degrees (`schaft_richtung_grad`), counter-clockwise from +X on the board.
- If the photo widened the shoulder (about 0.2 to 0.3 mm per side), correct the edges with the caliper width and keep the centre of the two edges.

## Steps
1. Read `kit-path.txt` in the kit folder for the absolute kit path (`KIT`). Use forward slashes in FreeCAD code.
2. Write the design down: groove = head + 0.3, groove height = head thickness + 0.3, lip opening = head - 2, wall 1.5, lip 1.0, passage = edges -/+ 0.15.
3. Call the freecad tool `execute_code` with:

```python
import time
exec(open(KIT + "/skills/key-cap/key_cap.py", encoding="utf-8").read())
cap = build_key_cap(doc_name="Cap_" + time.strftime("%H%M%S"), head_d=20.9, head_t=1.8,
                    shoulder_lo=-3.76, shoulder_hi=5.76, shaft_angle_deg=90.28, out_dir=__import__("os").environ.get("CAD_EVAL_OUTPUT", KIT + "/output"))
print(check_key_cap(cap))
```

4. The answer must show `'ok': True`. If not, say which check failed, fix the inputs, build again in a NEW document name. Do not claim success otherwise.
5. Tell the user the exported STEP/STL paths and these limits: one print on one printer decides the fit; TPU stretches about 10 percent on the lip; the upper lip overhangs the groove by about 1.15 mm and bridges the passage, so print slowly with good cooling.

## Do not
- Do not change the clearances without telling the user why.
- Do not make the passage taller than the groove: the two lips must stay closed all round (the checker tests this).
- Do not say "it fits". Only a print and a try on the key can show that.

Use the kit path from LOCAL_AI_CAD_KIT or workspace kit-path.txt. Reuse caliper values and control-image acceptance already supplied in this conversation; do not ask the same question again. Photo estimates and real fit remain distinct.
