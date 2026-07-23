# Qwen3-8B Python Runtime Compatibility (Phase 3C)

**Primary environment:** `.venv` (unchanged)  
**Interpreter:** Python 3.13.5  
**Host:** Windows 11 / RTX 4070

## Package versions (primary)

| Package | Version | Notes |
| --- | --- | --- |
| Python | 3.13.5 | Material diagnostic variable |
| torch | 2.6.0+cu124 | CUDA 12.4 build |
| transformers | 5.14.1 | Qwen3 chat-template support |
| accelerate | 1.14.0 | device_map helper |
| bitsandbytes | 0.49.2 | 4-bit / 8-bit path |

## Official support posture (local metadata)

Local `importlib.metadata` confirms the packages above are installed and importable under Python 3.13.5 in this environment. This does **not** prove that every native code path used during full Qwen3-8B 4-bit load is validated upstream for 3.13 on Windows.

## Native extensions

| Component | Observation |
| --- | --- |
| PyTorch CUDA | Initializes; `torch.cuda.is_available()` true in prior preflight |
| bitsandbytes | Importable; see `BITSANDBYTES_WINDOWS_DIAGNOSTIC.md` for Linear4bit micro-smoke |
| Wheel type | Environment uses installed wheels from the local venv; no source builds performed in Phase 3C |

## Phase 3C update

Windows Application Error events for the failing loads cite faulting module **`torch_cpu.dll`** (also `c10.dll`) under **Python 3.13.x**. Configuration `B` (explicit GPU, no CPU offload) loaded once, then the same mapping failed repeatedly in QUAL subprocesses. An isolated 3.11/3.12 environment was **not** created during Phase 3C (primary `.venv` immutability; attempt budget consumed; no alternate interpreter provisioned mid-phase). Isolation remains a justified **next** remediation option.

## Is Python 3.11/3.12 isolation justified?

**Yes, as a next authorized experiment — still not proven as sole root cause.** Hard `0xC0000005` crashes during Transformers+bitsandbytes load on Windows with Python 3.13 are a plausible compatibility risk class, especially given:

* crash occurs mid-weight-load, not during pure Python import,
* no catchable Python exception,
* WER faulting module in PyTorch native libs,
* prior Phase 2E / 32B crashes on the same host class.

Creating `.venv-load-diagnostic/` requires separate authorization plus:

* a Python 3.11 or 3.12 interpreter on the host,
* locked package versions with rationale,
* no mutation of `.venv`.

## Primary environment immutability

Phase 3C **must not** uninstall or downgrade packages inside `.venv`.
