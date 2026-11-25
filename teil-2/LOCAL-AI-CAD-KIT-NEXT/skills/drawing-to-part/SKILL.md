---
name: drawing-to-part
description: Build a CAD part from a dimensioned drawing and verify dimensions, holes, radii and view interpretation against that drawing.
---

# Drawing to part

Read the image and relate its views to one physical part. Before building, record overall dimensions, datum edges and each hole's centre, diameter, axis and depth. Follow dimension extension lines; distinguish edge-to-hole dimensions from hole-to-hole chains. Count features and account for every callout. Ask only about genuinely unreadable or missing values; retain values already supplied by the user.

Do not infer a cavity or wall thickness from rectangular projections alone. A radius is a circular arc, not a chamfer. For a planar plate, round only the corners called out. For a sheet bend, use the specified cross-section and bend radius; the supplied l_bracket() helper is available when it matches the design.

Unless actual threads are requested, represent M3/M4/M5/M6 threads as core holes 2.5/3.3/4.2/5.0 mm and M12x1 as an 11.0 mm core hole. Label them as core holes. A clearance hole is a separate requirement.

Build through FreeCAD using suitable Part or PartDesign operations. Helpers cad_helpers.py and part_report.py are available under the kit's skills/drawing-to-part folder. Resolve the kit through LOCAL_AI_CAD_KIT or the workspace kit-path.txt. Do not use the obsolete home-directory pointer file. The ordinary FreeCAD Python API remains available.

Verify the actual shape against the drawing: validity, one solid per physical part, overall size, hole count/centres/diameters/axes/depths, radii and clear passages. Use the stated tolerance; if absent, report the measured discrepancy rather than inventing a pass tolerance. Correct mismatches before claiming completion. Show a concise drawing-value/model-value table, then export STEP, STL and FCStd into CAD_EVAL_OUTPUT. State unresolved or user-supplied dimensions separately.
