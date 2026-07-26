# Connector Interface

## Protocol

```python
class EvidenceConnector(Protocol):
    connector_id: str
    def health(self) -> HealthStatus: ...
    def lookup(self, ref_id: str) -> EvidenceItem | None: ...
    def read(self, ref_id: str) -> EvidenceItem | None: ...
    def metadata(self, ref_id: str) -> dict | None: ...
    def search(self, query: RetrievalQuery) -> list[EvidenceItem]: ...
```

## Initial connectors

| ID | Status | Notes |
|----|--------|-------|
| `memory` | Implemented | In-process store; request-seeded refs |
| `mock` | Implemented | Deterministic fixtures for tests |
| `evidence_vault` | Stub only | Fail closed — no production integration |

## Future (out of scope for KC-027)

Evidence Vault (live), Google Drive, SharePoint, S3, filesystem, database.

## Registry

`ConnectorRegistry` / `CONNECTOR_REGISTRY` — register, list, health snapshot.
HTTP: `GET /kef/connectors` (authenticated).
