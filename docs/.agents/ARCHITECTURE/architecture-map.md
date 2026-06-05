# Architecture Map

> The authority hierarchy and dependency map that ties Vision → Architecture → ADRs → Specs →
> Implementation together. Use this to know which document owns a concern and which outranks
> which.

## Authority hierarchy

```
                       CONSTITUTION            (invariants; amend only via superseding ADR)
                            │
                          VISION               (00-VISION.md — north star)
                            │
                   ARCHITECTURE SUITE          (00–10; one concern per doc)
                            │
                          ADRs                 (expensive-to-reverse decisions; immutable)
                            │
                          SPECS                (implementation intent; SDD)
                            │
                          PLANS                (task-level execution)
                            │
                          CODE                 ◄── defines REALITY
                            │
                  IMPLEMENTATION_STATUS         ◄── defines TRUTH (code-evidenced)
```

Rule: higher layers constrain lower layers. But for the question *"is this actually true /
built right now?"*, **code + `IMPLEMENTATION_STATUS.md` win** over any aspirational doc. User
instructions override everything.

## Flow: from idea to reality

```
Vision ──▶ Architecture doc ──▶ ADR (decision) ──▶ Spec (intent) ──▶ Plan (tasks)
                                                                          │
                                                                          ▼
                                                          Code ──▶ Tests ──▶ Validation
                                                                          │
                                                                          ▼
                                                          IMPLEMENTATION_STATUS (truth)
```

## Dependency / ownership map (core spine)

```
ADR-0002 Model first-class ─────────────┐
ADR-0007 Canonical metadata ────────────┤
ADR-0003 Capability contract ───────────┤
                                         ▼
ADR-0001 Voice/Variant split ──▶ ADR-0004 Voice≠Variant≠Model ──▶ 10-RUNTIME (the Runtime)
                                         │
ADR-0006 Realization types ──▶ ADR-0008 Build lifecycle ──▶ ADR-0009 Artifact versioning
                                         │
ADR-0010 Source assets + provisioning ──▶ ADR-0011 Creation sources (generalizes 0010)
                                         │
ADR-0005 Edition-scoped availability ────┘   (governs which models appear per edition)
```

- **Runtime** (`10`) is cross-cutting, not one phase — see Roadmap mapping.
- Cloud architecture (`05`–`07`, `06`) depends on the CE spine (`01`–`04`, `10`) and is gated
  behind feature flags (ADR-0005, `01-PRODUCT`).

## Where to find each concern

| Question | Go to |
|---|---|
| What are the invariants? | [`../CONSTITUTION.md`](../CONSTITUTION.md) |
| What is the product/vision? | [`../CONTEXT/VISION.md`](../CONTEXT/VISION.md), `00-VISION.md` |
| What decision was made and why? | [`../DECISIONS/ADR_INDEX.md`](../DECISIONS/ADR_INDEX.md) |
| How does the runtime resolve/generate? | [`RUNTIME_ARCHITECTURE.md`](runtime-architecture.md) |
| What entities/tables exist? | [`DATA_ARCHITECTURE.md`](data-architecture.md) |
| What does the public API guarantee? | [`API_ARCHITECTURE.md`](api-architecture.md) |
| What is built right now? | [`../IMPLEMENTATION_STATUS.md`](../IMPLEMENTATION_STATUS.md) |
| What is next / planned? | [`../ROADMAP/`](../ROADMAP/), [`../NEXT_TASK.md`](../NEXT_TASK.md) |

---

**Related:** [`OVERVIEW.md`](overview.md) · [`../DOMAIN_MODEL.md`](../DOMAIN_MODEL.md) ·
[`../AGENT_WORKFLOW.md`](../AGENT_WORKFLOW.md)
