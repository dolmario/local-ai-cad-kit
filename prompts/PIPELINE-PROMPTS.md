# Pipeline prompts / Pipeline-Prompts

These prompts are wired into opencode as slash commands (see `opencode.json`). They load the kit skills in `skills/` (key-cap, drawing-to-part, printability, photo-vs-caliper, freecad-mcp-rules). You can also paste them into any other MCP client.
They work with both kit models: **Qwen3.8 27B** (profile big) and **Qwen3.6 35B-A3B** (profile medium).

Diese Prompts sind in opencode als Slash-Befehle hinterlegt. Man kann sie auch in jeden anderen MCP-Client kopieren.

| Command | Input / Eingabe | Example |
|---|---|---|
| `/kappe` | photo of a key on the markerboard | `/kappe C:\Fotos\schluessel.jpg` |
| `/zeichnung` | image (PNG/JPG) of a dimensioned drawing | `/zeichnung C:\Zeichnungen\halter.png` |
| `/beschreibung` | one or two sentences | `/beschreibung cable clip for a 6 mm cable, 3 mm wall, screw hole 3.5 mm` |
| `/pruefen` | nothing – checks the open FreeCAD part | `/pruefen` |

---

## /kappe – key cap from a photo

```
Design a TPU key cap for the key in this photo: $ARGUMENTS
First load the skills photo-vs-caliper, key-cap and freecad-mcp-rules and follow them, together with AGENTS.md:
1. Call photo-measure.measure_key with the photo path. Show the values and the path of the control image, and ask me to check it.
2. Ask me for caliper values (head diameter, head thickness, shoulder width right next to the head). Wait for my answer.
3. Write down the design with all numbers before building: groove diameter = head diameter + 0.3 mm (this fitted on our printed cap), groove height = head thickness + 0.3 mm,
   lip opening = head diameter - 2 mm, outer wall 1.5 mm, lip thickness 1.0 mm, shaft passage = shoulder edges + 0.15 mm per side.
4. Build ONE solid in a new FreeCAD document. Lips closed all round, only the passage open.
5. Check with code: isValid, solids == 1, bounding box, isInside probes (lips closed, passage free, groove free). Report the results.
6. Export STL and STEP to output/. Give the paths.
```

## /zeichnung – part from a technical drawing

```
Build the part shown in this technical drawing: $ARGUMENTS
First load the skills drawing-to-part, freecad-mcp-rules and printability and follow them.
1. Look at the image. List every view, every dimension with its value, and which feature it belongs to. Mark dimensions you cannot read
   or that are given as a letter or a star (for example ØX*) as OPEN. Never invent a number.
2. Explain in 3–5 sentences how the views fit together (which view shows which side, where holes go through).
3. Ask me about every OPEN dimension. If I say "leave it", build a plausible placeholder and name it clearly as a placeholder.
4. Threads: build core holes (M3 = 2.5, M4 = 3.3, M5 = 4.2, M6 = 5.0, M12x1 = 11.0) and say that they are core holes.
5. Build ONE solid in a new FreeCAD document, in the drawing's units (mm).
6. Check with code: isValid, solids == 1, bounding box against the overall dimensions, hole positions and diameters
   (cylinder faces: radius and axis). Report a table "drawing value / model value".
7. Export STL and STEP to output/.
```

## /beschreibung – part from a description

```
Build this part: $ARGUMENTS
First load the skills freecad-mcp-rules and printability and follow them.
1. Repeat the request as a short list of requirements with numbers. If something important is missing (size, wall thickness,
   hole size, what it attaches to), ask me – at most three short questions – then wait.
2. Propose a simple design in 3–5 sentences, including printing orientation without supports where possible.
3. Build ONE solid in a new FreeCAD document. Use fillets or chamfers only where they help printing or strength.
4. Check with code: isValid, solids == 1, bounding box, and every functional size from step 1.
5. Export STL and STEP to output/. Add one line of printing advice (orientation, material).
```

## /pruefen – check before printing

```
Load the skill printability. Check the part in the active FreeCAD document before I print it:
isValid, number of solids, bounding box, volume, minimum wall thickness at the thinnest place you can find,
overhangs steeper than 45 degrees in the printing orientation, and whether STL/STEP exist in output/.
Report problems first, then what is fine. Do not change the part unless I ask.
```
