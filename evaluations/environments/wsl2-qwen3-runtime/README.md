# WSL2 Qwen3-8B runtime environment (Phase 3E)

## Status

**Not created.** Gate 2 blocked: `WSLService` is Disabled (`Wsl/0x80070422`).

See:

* `../wsl2-audit/` — host/WSL audit
* `../cloud-gpu-fallback-spec.md` — cloud fallback (no instance created)
* `../../diagnostics/qwen3-8b-wsl2-runtime-qualification/OUTCOME.json` — Outcome E

When WSL2 becomes available under an authorized elevated session, recreate this tree with pinned Linux dependencies (Python 3.11 preferred), Linux-native repo copy at `~/cobra-core-wsl/` from commit `9ea6874f3edb71fb2734c427079dd454c5d75b59`, and model access without Hugging Face redownload.
