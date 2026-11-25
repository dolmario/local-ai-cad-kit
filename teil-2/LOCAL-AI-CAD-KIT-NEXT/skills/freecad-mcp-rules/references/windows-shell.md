# Windows shell and workspace paths

Use the syntax of the active shell. These examples are for PowerShell:

```powershell
Get-ChildItem -Name
Get-ChildItem -LiteralPath $env:CAD_EVAL_OUTPUT
Get-Content -LiteralPath (Join-Path $env:LOCAL_AI_CAD_KIT 'skills\freecad-mcp-rules\SKILL.md')
Test-Path -LiteralPath (Join-Path $env:LOCAL_AI_CAD_KIT 'skills\drawing-to-part\cad_helpers.py')
```

`dir /b` is CMD syntax; `ls -la` is POSIX syntax. In PowerShell, `dir` and `ls` are aliases for `Get-ChildItem`, whose arguments differ. Use `2>$null` to discard a known optional command's error stream when appropriate. Check whether a file exists before reading it; do not assume `kit-path.txt` exists.

The starter provides `LOCAL_AI_CAD_KIT` and `CAD_EVAL_OUTPUT` to both the harness and its FreeCAD process. In FreeCAD Python read them through `os.environ`. Use the case's supplied output directory for exports. Read FCStd archives with FreeCAD or a ZIP reader and STL with a mesh reader; neither format should be dumped into the conversation as text.

These notes derive from observed PowerShell command errors and successful corrected commands in the 23 November 2026 CAD runs. They change the later release guidance; earlier per-case instruction snapshots remain authoritative for those experiments.
