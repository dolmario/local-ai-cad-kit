# CAD Next: complete briefs, five harnesses and native editing

This is a local release candidate for the second CAD film. It has not been published to GitHub. The original photo/markerboard workflow remains available through START-HERE.bat and START-CAD.bat.

The new route uses five CAD procedure skills plus a skill-learning guide, pinned FreeCAD-MCP 0.1.31 with Python 3.12, and a complete numerical task. It keeps model services and configuration inside this kit. Outputs go into a fresh `runtime/<date>-<harness>/output` folder. A text model receives the same 17 advertised FreeCAD tool schemas and numerical feedback; captured views are saved separately for inspection. A tool appearing in the catalog does not establish successful execution. The starter now resolves and validates the separate FreeCADCmd executable before configuring its headless tool.

The starter gives its own FreeCAD instance a private temporary directory and checks an actual CAD request before handing over the task. The public Cline Core starter has passed a two-session integration check on our already configured Windows PC, including real FreeCAD/MCP, file tools, skill discovery and image transport. The model provider was synthetic: this checks the working connections, not a model's CAD, vision or learning ability. It is not a fresh-PC installation test.

The starter reads its two core instruction files, `freecad-mcp-rules` and `printability`, from the persistent project skill directory and includes them directly in the task prompt. The catalog supplies paths for the other relevant skills. The supplied `skills/` files remain the baseline; local improvements live in `.cad-learning/skills/` and survive new runtime folders. See [SKILL-LEARNING.md](SKILL-LEARNING.md) for persistence, native loaders and the exact evidence so far.

The CAD skills cover read-only object names, suffixed names after partial failures, explicit angle units, native document closure and binary-file inspection. Each controlled run keeps its own frozen skill hashes: the original clip series used the earlier files, while the newer v4 enclosure uses the corrected API and native-parameter instructions. Later package changes are not retroactive changes to those runs.

Later release guidance also removes a stale `kit-path.txt` assumption, explains PowerShell paths, uses the native `Spreadsheet::Sheet` type and names the mesh `CountPoints` property. These corrections follow observed tool results. The separately frozen five-skill CAD test snapshots were preserved; these release edits were not injected into the running web comparison.

New profiles allow up to 131072 generated tokens in total, including reasoning. They default to ThinkingBudget=-1: there is no separate smaller thinking cap. A separate 8192-token thinking cap was used in the controlled Qwen harness series; Flint's first attempt returned only reasoning at that cap and was classified as inconclusive. Its follow-up and Inkling use the full total budget. You can explicitly set `-ThinkingBudget 8192` when registering a profile, but it changes the tested configuration and may end reasoning before a useful answer.

## Start with an existing model

First install FreeCAD, uv and Node.js, and the FreeCAD-MCP addon using the original START-HERE.bat if needed. On a managed workstation, complete that workstation's service/Wiki/GPU preflight and run GPU work through its required pause wrapper. Only one GPU job at a time.

Install a harness in this kit:

```powershell
powershell -ExecutionPolicy Bypass -File setup-harness.ps1 -Harness opencode
```

Choices: opencode1.19.6, opencode2.3.2 (a separate package), cline-core with CLI3.0.75/Core0.2.1/SDK0.2.1, crush0.102.0. Installation is local and does not update your global assistant. Hermes0.23.3 uses its official PM-managed installation; supply its Python and entry file to the starter. Do not install dependencies into Hermes with pip or uv.

Register the actual GGUF, matching projector and llama-server executable already on your disk:

For the pinned runtime used on our Strix Halo, first run `powershell -ExecutionPolicy Bypass -File download-cpp-next.ps1 -Backend rocm-gfx1151`. It verifies the ZIP hash and prints the executable path. A separate Vulkan package is available with `-Backend vulkan`; the new CAD model tests here use ROCm. No model or GPU job starts during this download. Use the printed executable path as `-Server` below.

```powershell
powershell -ExecutionPolicy Bypass -File register-model-next.ps1 -Name qwen -Model .\models\model.gguf -Projector .\models\mmproj.gguf -Server .\llama\llama-server.exe
START-CAD-NEXT.bat -Harness opencode -ProfileFile models\profile-next-qwen.json -AutoApprove
```

`-AutoApprove` enables the file, shell and CAD operations for the construction. Cline Core's batch route requires it. Without the switch, the other harnesses use their normal permission handling. No additional worker/model agents are enabled in these configurations.

The included Cline Core starter runs one task through its tool turns, then ends that SDK session. It is a batch interface. The enclosure comparison used a separate supervisor adapter for measured follow-up reviews; that review loop is documented in the run sources and is not part of this starter's command-line interface.

The batch starter stops its own model/server processes after the task, including their identified children. An external model server is left to its owner. FreeCAD remains open for inspection: save open documents, then use STOP-CAD-NEXT.bat. It checks the recorded executable and process creation time and asks FreeCAD to close normally. It never kills a process by a name pattern.

`-DryRun` prints the selected profile and commands without starting any model, FreeCAD or harness. To use the larger task, add `-TaskFile tasks\editable-enclosure.txt`. Its five master dimensions must work after reopening the native file; STEP or STL alone cannot demonstrate that.

Web tools are optional and default to `-WebMode off`. Use `-WebMode fetch` for public documentation retrieval without SearXNG, or `-WebMode search -SearxngUrl <url>` for search plus retrieval. These switches configure this kit's adapter; they do not make the harness or its shell offline. See [WEB-CAD-TEST.md](WEB-CAD-TEST.md) for source receipts, capability checks and the separately prepared model comparison.

## Flint and Inkling 2 Mini

Flint is a text model. Register it with `-TextOnly -Sampling flint` and omit `-Projector`. The actual local file used in our tests is documented in the film's method records. The model's current card and its older embedded preview metadata are recorded separately.

Inkling 2 Mini needs the runtime matching its GGUF layout. The downloader defaults to Unsloth llama.cpp b12649-mix-c7059d6. Our updated stack uses the original looped GGUF, F16 projector and DSpark from `unsloth/Inkling-2-Mini-GGUF` at revision `8078d149286eec7193795413b9e0643da6d11fa1`. These are full upstream files verified against their official SHA256 values. Keep the runtime's DLLs together. This is not the metadata-renamed Mainline_Support GGUF. See the [Inkling instructions](https://unsloth.ai/docs/models/inkling-2-mini) and [pinned release](https://github.com/unslothai/llama.cpp/releases/tag/b12649-mix-c7059d6).

Register the compatible files with `-Sampling inkling`; `-Draft <dspark.gguf>` adds the official draft-dspark settings with two draft tokens. Registering files does not prove inference or a speedup. The controlled CAD profiles use262144 context and131072 maximum output. Inkling's advertised native one-million-token context is not a memory test on this64GB PC. Other hardware and layouts need their own checks. Model weights and third-party programs are not included in this source kit.

## Harness details

- OpenCode1 uses the original MCP schema; OpenCode2 uses mcp.servers and direct tools with codemode:false.
- Cline's MCP command belongs inside transport.args. Its tested CLI route requested32000 tokens, so the full-budget route uses the native SDK's maxTokensPerTurn instead. The SDK route is explicitly labelled Cline Core.
- Crush uses a private HTTP server port (default18433), separate from an existing global named-pipe server.
- Hermes eagerly exposes the FreeCAD tools (tool_search off). It may omit max_tokens in requests, so the model server's n-predict limit is also set.
- A configured limit is not an observed request. The film's method records contain actual slot/request checks and preserve setup failures separately from model results.

Hermes startup example, after its official PM installation has composed the runtime environment:

```powershell
START-CAD-NEXT.bat -Harness hermes -HermesPython .\hermes-runtime\python.exe -HermesEntry .\hermes\hermes -AutoApprove
```

FreeCAD instructions are available both as skills and ordinary files. The permitted modelling methods include primitives, sketches, PartDesign and optional helpers. Geometry checks still matter: a tool call or successful export does not prove the requested dimensions, editability, printed fit or material behaviour. The new clip and enclosure are not described as physically printed unless a separate print record says so.


## What the integration checks establish

On 24 November we ran the current Windows starter twice, with both the kit and FreeCAD installed in paths containing spaces. The earlier V5 check had exposed an argument-handling bug in Cline Core 0.2.1 on Windows. Cline split the executable path at the space in `FreeCAD 1.1`, so its tool catalog lacked FreeCAD. The corrected starter passes paths as complete arguments. The V6 check exercised that correction with a synthetic provider and real tools.

| Operation | Observed result |
| --- | --- |
| Get a FreeCAD view | The next provider request received the same 320 × 240 PNG that FreeCAD returned. |
| Run FreeCAD without a GUI | Both the image profile and the text profile measured a translated 2 × 5 × 7 mm solid. Each returned 70 mm³ and the expected coordinates. |
| Retain a project skill | The first session wrote the skill locally. The second session loaded it through Cline’s native skill loader. Both copies had the same hash. |
| Fetch a public reference | The text session retrieved FreeCAD’s spreadsheet-alias documentation and recorded the source. |

Both sessions advertised 17 FreeCAD tools and requested 131,072 output tokens. A deterministic provider chose the calls. Each session closed its own FreeCAD process. The source package manifest identifies the V6 result and the runtime files that were used.

### Earlier image and skill check

The recorded `release-starter-cpu-check-v4` passed two real public-starter sessions with synthetic provider responses. Both exposed 17 native FreeCAD tools, actually requested 131072 output tokens and used a profile with `ThinkingBudget=-1`.

- Session 1 created a synthetic 3×4×5 mm FreeCAD fixture and called the real `get_view`. Its 320×240 PNG reached the immediately following provider request as a typed `image_url`, byte-identical to the native PNG. No image Base64 remained in tool text.
- Session 1 also wrote a skill through the file editor. Session 2 reloaded it through Cline's native skill loader and fetched public FreeCAD documentation through the optional web tool. The skill had the same hash in both sessions.

The tool sequence was prescribed by the synthetic provider. No LLM chose the operations, learned the skill or interpreted the image. The check generated a small fixture, not the comparison's enclosure. No model/GPU inference ran; GPU-free viewport rendering was not established.

Separately, all 15 generated-configuration cases passed: five harnesses × web modes `off`, `fetch` and `search`, with text/vision profiles and two simulated file-persistence sessions per case. These were file/configuration checks without starting harnesses, CAD, MCP, network requests or models. The native Hermes skill-library check is described in [SKILL-LEARNING.md](SKILL-LEARNING.md).

## MCP images: start a fresh session after updating

The included Cline Core adapter uses `harnesses/mcp-image-bridge.mjs` through its `afterTool` hook. It converts new MCP image results to the typed content form expected by the installed provider, normalizing `mimeType` to `mediaType` while preserving the PNG bytes, text, error status and result metadata. It keeps the CAD tools and image feedback available.

Earlier Cline Core MCP image results had been serialized as JSON tool text containing Base64. That path did not establish actual image reception by the model. The byte-preserving typed-image path is now verified through the real starter with a synthetic provider; visual understanding by a real model remains a separate test.

**After updating, start a fresh session. Do not replay old history containing image JSON strings.** The hook handles newly completed tool calls; it does not rewrite saved history. The public batch starter already creates a new session for each invocation.

## Separate model results and current limits

| Recorded case | Result |
| --- | --- |
| Earlier b12631 Inkling clip | Normally completed; independent CAD-file checks passed. |
| Earlier b12631 enclosure | Exported files passed independent geometry and native-parameter checks, then the run failed with a ROCm launch error and Windows graphics timeout events. The file pass remains valid; the autonomous run did not complete normally. |
| Updated b12649 clip | Normally completed in 3346.218 s overall, including setup. Independent STEP, native reopen/equivalence and STL geometry/function checks passed. |
| Updated b12649 enclosure, before the image-bridge correction | Failed before export; zero model exports. Geometry and native editability could not be evaluated. The recorded cause is the MCP-image-text/tokenizer chain described below. |

The failed new enclosure supplied a valid MCP PNG, which Cline Core 0.2.1 converted to JSON tool text. That exact text reproduced the native b12649 tokenizer's `regex_error(error_stack)` in an isolated vocabulary-only CPU check without model-weight loading, inference or a server. The control without image Base64 passed. A system-wide RAM shortage was not required to reproduce this error; this was a different failure from the earlier ROCm timeout. It does not establish a general image-size limit or model ranking.

In the real-model web run, Inkling searched public sources and saved five files for the 120 mm enclosure. On 24 November at , a ROCm error ended the run. The operator had helped recover that run’s FreeCAD window after a command blocked it. The optional headless tool also lacked its FreeCADCmd path. These conditions limit what the comparison can tell us about the effect of web access.

The saved native 120 mm design passed all five parameter changes. Both STEP files matched the expected geometry and both STL meshes matched their STEP counterparts. Later, changing the existing `LengthMM` parameter to 140 mm on the CPU produced a second native assembly and exports. Both sizes passed the full geometry, editability, mesh-distance and saved-visibility checks. The model run ended before it could export that second size or attempt the skill-reuse exercise.

The CPU export helper produced both sizes from the saved native assembly in FreeCAD 1.1.4. The checks also confirmed that it refuses an existing destination and catches a length parameter that leaves the part unchanged. [Export guide](tools/EXPORT-NATIVE-LENGTHS.md) · [Test record](tools/CPU-EXPORT-PRUEFUNG.json)

The local Vulkan services also reported device loss after the ROCm error. After Windows restarted at 04:52 on 24 November, the router, Qwen and BGE were restored and all three answered their health checks.

Old file passes remain valid, while image reception through the older Cline adapter remains unproven. Updated runtime, GGUF/projector/drafter files and corrected instructions are multiple changed factors, so these cases are not an isolated runtime or timing comparison. Printed fit and real-model visual understanding need their own evidence.

To reproduce the earlier runtime pin, use `./download-cpp-next.ps1 -Build b12631-mix-acc0843`; this also requires that run's original model files and configuration. This source kit includes no model weights or runtime binaries. Vulkan remains an available hash-verified upstream download option; the recorded EVO model cases above used ROCm gfx1151.
