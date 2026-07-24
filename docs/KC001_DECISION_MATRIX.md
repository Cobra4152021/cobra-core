# KC-001 — Decision Matrix

Scoring: 1 (poor) – 5 (excellent). Subjective engineering judgment for Cobra Core direction.

| Approach | Legal clarity | Eng. difficulty | Train cost | Infer cost | Expected quality | Text regression risk | MoE compat | Maintainability | Commercial suitability | Cobra differentiation | **Total** |
|----------|---------------|-----------------|------------|------------|------------------|----------------------|------------|-----------------|------------------------|----------------------|-----------|
| 1. Reproduce GPT-OSS-Vision (PseudoDeepStack + QLoRA) | 3 | 3 | 3 | 3 | 3 | 3 | 4 | 3 | 3 | 4 | **32** |
| 2. SigLIP + simple projector + GPT-OSS LoRA | 4 | 4 | 4 | 3 | 2 | 3 | 3 | 4 | 3 | 3 | **33** |
| 3. SigLIP + resampler + GPT-OSS | 4 | 3 | 3 | 4 | 3 | 3 | 3 | 3 | 3 | 3 | **32** |
| 4. Cross-attention adapter | 4 | 2 | 2 | 3 | 3 | 2 | 2 | 2 | 3 | 4 | **27** |
| 5. Start from open multimodal base (e.g. InternVL/Qwen-VL) | 2–3 | 4 | 3 | 3 | 4 | 4 | n/a or varies | 4 | 2–3 | 2 | **~30** |
| 6. Continue provider-routed vision temporarily | 5 | 5 | 5 | 2 | 4 | 5 | n/a | 5 | 4 | 1 | **36** |

---

## Interpretation

- **Short-term product (users):** Approach **6** wins on risk — keep provider vision in Cobra Computer until Core is proven.  
- **Strategic Cobra Core:** Approach **1** or **2** on GPT-OSS foundation — highest differentiation; MoE requires LoRA (not projector-only).  
- **Approach 5** may win quality faster but weakens “Cobra-owned foundation” story and may carry license **D**.  
- **Approach 4** is higher engineering risk on MoE (custom layers).

---

## KC-001 recommendation

1. Continue **provider-routed vision** in production (no change).  
2. For Cobra Core R&D, pursue **Approach 1/2 hybrid**: PseudoDeepStack or single-layer SigLIP → MLP projector → GPT-OSS with **QLoRA** (attention; evaluate router).  
3. Block large-scale training until: real-weight overfit + image-dependence on ≥16–24GB GPU, and dataset legal status clears.  
4. Re-evaluate InternVL3.5-GPT-OSS only after LICENSE pin (**D** today).  
