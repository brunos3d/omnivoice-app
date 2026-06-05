# Specs

Feature specifications, following the Superpowers Spec-Driven Development lifecycle.

```
Brainstorm → Specification → Design → Tasks → Implementation → Validation → Review → Merge
```

## Structure

- [`FEATURES/`](FEATURES/) — one folder per feature: `SPEC.md`, `DESIGN.md`, `TASKS.md`,
  `VALIDATION.md`, `STATUS.md` (mirrors the SDD lifecycle).
- [`TEMPLATES/`](TEMPLATES/) — the blank templates to copy when starting a feature.
- [`ARCHIVE/`](ARCHIVE/) — shipped or abandoned specs.

The **active working set** lives in [`../SDD/`](../SDD/) (`CURRENT_SPEC` / `CURRENT_DESIGN` /
`CURRENT_TASKS` / `CURRENT_VALIDATION`). Promote a spec into `FEATURES/<feature>/` when it
graduates from the working slot.

Historical design specs (pre-this-KB) remain canonical under
[`FEATURES`](FEATURES) and are indexed in
[`FEATURES/README.md`](FEATURES/README.md).

---

**Related:** [`../AGENT_WORKFLOW.md`](../AGENT_WORKFLOW.md) · [`../DOCUMENTATION_RULES.md`](../DOCUMENTATION_RULES.md)
