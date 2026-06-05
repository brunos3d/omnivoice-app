# Retrospectives

Honest accounting of what is proven vs aspirational at each phase boundary. These are
**evidence** documents — they feed [`../../IMPLEMENTATION_STATUS.md`](../../IMPLEMENTATION_STATUS.md).

| Retrospective | Canonical | Date |
|---|---|---|
| Phase 1 Retrospective | [`phase-1-retrospective.md`](phase-1-retrospective.md) | 2026-06-04 |

## Phase 1 — key findings

- **The central distinction:** *architecture-validated* (the platform can represent and
  orchestrate a concept — proven by unit/integration tests) vs *provider-validated* (a real
  model installs, loads, builds a variant, resolves, and generates audio).
- **Result:** broad architecture validation, narrow provider validation. ~237 backend tests
  across 55 files at writing prove the contracts; **none load real weights, use a GPU, or
  synthesize audio.**
- **Only OmniVoice** has a real engine. Fish is integrated at the contract level only
  (`NotImplementedError` in `load`/`generate`); Kokoro is research-only.
- **The thesis** (model diversity absorbed by the adapter seam) holds **in architecture** but
  is **unproven empirically** — the real stress test is a non-cloning provider (Kokoro) which
  challenges ADR-0008's build-from-reference-audio assumption.
- **Recommendation / readiness gate:** do **not** begin SaaS/billing/auth/marketplace work
  until one non-OmniVoice provider generates real audio end-to-end.

---

**Related:** [`../PROVIDER_VALIDATIONS/README.md`](../PROVIDER_VALIDATIONS/README.md) ·
[`../../ROADMAP/MILESTONES.md`](../../ROADMAP/MILESTONES.md) · [`../../OPEN_DECISIONS.md`](../../OPEN_DECISIONS.md)
