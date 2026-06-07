"use client"

import { useState } from "react"
import { Heart, Pencil, Trash2, Wand2, Copy, Check, Code2, ChevronDown, ChevronRight, Loader2, Plus, Music2 } from "lucide-react"
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { AudioPlayer } from "@/components/AudioPlayer"
import { UseInApiDialog } from "@/components/api/UseInApiDialog"
import { VariantManager } from "@/components/voice/VariantManager"
import { ModelCompatibilitySection } from "@/components/voice/ModelCompatibilitySection"
import { getVoiceAudioUrl } from "@/lib/api"
import { cn, formatDuration } from "@/lib/utils"
import type { AnyVoice, VoiceProfile } from "@/types"
import { isVoiceProfile, isTemporaryVoice } from "@/types"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { setVoiceFavorite, importVoiceResource } from "@/lib/api"
import { useRouter } from "next/navigation"

interface VoiceDetailPanelProps {
  voice: AnyVoice | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onUse?: (voice: VoiceProfile) => void
  onEdit?: (voice: VoiceProfile) => void
  onDelete?: (voice: VoiceProfile) => void
}

const SOURCE_LABELS: Record<string, { label: string; className: string }> = {
  SOURCE_ASSET: { label: "Cloned", className: "bg-blue-500/10 text-blue-600 border-blue-500/20" },
  PRESET_VOICE: { label: "Preset", className: "bg-purple-500/10 text-purple-600 border-purple-500/20" },
  MARKETPLACE_VOICE: { label: "Marketplace", className: "bg-amber-500/10 text-amber-600 border-amber-500/20" },
  TRAINED_VOICE: { label: "Trained", className: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20" },
  IMPORTED_VOICE: { label: "Imported", className: "bg-violet-500/10 text-violet-600 border-violet-500/20" },
  SYSTEM_VOICE: { label: "System", className: "bg-muted text-muted-foreground border-border" },
}

const SOURCE_AUDIO_CREATIONS = new Set(["SOURCE_ASSET", "TRAINED_VOICE"])

function hasSourceAudio(voice: AnyVoice): voice is VoiceProfile {
  return isVoiceProfile(voice) && SOURCE_AUDIO_CREATIONS.has(voice.creation_source) && voice.source_asset != null
}

function hasTranscript(voice: AnyVoice): boolean {
  return isVoiceProfile(voice) && voice.creation_source !== "PRESET_VOICE" && !!voice.transcript
}

function hasProvider(voice: AnyVoice): string | null {
  if (isTemporaryVoice(voice)) return voice.provider_id
  if (isVoiceProfile(voice) && voice.meta?.provider != null) return String(voice.meta.provider)
  return null
}

function isSourceAssetVoice(voice: AnyVoice): voice is VoiceProfile {
  return isVoiceProfile(voice) && voice.creation_source === "SOURCE_ASSET"
}

function isTrainedVoice(voice: AnyVoice): voice is VoiceProfile {
  return isVoiceProfile(voice) && voice.creation_source === "TRAINED_VOICE"
}

function isPresetVoice(voice: AnyVoice): boolean {
  return isTemporaryVoice(voice) || (isVoiceProfile(voice) && voice.creation_source === "PRESET_VOICE")
}

function isVisionVoice(voice: AnyVoice): boolean {
  return isTemporaryVoice(voice)
}

function getIdentityBadge(voice: AnyVoice): { label: string; className: string } | null {
  if (isTemporaryVoice(voice)) {
    return { label: "Preset", className: "bg-purple-500/10 text-purple-600 border-purple-500/20" }
  }
  const src = voice.creation_source
  return src ? (SOURCE_LABELS[src] ?? { label: src, className: "" }) : null
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-1.5 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-foreground/90">{value}</span>
    </div>
  )
}

function Section({
  title,
  open: defaultOpen = true,
  children,
}: {
  title: string
  open?: boolean
  children: React.ReactNode
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  if (!children) return null

  return (
    <div className="border-b border-border last:border-b-0">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center gap-2 px-6 py-3 text-caption uppercase tracking-wide hover:bg-muted/30 transition-colors"
      >
        {isOpen ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        {title}
      </button>
      {isOpen && <div className="px-6 pb-4">{children}</div>}
    </div>
  )
}

export function VoiceDetailPanel({ voice, open, onOpenChange, onUse, onEdit, onDelete }: VoiceDetailPanelProps) {
  const [copied, setCopied] = useState(false)
  const [apiOpen, setApiOpen] = useState(false)
  const [importing, setImporting] = useState(false)
  const queryClient = useQueryClient()
  const router = useRouter()

  const toggleFav = useMutation({
    mutationFn: ({ id, value }: { id: string; value: boolean }) => setVoiceFavorite(id, value),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["voices-page"] })
      queryClient.invalidateQueries({ queryKey: ["voices"] })
    },
  })

  if (!voice) return null

  const profile = isVoiceProfile(voice) ? voice : null
  const tempVoice = isTemporaryVoice(voice) ? voice : null
  const badge = getIdentityBadge(voice)
  const previewable = profile
    ? profile.preview_summary.origin !== "none" || (profile.audio_duration ?? 0) > 0
    : !!tempVoice?.preview_audio_url

  const hasProv = hasProvider(voice)

  const handleImport = async () => {
    if (!tempVoice) return
    setImporting(true)
    try {
      await importVoiceResource(tempVoice.source_resource_id)
      queryClient.invalidateQueries({ queryKey: ["voices-page"] })
      queryClient.invalidateQueries({ queryKey: ["voices"] })
    } finally {
      setImporting(false)
    }
  }

  return (
    <>
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent side="right" className="w-full sm:max-w-md p-0 flex flex-col">
          <SheetHeader className="border-b border-border px-6 py-4">
            <div className="flex items-start justify-between">
              <div className="space-y-1 min-w-0">
                <SheetTitle className="truncate">{voice.name}</SheetTitle>
                <div className="flex items-center gap-2">
                  {badge && (
                    <Badge variant="outline" className={cn("px-2 py-0.5", badge.className)}>
                      {badge.label}
                    </Badge>
                  )}
                  {voice.language && (
                    <span className="text-sm text-muted-foreground">{voice.language}</span>
                  )}
                </div>
              </div>
              {profile && (
                <Button
                  variant="ghost"
                  size="icon"
                  className={cn("shrink-0", profile.is_favorite && "text-red-500 hover:text-red-600")}
                  onClick={() => toggleFav.mutate({ id: profile.id, value: !profile.is_favorite })}
                  disabled={toggleFav.isPending}
                  title={profile.is_favorite ? "Remove from favorites" : "Add to favorites"}
                >
                  <Heart className={cn("h-5 w-5", profile.is_favorite && "fill-current")} />
                </Button>
              )}
            </div>
          </SheetHeader>

          <div className="flex-1 overflow-y-auto divide-y divide-border">
            <Section title="Overview">
              <div className="space-y-3">
                {voice.description && (
                  <p className="text-sm text-foreground/90 leading-relaxed">{voice.description}</p>
                )}

                {hasProv && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">Provider:</span>
                    <Badge variant="secondary" className="gap-1 text-xs">{hasProv}</Badge>
                  </div>
                )}

                {isSourceAssetVoice(voice) && voice.source_asset && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">Source:</span>
                    <span className="text-xs text-foreground/70">
                      {voice.source_asset.original_filename ?? "Unknown source"}
                    </span>
                  </div>
                )}

                <div className="rounded-lg border border-border bg-surface px-3 divide-y divide-border">
                  <MetaRow
                    label="Language"
                    value={[voice.language, profile?.language_code ? `(${profile.language_code})` : null].filter(Boolean).join(" ") || "Auto"}
                  />
                  {profile && <MetaRow label="Usage count" value={String(profile.usage_count)} />}
                  {profile && <MetaRow label="Created" value={new Date(profile.created_at).toLocaleString()} />}
                  {profile && <MetaRow label="Last used" value={profile.last_used_at ? new Date(profile.last_used_at).toLocaleString() : "Never"} />}
                  {previewable && profile && <MetaRow label="Duration" value={formatDuration(profile.audio_duration)} />}
                </div>

                {hasTranscript(voice) && (
                  <div className="space-y-1">
                    <p className="text-caption uppercase tracking-wide">Transcript</p>
                    <p className="text-sm text-foreground/90 leading-relaxed">{voice.transcript}</p>
                  </div>
                )}

                {profile?.preset_tags && profile.preset_tags.length > 0 && (
                  <div className="space-y-1">
                    <p className="text-caption uppercase tracking-wide">Tags</p>
                    <div className="flex flex-wrap gap-1.5">
                      {profile.preset_tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">{tag}</Badge>
                      ))}
                    </div>
                  </div>
                )}

                {hasSourceAudio(voice) && (
                  <div className="rounded-lg border border-border bg-surface p-3 space-y-1.5">
                    <div className="flex items-center gap-1.5">
                      <Music2 className="h-3.5 w-3.5 text-muted-foreground" />
                      <p className="text-caption uppercase tracking-wide">Source Audio</p>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {voice.source_asset!.original_filename ?? "Untitled source"} &middot;{" "}
                      {voice.source_asset!.audio_duration ? formatDuration(voice.source_asset!.audio_duration) : "\u2014"}
                    </p>
                    <AudioPlayer
                      audioUrl={getVoiceAudioUrl(voice.id)}
                      title="Source audio"
                      duration={voice.audio_duration ?? undefined}
                    />
                  </div>
                )}
              </div>
            </Section>

            {previewable && (
              <Section title="Previews">
                <AudioPlayer
                  audioUrl={profile ? getVoiceAudioUrl(profile.id) : tempVoice!.preview_audio_url!}
                  title="Preview audio"
                  duration={profile?.audio_duration ?? undefined}
                />
              </Section>
            )}

            <Section title="Compatible Models">
              {profile ? (
                <ModelCompatibilitySection
                  voice={profile}
                  primaryModelId={profile.primary_model_id}
                  recommendedModelId={profile.recommended_model_id}
                />
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {voice.compatible_models.length > 0 ? (
                    voice.compatible_models.map((modelId) => (
                      <Badge key={modelId} variant="outline" className="text-xs">{modelId}</Badge>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">No compatibility info available</p>
                  )}
                </div>
              )}
            </Section>

            {profile && (
              <Section title="Variants" open={false}>
                <VariantManager publicVoiceId={profile.public_voice_id} />
              </Section>
            )}
          </div>

          <div className="border-t border-border p-4 flex items-center gap-2">
            {profile ? (
              <>
                {onUse && (
                  <Button className="flex-1 gap-2" onClick={() => onUse(profile)}>
                    <Wand2 className="h-4 w-4" /> Use voice
                  </Button>
                )}
                <Button variant="outline" size="icon" onClick={() => setApiOpen(true)} title="Use in API">
                  <Code2 className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="icon" onClick={() => {
                  navigator.clipboard?.writeText(profile.public_voice_id).then(() => {
                    setCopied(true)
                    setTimeout(() => setCopied(false), 1500)
                  })
                }} title="Copy voice ID">
                  {copied ? <Check className="h-4 w-4 text-success" /> : <Copy className="h-4 w-4" />}
                </Button>
                {onEdit && (
                  <Button variant="outline" size="icon" onClick={() => onEdit(profile)} title="Edit">
                    <Pencil className="h-4 w-4" />
                  </Button>
                )}
                {onDelete && (
                  <Button variant="outline" size="icon" className="text-error hover:text-error" onClick={() => onDelete(profile)} title="Delete">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </>
            ) : (
              <Button className="flex-1 gap-2" onClick={handleImport} disabled={importing}>
                {importing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                Import to Library
              </Button>
            )}
          </div>
        </SheetContent>
      </Sheet>
      {profile && (
        <UseInApiDialog voiceId={profile.public_voice_id} open={apiOpen} onOpenChange={setApiOpen} />
      )}
    </>
  )
}
