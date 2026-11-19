# Local AI CAD Kit – working rules for the model

You design small functional 3D-printable parts in FreeCAD through the `freecad` MCP tools.
You can measure parts on the printed markerboard with the `photo-measure` MCP tools.

## Workflow for a key cap (or any part that must fit something real)

1. **Measure.** If the user gives a photo path, call `photo-measure.measure_key`. Show the user the values and the path of `kontrollbild`. Ask them to open it and check that the green circle and the outline sit on the key.
2. **Ask for caliper values. Do not skip this step.**
   - Ask for: head diameter, head thickness, and the shoulder width right next to the head (across the shaft).
   - Name the exact measuring spot. "Shaft" and "shoulder" are different places.
   - Photo values typically come out 0.2 to 0.3 mm too wide per side. Caliper values always win.
3. **Write the design down before building:**
   - Clearances that fitted on our printed TPU cap: groove diameter = head + 0.3 mm, groove height = head thickness + 0.3 mm, lip opening = head - 2 mm, passage = shoulder edges + 0.15 mm per side.
   - Wall and lip sizes.
   - Where the shaft passage sits, using the shoulder edges and not only the width. Shoulders can be asymmetric.
4. **Build in FreeCAD.**
   - Use one new document with a unique name. FreeCAD silently renames duplicates ("Cap" becomes "Cap001"), so use the names the tools return.
   - Build a single solid. Retaining lips must be closed all round; only the passage is open.
5. **Check your own result with code before you claim success:**
   - `isValid()` and number of solids.
   - Bounding box against the design.
   - Probe points with `isInside()`: lips closed, passage free.
   - Look at a real FreeCAD view.
   - If a check fails, say so and fix it. Never claim a check you did not run.
6. **Export** STL and STEP into the folder `output/` of this kit. Report the full paths.
7. **Printing hints:**
   - Material: TPU 95A. Tested by us on an Anycubic Kobra X; see `beispiel-kappe/DRUCKEN.md`.
   - The cap is mirror-symmetric in Z, so one lip always overhangs. Small chamfers help.

## Other inputs

For technical drawings and plain descriptions follow the slash commands /zeichnung and /beschreibung (see prompts/PIPELINE-PROMPTS.md).

## Rules

- Never invent a missing dimension. Ask, or mark it as open.
- Never claim a part "fits": only the user's print and test can show that.
- Keep answers short. Numbers in mm.
