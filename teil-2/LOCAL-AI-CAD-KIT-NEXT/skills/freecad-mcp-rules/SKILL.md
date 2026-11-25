---
name: freecad-mcp-rules
description: Construct, inspect and export functional parts with FreeCAD MCP. Use for CAD work and when a FreeCAD tool fails.
---

# FreeCAD work

FreeCAD is already launched by the harness. Work through its MCP tools or Python API. Use a unique document name and the document/object names actually returned by the tools. Preserve unrelated documents.

Choose a suitable modelling method. Part primitives, sketches and PartDesign features are available; reusable helpers are optional. Keep editable dimensions when the task calls for later modifications. Use one connected solid per physical part; a multi-part assembly may contain several separately checked parts.

For a native parametric task, use FreeCAD expressions and dimensional properties that recompute after save, close and reopen. Spreadsheet aliases must be valid: use descriptive names such as LengthMM, WidthMM, HeightMM, WallMM and FloorMM, with explicit mm values. Single letters such as W and H can be reserved unit names. Change each requested master parameter in the reopened document and check that the relevant geometry follows without rerunning the construction script. A saved Part::Feature shape alone does not establish parametric editability. Avoid a custom Python Proxy when the file must reopen without your script.

The harness sets LOCAL_AI_CAD_KIT and CAD_EVAL_OUTPUT in FreeCAD's environment. Read those values with os.environ. Helpers are in skills/drawing-to-part/cad_helpers.py. Load them once when needed. Use real variables in paths, not the literal word KIT inside a path string. A pointer file is not required.

Match commands to the actual shell. In PowerShell use Get-ChildItem and Get-Content for text files. See [Windows shell and workspace paths](references/windows-shell.md) for examples.

Keep code blocks short enough to inspect their results. On an error, read the traceback and inspect the current document before correcting the cause. Do not repeatedly submit an unchanged failing operation, silently omit a required feature or report success after an unverified change.

For unattended work, prefer document and object Python APIs. GUI commands can open modal file dialogs and block all later GUI tools; do not probe import or file-opening commands with runCommand(). If the RPC reports a stuck GUI dispatch, preserve saved files and report that state rather than sending repeated GUI calls. A headless tool has a separate document and Python namespace and requires a configured FreeCADCmd executable.

An object's Name is read-only; Label is editable. Keep the object returned by addObject(): an existing requested name produces a suffixed Name. After a partially failed call, inspect the surviving objects before creating replacements or looking them up by a guessed name.

Use the actual FreeCAD API names: a shape has BoundBox; for a document feature use obj.Shape.BoundBox. A dimensional property can be a Quantity, so use its Value for numerical formatting. isInside requires the point, tolerance and boundary flag, for example shape.isInside(App.Vector(x, y, z), 0.001, True). Inspect the method or object with help() or dir() when its interface is unclear. Use doc.Name when reopening a document by name; FreeCAD can sanitize the requested name. Set cylinder directions explicitly or measure their transformed axes; do not assume an Euler-angle convention.

Angular units differ by interface: App.Rotation(axis, angle) takes degrees, while the Python Rotation.Angle getter returns radians. Use an explicit angular unit in an expression, for example "90 deg", and verify the transformed cylinder axis after recompute.

Create a native spreadsheet with sheet = doc.addObject("Spreadsheet::Sheet", "Parameters"). Use the returned sheet, set unit-bearing cell contents, assign valid aliases and bind object dimensions with setExpression(). Recompute and measure before exporting. Read one cell with sheet.getContents(cell_address); that method requires a cell address.

Batch related numerical checks in one execute_code call. Set include_screenshot=False for intermediate construction and numeric diagnostics; request useful views explicitly at meaningful inspection points. Save the intended part and exports once the complete shape passes basic validity checks, and update them after repairs.

Before completion, print isValid(), number of solids, bounding-box dimensions and the functional feature measurements. Probe required passages and closed regions with isInside(). Inspect an actual FreeCAD view when image feedback is available. Numbers in the final report must come from executed checks.

Export STEP and STL into CAD_EVAL_OUTPUT and save the FCStd document. export_part() is a convenience, not the only valid export method. Confirm that the files exist and disclose remaining defects. A geometric pass does not establish printed fit.

Standard exports are Part.export([obj], step_path), Mesh.export([obj], stl_path) and doc.saveAs(fcstd_path), after importing Part and Mesh. Document objects do not provide export() or exportStl(). Pass the intended final objects, then check the exported files.

Save before closing a document with App.closeDocument(doc.Name). A document object has no close() method. Reopen with App.openDocument(fcstd_path) and use the returned document's actual Name.

Keep a saved native checkpoint once the editable part is valid. If inference ends before all exports are written, the existing parameterized file can still be processed without another model call. The optional tools/export-native-lengths.py under LOCAL_AI_CAD_KIT exports length variants with the installed FreeCAD Python; read tools/EXPORT-NATIVE-LENGTHS.md there and use the actual sheet/object names. It checks that both parts' X extents follow the requested length. Report these later files as CPU-derived exports and keep the original model job's actual completion status.

Reopen an STL with Mesh.Mesh(stl_path). A Mesh object's Volume, CountPoints and CountFacets are properties; isSolid() is a method.

STL can be binary or ASCII. Inspect it with a mesh reader; text searches for "facet" or "solid" do not establish whether a binary STL contains triangles. FCStd is a ZIP archive and should not be dumped as plain text into the conversation.
