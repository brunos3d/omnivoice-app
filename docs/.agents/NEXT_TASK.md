# NEXT TASK

> Exactly one highest-priority task — the execution queue head. When this task is done, move
> it to the execution ledger and promote the next item from [`ROADMAP/BACKLOG.md`](ROADMAP/BACKLOG.md).

**As of:** 2026-06-05

## Task: Stabilize and commit the in-flight working tree

- **Priority:** P0 (blocks all other work — the tree is dirty and unverified).
- **Objective:** Bring the uncommitted Fish-adapter / variant-schema / migration changes to a
  verified, committed state on `feat/peakvox-phase-1`, with the backend test suite green.
- **Scope:**
  1. Run the backend test suite (`docker compose run --rm backend bash -c "python -m pytest tests/ -q"`).
  2. Resolve any failures introduced by the in-flight changes.
  3. Confirm the new `schemas/variant.py`, `tests/test_variants_api.py`, and migration are
     consistent and additive (Constitution Art. VI).
  4. Commit with Conventional Commit messages; update
     [`IMPLEMENTATION/EXECUTION_HISTORY/EXECUTION_LEDGER.md`](IMPLEMENTATION/EXECUTION_HISTORY/EXECUTION_LEDGER.md),
     [`PROJECT_STATE.md`](PROJECT_STATE.md), [`CURRENT_CONTEXT.md`](CURRENT_CONTEXT.md), and
     [`HANDOFF.md`](HANDOFF.md).
- **Dependencies:** none (the changes already exist in the tree).
- **Expected output:** clean `git status`; all backend tests passing; updated agent-OS state
  files reflecting the commit.
- **Blocking items:** none for stabilization. Note: this task does **not** require real Fish
  inference (that remains blocked — see [`OPEN_DECISIONS.md`](OPEN_DECISIONS.md), Decision 1).

## After this task

The next priority is the **provider-validation gate**: get one non-OmniVoice provider
generating real audio end-to-end. See [`OPEN_DECISIONS.md`](OPEN_DECISIONS.md) Decision 1 and
[`ROADMAP/BACKLOG.md`](ROADMAP/BACKLOG.md).

---

**Related:** [`ACTIVE_WORK.md`](ACTIVE_WORK.md) · [`ROADMAP/CURRENT_PHASE.md`](ROADMAP/CURRENT_PHASE.md)
