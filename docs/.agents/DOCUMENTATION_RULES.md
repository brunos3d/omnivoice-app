# DOCUMENTATION RULES

> How every document type in this knowledge base is created, evolved, and retired. The goal is
> a brain that stays **true** (matches code) and **navigable** (cross-linked) over time.

---

## General principles

- **One source of truth per document.** Every concept exists in exactly **one** file under
  `docs/.agents/`. There are no pointer files, no "canonical + reference" pairs, and no legacy
  documentation trees. Do not duplicate; if two docs overlap, merge or cross-link.
- **All documentation lives under `docs/.agents/`.** Creating docs under `docs/architecture/`,
  `docs/architecture/adrs/`, or `docs/superpowers/` is prohibited (those trees were migrated
  and removed).
- **Every major document cross-links** to related docs, ADRs, code, and validations.
- **No information loss.** Superseded material is moved to [`ARCHIVE/`](ARCHIVE/), not deleted.

## Lifecycle by document type

### Architecture documents (`ARCHITECTURE/<name>.md`, descriptive lowercase names)
- **Create:** when a new structural concern needs an owner.
- **Evolve:** edited in place as the design matures; each owns exactly one concern.
- **Authority:** below the constitution and ADRs; above specs.
- **Retire:** superseded sections are marked and link to the superseding doc/ADR.

### ADRs (`DECISIONS/adr-NNNN-*.md`, indexed in `DECISIONS/ADR_INDEX.md`)
- **Create:** for any expensive-to-reverse decision. Use [`DECISIONS/adr-template.md`](DECISIONS/adr-template.md); name `adr-NNNN-kebab-case.md`.
- **Status flow:** `Proposed → Accepted → (Superseded by NNNN / Deprecated)`.
- **Immutable once accepted.** To change a decision, write a **new** ADR that supersedes the
  old one and link both ways. Never edit accepted history.
- **Truth scope:** an ADR records a *decision*, never proof of *implementation*.

### Specs (`SPECS/FEATURES/<feature>/`, templates in `SPECS/TEMPLATES/`)
- **Create:** from a brainstorm, before code (SDD). One folder per feature with `SPEC.md`,
  `DESIGN.md`, `TASKS.md`, `VALIDATION.md`, `STATUS.md`.
- **Evolve:** through the SDD lifecycle; `STATUS.md` tracks where it is.
- **Retire:** move to `SPECS/ARCHIVE/` when shipped or abandoned; record outcome in the
  execution ledger.

### Validations (`VALIDATION/*`)
- **Create:** a retrospective/audit/provider-validation report when a phase or provider is
  assessed.
- **Authority:** evidence, not decisions. They feed `IMPLEMENTATION_STATUS.md`.
- **Evolve:** append-mostly; supersede with a newer dated report rather than rewriting history.

### Roadmap (`ROADMAP/*`)
- **Evolve:** `CURRENT_PHASE.md` changes per phase; `ROADMAP.md`/`MILESTONES.md` change when
  scope or ordering changes; `BACKLOG.md` is continuously groomed.
- **Authority:** intent/plan, not truth. Status of any roadmap item is confirmed against
  `IMPLEMENTATION_STATUS.md`.

### Implementation status (`IMPLEMENTATION_STATUS.md`)
- **Update cadence:** every time code lands. Must cite file + test evidence.
- **Rule:** downgrade status the moment evidence is missing. Designed to be partially
  regenerable from codebase analysis.

### Project state (`PROJECT_STATE.md`)
- **Update cadence:** whenever phase, priorities, risks, or blockers change. Objective facts
  only; no emojis or subjective language.

### Operational memory (`CURRENT_CONTEXT.md`, `ACTIVE_WORK.md`, `NEXT_TASK.md`, `HANDOFF.md`)
- **Update cadence:** start and end of every session. These change frequently and may be
  overwritten; durable history goes to the execution ledger.

### Execution ledger (`IMPLEMENTATION/EXECUTION_HISTORY/EXECUTION_LEDGER.md`)
- **Append-only.** One dated entry per meaningful unit of work. Never rewrite past entries.

### Constitution (`CONSTITUTION.md`)
- **Amend only via an accepted ADR** that names the article it revises. Highest authority.

## Adding a new document

1. Place it under the correct `docs/.agents/` subtree. All new documentation is created here;
   never under a legacy tree.
2. Add a cross-reference from its parent index and from related documents.
3. If it changes truth, update `IMPLEMENTATION_STATUS.md` and `PROJECT_STATE.md`.

---

**Related:** [`AGENT_WORKFLOW.md`](AGENT_WORKFLOW.md) · [`CONSTITUTION.md`](CONSTITUTION.md) ·
[`ARCHITECTURE/ARCHITECTURE_MAP.md`](ARCHITECTURE/architecture-map.md)
