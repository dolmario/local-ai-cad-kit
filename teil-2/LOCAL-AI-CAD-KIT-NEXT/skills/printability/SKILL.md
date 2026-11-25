---
name: printability
description: Assess FDM orientation, support risks, actual wall thickness and functional openings of a CAD model before printing.
---

# Printability

Treat printability as an assessment until the part has actually been printed. Use the requested material, nozzle and machine when supplied; otherwise state assumptions.

Inspect the actual model. Report the intended bed face, the thinnest relevant wall, long bridges, unsupported overhangs and fit-critical holes or clearances. Explain support risks in the proposed orientation; 45 degrees and generic bridge lengths are guidelines rather than universal pass/fail limits.

Keep specified dimensions. Do not silently enlarge screw holes, shrink channels, add fillets or change clearances to follow a generic printing rule. Suggest such changes separately if useful. Thread core holes are not finished threads. Printer-dependent hole shrinkage and fit allowances require a calibration or a real test.

Check that the exported STL is closed and connected per physical part, and that STEP and FCStd exports exist. Report measured geometry separately from slicer estimates and actual printing experience. For the key-cap example only, preserve the documented tested TPU geometry and identify untested changes.
