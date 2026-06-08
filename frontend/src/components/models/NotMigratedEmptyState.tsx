const MIGRATION_PHASE: Record<string, string> = {
  "omnivoice-base": "Phase 6 — OmniVoice migration",
  "omnivoice-singing": "Phase 6 — OmniVoice migration",
  "omnivoice-singing-emotion": "Phase 6 — OmniVoice migration",
  "fish-audio-s2": "Deferred — hardware blocker (codec/VRAM)",
  "fish-s2-pro": "Deferred — hardware blocker (codec/VRAM)",
  "f5-tts": "Phase 4 — F5-TTS reference",
  "xtts": "Future",
  "openvoice": "Future",
}

export function NotMigratedEmptyState({ modelId }: { modelId: string }) {
  const phase = MIGRATION_PHASE[modelId] ?? "Future runtime migration"
  return (
    <div className="rounded-md border border-dashed border-border bg-surface-2 p-3 space-y-1">
      <p className="text-sm font-medium text-foreground">Runtime Not Migrated</p>
      <p className="text-xs text-muted-foreground">
        This model is in the catalog, but its runtime-registry entry does not exist yet. Migration is scheduled —
        {" "}{phase}.
      </p>
    </div>
  )
}
