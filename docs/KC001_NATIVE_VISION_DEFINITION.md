# KC-001 — Native Vision Definition

**Project:** King Cobra / Cobra Core  
**Phase:** KC-001 (GPT-OSS Vision Audit)  
**Status:** Acceptance criteria locked for this research phase  

---

## Purpose

This document defines what counts as **native vision** for a GPT-OSS–based Cobra Core model.  
It is the acceptance gate for claiming that Cobra Core Vision is multimodal *inside* the language model, not via an external vision service.

---

## Acceptance definition (MUST)

A native GPT-OSS vision implementation **must**:

1. **Accept image input** as pixels (or losslessly decoded pixel tensors), not only as precomputed captions.
2. **Process pixels through an image encoder** (e.g. SigLIP / ViT) producing visual hidden states.
3. **Transform** those hidden states into representations consumable by GPT-OSS (projector / adapter / resampler).
4. **Inject** those representations into the GPT-OSS **token/embedding stream and/or model layers** such that they participate in the same forward pass as text tokens.
5. **Generate text conditioned directly** on those image representations (cross-attention or self-attention over image+text sequence).
6. **Train at least part** of the multimodal bridge and/or language model (projector, LoRA, router, etc.) so the path is learnable end-to-end for the intended trainable set.
7. **Function without calling** an external vision-language API at inference time.

### Tensor-level non-negotiable

Image features MUST appear as tensors that:

- share the GPT-OSS hidden size (or enter via a documented cross-attn interface into GPT-OSS layers), and
- are attended to by GPT-OSS attention (or MoE-routed MLP) during generation.

If image features never enter GPT-OSS hidden states / attention, the system is **not** native vision.

---

## Explicitly NOT native vision

The following do **not** count, even if the final answer mentions the image:

| Pattern | Why it fails |
|--------|----------------|
| OCR → text prompt → GPT-OSS | Image never enters LM; only text does |
| Caption API → GPT-OSS | External VLM; GPT-OSS sees text only |
| External Gemini / OpenAI / Claude vision call | Provider-routed vision; not Cobra-owned LM path |
| Detector / tagger output as plain text only | Same as OCR/caption pipeline |
| Retrieval of existing image descriptions | No live pixel→encoder→LM path |
| Separate vision model whose outputs never integrate into GPT-OSS hidden states | Dual-model glue, not native multimodal GPT-OSS |

---

## Borderline cases (KC-001 policy)

| Pattern | Verdict |
|--------|---------|
| Frozen encoder + trainable projector into GPT-OSS embeds | **Native** (bridge trained; features enter LM) |
| Frozen encoder + frozen projector + LoRA on GPT-OSS | **Native** if image embeds enter LM and LoRA trains |
| Prepended visual tokens via `inputs_embeds` | **Native** if those embeds are GPT-OSS-compatible and attended |
| Cross-attention layers added to GPT-OSS | **Native** if trained/used and image K/V feed GPT-OSS |
| Tool call to a local vision sidecar that returns text | **Not native** |

---

## KC-001 claim discipline

Until the image-dependence tests in KC-001 pass:

- Do **not** market the system as “native multimodal.”
- Prefer: “experimental GPT-OSS vision bridge under validation.”
- Do **not** deploy to Cobra Computer production routing.

---

## Verification checklist (used by KC-001)

- [ ] Encoder produces finite visual features from pixels  
- [ ] Projector maps to GPT-OSS hidden size  
- [ ] Sequence construction places image features into GPT-OSS forward  
- [ ] Gradients reach intended trainable parameters  
- [ ] Overfit on tiny image–answer pairs succeeds  
- [ ] Correct-image vs wrong/blank/noise/no-image outputs differ materially  
- [ ] Text-only regression suite does not collapse  

---

## Related docs

- `KC001_ARCHITECTURE.md` — tensor path  
- `KC001_FINAL_REPORT.md` — measured results against this definition  
