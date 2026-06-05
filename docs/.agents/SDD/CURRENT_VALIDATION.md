# Current Validation (SDD working set)

> How the active work is validated before review/merge. Template:
> [`../SPECS/TEMPLATES/VALIDATION.md`](../SPECS/TEMPLATES/VALIDATION.md).

**As of:** 2026-06-05

## Active validation target

Stabilization: the backend test suite must pass green with the in-flight changes committed.

```bash
docker compose run --rm backend bash -c "python -m pytest tests/ -q"
```

## Validation discipline (always)

- Distinguish **architecture-validated** (contract tests pass) from **provider-validated**
  (real model generates audio). State which one a result proves.
- CI has no GPU; real audio generation is validated out-of-band and recorded in
  [`../VALIDATION/PROVIDER_VALIDATIONS/README.md`](../VALIDATION/PROVIDER_VALIDATIONS/README.md).
- Use `superpowers:verification-before-completion` before claiming done.

---

**Related:** [`CURRENT_TASKS.md`](CURRENT_TASKS.md) · [`../VALIDATION/`](../VALIDATION/)
