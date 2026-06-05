# Milestones

Derived from [`ROADMAP.md`](ROADMAP.md). A milestone
is "done" only when [`../IMPLEMENTATION_STATUS.md`](../IMPLEMENTATION_STATUS.md) carries code
evidence.

| Milestone | Phases | Status |
|---|---|---|
| **M1 — CE spine** (Foundations + Model Registry + Voice/Variant split + Runtime) | 1, 2, 3 (+3.5–3.11) | DONE (architecture-validated) |
| **M2 — First foreign provider validated** (one non-OmniVoice model generates real audio E2E) | provider validation | OPEN — the readiness gate |
| **M3 — Public API frozen** (stable `/v1`, OpenAPI, SDK, deprecation policy) | 9 | PARTIAL (versioned API exists; freeze pending) |
| **M4 — Cloud foundation** (auth + billing live) | 4, 5 | NOT STARTED |
| **M5 — Ecosystem** (creators + marketplace + royalty loop) | 6, 7 | NOT STARTED |
| **M6 — Managed runtime** (Postgres/Alembic, workers, CDN, observability) | 8 | NOT STARTED |
| **M7 — Scale** (autoscaling, replicas, multi-region, SLA) | 10 | NOT STARTED |

**Hard gate:** M4–M7 are blocked until M2 is met. Building the Cloud ecosystem on an unproven
runtime is explicitly disallowed (Phase 1 retrospective recommendation).

---

**Related:** [`ROADMAP.md`](../ARCHIVE/LEGACY/ROADMAP.md) · [`RELEASE_PLAN.md`](RELEASE_PLAN.md) ·
[`../OPEN_DECISIONS.md`](../OPEN_DECISIONS.md)
