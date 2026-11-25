# Local AI CAD Kit – from a photo to a printed part

A local AI model (Qwen3.8 27B) designs 3D-printable parts in **FreeCAD** for you. It can also measure your part from a photo on a printed markerboard.
Everything runs on your own PC. No cloud, no account.

Companion files for the Dolmario Local AI video. German version: `LIESMICH.md`.

## Quick start (5 steps)

1. **Fully unpack** the ZIP (right click > Extract all) to `C:\local-ai-cad-kit`. Do not run it from inside the ZIP, and avoid paths with spaces.
2. Double-click **START-HERE.bat**. Windows may warn ("Windows protected your PC" > *More info* > *Run anyway*), and FreeCAD/Node ask for administrator rights. The install downloads about 23 GB and takes roughly an hour. Keep the window open until it says "Setup finished".
3. Double-click **START-CAD.bat**. Several windows open (model server minimised, FreeCAD, opencode). That is normal. The first start can take several minutes, please wait.
4. In the opencode window type one sentence, e.g. `/beschreibung cable clip for a 6 mm cable, 3 mm wall, screw hole 3.5 mm`. If opencode asks permission for a tool call, confirm (allow). Finished parts are saved as STL and STEP in `output\`.
5. Done? Type `/exit`, then double-click **STOP-CAD.bat**. This frees graphics memory and RAM.

You do not need a 3D printer to try it: `/beschreibung` and `/zeichnung` give files you can look at in FreeCAD on screen. You only need the markerboard for `/kappe` with a photo. Put photos or drawings into the kit folder (e.g. `eingabe\`) to avoid path problems; put paths with spaces in quotes.

## What you get

- **A printable markerboard.** Lay a key or a flat part on it, take a photo, and the tool turns the photo into millimetres.
- **The photo-measure MCP server.** It measures key head diameter, shoulder width and shaft direction.
- **FreeCAD-MCP** ([neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp), MIT). The AI builds real solids in FreeCAD and exports STL/STEP.
- **opencode**, a chat in the terminal. You type, and the AI uses the tools.
- **Skills** the model loads by itself: `key-cap` (parametric cap builder with self-check, reproduced our printed cap to 0.001 mm3), `drawing-to-part`, `printability`, `photo-vs-caliper`, `freecad-mcp-rules`. They are plain text files in `skills/`: read them, change them, add your own (a folder with a `SKILL.md`).
- **The cap from the video** (STEP/STL) and our printing notes for TPU 95A on the Anycubic Kobra X.

## Requirements

- Windows 10 or 11 with winget ("App Installer").
- About 30 GB free disk space.
- A graphics card. The installer detects it and picks the model:
  - **big** (22 GB or more GPU memory, e.g. RTX 3090/4090/5090, AMD Strix Halo with 64 GB or more): Qwen3.8 27B, fully on the GPU. Tested by us on a GMKtec EVO-X2 (Ryzen AI Max+ 395).
  - **medium** (8 to 22 GB GPU memory **plus at least 32 GB RAM**, e.g. RTX 3080 Ti 12 GB): Qwen3.6 35B-A3B. Attention runs on the GPU, the experts sit in system RAM. Slower, but it runs. Tested on an RTX 3080 Ti: see the known issues below.
  - Less than that: the installer stops with a clear message.
  - Force a profile with `START-HERE.bat -ModelProfile medium`.
- NVIDIA gets the CUDA build of llama.cpp (driver for CUDA 12.4 or newer); AMD and Intel get the Vulkan build.
- Internet for the first installation (about 20 GB download).

## Install (one click)

1. Unpack the ZIP to a folder **without** special characters, for example `C:\local-ai-cad-kit`.
2. Double-click **START-HERE.bat**.
   - It installs FreeCAD, uv, Node.js and opencode, then downloads llama.cpp and the model.
   - It installs the FreeCAD-MCP addon and runs a self-test.
   - Everything is logged to `install.log`.
3. Double-click **START-CAD.bat**. It starts the model, FreeCAD and opencode.

If you only want to see the steps without installing anything, run `START-HERE.bat -DryRun`.

## Use it

1. Print `markerboard/` (see `markerboard/DRUCKEN.md`). Lay your key in the middle and photograph it from straight above.
2. In opencode use a ready-made command (prompts in `prompts/PIPELINE-PROMPTS.md`):
   - `/kappe C:\Users\me\Pictures\key.jpg` – key cap from a photo
   - `/zeichnung C:\drawings\bracket.png` – part from a technical drawing
   - `/beschreibung cable clip for a 6 mm cable, 3 mm wall` – part from a description
   - `/pruefen` – check the open part before printing
3. The AI shows the photo values and asks for **caliper values**. Measure them, because photos read widths about 0.2 to 0.3 mm too large.
4. The AI builds the cap in FreeCAD, checks it and writes STL and STEP to `output/`.
5. Check the STL:
   `uv run --project foto-mcp --with trimesh --with networkx python pruefen/stl_pruefen.py output\cap.stl`
6. Slice and print. We used TPU 95A on the Anycubic Kobra X.

## How accurate is my board?

`uv run --project foto-mcp python pruefen/platte_pruefen.py <photo.jpg>` measures the small crosses on the plate (they are not used for the straightening). For us: median about 0.1 to 0.2 mm on the plate plane. Parts that stand higher than the plate look larger from above, so measure the part height with a caliper (a 2 mm height error is about 0.2 mm on a 30 mm feature).

## Honest limits

- The photo measurement is an estimate. It needs a flat board, even light and the whole board in the picture. The caliper always wins.
- The key mode needs a round key head.
- The model can make mistakes. In our tests it sometimes built a part in the wrong place and still said it was fine. That is why the kit asks for checks and why you should look at the part in FreeCAD.
- One cap fitted after one print. That is a working example, not a guarantee for every key and printer.

## Folders

| Folder | Content |
|---|---|
| `markerboard/` | printable plate and three optional walls (3MF/STL, v5 with more clearance in the T-slots), marker reference, generator |
| `skills/` | model skills (cap builder, drawing, printability, photo vs caliper, FreeCAD rules) |
| `prompts/` | pipeline prompts (also built in as opencode slash commands) |
| `foto-mcp/` | photo-measure MCP server (Python, runs with uv) |
| `freecad/` | starter for the FreeCAD MCP bridge |
| `beispiel-kappe/` | cap from the video + printing notes |
| `pruefen/` | STL check before slicing, plus `platte_pruefen.py`: how accurate is your printed board and photo? |
| `tests/` | synthetic self-test of the photo measurement |
| `programs/`, `models/` | created by the installer |

## Licences

- FreeCAD-MCP: MIT.
- FreeCAD: LGPL.
- llama.cpp: MIT.
- opencode: see its project page.
- Qwen3.8 model: see the model card on Hugging Face.
- The kit files: [JÖRG: Lizenz festlegen, z. B. MIT].

## Known issues and tips (from our test runs)
- **RAM:** the medium profile keeps about 23 GB of expert weights in system RAM. 32 GB RAM is the absolute minimum; close other programs (browser, other AI tools) before START-CAD.
- **FreeCAD "Document recovery" window:** if FreeCAD was closed hard, it shows this dialog at the next start. While it is open, the MCP connection times out ("modal dialog is open" / "Request timed out"). Click *Clean up* (Bereinigen) and confirm, then continue.
- **Images outside the kit folder:** `opencode run` refuses files outside the kit folder. In the normal chat window answer *allow* when asked, or copy your photo/drawing into the kit folder first.
- **Drawings are the hard part:** on the RTX 3080 Ti profile the model sometimes misreads drawings (wrong hole position, hollow instead of solid). It asks when a dimension is missing and does not invent numbers, but always check the table "drawing value / model value" yourself. Photo to cap and plain descriptions worked in our runs.
- **Unzip so that `START-HERE.bat` sits directly in the target folder** (for example `C:\local-ai-cad-kit`).
- **The model server stops in the middle of a task** (opencode says "Cannot connect to API"): the logs are in `logs\llama-server.err.log` (last lines show the reason). We saw this once on the EVO-X2 with the 27B model (Windows error 0xc0000409 = the program aborted itself). Try again after closing other programs; if it keeps happening, install a smaller context or a smaller model (see the model table) and send us the two log files.

## Choose or change the model (smaller PCs, your own model)
The installer picks a model from your hardware. You can force one, and you can keep several side by side.

| Profile | Model | Needs | Status |
|---|---|---|---|
| `big` | Qwen3.8 27B | 22 GB GPU memory or more | tested on the EVO-X2 |
| `medium` | Qwen3.6 35B-A3B (experts in RAM) | 8 GB GPU + 32 GB RAM | tested on an RTX 3080 Ti |
| `small` | Qwen3.5 9B | 8 GB GPU + 16 GB RAM | **not tested by us** |
| `mini` | Qwen3-VL 4B | 4 GB GPU + 16 GB RAM | **not tested by us**, photos and simple parts only |
| `custom` | any vision GGUF from Hugging Face | your choice | yours to test |

- Force a profile: `START-HERE.bat -ModelProfile small`
- Your own model: `START-HERE.bat -ModelRepo <user/repo> -ModelFile <name.gguf>` (optional `-Ctx 32768`, and `-CpuMoe 99` for MoE models). The repo needs a `mmproj-F16.gguf` vision file.
- Switch between installed models without downloading again: `START-CAD.bat -Profile medium`
- Smaller models read drawings less reliably. The kit asks when a value is missing, but always check the table "drawing value / model value".
- We plan a part 2 with more models. Tell us in the comments which one you want us to test.

## Already have Ollama or LM Studio? Already have opencode, FreeCAD, uv?
- **Use your own model server instead of ours:** run `START-HERE.bat -ExternalUrl <url> -ExternalModel <model name>`. The kit then downloads no model and starts no llama.cpp; it only sets up FreeCAD, the tools and opencode.
  - **Ollama:** `-ExternalUrl http://127.0.0.1:11434/v1 -ExternalModel <name from "ollama list">`. Ollama's default context is small: set `OLLAMA_CONTEXT_LENGTH=32768` (or more) before you start it.
  - **LM Studio:** start the local server (Developer tab), then `-ExternalUrl http://127.0.0.1:1234/v1 -ExternalModel <model id shown there>`. Load the model with a context length of 32768 or more.
  - The model must support **images (vision)** and **tool calling**. Without vision, `/kappe` and `/zeichnung` cannot read photos and drawings.
  - Switch back to our own server any time: `START-CAD.bat -Profile big` (or the profile you installed before).
- **Already installed programs are detected and kept:** FreeCAD 1.x, uv, Node.js and opencode are only installed when missing, and `winget` is only needed for that. The kit starts opencode with its own config file, so your own opencode settings and models stay untouched. We tested opencode 1.19.0 and FreeCAD 1.1; other versions may behave differently.

## Advertisement
Our printer, the Anycubic Kobra X: https://pboost.me/E6KBb0ba (advertisement / affiliate link: I may earn a commission on qualifying purchases, the price stays the same for you).

## Part 2
Companion files for video part 2 (five models, cable clip, editable enclosure, experimental multi-assistant kit): see [`teil-2/`](teil-2/README.md).
