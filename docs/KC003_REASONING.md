# KC-003 — Reasoning

## Pipeline

1. Question  
2. Identify project (explicit or name/slug inference)  
3. Load project memory  
4. Search Evidence Vault citations (attached refs only)  
5. Search graph  
6. Hybrid search (keyword + optional embedding scores)  
7. Merge + dedupe  
8. Rank  
9. Compose grounded answer (structured; LLM hook later)  
10. Store new research memory  

## Guarantees

- Open conflicts are **surfaced**, not silently resolved.  
- Decisions include **why**.  
- Citations are never invented.  

## API

`POST /investigate` and `CkeApi.streamInvestigate` for streaming chunks.
