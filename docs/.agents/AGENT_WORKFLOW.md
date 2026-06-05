# AGENT WORKFLOW

> The official workflow every agent follows when working on PeakVox. Read this before opening
> code. It enforces the [`CONSTITUTION.md`](CONSTITUTION.md) and keeps the knowledge base true.

---

## Required reading order

```
1. README.md
2. PROJECT_STATE.md
3. IMPLEMENTATION_STATUS.md
4. CURRENT_CONTEXT.md
5. NEXT_TASK.md
6. Relevant ADRs        (DECISIONS/ADR_INDEX.md → the specific ADR)
7. Relevant Specs       (SPECS/ → the specific feature)
8. Code                 (backend/, frontend/)
```

Also read [`CONSTITUTION.md`](CONSTITUTION.md) (invariants) before designing anything.

## Core rules

1. **Never assume implementation.** A feature is built only if code exists. ADRs and specs are
   not proof.
2. **Always verify code.** Open the files cited in [`IMPLEMENTATION_STATUS.md`](IMPLEMENTATION_STATUS.md);
   confirm before claiming.
3. **Code is proof. Implementation status defines truth.** Architecture defines structure,
   ADRs define decisions, specs define intent — but reality is what the code does.
4. **Distinguish architecture-validated from provider-validated.** Never claim a model "works"
   without real end-to-end inference evidence.
5. **Uphold the constitution.** If a task would violate an article, stop and resolve it (raise
   it in [`OPEN_DECISIONS.md`](OPEN_DECISIONS.md) or write a superseding ADR) before coding.
6. **Always update the knowledge base when you change things.** Documentation is part of
   implementation (Constitution Art. VII). On any meaningful change, update:
   - [`IMPLEMENTATION_STATUS.md`](IMPLEMENTATION_STATUS.md) (status + evidence),
   - [`PROJECT_STATE.md`](PROJECT_STATE.md) (phase/priorities/risks/blockers),
   - [`CURRENT_CONTEXT.md`](CURRENT_CONTEXT.md) (focus/target),
   - [`HANDOFF.md`](HANDOFF.md) (what you did, risks, next),
   - [`IMPLEMENTATION/EXECUTION_HISTORY/EXECUTION_LEDGER.md`](IMPLEMENTATION/EXECUTION_HISTORY/EXECUTION_LEDGER.md)
     (a new dated entry).

## Building a feature (Spec-Driven Development)

PeakVox uses the Superpowers SDD lifecycle. For any non-trivial feature:

```
Brainstorm → Specification → Design → Tasks → Implementation → Validation → Review → Merge
```

1. Use the `superpowers:brainstorming` skill first.
2. Capture working artifacts in [`SDD/`](SDD/) (`CURRENT_SPEC`, `CURRENT_DESIGN`,
   `CURRENT_TASKS`, `CURRENT_VALIDATION`).
3. Promote a feature to its own folder under [`SPECS/FEATURES/`](SPECS/FEATURES/) using the
   [`SPECS/TEMPLATES/`](SPECS/TEMPLATES/) (`SPEC.md`, `DESIGN.md`, `TASKS.md`,
   `VALIDATION.md`, `STATUS.md`).
4. Implement with TDD (`superpowers:test-driven-development`).
5. Validate, request review, then finish the branch.

## Commits

- Atomic commits, **Conventional Commits** (`feat:`, `fix:`, `chore:`, `docs:`, …).
- Migrations must be additive and idempotent (Constitution Art. VI).
- Commit/push only when the user asks; branch off `main` for new work.

## Authority hierarchy (when documents disagree)

```
CONSTITUTION  >  ADRs  >  Architecture docs  >  Specs  >  Plans
        (and over all of them, for "what is true now":  CODE + IMPLEMENTATION_STATUS)
```

User instructions (CLAUDE.md / AGENTS.md / direct requests) always take precedence.

---

**Related:** [`DOCUMENTATION_RULES.md`](DOCUMENTATION_RULES.md) · [`CONSTITUTION.md`](CONSTITUTION.md) ·
[`ARCHITECTURE/ARCHITECTURE_MAP.md`](ARCHITECTURE/architecture-map.md)
