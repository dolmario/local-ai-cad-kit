# Third-party software

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