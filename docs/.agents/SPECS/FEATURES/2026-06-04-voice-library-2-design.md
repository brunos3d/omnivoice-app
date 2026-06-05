# Voice Library 2.0 — Design Document

**Status:** Draft for review
**Date:** 2026-06-04
**Deciders:** Bruno Silva (product owner)

---

## 1. Current-State Analysis (Phase 1 — Product Discovery)

### 1.1 What exists

The Voice Library (`/voices` page) is a working CRUD application for voice management:

**Frontend UI:**
- Cursor-paginated voice grid (24/page) — name, avatar, language badge, duration, characteristics chips, favorite star, preview play, copy Voice ID, usage count
- Four scope tabs: My Voices (active), Community (coming soon), Preset (coming soon), Recently Used (filter)
- FilterBar: search, favorites-only chip, language/gender/age/accent filters
- VoiceDetailsDrawer: Voice ID copy, audio player, description, transcript, metadata (language, usage, timestamps, duration), characteristics badges, preset tags, generation defaults, VariantManager
- VoiceEditDialog: name, transcript, language, voice design, generation defaults, audio replacement
- VoiceCard actions: preview play, favorite star, edit, delete, copy Voice ID
- VariantManager (in details drawer): per-model variant status list with Build/Rebuild buttons, status icons, version badge, error messages

**Backend:**
- Full `VoiceProfile` / `Voice` / `VoiceVariant` / `VoiceVariantArtifact` / `VoiceSourceAsset` chain implemented
- `mirror_profile_to_split` keeps Voice/VoiceVariant in sync with VoiceProfile on create/update/delete
- Variant lifecycle API: `GET/POST /voices/{id}/variants`, rebuild, rollback, artifact version listing
- `PeakVoxRuntime`: `build_variant`, `rebuild_variant`, `ensure_variant`, `get_variant_status`
- 258 passing tests

### 1.2 What is missing

| Gap | Impact |
|---|---|
| Frontend consumes `VoiceProfile` not `Voice` | `creation_source`, `source_assets`, and split-table metadata invisible |
| `creation_source` never rendered | Users cannot distinguish cloned voices from presets |
| No Source Asset visible | Voice provenance invisible; no rebuild-from-source concept |
| No artifact version browser | `fetchArtifactVersions` in `api.ts` exists but never called; no way to inspect older builds |
| No rollback UI | `rollbackVariant` in `api.ts` exists but never called; no way to revert a bad rebuild |
| VariantManager in details drawer only | No variant dashboard; variant status inaccessible at a glance |
| Community/Preset tabs show "coming soon" | Empty UI surface; no value |
| Generation uses `voice_profile_id` | Backend handles normalization but frontend sends legacy field |
| Runtime status invisible | No health/load/available-models indicators in the voice context |
| Source Asset metadata not exposed | `VoiceSourceAsset` table written but no UI anywhere |

### 1.3 What backend functionality exists but is hidden from the UI

- `GET /voices/{id}/variants/{model_id}/artifacts` — artifact version list
- `POST /voices/{id}/variants/{model_id}/rollback/{version}` — rollback to prior version
- `GET /voices/{public_voice_id}/variants` — full variant list with status
- `POST /voices/{public_voice_id}/variants/{model_id}` — build/ensure variant
- VoiceSourceAsset rows written on create — no reader endpoint needed initially

---

## 2. Design Approaches (Phase 2 — Brainstorming)

### Approach A: Voice Consumption Optimized

Focus: the **generation use case** — find a voice, pick a model, generate. Variants and artifacts are hidden behind "Advanced" affordances.

| Aspect | Detail |
|---|---|
| **Tabs** | All Voices (default), Favorites, Recently Used. No Community/Preset tabs. |
| **Voice card** | Play, select, favorite, copy ID. No variant badge. |
| **Voice details** | Audio player, metadata, generation defaults. Variant status as tiny indicator in footer. |
| **Variant access** | "Runtime Details" expandable section — collapsed by default |
| **Artifacts** | Not shown. Rollback via "Restore" in Runtime Details. |

**Pros:** Simplest UX. Fast path for generation. No user confusion about variants.

**Cons:** Hides PeakVox's core differentiator (Universal Voice Runtime). Power users cannot inspect variant health. No variant-as-product concept. Contradicts ADR-0010 §6 (CE must expose variant state).

**ADR alignment:** Weak. ADR-0010 §6 requires CE to surface per-voice variant status. Hiding it contradicts the CE-hardware-aware principle.

**Vision alignment:** Weak. A Universal Voice Runtime whose runtime state is invisible is a contradiction.

---

### Approach B: Runtime Management Optimized

Focus: the **operator/developer use case** — inspect variants, manage artifacts, monitor builds, track model compatibility. Generation is one action among many.

| Aspect | Detail |
|---|---|
| **Tabs** | My Voices, Variants (cross-voice), Artifacts, Models (health) |
| **Voice card** | Status badge count (e.g. "3/4 models ready"), variant indicator per model |
| **Voice details** | Full variant matrix as primary content. Source Asset section. Artifact timeline. |
| **Variant access** | First-class — each variant is a row with status, version, build time, error |
| **Artifacts** | Version list with active marker, rollback button, rebuild button |

**Pros:** Full transparency. Power-user dream. Complete ADR-0010 §6 compliance.

**Cons:** Overwhelming for simple users. Generation path buried. Risk of "variant" becoming a user-facing concept too early.

**ADR alignment:** Strong on ADR-0010 §6. Risk of violating ADR-0004 (variant internals leaking to users who don't need them).

**Vision alignment:** Correct but premature. The Runtime is the product, but the *user* is a creator, not an operator. Over-indexing on runtime management creates an ops tool, not a voice product.

---

### Approach C: Hybrid Model (Recommended)

Focus: **progressive disclosure** — simple for generation, powerful for management. Every layer is visible but not overwhelming.

| Aspect | Detail |
|---|---|
| **Tabs** | My Voices (default, grid), Inactive: Community / Preset / Marketplace (architecture markers only) |
| **Voice card** | Variant availability indicator (e.g. "3 models" badge), clickable |
| **Voice details** | Tabbed panel: Overview, Source Asset, Variants, Artifacts |
| **Variant access** | Variants tab shows a **compatibility matrix** — models × status, with Build/Rebuild per cell |
| **Artifacts** | Artifacts tab shows version timeline (if >1 version) with active marker + rollback |
| **Model status** | "Supported Models" section in details — which models can render this voice |
| **Creation source** | Badge on voice card: "Source Audio" / "Preset" / etc. |
| **Generation** | VoiceSelector in TTS panel shows variant availability inline without details drawer |

**Pros:** Progressive disclosure. All ADR-0010 §6 requirements met. Power users get full runtime visibility. Simple users ignore advanced tabs. Natural Marketplace integration point. Each layer maps to a real concept.

**Cons:** More UI surface to build. Tabbed details panel is a new pattern.

**ADR alignment:** Strong. ADR-0001 (Voice identity visible), ADR-0004 (variant internals behind tabs, not leaked), ADR-0006 (realization types shown as labels), ADR-0008 (variant lifecycle visible), ADR-0009 (artifact versions accessible but not primary), ADR-0010 (Source Asset visible, CE variant status per §6), ADR-0011 (creation_source badge on every voice).

**Vision alignment:** Strong. A Universal Voice Runtime whose management surface matches its architecture.

---

## 3. Voice Library 2.0 Design (Phase 3)

### 3.1 Goals

1. Expose the full `Voice → Source Asset → Variant → Artifact → Generation` chain in the UI with progressive disclosure
2. Surface `creation_source` at every level (card, details, selector)
3. Make variant status visible per voice (ADR-0010 §6 CE requirement)
4. Add artifact version browser and rollback UI
5. Replace "coming soon" Community/Preset tabs with architecture-accurate placeholders
6. Maintain the fast generation path — Voice Library 2.0 must not regress TTS panel performance
7. All backend APIs and types already exist — no new backend endpoints required

### 3.2 Non-goals

- Marketplace implementation (Cloud-deferred)
- Community voices (Cloud-deferred)
- Preset voice provisioning beyond Kokoro (future)
- Auth/billing/creators
- Async variant build queue (deferred to platform scale)

### 3.3 Information Architecture

```
Voice Library 2.0  (/voices)
│
├─ Tabs: [My Voices] [Community - future] [Preset - future] [Marketplace - future]
│
├─ VoiceCard (grid)
│   ├─ Avatar (initials)
│   ├─ Name
│   ├─ Creation Source badge ("Source Audio" / "Preset")
│   ├─ Variant indicator (e.g. "✓ 2 models" with color dot per model)
│   ├─ Language badge
│   ├─ Characteristics chips (truncated)
│   ├─ Preview play button
│   ├─ Favorite star
│   ├─ Usage count
│   └─ Copy Voice ID
│
├─ VoiceDetailsDrawer (right panel, tabbed)
│   ├─ Tab 1: Overview
│   │   ├─ Audio player (reference preview)
│   │   ├─ Name, Description, Transcript
│   │   ├─ Creation Source label + info
│   │   ├─ Metadata: language, duration, created, updated, usage count
│   │   ├─ Characteristics badges
│   │   ├─ Generation defaults summary
│   │   └─ Edit / Delete actions
│   │
│   ├─ Tab 2: Source Asset
│   │   ├─ Status: Present / None
│   │   ├─ Filename, size, audio duration, content type
│   │   ├─ Asset type label
│   │   └─ "Rebuild All Variants from Source" button (when variant rebuild needed)
│   │
│   ├─ Tab 3: Variants (compatibility matrix)
│   │   ├─ Table: Model | Status | Realization Type | Version | Actions
│   │   ├─ Per row: Build/Rebuild, Build progress, Error details
│   │   └─ Model availability indicator (installed, edition-available, not installed)
│   │
│   └─ Tab 4: Artifacts
│       ├─ Version list (when >1 version exists)
│       ├─ Active marker per version
│       ├─ Version metadata: created, model version, size
│       ├─ Rollback button (to prior version)
│       └─ Prune button (CE retention policy)
│
└─ Empty states
    ├─ No voices: CTA to create first voice
    ├─ No variants: "This voice has no built variants. Go to Variants tab to build."
    └─ No artifacts: "No previous versions — only the active build exists."
```

### 3.4 Navigation Structure

The `/voices` page retains its top-level route. The sidebar nav item "Voice Library" is unchanged.

Within the page:
- **Top bar:** Scope tabs (My Voices default), FilterBar, "Create Voice" button
- **Main area:** VoiceGrid (responsive, skeleton-loading)
- **Right panel:** VoiceDetailsDrawer (opened by clicking any voice card)
- **Drawer tabs:** Overview | Source Asset | Variants | Artifacts

### 3.5 Voice Details Panel

The existing `VoiceDetailsDrawer` gains tabs. The current single-scroll design becomes a tabbed layout:

**Tab 1 — Overview:** Mirrors the current drawer content: audio player, identity metadata, characteristics, generation defaults. The new addition is a prominent **Creation Source** label at the top.

**Tab 2 — Source Asset:** Shows the `VoiceSourceAsset` provenance. If a source asset exists: filename, duration, size, content type, upload date, storage key (truncated). If no source asset (e.g. preset voice): "Not applicable — this voice is a preset" message.

**Tab 3 — Variants (Compatibility Matrix):** A table where columns = models, rows = this voice's variants. Shows: model name, status badge, realization type label, current artifact version, actions. The existing `VariantManager` logic flows into this tab.

**Tab 4 — Artifacts:** A timeline of artifact versions for the currently selected variant. Each entry: version number, creation date, model version at build time, active indicator, rollback button (non-active versions only). Prune button for CE retention cleanup.

### 3.6 Variant Dashboard (Phase 2 in the priority list)

A **dedicated Variant Dashboard** lives inside the VoicesLibrary page as a secondary view — accessible via a toggle button ("Library View" / "Variant View") or as a link from the Variants tab in details.

Contents:
- **Cross-voice variant summary table:** All voices × all models
- **Status badges per cell:** ready (green), building (spinner), pending (gray), failed (red), deprecated (yellow)
- **Bulk actions:** "Build Variant for all voices on model X" (when a model is newly installed)
- **Filter by status:** Show only failed/pending variants
- **Summary header:** X voices, Y models, Z variants ready, W failed

This view is **opt-in** — accessed via a "Variants" header button, not the default view.

### 3.7 Artifact History

The Artifacts tab in the VoiceDetailsDrawer provides:
- Version list sorted descending by creation date
- Each item: `v{N}`, created date, model version tag, size, active badge
- **Rollback action**: "Set as active" button on any non-active version triggers `POST /variants/{model_id}/rollback/{version}`
- **Prune action**: "Remove old versions" button triggers `GET && prune` for CE retention

If only one version exists: message "No previous versions to show. Rebuild this variant to create version history."

### 3.8 Creation Source Visibility

Every voice card shows a **small badge** indicating its origin:

| `creation_source` | Badge label | Color |
|---|---|---|
| `SOURCE_ASSET` | "Source Audio" | Slate/blue |
| `PRESET_VOICE` | "Preset" | Amber |
| `MARKETPLACE_VOICE` | "Marketplace" | (hidden until Cloud) |
| `TRAINED_VOICE` | "Trained" | (reserved) |
| `IMPORTED_VOICE` | "Imported" | (reserved) |
| `SYSTEM_VOICE` | "System" | (reserved) |
| unknown/null | "—" | (legacy fallback) |

In the details drawer Overview tab, the creation source is displayed as a prominent label with a short explanatory text.

### 3.9 Source Asset Visibility

Source Asset is visible in Tab 2 of the details drawer and **not** on the card or the TTS selector. This preserves progressive disclosure — basic users never encounter it.

### 3.10 Runtime Status Visibility

Within each variant row in the Variants tab:
- **Model availability indicator:** Installed + Active (full color), edition-available but not installed (dimmed with "Not installed" label), not available in edition (grayed with lock icon)
- **Runtime health:** Not shown per-variant (that's a system-level concern, deferred to Runtime Observability — Phase 4 of this priority list)

### 3.11 Supported Models Section

The Variants tab doubles as the "Supported Models" section — it literally lists every model and whether a variant exists for it. No separate section needed.

### 3.12 Variant Compatibility Matrix

The compatibility matrix is the core of the Variants tab:

```
                    Status              Realization     Artifact    Actions
─────────────────────────────────────────────────────────────────────────────
OmniVoice          ✓ ready             reference_sample  v3          [Rebuild]
OmniVoice Singing  ✓ ready             reference_sample  v2          [Rebuild]
Fish Audio         ✗ failed            speaker_embedding —           [Retry]
Kokoro             — not installed     voice_pack        —           [Install]
```

Each row shows:
- **Model name** (with provider icon)
- **Status** with icon + color
- **Realization type** (from `realization_type` on the variant, else inferred from model capabilities)
- **Active artifact version** (or `—` if none)
- **Action button**: Build (pending/none), Rebuild (ready/deprecated), Retry (failed)

### 3.13 Model Availability Indicators

In the compatibility matrix, models appear if they meet any of:
1. **Installed + available in edition** — full row
2. **Installed but not in edition** — dimmed, "Not available in this edition" tooltip
3. **Not installed but available in edition** — dimmed, "Install in Model Library" link
4. **Not available in any edition** — hidden (noise reduction)

### 3.14 Future Marketplace Integration Points

The tab bar already has a reserved "Marketplace" tab. The details drawer Overview tab has a footer area reserved for marketplace metadata (price, creator attribution, usage stats) — rendered only when `PlatformFeatures.marketplace` is enabled.

### 3.15 Future Cloud Integration Points

- **Source Asset tab** — Cloud adds asset management (replace, version, delete)
- **Artifact tab** — Cloud adds indefinite retention pinning
- **Variants tab** — Cloud hides the tab entirely (ADR-0010 §7: Cloud abstracts variants)
- **Creation Source** — Cloud adds `MARKETPLACE_VOICE` type with click-through attribution

---

## 4. Runtime Observability Exploration (Phase 4)

### 4.1 Where it fits

A Runtime dashboard is distinct from the Voice Library. It belongs under a **Runtime** navigation item in the sidebar, between "Models" and "Voice Library" (or as a subsection of "Models").

### 4.2 What it would show

```
Runtime Dashboard  (/runtime)
│
├─ Providers
│   ├─ Provider name, adapter version, status (healthy/degraded/down)
│   ├─ Models per provider + their status
│   └─ Last health check
│
├─ Models
│   ├─ Model list with status (loaded/unloaded/error)
│   ├─ VRAM usage per loaded model
│   ├─ Load/unload actions
│   └─ Model version + capability summary
│
├─ Variants
│   ├─ Cross-voice variant health (already covered by Voice Library 2.0 Variant Dashboard)
│   │  This section would be the same as the Variant Dashboard proposed above.
│   └─ Could redirect to Voice Library 2.0 Variant view
│
├─ Artifacts
│   ├─ Storage usage per voice/model
│   ├─ Retention policy status
│   └─ Pruning actions
│
├─ Generation Queue
│   ├─ Active jobs (currently processing)
│   ├─ Pending jobs (queued)
│   ├─ Failed/recently completed
│   └─ Per-job: voice, model, status, duration, error
│
└─ System
    ├─ GPU: model, VRAM total/used, temperature, utilization
    ├─ Storage: data directory usage
    └─ Runtime version + uptime
```

### 4.3 Relationship to Voice Library 2.0

The Runtime Dashboard and Voice Library 2.0 overlap in the **Variants** area. Recommendation: the Variant Dashboard (cross-voice variant status) lives in Voice Library 2.0 as a secondary view, not in Runtime Dashboard. The Runtime Dashboard focuses on:

- **System-level** concerns (GPU, storage, provider health, queue depth)
- **Not** per-voice variant management (that belongs to the Voice Library)

This separation keeps responsibility clear: Voice Library = voice-level management, Runtime Dashboard = infrastructure-level management.

### 4.4 Implementation recommendation

**Do not implement** a full Runtime Dashboard in this phase. Defer to a dedicated CE hardening phase after Voice Library 2.0, Kokoro, and ADR-0012 are complete. The one exception: a **Generation Queue mini-dashboard** added to the bottom of the existing History page could ship as CE prep work with minimal backend changes.

---

## 5. ADR Alignment Review (Phase 6 — Self-Review)

| ADR | Requirement | How Design Meets It |
|---|---|---|
| ADR-0001 | Voice is the identity spine; public_voice_id is permanent | VoiceCard prominently displays Voice ID + copy button. Overview tab centers voice identity. |
| ADR-0004 | Variant internals never leak into public API | Source Asset, Variants, Artifacts tabs are opt-in disclosure. Card/selector show only status, never realization internals. |
| ADR-0006 | Realization types are visible but not primary | Realization type shown as label in Variants tab matrix. Not on card, not in selector. |
| ADR-0008 | Five-state lifecycle visible; Build/Rebuild actions | Variant status icons + Build/Rebuild/Retry per row. Full state visualization. |
| ADR-0009 | Artifact versions exist but active pointer is what matters | Artifacts tab shows timeline with active marker. Rollback is a deliberate action. |
| ADR-0010 §6 | CE variant state explicit; block-on-missing; Source Asset visible | Source Asset tab authenticated. Variant status per row. CE block-on-missing already in backend (P4). |
| ADR-0011 | Creation Source visible; model-independent origin badge | Badge on every card + prominent label in details. |

### 5.1 Verifications

- **No architecture drift:** Each UI element maps to a real domain concept (Voice, VoiceSourceAsset, VoiceVariant, VoiceVariantArtifact). No new entities invented.
- **No Voice/Variant collapse:** Voice identity is the primary navigation axis. Variants are a sub-section of a voice, never promoted to the same level.
- **No Artifact leakage into public API:** Artifact versions are behind a tab. The card, selector, and generation path never expose artifact internals.
- **No Marketplace assumptions:** Marketplace tab is a reserved, non-functional tab. `MARKETPLACE_VOICE` creation source is documented but not rendered.
- **No SaaS assumptions:** No auth, billing, creator, credit, or Cloud concepts appear in any UI path.

---

## 6. Implementation Recommendations (Phase 5)

### 6.1 Execution order

1. **Frontend: Creation Source badge** — Add `creation_source` rendering to VoiceCard + details. Read `creation_source` from `VoiceProfileResponse` (already serialized from P3).
2. **Frontend: Tabbed VoiceDetailsDrawer** — Refactor the single-scroll drawer into a tabbed panel. Create the Source Asset tab (read-only, uses existing backend data).
3. **Frontend: Variants compatibility matrix** — Refactor `VariantManager` into a table component for the Variants tab. Add model availability indicators.
4. **Frontend: Artifact version browser** — Wire up `fetchArtifactVersions` + new UI component for the Artifacts tab. Add rollback button.
5. **Frontend: Variant Dashboard** — Add "Variants" toggle to the Voice Library page for cross-voice variant view.
6. **Cleanup: Remove "coming soon" tabs** — Replace Community/Preset/Marketplace tabs with architecture-accurate reserved-until-future state (or remove them entirely and add a single "All Voices" filter).

### 6.2 No new backend endpoints required

All data flows through existing routes:
- `GET /voices` → `VoiceProfileResponse.creation_source`
- `GET /voices/{id}` → full voice details
- `GET /voices/{id}/variants` → variant list with status
- `GET /voices/{id}/variants/{model}/artifacts` → artifact version list
- `POST /voices/{id}/variants/{model}/rebuild` → trigger rebuild
- `POST /voices/{id}/variants/{model}/rollback/{version}` → rollback

### 6.3 Backend changes (minimal)

- **Source Asset endpoint** (optional): `GET /voices/{id}/source-asset` to read `VoiceSourceAsset` metadata. Or inline it in the voice response. Recommendation: inline a `source_asset` field on the voice response to avoid a new round trip.

### 6.4 Test strategy

- Tests for new components follow the existing pattern (React Testing Library for UI, Vitest for logic)
- No new backend tests needed (no backend changes beyond optional source-asset field)
- Variant state rendering: test each status icon renders correctly
- Artifact version list: test active marker, rollback button presence
- Creation Source badge: test each source type renders correct label
- Tab routing: test each tab renders correct content

---

## 7. Suggested Execution Plan

```
Week 1: Creation Source badge + Tabbed Details Drawer
Week 2: Source Asset tab + Variant compatibility matrix
Week 3: Artifact version browser + Variant Dashboard toggle
Week 4: Polish, edge cases, tests, cleanup
```

Each item is independently shippable. No item breaks existing functionality.

---

*End of design document. Ready for review.*
