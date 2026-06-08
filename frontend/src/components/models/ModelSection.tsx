import { CheckCircle2, Cpu, HardDrive, Server } from "lucide-react"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import type { Model, ModelCapabilities } from "@/types"

const capabilityLabels: Array<[keyof ModelCapabilities, string]> = [
  ["supports_tts", "TTS"],
  ["supports_voice_cloning", "Voice cloning"],
  ["supports_voice_design", "Voice design"],
  ["supports_emotion_tags", "Emotion tags"],
  ["supports_singing", "Singing"],
  ["supports_multilingual", "Multilingual"],
  ["supports_reference_audio", "Reference audio"],
  ["supports_voice_conversion", "Voice conversion"],
  ["supports_streaming", "Streaming"],
  ["supports_api", "API"],
]

const statusClasses: Record<Model["status"], string> = {
  available: "bg-success/15 text-success",
  loaded: "bg-primary/15 text-primary",
  loading: "bg-warning/15 text-warning",
  error: "bg-error/15 text-error",
  disabled: "bg-muted text-muted-foreground",
  inactive: "bg-muted text-muted-foreground",
  deprecated: "bg-warning/15 text-warning",
}

function formatMemory(model: Model): string {
  return model.memory_requirements.min_vram_gb == null
    ? "Unknown"
    : `${model.memory_requirements.min_vram_gb} GB VRAM`
}

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

function Metric({ icon: Icon, label, value }: { icon: typeof Cpu; label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-3">
      <div className="flex items-center gap-2 text-caption">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </div>
      <p className="mt-1 text-sm font-medium">{value || "Not specified"}</p>
    </div>
  )
}

function InfoLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-3 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="max-w-[220px] text-right text-foreground">{value}</span>
    </div>
  )
}

function InfoLink({ label, href, fallback }: { label: string; href: string | null; fallback: string }) {
  return (
    <div className="flex items-start justify-between gap-3 text-sm">
      <span className="text-muted-foreground">{label}</span>
      {href ? (
        <a
          href={href}
          target="_blank"
          rel="noreferrer"
          className="max-w-[220px] truncate text-right text-primary underline-offset-2 hover:underline"
          title={href}
        >
          {fallback === "Unknown" ? href : fallback}
        </a>
      ) : (
        <span className="max-w-[220px] text-right text-foreground">{fallback}</span>
      )}
    </div>
  )
}

function metadataString(value: string | string[] | undefined, fallback: string): string {
  if (Array.isArray(value)) return value.join(", ")
  return value ?? fallback
}

export function ModelSection({ model }: { model: Model }) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <p className="text-caption uppercase tracking-wide">Model</p>
        <p className="text-sm text-muted-foreground">{model.description}</p>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
        <Metric icon={Server} label="Runtime" value={model.runtime_requirements.runtime ?? "Unknown"} />
        <Metric icon={HardDrive} label="Memory" value={formatMemory(model)} />
        <Metric icon={Cpu} label="GPU" value={model.gpu_requirements.required ? "Required" : "Optional"} />
        <Metric
          icon={CheckCircle2}
          label="Edition"
          value={[model.available_in_ce && "CE", model.available_in_cloud && "Cloud"].filter(Boolean).join(" + ")}
        />
      </div>

      <div className="space-y-2">
        <p className="text-caption uppercase tracking-wide">Sources</p>
        <InfoLink label="Provider" href={model.provider_url} fallback={model.provider} />
        <InfoLink label="Repository" href={model.repository_url} fallback="Unknown" />
        <InfoLink label="Model page" href={model.homepage_url} fallback="Unknown" />
        <InfoLink label="License" href={model.license_url} fallback={model.license_name ?? "Unknown"} />
      </div>

      <div className="space-y-2">
        <p className="text-caption uppercase tracking-wide">Capabilities</p>
        <div className="flex flex-wrap gap-1.5">
          {capabilityLabels.map(([key, label]) => (
            <CapabilityBadge key={key} label={label} supported={!!model.capabilities[key]} />
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <p className="text-caption uppercase tracking-wide">Languages and tags</p>
        <InfoLine
          label="Languages"
          value={
            model.supported_languages.length > 0
              ? model.supported_languages.join(", ")
              : metadataString(model.provider_metadata?.languages_summary, "Unknown")
          }
        />
        <InfoLine label="Tags" value={model.supported_tags.length > 0 ? model.supported_tags.join(", ") : "None declared"} />
        <InfoLine
          label="Voice design"
          value={model.supported_voice_design.length > 0 ? `${model.supported_voice_design.length} attributes` : "Not supported"}
        />
        <InfoLine label="Memory source" value={model.memory_requirements.source} />
        <InfoLine label="Edition basis" value={model.edition_availability.basis} />
      </div>
    </div>
  )
}

export { statusClasses }
