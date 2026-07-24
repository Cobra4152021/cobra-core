# KC-002 — Real Image Dependence

## Status

**NOT EXECUTED**

## Protocol

For each eval item in `data/kc002` (split=eval):

| Condition | Description |
|-----------|-------------|
| A | Correct image |
| B | Wrong image (different label) |
| C | Blank |
| D | Noise |
| E | No image |
| F | Shuffled image tokens (optional) |

Pass: correct-image accuracy / logp **materially exceeds** B–E.

## Command

```bash
cd kc002 && make dependence
```
