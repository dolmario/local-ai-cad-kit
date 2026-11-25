# Third-party software

## CAD Next additions, 23 November 2026

The following versions are downloaded separately by the new route. They are not included in the source ZIP. Names and licenses below were checked against the installed package metadata and the indicated upstream license. A source kit under MIT does not change the licenses of its dependencies or model weights.

| Component | Tested version | License reference |
|---|---|---|
| OpenCode, `opencode-ai` | 1.19.6 | MIT, installed package metadata; https://github.com/sst/opencode |
| OpenCode 2, `@opencode/cli` | 2.3.2 | MIT, https://github.com/anomalyco/opencode/blob/v2.3.2/LICENSE |
| Cline CLI / native Core and SDK | 3.0.75 / 0.2.1 | Apache-2.0, installed package metadata; https://github.com/cline/cline/blob/main/LICENSE |
| Crush, `@charmland/crush` | 0.102.0 | FSL-1.1-MIT, https://github.com/charmbracelet/crush/blob/v0.102.0/LICENSE.md |
| Hermes, official PM-managed runtime | 0.23.3 | MIT, the downloaded release LICENSE; https://github.com/NousResearch/hermes-agent |
| Unsloth llama.cpp | Updated default b12649-mix-c7059d6 (actual tested binary commit 189f431bf); historical b12631-mix-acc0843 (59f66204f) remains selectable | MIT, https://github.com/unslothai/llama.cpp |
| Flint | existing UD-Q4_K_XL | Current card Apache-2.0, https://huggingface.co/RecursiveSI/flint ; older embedded preview metadata is preserved in the companion provenance |
| Inkling 2 Mini | Unsloth UD-Q4_K_XL plus separate projector and optional DSpark | Apache-2.0, https://huggingface.co/thinkingmachines/Inkling-2-Mini and https://huggingface.co/unsloth/Inkling-2-Mini-GGUF |

Crush's current release uses the Functional Source License with a future MIT grant; it is not described here as an MIT release. Consult its exact versioned terms for redistribution and commercial service use. The kit distributes only configuration and launcher code for it.

## Original route

This repository contains only our own scripts, skills, markerboard files and an example part.
The installer **downloads** the following software from its original sources at install time; none of it is included here.
Licenses were read from the project pages on 18 Nov 2026 - check them again before you redistribute anything.

| Component | Used for | License | Source |
|---|---|---|---|
| llama.cpp (build b11580) | runs the model | MIT | https://github.com/ggml-org/llama.cpp |
| opencode 1.19.0 | terminal chat with tools and skills | MIT | https://github.com/sst/opencode |
| freecad-mcp 0.1.31 (neka-nat) | MCP bridge to FreeCAD | MIT | https://github.com/neka-nat/freecad-mcp |
| Qwen3.8-27B (GGUF by unsloth) | model, profile "big" | Apache-2.0 (as listed on the model page) | https://huggingface.co/unsloth/Qwen3.8-27B-GGUF |
| Qwen3.6-35B-A3B (GGUF by unsloth) | model, profile "medium" | Apache-2.0 (as listed on the model page) | https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF |
| FreeCAD | CAD program (installed with winget) | LGPL-2.1-or-later (see freecad.org) | https://www.freecad.org |
| uv, Node.js | Python / JavaScript tooling (installed with winget) | see their projects | https://github.com/astral-sh/uv , https://nodejs.org |
| Python packages: mcp, opencv-contrib-python, numpy, pillow | photo measurement | see PyPI pages (installed by uv) | https://pypi.org |

The CUDA runtime DLLs (cudart) that llama.cpp ships for NVIDIA cards are downloaded together with the llama.cpp release and stay under their own terms.
The ArUco marker dictionary (DICT_4X4_50) comes from OpenCV.

Our own files are under the MIT license in LICENSE. Printing advice in this repository is based on one printer (Anycubic Kobra X) and one material (TPU 95A) and comes without any guarantee.
