# Cloud qualification execution (after authorization)

1. Confirm `evaluations/cloud/authorization-record.json` authorized fields are complete.
2. Provision **one** Linux GPU host (≥16 GB VRAM; prefer 24 GB).
3. Transfer this directory + model weights via encrypted private channel.
4. Clone bundle → `~/cobra-core-cloud` at `695ea8833229b183e5792c49e3888ec4dde9e5f2`.
5. Verify frozen hashes and protocol `prepared-not-run`.
6. Verify model inventory `8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f`.
7. Create `.venv-qwen-cloud` and install pinned deps.
8. Run native backend validation; stop on failure.
9. Run `scripts/qualify_qwen3_8b_cloud.py` (max 6 full loads).
10. Export artifacts; verify locally; terminate instance; fill cost/cleanup records.

Do **not** execute CobraBench in Phase 3F.
