# KC-007 — Intelligence Studio Architecture (cobra-core)

Pure TypeScript visualization transforms under `cobra/src/investigator/domains/studio/`.

- Consumes Investigator / Government / Labor data shapes — does not reimplement investigation logic.
- Exports `studio` namespace from investigator package index.
- Decision-support visualization only; not legal advice; human review required.

See Worker docs (`KC007_ARCHITECTURE.md`) for API and UI deployment.
