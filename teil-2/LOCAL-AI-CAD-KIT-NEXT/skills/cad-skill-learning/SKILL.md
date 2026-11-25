---
name: cad-skill-learning
description: Use when CAD work reveals a reusable method or correction.
---

# Improve the project's CAD skills

Read relevant existing skills before construction or diagnosing an API error. This kit reloads
its persistent skills across sessions. Use the directory in `learning-instructions.md`
(`.cad-learning/skills` in the kit). `skills/` is the supplied baseline and stays intact.

When real work reveals a reusable API correction, modelling method or verification technique,
improve the narrowest existing skill there. Create a new skill when the topic has a distinct
trigger. Use a lowercase hyphenated folder with `SKILL.md`, matching `name`, and a short
`description` saying when to use it. Keep automatic discovery enabled. Store substantial
examples and evidence under `references/`, and useful tested helpers under `scripts/`.

Distil the useful procedure, not the incident transcript: what to do, when, why it works,
and how to verify it. A successful alternative is more useful than a list of failed calls.
Keep ordinary task completion moving; do not run unrelated experiments just to fill memory.

Before describing a correction as **verified**, reproduce the narrow claim with the available
tools and record the observed result, scope, relevant FreeCAD/MCP/harness versions and primary
source. Preserve limits: file tests do not verify geometry, geometric validity does not prove
parametric editability, and neither proves printed fit. Mark plausible but unexecuted ideas
**unverified**, with the missing check. Never promote them into mandatory API rules.
See [references/evidence.md](references/evidence.md) for the compact evidence format.

With Hermes, use the available `skill_manage` schema (`operations` in the checked 0.23.3
installation); creation is configured to the persistent directory. Existing skills are
updated where found. Read the tool result and respect its actual approval response.
With another harness, use its project file tools to create or edit the same real skill files.
If you edited Cline's `.cline/skills` copy, the kit synchronizes it on exit and recovers it
before the next launch. Conflicting edits are retained under `.cad-learning/conflicts`.

After saving, read the file back and check its applicability, evidence and any helper you
changed. Report the skill path and what was actually learned. A later session must load the
relevant saved skill before relying on it; creating a file alone is not observed model use.
No model weights or global user profiles are changed.

Save portable procedures only. Exclude private CAD designs, customer dimensions, filenames,
photos, conversation transcripts, credentials and absolute personal paths. Use small synthetic
examples. No upload or publication is implied by local learning.
