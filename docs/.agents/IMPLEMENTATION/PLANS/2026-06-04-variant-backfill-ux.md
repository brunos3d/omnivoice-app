# Variant Backfill UX + Manual Variant Provisioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users manually and automatically create missing variants from existing Voice Source Assets, and see compatibility against all installed models.

**Architecture:** Extends the existing Voice Library 2.0 frontend (VoiceDetailsDrawer Overview tab, VariantManager, VariantDashboard) and backend (variants API, runtime). Adds a Model Compatibility section to the Overview tab, fixes the variant summary endpoint to enumerate all models, improves query cache invalidation, and creates a bulk backfill script.

**Tech Stack:** FastAPI, Next.js 15, React Query, SQLAlchemy, PeakVoxRuntime

---

### Task 1: Fix Variant Summary endpoint to include all models

**Files:**
- Modify: `backend/app/api/variants_summary.py`

The current `GET /variants/summary` only returns models that have VoiceVariant rows. For the dashboard and compatibility matrix to show all installed models (Part 4 requirement), the endpoint must also include models without variants — marked with status `"missing"`.

- [ ] **Step 1: Read the current implementation**

Read `backend/app/api/variants_summary.py` to understand the existing logic.

- [ ] **Step 2: Modify the endpoint to include all models**

```python
@router.get("/variants/summary")
async def get_variant_summary(db: AsyncSession = Depends(get_db)):
    """Return variant status across all voices for the Variant Dashboard.

    Enumerates ALL models available in the current edition (not just those with
    variants), so the matrix shows every voice × model combination. Models without
    a variant appear with status "missing".
    """
    voices = (await db.execute(select(Voice))).scalars().all()
    models = (await db.execute(select(Model))).scalars().all()
    model_map = {m.id: m.name for m in models}
    model_ids = {m.id for m in models}

    variants = (
        await db.execute(select(VoiceVariant))
    ).scalars().all()

    voice_map: dict[str, list[dict]] = {}
    for v in variants:
        voice_map.setdefault(v.voice_id, []).append({
            "model_id": v.model_id,
            "model_name": model_map.get(v.model_id, v.model_id),
            "status": v.status,
            "active_artifact_id": v.active_artifact_id,
            "error_message": v.error_message,
        })

    result = []
    for voice in voices:
        existing = voice_map.get(voice.id, [])
        existing_ids = {m["model_id"] for m in existing}
        # Include all models — fill in "missing" for those without a variant
        all_models = list(existing)
        for mid in sorted(model_ids - existing_ids):
            all_models.append({
                "model_id": mid,
                "model_name": model_map.get(mid, mid),
                "status": "missing",
                "active_artifact_id": None,
                "error_message": None,
            })
        result.append({
            "voice_id": voice.id,
            "voice_name": voice.name,
            "models": all_models,
        })

    return result
```

- [ ] **Step 3: Run backend syntax check**

```bash
cd backend && .venv/bin/python -m py_compile app/api/variants_summary.py && echo "OK"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/variants_summary.py
git commit -m "fix: enumerate all models in variant summary endpoint"
```

---

### Task 2: Update VariantDashboard and VariantManager for "missing" status

**Files:**
- Modify: `frontend/src/components/voice/VariantDashboard.tsx`
- Modify: `frontend/src/components/voice/VariantManager.tsx`

These components already handle `"ready"`, `"building"`, `"pending"`, `"failed"`, `"deprecated"` statuses. Need to add `"missing"` status with a `MinusCircle` icon and "Missing" label.

- [ ] **Step 1: Add "missing" status icons/colors/labels to VariantDashboard**

```typescript
// In VariantDashboard.tsx, add to the existing records:
import { MinusCircle } from "lucide-react"

const STATUS_ICONS: Record<string, typeof CheckCircle2> = {
  ready: CheckCircle2,
  building: Loader2,
  pending: Clock,
  failed: XCircle,
  deprecated: AlertCircle,
  missing: MinusCircle,
}

const STATUS_COLORS: Record<string, string> = {
  ready: "text-success",
  building: "text-primary",
  pending: "text-muted-foreground",
  failed: "text-error",
  deprecated: "text-warning",
  missing: "text-muted-foreground",
}
```

- [ ] **Step 2: Add "missing" status to VariantManager**

```typescript
// In VariantManager.tsx
import { MinusCircle } from "lucide-react"

const STATUS_ICONS: Record<string, typeof CheckCircle2> = {
  ready: CheckCircle2,
  building: Loader2,
  pending: Clock,
  failed: XCircle,
  deprecated: AlertCircle,
  missing: MinusCircle,
}

const STATUS_COLORS: Record<string, string> = {
  ready: "text-success",
  building: "text-primary",
  pending: "text-muted-foreground",
  failed: "text-error",
  deprecated: "text-warning",
  missing: "text-muted-foreground",
}

const STATUS_LABELS: Record<string, string> = {
  ready: "Ready",
  building: "Building\u2026",
  pending: "Not built",
  failed: "Failed",
  deprecated: "Deprecated",
  missing: "Missing",
}
```

Note: The `mergeModelsWithVariants` function already handles models-without-variants as `variant === null`, which maps to `Clock` icon / `"Not built"` label. Update the null-handling to use the new status instead:

In the JSX where `!row.variant` is checked (around line 159), change the button label from "Build" to "Create Variant" to match the spec:

```tsx
{!row.variant ? (
  <Button
    variant="secondary"
    size="sm"
    className="h-7 gap-1.5 text-xs"
    disabled={busy}
    onClick={() => buildMut.mutate(row.id)}
  >
    {thisBusy
      ? <Loader2 className="h-3 w-3 animate-spin" />
      : <Hammer className="h-3 w-3" />}
    Create Variant
  </Button>
) : ...
```

- [ ] **Step 3: Verify frontend builds**

```bash
cd frontend && npm run build 2>&1 | tail -10
```

Expected: `✓ Compiled successfully`

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/voice/VariantDashboard.tsx frontend/src/components/voice/VariantManager.tsx
git commit -m "feat: support 'missing' variant status across frontend components"
```

---

### Task 3: Add Model Compatibility section to Overview tab

**Files:**
- Create: `frontend/src/components/voice/ModelCompatibilitySection.tsx`
- Modify: `frontend/src/components/voice/VoiceDetailsDrawer.tsx`

Add a compact "Model Compatibility" section to the Overview tab that shows all available models with their variant status, and a "Create Variant" button for missing ones.

- [ ] **Step 1: Create ModelCompatibilitySection component**

Create `frontend/src/components/voice/ModelCompatibilitySection.tsx`:

```tsx
"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  CheckCircle2,
  Clock,
  Hammer,
  Loader2,
  MinusCircle,
  XCircle,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { fetchModels, fetchVoiceVariants, ensureVariant } from "@/lib/api"

interface ModelCompatibilitySectionProps {
  publicVoiceId: string
}

const STATUS_ICONS: Record<string, typeof CheckCircle2> = {
  ready: CheckCircle2,
  building: Loader2,
  pending: Clock,
  failed: XCircle,
  missing: MinusCircle,
}

const STATUS_COLORS: Record<string, string> = {
  ready: "text-success",
  building: "text-primary",
  pending: "text-muted-foreground",
  failed: "text-error",
  missing: "text-muted-foreground",
}

const STATUS_LABELS: Record<string, string> = {
  ready: "Ready",
  building: "Building\u2026",
  pending: "Not built",
  failed: "Failed",
  missing: "Create Variant",
}

export function ModelCompatibilitySection({ publicVoiceId }: ModelCompatibilitySectionProps) {
  const queryClient = useQueryClient()

  const modelsQ = useQuery({
    queryKey: ["models"],
    queryFn: fetchModels,
  })

  const variantsQ = useQuery({
    queryKey: ["voice-variants", publicVoiceId],
    queryFn: () => fetchVoiceVariants(publicVoiceId),
  })

  const buildMut = useMutation({
    mutationFn: (modelId: string) => ensureVariant(publicVoiceId, modelId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["voice-variants", publicVoiceId] })
      queryClient.invalidateQueries({ queryKey: ["variant-summary"] })
    },
  })

  const models = modelsQ.data ?? []
  const variants = variantsQ.data ?? []
  const variantMap = new Map(variants.map((v) => [v.model_id, v]))

  if (modelsQ.isLoading) return null
  if (models.length === 0) return null

  return (
    <div className="space-y-1">
      <p className="text-caption uppercase tracking-wide">Model Compatibility</p>
      <div className="rounded-lg border border-border divide-y divide-border">
        {models.map((model) => {
          const variant = variantMap.get(model.id)
          const status = variant?.status ?? "missing"
          const Icon = STATUS_ICONS[status] ?? MinusCircle
          const color = STATUS_COLORS[status] ?? "text-muted-foreground"
          const busy = buildMut.isPending && buildMut.variables === model.id

          return (
            <div key={model.id} className="flex items-center justify-between px-3 py-2.5">
              <div className="flex items-center gap-2.5 min-w-0">
                <Icon className={`h-4 w-4 shrink-0 ${color} ${status === "building" ? "animate-spin" : ""}`} />
                <span className="text-sm font-medium truncate">{model.name}</span>
              </div>

              {(!variant || status === "missing") && (
                <Button
                  variant="secondary"
                  size="sm"
                  className="h-7 gap-1.5 text-xs shrink-0"
                  disabled={busy || buildMut.isPending}
                  onClick={() => buildMut.mutate(model.id)}
                >
                  {busy
                    ? <Loader2 className="h-3 w-3 animate-spin" />
                    : <Hammer className="h-3 w-3" />}
                  Create Variant
                </Button>
              )}

              {variant && status !== "missing" && (
                <span className={`inline-flex items-center gap-1 text-xs ${color}`}>
                  {STATUS_LABELS[status] ?? status}
                </span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Wire ModelCompatibilitySection into VoiceDetailsDrawer**

In `frontend/src/components/voice/VoiceDetailsDrawer.tsx`:

Add import:
```typescript
import { ModelCompatibilitySection } from "@/components/voice/ModelCompatibilitySection"
```

Insert the Model Compatibility section after the metadata section (after the Metadata `div` closing tag around line 147) and before the characteristics section:

```tsx
<ModelCompatibilitySection publicVoiceId={voice.public_voice_id} />
```

Add this between line 147 (closing `</div>` for metadata) and line 149 (characteristics check).

- [ ] **Step 3: Verify frontend builds**

```bash
cd frontend && npm run build 2>&1 | tail -10
```

Expected: `✓ Compiled successfully`

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/voice/ModelCompatibilitySection.tsx frontend/src/components/voice/VoiceDetailsDrawer.tsx
git commit -m "feat: add Model Compatibility section to voice details overview tab"
```

---

### Task 4: Improve query key invalidation for variant changes

**Files:**
- Modify: `frontend/src/components/voice/VariantManager.tsx`
- Modify: `frontend/src/components/voice/ArtifactHistory.tsx`

When a variant is built, rebuilt, or rolled back, the `["variant-summary"]` query key needs to be invalidated so the VariantDashboard and any other consumers get fresh data. Also invalidate `["voice-variants"]` across all voices since a global change affects the dashboard.

- [ ] **Step 1: Add variant-summary invalidation to VariantManager build/rebuild**

In `frontend/src/components/voice/VariantManager.tsx`, in the `onSuccess` callbacks for both `buildMut` and `rebuildMut`:

```typescript
const buildMut = useMutation({
  mutationFn: (modelId: string) => ensureVariant(publicVoiceId, modelId),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["voice-variants", publicVoiceId] })
    queryClient.invalidateQueries({ queryKey: ["variant-summary"] })
  },
})

const rebuildMut = useMutation({
  mutationFn: (modelId: string) => rebuildVariant(publicVoiceId, modelId),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["voice-variants", publicVoiceId] })
    queryClient.invalidateQueries({ queryKey: ["variant-summary"] })
  },
})
```

- [ ] **Step 2: Add variant-summary invalidation to ArtifactHistory rollback**

In `frontend/src/components/voice/ArtifactHistory.tsx`, find the `rollbackMut` mutation and add variant-summary invalidation:

```typescript
const rollbackMut = useMutation({
  mutationFn: (version: number) =>
    rollbackVariant(publicVoiceId, selectedModel!, version),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["artifact-versions", publicVoiceId, selectedModel] })
    queryClient.invalidateQueries({ queryKey: ["voice-variants", publicVoiceId] })
    queryClient.invalidateQueries({ queryKey: ["variant-summary"] })
  },
})
```

- [ ] **Step 3: Verify frontend builds**

```bash
cd frontend && npm run build 2>&1 | tail -10
```

Expected: `✓ Compiled successfully`

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/voice/VariantManager.tsx frontend/src/components/voice/ArtifactHistory.tsx
git commit -m "fix: invalidate variant-summary query on variant lifecycle changes"
```

---

### Task 5: Create bulk backfill script

**Files:**
- Create: `scripts/backfill_variants.py`
- Create: `scripts/backfill_variants.sh`

Create a standalone script that iterates over all voices and all installed models, building missing variants.

- [ ] **Step 1: Create scripts directory**

```bash
mkdir -p scripts
```

- [ ] **Step 2: Create backfill_variants.py**

Create `scripts/backfill_variants.py`:

```python
#!/usr/bin/env python3
"""Backfill missing VoiceVariants for all voices × all installed models.

Usage:
    # Run inside the Docker container or with backend venv activated:
    python scripts/backfill_variants.py
    python scripts/backfill_variants.py --dry-run
    python scripts/backfill_variants.py --model fish-audio
    python scripts/backfill_variants.py --dry-run --model fish-audio

Algorithm:
    For each Voice:
        locate VoiceSourceAsset
        for each installed model (optionally filtered by --model):
            if variant exists (status in ready|pending|building|failed|deprecated): skip
            else: build variant via runtime.ensure_variant

Environment:
    Requires DATABASE_URL (default: sqlite+aiosqlite:////data/omnivoice.db)
    and DATA_DIR (default: /data) matching the Docker setup.
"""

import argparse
import asyncio
import os
import sys

# Add backend directory to path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.models.db import Voice, Model, VoiceVariant
from app.services.runtime import PeakVoxRuntime, ModelNotRegistered
from app.services.voice_variant_repository import get_voice_identity_by_public_id

# Must happen before any app imports that reference the runtime singleton
# We create a fresh runtime to avoid depending on the app's lifecycle
from app.services.model_adapter import ModelAdapter


async def backfill(
    dry_run: bool = False,
    model_filter: str | None = None,
):
    from app.core.database import get_db, init_db

    # Use the app's database URL from settings
    database_url = os.environ.get("DATABASE_URL", settings.DATABASE_URL)
    engine = create_async_engine(database_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: None)  # ensure connection works

    async with AsyncSession(engine) as db:
        # Init tables if needed (idempotent)
        await init_db()

        # Get all voices
        voices = (await db.execute(select(Voice))).scalars().all()
        print(f"Found {len(voices)} voices")

        if not voices:
            print("No voices found. Nothing to do.")
            return

        # Get all installed/available models
        models = (await db.execute(select(Model))).scalars().all()
        if model_filter:
            models = [m for m in models if model_filter.lower() in m.id.lower() or model_filter.lower() in m.name.lower()]
        print(f"Found {len(models)} target models" + (f" (filter: {model_filter})" if model_filter else ""))

        if not models:
            print("No target models found. Nothing to do.")
            return

        # Collect existing variants for bulk lookup
        all_variants = (await db.execute(select(VoiceVariant))).scalars().all()
        variant_lookup: dict[tuple[str, str], VoiceVariant] = {}
        for v in all_variants:
            variant_lookup[(v.voice_id, v.model_id)] = v

        # Initialize runtime
        runtime = PeakVoxRuntime()

        # Register adapters from the app's adapter registry
        _init_runtime_adapters(runtime)

        total_built = 0
        total_skipped = 0
        total_errors = 0

        for voice in voices:
            for model in models:
                key = (voice.id, model.id)
                existing = variant_lookup.get(key)

                if existing is not None:
                    print(f"  SKIP  voice={voice.name} ({voice.id}) model={model.name} ({model.id}) — variant exists ({existing.status})")
                    total_skipped += 1
                    continue

                if dry_run:
                    print(f"  WOULD_BUILD  voice={voice.name} ({voice.id}) model={model.name} ({model.id})")
                    total_built += 1
                    continue

                print(f"  BUILD voice={voice.name} ({voice.id}) model={model.name} ({model.id}) ...", end=" ", flush=True)
                try:
                    resolved_voice = await get_voice_identity_by_public_id(db, voice.public_voice_id)
                    if resolved_voice is None:
                        print("FAIL (voice not found by public ID)")
                        total_errors += 1
                        continue

                    variant = await runtime.ensure_variant(db, voice=resolved_voice, model_id=model.id)
                    print(f"OK (status={variant.status})")
                    total_built += 1
                except ModelNotRegistered as e:
                    print(f"FAIL (model not registered: {e})")
                    total_errors += 1
                except Exception as e:
                    print(f"FAIL ({e})")
                    total_errors += 1

        await db.commit()

    await engine.dispose()

    print(f"\nSummary: {total_built} built, {total_skipped} skipped, {total_errors} errors")
    if dry_run:
        print("(dry run — no changes made)")


def _init_runtime_adapters(runtime: PeakVoxRuntime) -> None:
    """Register available adapters from the app's adapter module."""
    from app.services.model_adapters.omnivoice_adapter import OmniVoiceAdapter
    from app.services.model_adapters.fish_adapter import FishAudioAdapter

    try:
        runtime.register_adapter(OmniVoiceAdapter())
        print("  Registered OmniVoice adapter")
    except Exception as e:
        print(f"  WARN: Could not register OmniVoice adapter: {e}")

    try:
        runtime.register_adapter(FishAudioAdapter())
        print("  Registered Fish Audio adapter")
    except Exception as e:
        print(f"  WARN: Could not register Fish Audio adapter: {e}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill missing VoiceVariants for all voices",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only display actions without making changes",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Only process models whose id or name contains this string",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    asyncio.run(backfill(dry_run=args.dry_run, model_filter=args.model))


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Create backfill_variants.sh**

Create `scripts/backfill_variants.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Default: run via Docker (primary workflow)
# Fallback: run directly with backend venv
if command -v docker &>/dev/null && docker compose ls &>/dev/null 2>&1; then
  echo "Running backfill via Docker..."
  docker compose exec -T backend python /app/scripts/backfill_variants.py "$@"
else
  echo "Running backfill directly (requires backend venv)..."

  # Activate backend virtual environment
  if [ -f "$PROJECT_DIR/backend/.venv/bin/activate" ]; then
    source "$PROJECT_DIR/backend/.venv/bin/activate"
  fi

  cd "$PROJECT_DIR"
  PYTHONPATH="$PROJECT_DIR/backend:$PYTHONPATH" \
    python scripts/backfill_variants.py "$@"
fi
```

- [ ] **Step 4: Make scripts executable**

```bash
chmod +x scripts/backfill_variants.py scripts/backfill_variants.sh
```

- [ ] **Step 5: Verify script imports correctly**

```bash
cd backend && .venv/bin/python -m py_compile ../scripts/backfill_variants.py 2>&1 || echo "Expected: may need Docker venv (pydantic-core dependency)"
```

- [ ] **Step 6: Commit**

```bash
git add scripts/
git commit -m "feat: add bulk variant backfill script with dry-run and model filter"
```

---

### Task 6: Sync active_artifact_version in variants list endpoint

**Files:**
- Modify: `backend/app/api/variants.py`

The `_variant_row_to_list_item` function currently always sets `active_artifact_version=None`. For the frontend to display version numbers correctly, it needs to query the active artifact.

- [ ] **Step 1: Fix active_artifact_version resolution**

In `backend/app/api/variants.py`, modify the `list_variants` endpoint and `_variant_row_to_list_item`:

Keep `_variant_row_to_list_item` as a pure mapper, but add artifact version resolution in the endpoint:

```python
@router.get("/{public_voice_id}/variants", response_model=list[VariantListItem])
async def list_variants(public_voice_id: str, db: AsyncSession = Depends(get_db)):
    """List all variants for a voice with their lifecycle statuses."""
    voice = await _resolve_voice(db, public_voice_id)
    rows = (
        await db.execute(select(VoiceVariant).where(VoiceVariant.voice_id == voice.id))
    ).scalars().all()
    items = []
    for row in rows:
        item = _variant_row_to_list_item(row)
        if row.active_artifact_id:
            active = await get_active_artifact(db, row)
            if active:
                item.active_artifact_version = active.version
        items.append(item)
    return items
```

(The code already has this — verify it's already in place.)

- [ ] **Step 2: Verify backend syntax**

```bash
cd backend && .venv/bin/python -m py_compile app/api/variants.py && echo "OK"
```

Expected: `OK`

- [ ] **Step 3: Commit (if changes were needed)**

```bash
git add backend/app/api/variants.py
git commit -m "fix: resolve active_artifact_version in variants list endpoint"
```

---

### Task 7: Verify and lint

**Files:** None (verification only)

- [ ] **Step 1: Run frontend build**

```bash
cd frontend && npm run build 2>&1 | tail -15
```

Expected: `✓ Compiled successfully`

- [ ] **Step 2: Run frontend lint**

```bash
cd frontend && npm run lint 2>&1
```

Expected: no errors

- [ ] **Step 3: Verify backend syntax for all changed files**

```bash
cd backend && for f in app/api/variants_summary.py app/api/variants.py; do
  .venv/bin/python -m py_compile "$f" && echo "$f OK" || echo "$f FAIL"
done
```

Expected: both OK

- [ ] **Step 4: Commit any remaining changes**

```bash
git add -A
git status
```
