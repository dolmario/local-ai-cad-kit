---
name: drawing-to-part
description: Build a 3D part from a dimensioned technical drawing image (several views, sections, hole callouts) and prove it against the drawing. Use when the user gives a drawing as an image or PDF page and wants a printable or CAD model.
---

# Drawing to part

## 1. Read before you build (write this down for the user)
- List every view and what it shows (front, side, section A-A). Say which view shows which side.
- List every dimension with its value, the feature it belongs to and its tolerance if given.
- Mark anything you cannot read, or that is only a letter or a star (for example a diameter X marked with a star), as OPEN. **Never invent a number.** Ask the user. A user-supplied value must be marked "from the user" in your report.
- Do not turn a related size into a hole size (a cylinder piston of 10 mm does not mean a 10 mm hole).

## 2. Common callouts
| Callout | Model it as |
|---|---|
| M3 / M4 / M5 / M6 thread | core hole 2.5 / 3.3 / 4.2 / 5.0 mm (say it is a core hole, not a thread) |
| M12x1 thread | core hole 11.0 mm. A clearance hole for a body with M12x1 thread is the number the user gives (we used 12.5) |
| through hole with counterbore | cylinder counterbore with the given depth, same axis as the hole |
| 2x R5 / inner bend radius | fillet on the stated edges. Outer radius = inner + sheet thickness only if the user agrees (say it is derived) |
| chamfer 1 x 45 | chamfer on the stated edges |
| dimensions "from below / left" | measure from the edge of the stated view, check against the section |

Sheet metal bends: build as one solid; state inner radius, thickness and that the outer radius is derived.
**Never build a bend with `makeFillet`.** It fails on cut solids (OCCError). Build the bend as a profile with a real arc: use `l_bracket()` from `cad_helpers.py` (below), then cut the outline and the holes. If any operation fails twice, do NOT try a third variant: leave that feature out, say so, and finish the rest.

## 2b. Reading dimensions without mistakes
- Views are orthogonal projections of ONE body. A square in two views is a solid block unless hidden lines or a section show a cavity. Do not invent a hollow part, wall thickness or depth.
- A dimension belongs to the two features its extension lines touch. Write for each dimension "from <edge/feature> to <feature>" before you use it. A hole needs X and Y from the same edges; both come from different dimension chains.
- Chains: "6" and "18" next to each other usually run edge-hole and hole-hole, so the second hole is at 6 + 18 = 24, not 18.
- Count the holes in the view and check each one has a position. Put your list "hole -> X, Y, diameter" in the answer before you build.
- Symmetric parts: a dimension like "2x 15" from the centre line means the overall width is 30.

## 3. Build
One new FreeCAD document with a unique name. One solid. Use the drawing's units (mm). Build holes as cut cylinders on the exact axes.
Load the helpers once per script:
```python
exec(open(open(__import__("os").path.expanduser("~/.local-ai-cad-kit-path.txt")).read().strip() + "/skills/drawing-to-part/cad_helpers.py", encoding="utf-8").read())
```
They give you `KIT`, `l_bracket(thickness, inner_r, base_len, wall_h, width)` (bent plate, Y = height, Z = width), `profile_solid(points, height)`, `cyl_cut(shape, d, centre, axis)` and `export_part(obj, name)`.
Chamfer on a plain box: `shape.makeChamfer(1.0, shape.Edges)` is fine. Solid cube = solid, do not hollow it.

## 4. Prove it
Run the helper to list what you built:

```python
exec(open("KIT/skills/drawing-to-part/part_report.py", encoding="utf-8").read())
print(part_report(App.getDocument("<doc>").getObject("<obj>").Shape))
```

(`KIT` is the absolute path in `kit-path.txt`, forward slashes.)
Then give the user a table "drawing value / model value / ok" for the overall size and every hole (diameter, centre, axis, depth). Differences above the stated tolerance (default 0.2 mm) are a failure: fix and rebuild in a new document, never relax the tolerance yourself.

## 5. Export
Use `export_part(obj, "<PartName>")` from `cad_helpers.py`. It writes STEP and STL into the kit `output` folder and prints the real sizes. Do not write your own export code and do not use relative paths or /tmp. Tell the user what is OPEN or derived. Every number in your final table must come from code (`part_report`, `BoundBox`, `Volume`), never from text you typed.
