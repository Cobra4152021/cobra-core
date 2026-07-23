# Cobra Core

Proprietary model track for Project **King Cobra**.

## Active work

| Phase | Branch | Status |
|-------|--------|--------|
| KC-001 GPT-OSS Vision Audit | `kc-001-gpt-oss-vision-audit` | Research / validation |

### KC-001

- Docs: `docs/KC001_*.md`
- Code: `kc001/`
- Eval metadata: `eval/kc001/`

```bash
cd kc001
make setup && make test && make overfit && make image-dependence
```

**Do not** deploy unverified models to Cobra Computer users.  
**Do not** modify production chat/vision routing from this repository.
