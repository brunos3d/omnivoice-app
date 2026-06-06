"use client"

import { useState } from "react"
import { Pencil, Trash2, Wand2, Copy, Check, Code2 } from "lucide-react"
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { AudioPlayer } from "@/components/AudioPlayer"
import { UseInApiDialog } from "@/components/api/UseInApiDialog"
import { VariantManager } from "@/components/voice/VariantManager"
import { ArtifactHistory } from "@/components/voice/ArtifactHistory"
import { ModelCompatibilitySection } from "@/components/voice/ModelCompatibilitySection"
import { SourceAssetTab } from "@/components/voice/SourceAssetTab"
import { getVoiceAudioUrl } from "@/lib/api"
import { cn, formatDuration } from "@/lib/utils"
import type { VoiceProfile } from "@/types"

interface VoiceDetailsDrawerProps {
  voice: VoiceProfile | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onUse?: (voice: VoiceProfile) => void
  onEdit?: (voice: VoiceProfile) => void
  onDelete?: (voice: VoiceProfile) => void
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-1.5 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-foreground/90">{value}</span>
    </div>
  )
}

const CHARACTERISTIC_LABELS: Record<string, string> = {
  gender: "Gender",
  age_group: "Age",
  accent: "Accent",
  pitch: "Pitch",
  speaking_speed: "Speed",
  emotional_range: "Emotion",
}

const CREATION_SOURCE_LABELS: Record<string, { label: string; className: string }> = {
  SOURCE_ASSET: { label: "Cloned", className: "bg-blue-500/10 text-blue-600 border-blue-500/20" },
  PRESET_VOICE: { label: "Preset", className: "bg-purple-500/10 text-purple-600 border-purple-500/20" },
  MARKETPLACE_VOICE: { label: "Marketplace", className: "bg-amber-500/10 text-amber-600 border-amber-500/20" },
  TRAINED_VOICE: { label: "Trained", className: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20" },
  IMPORTED_VOICE: { label: "Imported", className: "bg-violet-500/10 text-violet-600 border-violet-500/20" },
  SYSTEM_VOICE: { label: "System", className: "bg-muted text-muted-foreground border-border" },
}

function usePreviewable(voice: VoiceProfile): boolean {
  return voice.preview_summary
    ? voice.preview_summary.origin !== "none"
    : (voice.audio_duration ?? 0) > 0
}

export function VoiceDetailsDrawer({ voice, open, onOpenChange, onUse, onEdit, onDelete }: VoiceDetailsDrawerProps) {
  const [copied, setCopied] = useState(false)
  const [apiOpen, setApiOpen] = useState(false)
  const isPreset = voice?.creation_source === "PRESET_VOICE"
  const previewable = voice ? usePreviewable(voice) : false

  const copyId = () => {
    if (!voice) return
    navigator.clipboard?.writeText(voice.public_voice_id).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }

  return (
    <>
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-md p-0">
        {voice && (
          <>
            <SheetHeader className="border-b border-border">
              <SheetTitle>{voice.name}</SheetTitle>
              <SheetDescription>
                {[voice.language, previewable ? formatDuration(voice.audio_duration) : null].filter(Boolean).join(" · ")}
              </SheetDescription>
            </SheetHeader>

            <Tabs defaultValue="overview" className="flex flex-col h-full">
              <div className="border-b border-border px-4 pt-4">
                <TabsList className={isPreset ? "grid grid-cols-3" : "grid grid-cols-4"}>
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  {!isPreset && <TabsTrigger value="source">Source</TabsTrigger>}
                  <TabsTrigger value="variants">Variants</TabsTrigger>
                  <TabsTrigger value="artifacts">Artifacts</TabsTrigger>
                </TabsList>
              </div>

              <div className="flex-1 overflow-y-auto">
                <TabsContent value="overview" className="p-6 space-y-6">
                  {voice.creation_source && (
                    <div className="flex items-center gap-2">
                      <span className="text-caption uppercase tracking-wide">Origin</span>
                      <Badge
                        variant="outline"
                        className={cn(
                          "px-2 py-0.5",
                          CREATION_SOURCE_LABELS[voice.creation_source]?.className
                        )}
                      >
                        {CREATION_SOURCE_LABELS[voice.creation_source]?.label ?? voice.creation_source}
                      </Badge>
                    </div>
                  )}

                  <div className="space-y-1">
                    <p className="text-caption uppercase tracking-wide">Voice ID</p>
                    <button
                      type="button"
                      onClick={copyId}
                      title="Copy Voice ID"
                      className="flex w-full items-center justify-between gap-2 rounded-lg border border-border bg-surface px-3 py-2 text-sm font-mono hover:bg-surface-2"
                    >
                      <span className="truncate">{voice.public_voice_id}</span>
                      {copied ? <Check className="h-4 w-4 shrink-0 text-success" /> : <Copy className="h-4 w-4 shrink-0 text-muted-foreground" />}
                    </button>
                  </div>

                  {previewable && !isPreset && (
                    <AudioPlayer audioUrl={getVoiceAudioUrl(voice.id)} title="Reference audio" duration={voice.audio_duration} />
                  )}
                  {isPreset && previewable && (
                    <AudioPlayer audioUrl={getVoiceAudioUrl(voice.id)} title="Provider audio" duration={voice.audio_duration} />
                  )}

                  {voice.description && (
                    <div className="space-y-1">
                      <p className="text-caption uppercase tracking-wide">Description</p>
                      <p className="text-sm text-foreground/90">{voice.description}</p>
                    </div>
                  )}

                  {isPreset && voice.meta?.provider != null && (
                    <div className="space-y-1">
                      <p className="text-caption uppercase tracking-wide">Provider</p>
                      <Badge variant="secondary" className="gap-1">
                        {String(voice.meta.provider)}
                      </Badge>
                    </div>
                  )}

                  {voice.transcript && !isPreset && (
                    <div className="space-y-1">
                      <p className="text-caption uppercase tracking-wide">Transcript</p>
                      <p className="text-sm text-foreground/90 leading-relaxed">{voice.transcript}</p>
                    </div>
                  )}

                  <div className="space-y-1">
                    <p className="text-caption uppercase tracking-wide">Metadata</p>
                    <div className="rounded-lg border border-border bg-surface px-3 divide-y divide-border">
                      <MetaRow
                        label="Language"
                        value={[voice.language, voice.language_code ? `(${voice.language_code})` : null].filter(Boolean).join(" ") || "Auto"}
                      />
                      <MetaRow label="Usage count" value={String(voice.usage_count)} />
                      <MetaRow label="Created" value={new Date(voice.created_at).toLocaleString()} />
                      <MetaRow label="Last used" value={voice.last_used_at ? new Date(voice.last_used_at).toLocaleString() : "Never"} />
                      {previewable && <MetaRow label="Duration" value={formatDuration(voice.audio_duration)} />}
                    </div>
                  </div>

                  <ModelCompatibilitySection publicVoiceId={voice.public_voice_id} />

                  {voice.characteristics && Object.values(voice.characteristics).some((v) => (Array.isArray(v) ? v.length : v)) && (
                    <div className="space-y-1">
                      <p className="text-caption uppercase tracking-wide">Voice characteristics</p>
                      <div className="flex flex-wrap gap-1.5">
                        {Object.entries(CHARACTERISTIC_LABELS).map(([key, label]) => {
                          const value = voice.characteristics?.[key as keyof typeof voice.characteristics]
                          if (!value || Array.isArray(value)) return null
                          return (
                            <Badge key={key} variant="secondary" className="gap-1 capitalize">
                              <span className="text-muted-foreground normal-case">{label}:</span> {value}
                            </Badge>
                          )
                        })}
                        {voice.characteristics.style_tags?.map((tag) => (
                          <Badge key={tag} variant="outline" className="capitalize">{tag}</Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {voice.preset_tags && voice.preset_tags.length > 0 && (
                    <div className="space-y-1">
                      <p className="text-caption uppercase tracking-wide">Preset tags</p>
                      <div className="flex flex-wrap gap-1.5">
                        {voice.preset_tags.map((tag) => (
                          <Badge key={tag} variant="outline">{tag}</Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {voice.generation_defaults && (
                    <div className="space-y-1">
                      <p className="text-caption uppercase tracking-wide flex items-center gap-1.5">
                        Generation defaults <Badge className="bg-primary/15 px-1.5 py-0 text-[10px] text-primary">preset</Badge>
                      </p>
                      <div className="rounded-lg border border-border bg-surface px-3 divide-y divide-border">
                        <MetaRow label="Steps" value={String(voice.generation_defaults.num_step)} />
                        <MetaRow label="Guidance" value={voice.generation_defaults.guidance_scale.toFixed(1)} />
                        <MetaRow label="Speed" value={voice.generation_defaults.speed ? `${voice.generation_defaults.speed}x` : "Auto"} />
                        <MetaRow label="Time shift" value={voice.generation_defaults.t_shift.toFixed(2)} />
                        <MetaRow label="Denoise" value={voice.generation_defaults.denoise ? "On" : "Off"} />
                        <MetaRow label="GPU" value={voice.generation_defaults.use_gpu ? "On" : "Off"} />
                      </div>
                    </div>
                  )}
                </TabsContent>

                {!isPreset && (
                  <TabsContent value="source" className="p-6 space-y-6">
                    <SourceAssetTab voice={voice} />
                  </TabsContent>
                )}

                <TabsContent value="variants" className="p-6 space-y-6">
                  <VariantManager publicVoiceId={voice.public_voice_id} />
                </TabsContent>

                <TabsContent value="artifacts" className="p-6 space-y-6">
                  <ArtifactHistory publicVoiceId={voice.public_voice_id} />
                </TabsContent>
              </div>
            </Tabs>

            <div className="border-t border-border p-4 flex items-center gap-2">
              {onUse && (
                <Button className="flex-1 gap-2" onClick={() => onUse(voice)}>
                  <Wand2 className="h-4 w-4" /> Use voice
                </Button>
              )}
              <Button variant="outline" size="icon" onClick={() => setApiOpen(true)} title="Use in API">
                <Code2 className="h-4 w-4" />
              </Button>
              {onEdit && (
                <Button variant="outline" size="icon" onClick={() => onEdit(voice)} title="Edit">
                  <Pencil className="h-4 w-4" />
                </Button>
              )}
              {onDelete && (
                <Button variant="outline" size="icon" className="text-error hover:text-error" onClick={() => onDelete(voice)} title="Delete">
                  <Trash2 className="h-4 w-4" />
                </Button>
              )}
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
    {voice && (
      <UseInApiDialog voiceId={voice.public_voice_id} open={apiOpen} onOpenChange={setApiOpen} />
    )}
    </>
  )
}
