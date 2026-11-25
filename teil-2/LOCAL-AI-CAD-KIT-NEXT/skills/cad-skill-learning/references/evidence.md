# Evidence for a learned procedure

Keep the active instruction short in `SKILL.md`. Put its supporting evidence in one topic
file under `references/`, extending the existing topic instead of accumulating incident logs.
Write in the language that best serves the skill's users.

For each portable claim, record:

- **Status:** verified or unverified.
- **Trigger and procedure:** the recurring situation and the successful method.
- **Reason:** the API contract or measured effect that makes it useful.
- **Versions:** actual FreeCAD, freecad-mcp and relevant harness versions. Use unknown where
  not inspected; do not copy another session's values as if measured now.
- **Primary source:** official documentation or the locally inspected module and symbol.
  A model's explanation is not a source. Prefer a stable URL or source revision.
- **Executed check:** minimal synthetic code or command, observed result and test date.
  Keep the evidence portable; no private geometry, logs or personal absolute paths.
- **Limits:** what was not tested, including other versions, geometry and print acceptance.

A hypothesis may be saved with its source and missing check, but must remain explicitly
unverified. If new evidence contradicts an existing procedure, narrow or correct the rule
and keep enough evidence to explain the new scope. Do not retain contradictory active rules.

Example structure (replace the example with actual observations before calling it verified):

```markdown
## Reopen documents using the returned document name

Status: unverified in this session.
Procedure: use the document returned by App.openDocument(path), then its Name.
Reason: FreeCAD may sanitize or disambiguate the requested document name.
Versions: FreeCAD unknown; freecad-mcp unknown; harness unknown.
Source: actual FreeCAD API documentation or inspected source symbol goes here.
Check still required: save a synthetic document, close it and reopen it; record returned Name.
Limits: no geometric or printed-fit claim.
```

The persistence test in `tests/skill_learning_test.py` deliberately writes synthetic skills.
It proves that those files survive restarts and conflicts. It is not evidence that a model
invented a useful CAD method, chose to save it, or used it successfully in a later CAD task.
