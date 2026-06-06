"use client"

import { useState } from "react"
import { Heart, Pencil, Trash2, Wand2, Copy, Check, Code2, Play, ChevronDown, ChevronRight } from "lucide-react"
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { AudioPlayer } from "@/components/AudioPlayer"
import { UseInApiDialog } from "@/components/api/UseInApiDialog"
import { VariantManager } from "@/components/voice/VariantManager"
import { ModelCompatibilitySection } from "@/components/voice/ModelCompatibilitySection"
import { getVoiceAudioUrl } from "@/lib/api"
import { cn, formatDuration } from "@/lib/utils"
import type { VoiceProfile } from "@/types"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { setVoiceFavorite } from "@/lib/api"

interface VoiceDetailPanelProps {
  voice: VoiceProfile | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onUse?: (voice: VoiceProfile) => void
  onEdit?: (voice: VoiceProfile) => void
  onDelete?: (voice: VoiceProfile) => void
}

const CREATION_SOURCE_LABELS: Record<string, { label: string; className: string }> = {
  SOURCE_ASSET: { label: "Cloned", className: "bg-blue-500/10 text-blue-600 border-blue-500/20" },
  PRESET_VOICE: { label: "Preset", className: "bg-purple-500/10 text-purple-600 border-purple-500/20" },
  MARKETPLACE_VOICE: { label: "Marketplace", className: "bg-amber-500/10 text-amber-600 border-amber-500/20" },
  TRAINED_VOICE: { label: "Trained", className: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20" },
  IMPORTED_VOICE: { label: "Imported", className: "bg-violet-500/10 text-violet-600 border-violet-500/20" },
  SYSTEM_VOICE: { label: "System", className: "bg-muted text-muted-foreground border-border" },
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
  const queryClient = useQueryClient()

  const toggleFav = useMutation({
    mutationFn: ({ id, value }: { id: string; value: boolean }) => setVoiceFavorite(id, value),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["voices-page"] })
      queryClient.invalidateQueries({ queryKey: ["voices"] })
    },
  })

  if (!voice) return null

  const previewable = voice.preview_summary
    ? voice.preview_summary.origin !== "none"
    : (voice.audio_duration ?? 0) > 0

  const badge = voice.creation_source
    ? CREATION_SOURCE_LABELS[voice.creation_source] ?? { label: voice.creation_source, className: "" }
    : null

  return (
    <>
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent side="right" className="w-full sm:max-w-md p-0 flex flex-col">
          {/* Header */}
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
                    <span className="text-sm text-muted-foreground">
                      {voice.language}
                    </span>
                  )}
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className={cn(
                  "shrink-0",
                  voice.is_favorite && "text-red-500 hover:text-red-600"
                )}
                onClick={() => toggleFav.mutate({ id: voice.id, value: !voice.is_favorite })}
                disabled={toggleFav.isPending}
                title={voice.is_favorite ? "Remove from favorites" : "Add to favorites"}
              >
                <Heart className={cn("h-5 w-5", voice.is_favorite && "fill-current")} />
              </Button>
            </div>
          </SheetHeader>

          {/* Scrollable sections */}
          <div className="flex-1 overflow-y-auto divide-y divide-border">
            {/* Overview */}
            <Section title="Overview">
              <div className="space-y-3">
                {voice.description && (
                  <p className="text-sm text-foreground/90 leading-relaxed">{voice.description}</p>
                )}

                {voice.meta?.provider != null && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">Provider:</span>
                    <Badge variant="secondary" className="gap-1 text-xs">
                      {String(voice.meta.provider)}
                    </Badge>
                  </div>
                )}

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

                {voice.transcript && (
                  <div className="space-y-1">
                    <p className="text-caption uppercase tracking-wide">Transcript</p>
                    <p className="text-sm text-foreground/90 leading-relaxed">{voice.transcript}</p>
                  </div>
                )}

                {voice.preset_tags && voice.preset_tags.length > 0 && (
                  <div className="space-y-1">
                    <p className="text-caption uppercase tracking-wide">Tags</p>
                    <div className="flex flex-wrap gap-1.5">
                      {voice.preset_tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">{tag}</Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </Section>

            {/* Previews */}
            <Section title="Previews" open={previewable}>
              {previewable ? (
                <AudioPlayer
                  audioUrl={getVoiceAudioUrl(voice.id)}
                  title="Preview audio"
                  duration={voice.audio_duration}
                />
              ) : (
                <div className="flex flex-col items-center justify-center py-6 text-center">
                  <Play className="h-8 w-8 text-muted-foreground/40 mb-2" />
                  <p className="text-sm text-muted-foreground">No preview available</p>
                  <p className="text-xs text-muted-foreground/60 mt-0.5">
                    This voice does not have any audio preview
                  </p>
                </div>
              )}
            </Section>

            {/* Compatible Models */}
            <Section title="Compatible Models">
              <ModelCompatibilitySection publicVoiceId={voice.public_voice_id} />
            </Section>

            {/* Variants */}
            <Section title="Variants" open={false}>
              <VariantManager publicVoiceId={voice.public_voice_id} />
            </Section>
          </div>

          {/* Actions bar */}
          <div className="border-t border-border p-4 flex items-center gap-2">
            {onUse && (
              <Button className="flex-1 gap-2" onClick={() => onUse(voice)}>
                <Wand2 className="h-4 w-4" /> Use voice
              </Button>
            )}
            <Button variant="outline" size="icon" onClick={() => setApiOpen(true)} title="Use in API">
              <Code2 className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" onClick={() => {
              navigator.clipboard?.writeText(voice.public_voice_id).then(() => {
                setCopied(true)
                setTimeout(() => setCopied(false), 1500)
              })
            }} title="Copy voice ID">
              {copied ? <Check className="h-4 w-4 text-success" /> : <Copy className="h-4 w-4" />}
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
        </SheetContent>
      </Sheet>
      {voice && (
        <UseInApiDialog voiceId={voice.public_voice_id} open={apiOpen} onOpenChange={setApiOpen} />
      )}
    </>
  )
}
