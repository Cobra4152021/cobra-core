# KC-001 — Dataset Audit

**Policy:** Do not download large datasets during the initial audit.  
KC-001 training uses **synthetic procedural** images only.

---

## Categories & candidates

| Category | Candidate | Size (order) | License notes | Commercial | Status |
|----------|-----------|--------------|---------------|------------|--------|
| Captioning | COCO Captions | 100K+ images | COCO terms; annotations research-oriented | Careful | **B/D** |
| VQA | VQAv2 | 200K+ | Research license common | Often research-only | **C/D** |
| Instruct | LLaVA-Instruct-150K | ~150K | Built on COCO + GPT text | **D** | **D** |
| Mixed MM | BAAI Infinity-MM | Millions | Per-subset varies | **D** | **D** |
| OCR / docs | DocVQA / TextVQA | 10K–50K | Check each | Often research | **C/D** |
| Charts | ChartQA | ~20K+ | Check card | TBD | **D** |
| Diagrams | AI2D | ~5K | Research | **C** | **C** |
| UI / screenshots | RICO / proprietary | varies | Often restricted | **E/D** | **D** |
| Spatial | CLEVR | 100K | BSD-ish / research | Review | **B** |
| Safety | Dedicated red-team sets | small | Internal preferred | Internal | **B** |
| **KC-001 synthetic** | Procedural colors | 16–32 | Generated in-repo | **A** | **A** |

---

## Provenance / risk checklist (for any future download)

For each dataset before use:

- [ ] Source URL + version/commit  
- [ ] Image provenance (web scrape? photographer consent?)  
- [ ] Annotation provenance (crowd / model-generated?)  
- [ ] Known train-test contamination vs eval  
- [ ] Demographic / geographic bias notes  
- [ ] PII / faces / plates  
- [ ] Violent / sexual content policy  
- [ ] Takedown / complaint mechanism  
- [ ] Storage estimate  

---

## Selected reproduction subset (KC-001)

**Synthetic color–answer pairs** in `cobra_kc001.synthetic` (~16 examples).

- No copyrighted photographs committed  
- No PII  
- Sufficient for overfit + image-dependence proofs  

---

## Recommendation for KC-002

1. Legal review of any LLaVA / Infinity-MM subset before commercial training (**D**).  
2. Prefer datasets with explicit commercial terms or fully synthetic/rendered data for Cobra Evidence use cases.  
3. Keep Benchmark Lab vision suite **disjoint** from training subsets.  
