---
name: freecad-mcp-rules
description: Practical rules for working with the FreeCAD MCP tools (documents, execute_code, exports, views). Use at the start of any CAD task in FreeCAD and when a tool call fails.
---

# FreeCAD MCP rules

- FreeCAD must be running with the MCP bridge (port 9875). If a tool cannot connect, tell the user to run START-CAD.bat; do not try to start things yourself.
- **One new document per attempt, unique name** (`Name_` + time). FreeCAD silently renames duplicates (`Cap` becomes `Cap001`). Use the name the tool returns.
- `execute_code` runs Python inside FreeCAD. Print what you need to see; the result is only what you print. Keep scripts short and put reusable code in files (see the other skills).
- Build with `Part` solids (`Part.makeCylinder`, `makeBox`, `cut`, `fuse`) and put the final shape into ONE object. Call `doc.recompute()`.
- Export:

```python
import Part, MeshPart
Part.export([obj], "KIT/output/name.step")
MeshPart.meshFromShape(Shape=obj.Shape, LinearDeflection=0.01, AngularDeflection=0.05).write("KIT/output/name.stl")
```

- `KIT` is the absolute kit path from `kit-path.txt`, with forward slashes.
- Before you say a model is done, run checks in code: `shape.isValid()`, `len(shape.Solids) == 1`, bounding box, and `shape.isInside(point, 1e-6, True)` probes for features that must be open or closed. Show the numbers.
- Look at a real view when a view tool is available. A software-rendered picture can show a gap that does not exist; trust measurements first.
- Never claim a check you did not run. If a check fails, say so and rebuild in a new document.
- Keep answers short; units are mm.
