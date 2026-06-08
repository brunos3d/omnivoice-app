import { Cpu } from "lucide-react"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import type { Model, ModelCapabilities } from "@/types"

type ModelFilter = "all" | "installed" | "available"

const statusClasses: Record<Model["status"], string> = {
  available: "bg-success/15 text-success",
  loaded: "bg-primary/15 text-primary",
  loading: "bg-warning/15 text-warning",
  error: "bg-error/15 text-error",
  disabled: "bg-muted text-muted-foreground",
  inactive: "bg-muted text-muted-foreground",
  deprecated: "bg-warning/15 text-warning",
}

const capabilityLabels: Array<[keyof ModelCapabilities, string]> = [
  ["supports_tts", "TTS"],
  ["supports_voice_cloning", "Clone"],
  ["supports_voice_design", "Design"],
  ["supports_emotion_tags", "Emotion"],
  ["supports_singing", "Singing"],
  ["supports_multilingual", "Multilingual"],
  ["supports_reference_audio", "Reference audio"],
  ["supports_voice_conversion", "Voice conversion"],
  ["supports_streaming", "Streaming"],
  ["supports_api", "API"],
]

function CapabilityBadge({ supported, label }: { supported: boolean; label: string }) {
  return (
    <Badge
      variant={supported ? "default" : "secondary"}
      className={cn(
        "rounded-md px-2 py-0.5 text-[11px] font-normal",
        supported ? "bg-primary/15 text-primary hover:bg-primary/20" : "text-muted-foreground",
      )}
    >
      {supported ? "✓" : "−"} {label}
    </Badge>
  )
}

export function ModelRow({
  model,
  selected,
  onSelect,
}: {
  model: Model
  selected: boolean
  onSelect: (model: Model) => void
}) {
  const caps = model.capabilities

  return (
    <button
      type="button"
      onClick={() => onSelect(model)}
      className={cn(
        "w-full rounded-lg border bg-surface p-4 text-left transition-colors hover:bg-surface-2",
        selected ? "border-primary ring-1 ring-primary/30" : "border-border",
      )}
    >
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/15 text-primary">
          <Cpu className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-card-title">{model.name}</h2>
            {model.is_default && <Badge className="rounded-md bg-primary/15 text-primary">Default</Badge>}
            <span className={cn("rounded px-1.5 py-0.5 text-[10px] font-medium capitalize", statusClasses[model.status])}>
              {model.install_status.replace("_", " ")} / {model.activation_status}
            </span>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            {model.provider} · v{model.version} · {model.license_name ?? model.license?.code ?? "License unknown"}
          </p>
          <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">{model.description}</p>
          <div className="mt-3 flex flex-wrap gap-1.5">
            <CapabilityBadge label="TTS" supported={caps.supports_tts} />
            <CapabilityBadge label="Clone" supported={caps.supports_voice_cloning} />
            <CapabilityBadge label="Design" supported={caps.supports_voice_design ?? false} />
            <CapabilityBadge label="Singing" supported={caps.supports_singing} />
          </div>
        </div>
      </div>
    </button>
  )
}

export { capabilityLabels, statusClasses, type ModelFilter }
