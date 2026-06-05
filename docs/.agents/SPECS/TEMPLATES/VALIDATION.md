# VALIDATION — <feature name>

> How the work is proven. SDD stage 6.

## Tests
- Architecture-validated (contract/unit/integration):
- Provider-validated (real model E2E), if applicable:

## Commands
```bash
docker compose run --rm backend bash -c "python -m pytest tests/ -q"
```

## Result
State plainly: pass/fail with evidence. Distinguish architecture- vs provider-validation.

---
Related: `TASKS.md` · `../../VALIDATION/`
