# ACTIVE WORK

> Only work that is **actively being executed right now**. No roadmap, no future ideas, no
> speculative work — those live in [`ROADMAP/BACKLOG.md`](ROADMAP/BACKLOG.md) and
> [`OPEN_DECISIONS.md`](OPEN_DECISIONS.md). When an item is no longer being worked, move it
> to the execution ledger or remove it.

**As of:** 2026-06-07 · **Branch:** `feat/peakvox-phase-1`

## In flight

1. **Runtime-Service migration — Phase 2 Sub-phase 2B (DockerRuntimeDriver).**
   **Ready to start.** TDD-shaped tasks in
   [`docs/.agents/SPECS/FEATURES/runtime-services-implementation/TASKS.md`](../SPECS/FEATURES/runtime-services-implementation/TASKS.md) §2B.
   The 7 tasks are: `DockerRuntimeDriver` skeleton; `install_runtime`
   implementation; `start_runtime` + readiness probe; lifecycle
   operations (stop / restart / update / remove / status / logs /
   health / metrics); `lint_no_docker_outside_driver.py` AST
   check; wire driver into `RuntimeManager`; status updates.

## Not in flight (recently completed)

- **Runtime-Service architecture (Phase 1, ADR-0016).** ✅ Accepted 2026-06-07.
  See `docs/.agents/SPECS/FEATURES/models-as-runtime-services/`.
- **Runtime-Service Phase 2 implementation architecture (ADR-0017).** ✅
  Accepted 2026-06-07. Architecture review: 0 blocking issues;
  non-blocking suggestions applied (Runtime Persistence →
  `OPEN_DECISIONS.md` Decision 12; ADR_INDEX/IMPLEMENTATION_STATUS
  consistency fixed). `OPEN_DECISIONS.md` Decision 10 is RESOLVED.
  See `docs/.agents/SPECS/FEATURES/runtime-services-implementation/`.
- **Runtime-Service migration — Phase 2 Sub-phase 2A (Foundations).** ✅
  **Complete 2026-06-07.** 9 new modules + 9 test files delivered:
  `RuntimeDescriptor` (12 tests), `RuntimeInstance` (7),
  `HealthReport`/`Metrics` (6), `RuntimeDriverError` (8),
  `RuntimeDriver` Protocol (3), `RuntimeRegistry`/`Loader`
  (10), `RuntimeEventBus` (8), `RuntimeManager` skeleton (11),
  `PeakVoxRuntime` bridge integration (10). 76 new tests, 0
  regressions, 401 pre-existing tests pass. No Docker integration,
  no model framework imports, no HTTP client imports, no runtime
  activation, no Runtime Service communication. The
  `PeakVoxRuntime` bridge is a transitional pass-through; behavior
  is unchanged in 2A.
- **Validation reports and state cleanup.** Kokoro provider validation complete (G5 passed).
- **Kokoro Preset Voice Adapter (Phase 1 + 2).** Complete. 54 presets, catalog-only registry,
  metadata-only build_variant, Preset Voices tab.
- **Fish Audio adapter integration.** Wired at the adapter level; blocked on inference hardware.
- **Voice Library 2.0 frontend.** All components implemented (tabs, source asset, artifacts,
  variant dashboard, preset tab).

## Not in flight (explicitly paused)

- **Sub-phases 2C, 2D** of the Runtime-Service migration — sequenced behind 2B.
- **Phases 3–7 of the Runtime-Service migration** (Kokoro, F5-TTS, Fish, OmniVoice
  migrations, in-process path removal). Sequenced behind Phase 2.
- **Cloud phases** (auth/billing/creators/marketplace) — held behind the provider-validation
  readiness gate. The Runtime-Service target is identical in CE and Cloud, so Phase 2
  unblocks both editions; Cloud planning remains a deliberate decision.
- **Runtime Persistence ADR** (Decision 12) — future ADR, non-blocking.

---

**Related:** [`NEXT_TASK.md`](NEXT_TASK.md) · [`CURRENT_CONTEXT.md`](CURRENT_CONTEXT.md) ·
[`IMPLEMENTATION/EXECUTION_HISTORY/EXECUTION_LEDGER.md`](IMPLEMENTATION/EXECUTION_HISTORY/EXECUTION_LEDGER.md) ·
[`docs/.agents/SPECS/FEATURES/models-as-runtime-services/`](../SPECS/FEATURES/models-as-runtime-services/) ·
[`docs/.agents/SPECS/FEATURES/runtime-services-implementation/`](../SPECS/FEATURES/runtime-services-implementation/)
