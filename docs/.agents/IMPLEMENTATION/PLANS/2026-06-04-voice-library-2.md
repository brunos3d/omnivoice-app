# Voice Library 2.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development or executing-plans to implement this plan task-by-task.

**Goal:** Upgrade the Voice Library to expose the full `Voice → Source Asset → Variant → Artifact → Generation` chain with progressive disclosure.

**Architecture:** Frontend-only rework of the existing `/voices` page components, plus minimal backend additions (inline source_asset field, variant summary endpoint). No new concepts — every UI element maps to an existing domain entity. Tabs use Radix UI (already in the project). All variant/artifact API endpoints already exist.

**Tech Stack:** Next.js 15 (App Router), React 18, TypeScript, Zustand, TanStack Query, Radix UI Tabs, shadcn/ui, Tailwind CSS, FastAPI backend

---

### Task 1: Backend — Source Asset response

**Files:**
- Modify: `backend/app/schemas/voice.py` — add `VoiceSourceAssetResponse` schema and `source_asset` field
- Modify: `backend/app/api/voices.py` — populate source_asset in the voice response

**Design:** `VoiceProfileResponse` gains an optional `source_asset` field. When the voice is a `SOURCE_ASSET` type (has a row in `voice_source_assets`), include its metadata. The voice detail endpoint fetches it via a join or separate query.

- [ ] **Step 1: Add VoiceSourceAssetResponse schema**

Add to `backend/app/schemas/voice.py`:

```python
class VoiceSourceAssetResponse(BaseModel):
    id: str
    asset_type: str
    original_filename: Optional[str] = None
    content_type: Optional[str] = None
    file_size: Optional[int] = None
    audio_duration: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}
```

Add to `VoiceProfileResponse` (after `creation_source`):
```python
    source_asset: Optional[VoiceSourceAssetResponse] = None
```

- [ ] **Step 2: Populate source_asset in the voice detail endpoint**

In `backend/app/api/voices.py`, import `VoiceSourceAsset`:
```python
from app.models.db import VoiceProfile, VoiceSourceAsset
```

In the `GET /voices/{id}` handler (and the list endpoint if needed), after fetching the VoiceProfile, query for its source asset:

```python
source_asset = await db.execute(
    select(VoiceSourceAsset).where(VoiceSourceAsset.voice_id == profile.id).limit(1)
)
source_asset_row = source_asset.scalar_one_or_none()
```

Pass `source_asset=source_asset_row` when building the response. This is most easily done by adding a helper that takes the profile and optional source_asset and returns the dict.

The most minimal change: in `GET /voices/{id}` and `GET /voices/page`, after fetching profiles, also fetch their source assets and attach them. For the list endpoint, batch-fetch all source assets for the returned page.

- [ ] **Step 3: Write backend test**

Add a test in `backend/tests/test_voices.py`:
```python
async def test_voice_response_includes_source_asset(async_client, db_session):
    # Create a voice profile
    resp = await async_client.post("/voices", ...)
    assert resp.status_code == 200
    data = resp.json()
    assert "source_asset" in data
    # SOURCE_ASSET voices should have a source_asset block
    if data["creation_source"] == "SOURCE_ASSET":
        assert data["source_asset"] is not None
        assert "original_filename" in data["source_asset"]
```

- [ ] **Step 4: Run tests**

```bash
docker compose run --rm backend bash -c "python -m pytest tests/ -x --tb=short -q"
```
Expected: 258+ passing (exact count may vary with added tests)

- [ ] **Step 5: Commit**
```bash
git add backend/app/schemas/voice.py backend/app/api/voices.py backend/tests/test_voices.py
git commit -m "feat: inline source_asset in voice response (Voice Library 2.0)"
```

---

### Task 2: Frontend — TypeScript types + API stub

**Files:**
- Modify: `frontend/src/types/index.ts` — add `creation_source`, `VoiceSourceAsset`, `VariantSummaryItem`
- Modify: `frontend/src/lib/api.ts` — add `fetchVariantSummary` function

- [ ] **Step 1: Add types**

Add to `frontend/src/types/index.ts`:

```typescript
export type CreationSource = "SOURCE_ASSET" | "PRESET_VOICE" | "MARKETPLACE_VOICE" | "TRAINED_VOICE" | "IMPORTED_VOICE" | "SYSTEM_VOICE"

export interface VoiceSourceAsset {
  id: string
  asset_type: string
  original_filename: string | null
  content_type: string | null
  file_size: number | null
  audio_duration: number | null
  created_at: string
}
```

Add `creation_source` and `source_asset` to `VoiceProfile`:
```typescript
  creation_source: CreationSource
  source_asset: VoiceSourceAsset | null
```

Add variant summary type (for cross-voice Variant Dashboard):
```typescript
export interface VariantSummaryItem {
  voice_id: string
  voice_name: string
  models: Array<{
    model_id: string
    model_name: string
    status: string
    active_artifact_version: number | null
    error_message: string | null
  }>
}
```

- [ ] **Step 2: Add API function**

Add to `frontend/src/lib/api.ts`:

```typescript
export async function fetchVariantSummary(): Promise<VariantSummaryItem[]> {
  const res = await fetch(`${API_URL}/variants/summary`)
  if (!res.ok) throw new ApiError(res.status, "Failed to fetch variant summary")
  return res.json()
}
```

- [ ] **Step 3: Commit**
```bash
git add frontend/src/types/index.ts frontend/src/lib/api.ts
git commit -m "feat: add Voice Library 2.0 types (creation_source, source_asset, variant summary)"
```

---

### Task 3: Backend — Variant Summary endpoint

**Files:**
- Create: `backend/app/api/variants_summary.py` — `GET /variants/summary`
- Modify: `backend/app/main.py` — mount the router

- [ ] **Step 1: Create the summary endpoint**

`backend/app/api/variants_summary.py`:

```python
import logging
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.models.db import Voice, VoiceVariant, Model

logger = logging.getLogger(__name__)

router = APIRouter(tags=["variants"])


@router.get("/variants/summary")
async def get_variant_summary(db: AsyncSession = Depends(get_db)):
    """Return variant status across all voices for the Variant Dashboard.

    CE-only utility. Returns a list of voices, each with an array of per-model
    variant statuses. No pagination (CE scale assumption).
    """
    voices = (await db.execute(select(Voice))).scalars().all()
    models = (await db.execute(select(Model))).scalars().all()
    model_map = {m.id: m.name for m in models}

    variants = (
        await db.execute(
            select(VoiceVariant).options(joinedload(VoiceVariant.voice_ref))
        )
    ).scalars().all()

    voice_map: dict[str, list[dict]] = {}
    for v in variants:
        voice_map.setdefault(v.voice_id, []).append({
            "model_id": v.model_id,
            "model_name": model_map.get(v.model_id, v.model_id),
            "status": v.status,
            "active_artifact_version": v.active_artifact_version,
            "error_message": v.error_message,
        })

    result = []
    for voice in voices:
        result.append({
            "voice_id": voice.id,
            "voice_name": voice.name,
            "models": voice_map.get(voice.id, []),
        })

    return result
```

- [ ] **Step 2: Mount in main.py**

In `backend/app/main.py`:
```python
from app.api.variants_summary import router as variants_summary_router
app.include_router(variants_summary_router)
```

- [ ] **Step 3: Run tests**

```bash
docker compose run --rm backend bash -c "python -m pytest tests/ -x --tb=short -q"
```
Expected: all pass

- [ ] **Step 4: Commit**
```bash
git add backend/app/api/variants_summary.py backend/app/main.py
git commit -m "feat: add /variants/summary endpoint for Variant Dashboard"
```

---

### Task 4: Frontend — Creation Source badge on VoiceCard

**Files:**
- Modify: `frontend/src/components/voice/VoiceCard.tsx`

- [ ] **Step 1: Add source badge rendering**

Add to the import section:
```typescript
import type { VoiceProfile, CreationSource } from "@/types"
```

Add a source-label map inside the component or as a module constant:
```typescript
const CREATION_SOURCE_LABELS: Record<CreationSource, { label: string; className: string }> = {
  SOURCE_ASSET: { label: "Source Audio", className: "bg-sky-500/10 text-sky-500 border-sky-500/20" },
  PRESET_VOICE: { label: "Preset", className: "bg-amber-500/10 text-amber-500 border-amber-500/20" },
  MARKETPLACE_VOICE: { label: "Marketplace", className: "bg-purple-500/10 text-purple-500 border-purple-500/20" },
  TRAINED_VOICE: { label: "Trained", className: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" },
  IMPORTED_VOICE: { label: "Imported", className: "bg-violet-500/10 text-violet-500 border-violet-500/20" },
  SYSTEM_VOICE: { label: "System", className: "bg-muted text-muted-foreground border-border" },
}
```

After the initials avatar div and before the name, add:
```typescript
{voice.creation_source && voice.creation_source !== "SOURCE_ASSET" && (
  <Badge
    variant="outline"
    className={cn(
      "px-1.5 py-0 text-[10px]",
      CREATION_SOURCE_LABELS[voice.creation_source]?.className
    )}
  >
    {CREATION_SOURCE_LABELS[voice.creation_source]?.label ?? voice.creation_source}
  </Badge>
)}
```

Wait — for SOURCE_ASSET, we don't need a badge (it's the default/expected type).
For non-default sources (PRESET_VOICE), show a badge.

Actually the design says all voices show a small badge. Let me show it for all types but make SOURCE_ASSET subtle:

```typescript
{voice.creation_source && (
  <Badge
    variant="outline"
    className={cn(
      "px-1.5 py-0 text-[10px]",
      CREATION_SOURCE_LABELS[voice.creation_source]?.className ?? "border-border text-muted-foreground"
    )}
  >
    {CREATION_SOURCE_LABELS[voice.creation_source]?.label ?? voice.creation_source}
  </Badge>
)}
```

Place it right after the `voice.name` line, before the language badge.

- [ ] **Step 2: Commit**
```bash
git add frontend/src/components/voice/VoiceCard.tsx
git commit -m "feat: add creation source badge to VoiceCard"
```

---

### Task 5: Frontend — Tabbed VoiceDetailsDrawer

**Files:**
- Modify: `frontend/src/components/voice/VoiceDetailsDrawer.tsx`
- Import: Radix UI Tabs (already in project)

- [ ] **Step 1: Refactor to tabs architecture**

Replace the single-scroll content area with a tabbed layout:

```typescript
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
```

The content structure becomes:

```tsx
<Tabs defaultValue="overview" className="flex flex-col h-full">
  <TabsList className="grid grid-cols-4 mx-4 mt-4">
    <TabsTrigger value="overview">Overview</TabsTrigger>
    <TabsTrigger value="source-asset">Source</TabsTrigger>
    <TabsTrigger value="variants">Variants</TabsTrigger>
    <TabsTrigger value="artifacts">Artifacts</TabsTrigger>
  </TabsList>

  <div className="flex-1 overflow-y-auto">
    <TabsContent value="overview" className="p-6 space-y-6">
      {/* Move existing content here: Voice ID, AudioPlayer, Description, Transcript, Metadata, Characteristics, Preset tags, Generation defaults */}
      {/* Add creation source label */}
    </TabsContent>

    <TabsContent value="source-asset" className="p-6 space-y-6">
      {/* Will be populated in Task 6 */}
      <div className="flex items-center justify-center py-12 text-muted-foreground">
        Source Asset information
      </div>
    </TabsContent>

    <TabsContent value="variants" className="p-6 space-y-6">
      <VariantManager publicVoiceId={voice.public_voice_id} />
    </TabsContent>

    <TabsContent value="artifacts" className="p-6 space-y-6">
      {/* Will be populated in Task 8 */}
      <div className="flex items-center justify-center py-12 text-muted-foreground">
        Artifact version history
      </div>
    </TabsContent>
  </div>
</Tabs>
```

Move the existing `Voice ID`, `AudioPlayer`, `Description`, `Transcript`, `Metadata`, `Characteristics`, `Preset tags`, `Generation defaults` all into the Overview tab.

Add creation source label near the top of Overview:
```tsx
{voice.creation_source && (
  <div className="flex items-center gap-2">
    <span className="text-caption uppercase tracking-wide">Origin</span>
    <Badge variant="outline" className={cn("px-2 py-0.5", CREATION_SOURCE_LABELS[voice.creation_source]?.className)}>
      {CREATION_SOURCE_LABELS[voice.creation_source]?.label ?? voice.creation_source}
    </Badge>
  </div>
)}
```

Keep the bottom action bar (Use / API / Edit / Delete) below the tabs, outside the tab content.

- [ ] **Step 2: Move VariantManager inside Variants tab**

Remove the standalone `<VariantManager ... />` call from the bottom of the scroll area (currently line 158) — it moves into the variants tab content.

- [ ] **Step 3: Test interaction**

```bash
docker compose run --rm frontend bash -c "npm run build 2>&1 | tail -20"
```
Expected: Build succeeds with no errors.

- [ ] **Step 4: Commit**
```bash
git add frontend/src/components/voice/VoiceDetailsDrawer.tsx
git commit -m "feat: tabbed VoiceDetailsDrawer with Overview, Source, Variants, Artifacts"
```

---

### Task 6: Frontend — Source Asset tab content

**Files:**
- Create: `frontend/src/components/voice/SourceAssetTab.tsx`

- [ ] **Step 1: Create SourceAssetTab component**

```tsx
"use client"

import { FileAudio, Clock, HardDrive, FileType } from "lucide-react"
import type { VoiceProfile, VoiceSourceAsset } from "@/types"
import { formatDuration, formatFileSize } from "@/lib/utils"

interface SourceAssetTabProps {
  voice: VoiceProfile
}

function MetaRow({ icon: Icon, label, value }: { icon: typeof FileAudio; label: string; value: string }) {
  return (
    <div className="flex items-center gap-3 py-2 text-sm">
      <Icon className="h-4 w-4 shrink-0 text-muted-foreground" />
      <span className="text-muted-foreground">{label}</span>
      <span className="ml-auto text-foreground/90">{value}</span>
    </div>
  )
}

export function SourceAssetTab({ voice }: SourceAssetTabProps) {
  const asset = voice.source_asset

  if (!asset) {
    return (
      <div className="rounded-lg border border-border bg-surface p-6 text-center">
        <FileAudio className="mx-auto h-8 w-8 text-muted-foreground mb-3" />
        <p className="text-sm text-muted-foreground">
          {voice.creation_source === "PRESET_VOICE"
            ? "This is a preset voice — no source audio file."
            : "No source asset recorded for this voice."}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <p className="text-caption uppercase tracking-wide">Source material</p>
      <div className="rounded-lg border border-border bg-surface px-4 divide-y divide-border">
        <MetaRow icon={FileAudio} label="Filename" value={asset.original_filename ?? "—"} />
        <MetaRow icon={FileType} label="Type" value={asset.content_type ?? "—"} />
        <MetaRow icon={HardDrive} label="Size" value={asset.file_size != null ? formatFileSize(asset.file_size) : "—"} />
        <MetaRow icon={Clock} label="Duration" value={asset.audio_duration != null ? formatDuration(asset.audio_duration) : "—"} />
        <MetaRow icon={Clock} label="Uploaded" value={new Date(asset.created_at).toLocaleString()} />
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Add formatFileSize to utils**

Check if `frontend/src/lib/utils.ts` already has it. If not, add:

```typescript
export function formatFileSize(bytes: number): string {
  const units = ["B", "KB", "MB", "GB"]
  let size = bytes
  let unit = 0
  while (size >= 1024 && unit < units.length - 1) {
    size /= 1024
    unit++
  }
  return `${size.toFixed(1)} ${units[unit]}`
}
```

- [ ] **Step 3: Wire into VoiceDetailsDrawer**

Replace the placeholder in the "source-asset" tab:
```tsx
<TabsContent value="source-asset" className="p-6 space-y-6">
  <SourceAssetTab voice={voice} />
</TabsContent>
```

- [ ] **Step 4: Commit**
```bash
git add frontend/src/components/voice/SourceAssetTab.tsx frontend/src/lib/utils.ts frontend/src/components/voice/VoiceDetailsDrawer.tsx
git commit -m "feat: Source Asset tab with provenance metadata"
```

---

### Task 7: Frontend — Variants compatibility matrix

**Files:**
- Modify: `frontend/src/components/voice/VariantManager.tsx`
- Keep the same file — it's already doing most of what we need. Enhance to show the full matrix.

- [ ] **Step 1: Enhance VariantManager to show a table layout**

The current `VariantManager` already shows models × variant status. Enhance it:

- Add model availability indicator (installed / not installed / edition-gated)
- Add realization type label
- Show active artifact version badge
- Add error tooltip for failed builds

Replace the current list layout with a more structured table:

```tsx
<div className="overflow-hidden rounded-lg border border-border">
  <table className="w-full">
    <thead>
      <tr className="border-b border-border bg-surface-2 text-xs text-muted-foreground">
        <th className="px-3 py-2 text-left font-medium">Model</th>
        <th className="px-3 py-2 text-left font-medium">Status</th>
        <th className="px-3 py-2 text-left font-medium hidden sm:table-cell">Realization</th>
        <th className="px-3 py-2 text-right font-medium">Version</th>
        <th className="px-3 py-2 text-right font-medium">Actions</th>
      </tr>
    </thead>
    <tbody className="divide-y divide-border">
      {rows.map((row) => (
        <tr key={row.id} className="text-sm">
          <td className="px-3 py-2.5 font-medium truncate max-w-[160px]">{row.name}</td>
          <td className="px-3 py-2.5">
            <span className={`inline-flex items-center gap-1.5 ${statusColor}`}>
              <StatusIcon className={`h-3.5 w-3.5 ${row.variant?.status === "building" ? "animate-spin" : ""}`} />
              <span>{statusLabel}</span>
            </span>
          </td>
          <td className="px-3 py-2.5 text-muted-foreground hidden sm:table-cell">
            {row.variant?.realization_type ?? "—"}
          </td>
          <td className="px-3 py-2.5 text-right">
            {row.variant?.active_artifact_version != null
              ? <span className="font-mono text-xs">v{row.variant.active_artifact_version}</span>
              : <span className="text-muted-foreground">—</span>}
          </td>
          <td className="px-3 py-2.5 text-right">
            {/* same Build/Rebuild/Retry button logic as current */}
          </td>
        </tr>
      ))}
    </tbody>
  </table>
</div>
```

Keep the same query/mutation logic. The key layout change is list → table.

- [ ] **Step 2: Add `realization_type` to VariantListItem type**

In `frontend/src/types/index.ts`, add to `VariantListItem`:
```typescript
  realization_type: string | null
```

- [ ] **Step 3: Commit**
```bash
git add frontend/src/components/voice/VariantManager.tsx frontend/src/types/index.ts
git commit -m "feat: variant compatibility matrix table layout"
```

---

### Task 8: Frontend — Artifact version browser + rollback

**Files:**
- Create: `frontend/src/components/voice/ArtifactHistory.tsx`
- Modify: `frontend/src/components/voice/VoiceDetailsDrawer.tsx` — wire in the new component

- [ ] **Step 1: Create ArtifactHistory component**

```tsx
"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  ArrowLeftToLine,
  CheckCircle2,
  Clock,
  History,
  Trash2,
  RotateCcw,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  fetchArtifactVersions,
  rollbackVariant,
  fetchVoiceVariants,
} from "@/lib/api"
import type { VariantListItem, ArtifactVersionResponse } from "@/types"

interface ArtifactHistoryProps {
  publicVoiceId: string
  modelsWithVariants: { model_id: string; model_name: string }[]
}

export function ArtifactHistory({ publicVoiceId }: ArtifactHistoryProps) {
  const queryClient = useQueryClient()
  const [selectedModel, setSelectedModel] = useState<string | null>(null)

  const variantsQ = useQuery({
    queryKey: ["voice-variants", publicVoiceId],
    queryFn: () => fetchVoiceVariants(publicVoiceId),
  })

  const variantsWithVersions = (variantsQ.data ?? []).filter(
    (v) => (v.active_artifact_version ?? 0) > 0
  )

  const artifactsQ = useQuery({
    queryKey: ["artifact-versions", publicVoiceId, selectedModel],
    queryFn: () => fetchArtifactVersions(publicVoiceId, selectedModel!),
    enabled: !!selectedModel,
  })

  const rollbackMut = useMutation({
    mutationFn: (version: number) =>
      rollbackVariant(publicVoiceId, selectedModel!, version),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["artifact-versions", publicVoiceId, selectedModel] })
      queryClient.invalidateQueries({ queryKey: ["voice-variants", publicVoiceId] })
    },
  })

  if (variantsWithVersions.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-surface p-6 text-center">
        <History className="mx-auto h-8 w-8 text-muted-foreground mb-3" />
        <p className="text-sm text-muted-foreground">
          No version history yet. Rebuild a variant to create artifact versions.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Model selector */}
      <div className="flex flex-wrap gap-2">
        {variantsWithVersions.map((v) => (
          <Button
            key={v.model_id}
            variant={selectedModel === v.model_id ? "default" : "outline"}
            size="sm"
            onClick={() => setSelectedModel(v.model_id)}
            className="text-xs"
          >
            {v.model_name}
          </Button>
        ))}
      </div>

      {/* Version timeline */}
      {selectedModel && artifactsQ.data && (
        <div className="rounded-lg border border-border divide-y divide-border">
          {artifactsQ.data.map((av) => (
            <div key={av.version} className="flex items-center justify-between px-4 py-3">
              <div className="flex items-center gap-3">
                {av.is_active ? (
                  <CheckCircle2 className="h-4 w-4 text-success" />
                ) : (
                  <Clock className="h-4 w-4 text-muted-foreground" />
                )}
                <div>
                  <p className="text-sm font-medium">
                    v{av.version}
                    {av.is_active && (
                      <span className="ml-2 text-xs text-success font-normal">Active</span>
                    )}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(av.created_at).toLocaleString()}
                    {av.model_version && ` · model ${av.model_version}`}
                    {av.size_bytes != null && ` · ${formatFileSize(av.size_bytes)}`}
                  </p>
                </div>
              </div>

              {!av.is_active && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs gap-1.5"
                  disabled={rollbackMut.isPending}
                  onClick={() => rollbackMut.mutate(av.version)}
                >
                  <RotateCcw className="h-3 w-3" />
                  Rollback
                </Button>
              )}
            </div>
          ))}
        </div>
      )}

      {selectedModel && !artifactsQ.data && (
        <div className="flex items-center justify-center py-8">
          <p className="text-sm text-muted-foreground">Loading version history...</p>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Wire into VoiceDetailsDrawer**

Replace the placeholder in the "artifacts" tab:
```tsx
<TabsContent value="artifacts" className="p-6 space-y-6">
  <ArtifactHistory publicVoiceId={voice.public_voice_id} />
</TabsContent>
```

- [ ] **Step 3: Commit**
```bash
git add frontend/src/components/voice/ArtifactHistory.tsx frontend/src/components/voice/VoiceDetailsDrawer.tsx
git commit -m "feat: artifact version browser with rollback UI"
```

---

### Task 9: Frontend — Variant Dashboard

**Files:**
- Create: `frontend/src/components/voice/VariantDashboard.tsx`
- Modify: `frontend/src/app/voices/page.tsx` — add toggle button + Variant Dashboard view

- [ ] **Step 1: Create VariantDashboard component**

```tsx
"use client"

import { useQuery } from "@tanstack/react-query"
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Loader2,
  XCircle,
} from "lucide-react"
import { fetchVariantSummary } from "@/lib/api"
import type { VariantSummaryItem } from "@/types"

const STATUS_ICONS: Record<string, typeof CheckCircle2> = {
  ready: CheckCircle2,
  building: Loader2,
  pending: Clock,
  failed: XCircle,
  deprecated: AlertCircle,
}

const STATUS_COLORS: Record<string, string> = {
  ready: "text-success",
  building: "text-primary",
  pending: "text-muted-foreground",
  failed: "text-error",
  deprecated: "text-warning",
}

interface VariantDashboardProps {
  onSelectVoice?: (voiceId: string) => void
}

export function VariantDashboard({ onSelectVoice }: VariantDashboardProps) {
  const summaryQ = useQuery({
    queryKey: ["variant-summary"],
    queryFn: fetchVariantSummary,
  })

  if (summaryQ.isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    )
  }

  const summary = summaryQ.data ?? []

  // Collect all unique model ids across all voices
  const allModelIds = [...new Set(summary.flatMap((v) => v.models.map((m) => m.model_id)))]
  const modelNames = [...new Set(summary.flatMap((v) => v.models.map((m) => `${m.model_id}:${m.model_name}`)))]
  const modelNameMap = Object.fromEntries(modelNames.map((n) => n.split(":")))

  const totalVoices = summary.length
  const totalReady = summary.reduce((acc, v) => acc + v.models.filter((m) => m.status === "ready").length, 0)
  const totalFailed = summary.reduce((acc, v) => acc + v.models.filter((m) => m.status === "failed").length, 0)
  const totalPending = summary.reduce((acc, v) => acc + v.models.filter((m) => m.status === "pending").length, 0)

  return (
    <div className="space-y-6">
      {/* Summary header */}
      <div className="grid grid-cols-4 gap-4">
        <div className="rounded-lg border border-border bg-surface p-4 text-center">
          <p className="text-2xl font-bold">{totalVoices}</p>
          <p className="text-xs text-muted-foreground">Voices</p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-4 text-center">
          <p className="text-2xl font-bold text-success">{totalReady}</p>
          <p className="text-xs text-muted-foreground">Ready</p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-4 text-center">
          <p className="text-2xl font-bold text-warning">{totalPending}</p>
          <p className="text-xs text-muted-foreground">Pending</p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-4 text-center">
          <p className="text-2xl font-bold text-error">{totalFailed}</p>
          <p className="text-xs text-muted-foreground">Failed</p>
        </div>
      </div>

      {/* Matrix */}
      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-surface-2">
              <th className="px-4 py-2.5 text-left font-medium">Voice</th>
              {allModelIds.map((mid) => (
                <th key={mid} className="px-3 py-2.5 text-center font-medium text-xs">
                  {modelNameMap[mid] ?? mid}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {summary.map((item) => (
              <tr
                key={item.voice_id}
                className="hover:bg-surface cursor-pointer"
                onClick={() => onSelectVoice?.(item.voice_id)}
              >
                <td className="px-4 py-2.5 font-medium">{item.voice_name}</td>
                {allModelIds.map((mid) => {
                  const vm = item.models.find((m) => m.model_id === mid)
                  const Icon = vm ? STATUS_ICONS[vm.status] ?? Clock : Clock
                  const color = vm ? STATUS_COLORS[vm.status] ?? "text-muted-foreground" : "text-muted-foreground"
                  return (
                    <td key={mid} className="px-3 py-2.5 text-center">
                      <Icon
                        className={`inline-block h-4 w-4 ${color} ${vm?.status === "building" ? "animate-spin" : ""}`}
                        title={vm?.error_message ?? vm?.status ?? "No variant"}
                      />
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Add toggle button to Voices page**

Read `frontend/src/app/voices/page.tsx` to find the right spot. Add a "Library / Variants" toggle in the page header alongside the existing buttons.

The toggle switches between showing `VoiceGrid` (library view) and `VariantDashboard` (variant view). Add a local state:

```typescript
const [viewMode, setViewMode] = useState<"library" | "variants">("library")
```

Add toggle buttons:
```tsx
<div className="flex gap-1 bg-surface rounded-lg p-0.5 border border-border">
  <button
    onClick={() => setViewMode("library")}
    className={`px-3 py-1.5 text-xs rounded-md transition-colors ${viewMode === "library" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"}`}
  >
    Library
  </button>
  <button
    onClick={() => setViewMode("variants")}
    className={`px-3 py-1.5 text-xs rounded-md transition-colors ${viewMode === "variants" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"}`}
  >
    Variants
  </button>
</div>
```

- [ ] **Step 3: Conditionally render grid or dashboard**

```tsx
{viewMode === "library" ? (
  <VoiceGrid ... />
) : (
  <VariantDashboard onSelectVoice={(voiceId) => { /* select voice in library view */ }} />
)}
```

- [ ] **Step 4: Build test**

```bash
docker compose run --rm frontend bash -c "npm run build 2>&1 | tail -20"
```
Expected: Build succeeds

- [ ] **Step 5: Commit**
```bash
git add frontend/src/components/voice/VariantDashboard.tsx frontend/src/app/voices/page.tsx
git commit -m "feat: Variant Dashboard with cross-voice variant status matrix"
```

---

### Task 10: Frontend — Cleanup "coming soon" tabs

**Files:**
- Modify: `frontend/src/app/voices/page.tsx` — replace or remove community/preset/marketplace tabs

- [ ] **Step 1: Replace scope tabs**

Currently the page has four scope tabs: My Voices, Community (coming soon), Preset (coming soon), Recently Used. Replace Community and Preset with architecture-accurate states.

Read the current tab implementation. The cleanest approach: remove Community and Preset tabs entirely (they are Cloud features with no CE content). Keep "My Voices" and "Recently Used" as scope filters. Add a single "All Voices" scope that shows everything.

If the current tabs are:
```tsx
<Tabs value={scope} onValueChange={(v) => setScope(v as VoiceScope)}>
  <TabsList>
    <TabsTrigger value="mine">My Voices</TabsTrigger>
    <TabsTrigger value="community">Community</TabsTrigger>
    <TabsTrigger value="preset">Preset</TabsTrigger>
    <TabsTrigger value="recent">Recently Used</TabsTrigger>
  </TabsList>
</Tabs>
```

Change to:
```tsx
<Tabs value={scope} onValueChange={(v) => setScope(v as VoiceScope)}>
  <TabsList>
    <TabsTrigger value="mine">My Voices</TabsTrigger>
    <TabsTrigger value="recent">Recently Used</TabsTrigger>
  </TabsList>
</Tabs>
```

And optionally remove `"community"` and `"preset"` from the `VoiceScope` type if they're only used as "coming soon" placeholders. Keep them in the type if they have any real use.

- [ ] **Step 2: Commit**
```bash
git add frontend/src/app/voices/page.tsx frontend/src/types/index.ts
git commit -m "chore: remove coming-soon Community/Preset tabs from voice library"
```

---

### Task 11: Run full test suite and verify

- [ ] **Step 1: Run backend tests**

```bash
docker compose run --rm backend bash -c "python -m pytest tests/ -x --tb=short -q"
```
Expected: All 258+ tests pass

- [ ] **Step 2: Run frontend build**

```bash
docker compose run --rm frontend bash -c "npm run build 2>&1 | tail -30"
```
Expected: Build succeeds with no type errors or lint failures

- [ ] **Step 3: Run frontend lint**

```bash
docker compose run --rm frontend bash -c "npm run lint 2>&1 | tail -20"
```
Expected: No lint errors

- [ ] **Step 4: Commit if fixes were needed**

```bash
git add -A && git commit -m "chore: fix tests and lint after Voice Library 2.0 changes"
```

---

### Verification checklist

- [ ] VoiceCard shows creation source badge (all types)
- [ ] VoiceDetailsDrawer has four tabs: Overview, Source, Variants, Artifacts
- [ ] Overview tab shows creation source label prominently
- [ ] Source tab shows asset metadata or "no source" message
- [ ] Variants tab shows compatibility matrix table with status per model
- [ ] Artifacts tab shows version list with active marker and rollback button
- [ ] Rollback button triggers POST to backend and refreshes data
- [ ] Variant Dashboard toggle shows cross-voice matrix
- [ ] Variant Dashboard summary numbers match actual data
- [ ] "Coming soon" tabs are removed (or show meaningful empty states)
- [ ] All 258+ backend tests pass
- [ ] Frontend builds with no errors
