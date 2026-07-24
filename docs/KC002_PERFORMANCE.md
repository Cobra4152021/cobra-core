# KC-002 — Performance

## Status

**NOT MEASURED** on real weights (environment blocked).

## Local observations

| Metric | Value |
|--------|--------|
| Host GPU | RTX 4070 12GB (insufficient) |
| PyTorch | 2.13.0+cpu |
| Disk free | ~8.5 GB |
| Unit tests | see CI / local pytest |

## To fill on CUDA host

Record for text-only, 1-image forward, training step, checkpoint save/load:

- load time, peak/reserved VRAM, RAM, TTFT, tok/s, encoder/projector latency, step time, GPU util
