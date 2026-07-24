# User personas — Cobra Core

Personas describe **intended users of the model’s capabilities**. They may use Cobra via CLI, notebooks, Investigator, or other hosts. This repo still does not ship Investigator UI.

---

## Persona 1 — Investigator

**Who:** Case analysts, investigative journalists, corporate investigators, private investigators working from documentary evidence.

### Primary workflows
1. Ingest source packs → extract facts with citations  
2. Build timelines and exhibit registers  
3. Detect contradictions across witnesses/documents  
4. Draft findings with confidence and missing-information sections  
5. Refuse premature attribution when evidence is thin  

### Expected outcomes
- Sourced timelines and exhibit lists ready for human review  
- Explicit contradiction records (hard vs soft)  
- Findings that a supervisor can audit source-by-source  

### Critical capabilities
- Citation consistency; quote fidelity  
- Contradiction detection; overclaim refusal  
- Confidence reporting; evidence organization  

### Unacceptable failure modes
- Invented sources, quotes, or exhibits  
- Naming a culprit without support  
- Silent resolution of conflicting dates/facts  
- High confidence on thin evidence  

---

## Persona 2 — Researcher

**Who:** Academic, policy, or industry researchers synthesizing literature and long documents.

### Primary workflows
1. Long-document Q&A grounded in supplied text  
2. Evidence extraction tables (entities, dates, amounts)  
3. Structured summaries / JSON digests  
4. Citation-consistent literature-style briefs (on provided sources only)  

### Expected outcomes
- Faithful multi-source briefs  
- Schema-valid structured outputs  
- Clear separation of fact vs inference  

### Critical capabilities
- Long-form reasoning; evidence extraction  
- Citation consistency; structured summaries  

### Unacceptable failure modes
- Hallucinated papers, DOIs, or quotes  
- Answers from parametric memory presented as document-grounded  
- Invalid structured output when JSON was required  

---

## Persona 3 — Software Engineer

**Who:** Engineers building evaluation tooling, Workers/APIs, data pipelines, or integrating models into products.

### Primary workflows
1. Generate/debug/refactor Python, TypeScript, SQL, Shell  
2. Cloudflare Workers sketches with correct binding mental model  
3. Author technical docs and architecture risk notes  
4. Operational SOPs (cleanup, verify hashes)  

### Expected outcomes
- Paste-testable code with sane errors  
- Minimal diffs for debugging  
- Docs that match real runbooks (no invented flags/secrets)  

### Critical capabilities
- Code generation + debugging + refactoring  
- Tech documentation; architecture review assist  
- Reliability under malformed inputs  

### Unacceptable failure modes
- Destructive shell defaults; credential hardcoding  
- Fake package/API names  
- “Fixed” bugs via unrelated rewrites  
- Express/Node idioms in Workers as if valid  

---

## Persona 4 — Public Safety / Government Analyst

**Who:** Analysts in public safety, regulatory, or government research units (often high-scrutiny environments).

### Primary workflows
1. Source-bound situational summaries  
2. Timeline and contradiction packs for briefings  
3. Confidence-tagged assessments with explicit unknowns  
4. SOP-style procedures for evidence handling (non-operational legal advice)  

### Expected outcomes
- Briefing-ready structured notes with audit trail of sources  
- Clear “insufficient evidence” outcomes when warranted  
- Conservative language under uncertainty  

### Critical capabilities
- All Investigator-critical capabilities  
- Research grounding + large-context fidelity  
- Reliability / safe refusal  
- SOP clarity without overreach into legal conclusions  

### Unacceptable failure modes
- Overclaim affecting liberty, reputation, or enforcement decisions  
- Fabricated evidence or authorities  
- Mixing policy advocacy with evidence summary without label  
- Ignoring classification/sensitivity cues in prompts (when provided)  

---

## Persona 5 — Business Analyst

**Who:** Product managers, ops analysts, diligence leads needing plans, SOPs, and structured write-ups.

### Primary workflows
1. Delivery / tradeoff planning under constraints  
2. Technical documentation for stakeholders  
3. Architecture review notes for build-vs-buy  
4. SOP generation for recurring ops  

### Expected outcomes
- Actionable phased plans with risks  
- Scannable docs; realistic SOPs with checks  

### Critical capabilities
- Planning; documentation; architecture review; SOPs  
- Enough grounding/reliability to avoid invented metrics  

### Unacceptable failure modes
- Fabricated ROI, vendors, or compliance certifications  
- SOPs that skip verification / safety checks  
- Confident recommendations that ignore stated constraints  

---

## Persona coverage matrix (summary)

| Persona | Primary pillars | Phase 4 domains (primary) |
| --- | --- | --- |
| Investigator | P1–P4, P6 | Investigator, Research, Reliability |
| Researcher | P1, P3, P4, P6 | Research, Reliability |
| Software Engineer | P5–P7 | Code, Business (docs), Reliability |
| Public Safety / Gov Analyst | P1–P4, P6–P7 | Investigator, Research, Reliability, Business (SOP) |
| Business Analyst | P4–P7 | Business, Reliability, light Research |
