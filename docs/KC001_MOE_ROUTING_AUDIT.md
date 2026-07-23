# KC-001 — MoE Routing Audit

## Why this matters

GPT-OSS is a Mixture-of-Experts LM. Visual tokens are a **new modality** never seen during text pretraining. Community report (Kaufmann GPT-OSS-20B-Vision):

> Projector-only training completely fails on MoE models — expert routing mis-handles visual tokens; QLoRA on attention (and related projections) is required.

KC-001 measures routing on a **Tiny MoE surrogate** with the same conceptual structure (router → top-k experts). Real GPT-OSS instrumentation is specified but deferred until ≥16GB GPU is available.

---

## Instrumentation

Implemented in `cobra_kc001.moe_probe`:

- per-layer router logits  
- top-k expert indices  
- routing entropy  
- expert load histogram  
- separate histograms for image-token vs text-token positions (prepend layout)

---

## Conditions

| ID | Condition |
|----|-----------|
| 1 | text-only |
| 2 | same prompt + unrelated image |
| 3 | same prompt + relevant image |
| 4 | blank image |
| 5 | noise image |

---

## Surrogate findings (expected pattern to confirm via `image-dependence` / custom probe)

On an **untrained** random Tiny MoE:

- Image vs text tokens show **different** expert histograms (embeddings differ).  
- Entropy is high / diffuse (random router).  
- No claim of “meaningful” vision routing until after overfit / LoRA.

After tiny overfit (projector + attention):

- Expert load may still be uneven.  
- Correct-image vs wrong-image conditions produce different router logits upstream of experts because inputs_embeds differ.  
- This supports the hypothesis that **adaptation inside the LM** (not projector alone) is needed for stable generation — matching the community MoE finding.

---

## Real GPT-OSS measurement plan (KC-002 hardware)

1. Load `openai/gpt-oss-20b` with `output_router_logits=True` if supported, or hooks on `mlp.router`.  
2. Run five conditions with fixed prompt.  
3. Compare:  
   - image-token expert distribution vs text-token  
   - entropy gap  
   - load balance / dropped tokens  
4. Repeat after projector-only vs projector+LoRA checkpoints.  
5. **Do not change router weights** until baseline distributions are logged.

---

## Preliminary conclusions

| Question | Surrogate | Real GPT-OSS |
|----------|-----------|--------------|
| Do image embeds change routing inputs? | **Yes** | Expected yes |
| Projector-only sufficient? | Likely **no** for coherent gen (community + theory) | Measure in KC-002 |
| Router fine-tune required? | Optional config **C**; not selected yet | TBD |
| Collapse onto few experts? | Measure per run | TBD |

**Do not modify MoE routing for production until real-weight baselines exist.**
