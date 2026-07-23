# Dependency selection rationale (Phase 3D)

## Goal

Isolate **Python interpreter version** as the primary experimental variable while keeping the CUDA/PyTorch/Transformers/bitsandbytes stack as close as practical to the Phase 3C primary environment.

## Python 3.12 first

* Phase 3C implicated native PyTorch load crashes under Python **3.13.5**.
* Python **3.12** is the newest widely supported scientific-wheel baseline before 3.13.
* Python 3.11 is conditional only if 3.12 cannot qualify.

## Exact pins (`.venv-qwen312`)

| Package | Version | Rationale |
| --- | --- | --- |
| Python | 3.12.10 | Side-by-side install via winget; does not replace `C:\Python313` |
| torch | 2.6.0+cu124 | Same CUDA 12.4 build family as primary for comparability |
| transformers | 5.14.1 | Match primary; required for existing Qwen3 chat-template path |
| accelerate | 1.14.0 | Match primary device_map behavior |
| bitsandbytes | 0.49.2 | Match primary; Windows wheel; Linear4bit already validated on primary |
| safetensors / tokenizers / huggingface-hub | match primary | Avoid tokenizer/loader drift |
| numpy / sympy / networkx | match primary where available | Torch dependency alignment |

## Explicitly avoided

* Nightly / preview / source builds
* Compiling torch or bitsandbytes
* Floating ranges (`>=`)
* Starting with `device_map=auto` or CPU offload
* Editable installs that mutate the primary `.venv`

## Torch install channel

`torch==2.6.0+cu124` is installed from `https://download.pytorch.org/whl/cu124` before the remaining requirements file.
