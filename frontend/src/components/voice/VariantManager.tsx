"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Hammer,
  Loader2,
  MinusCircle,
  RefreshCw,
  XCircle,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  fetchModels,
  fetchVoiceVariants,
  ensureVariant,
  rebuildVariant,
} from "@/lib/api"
import type { VariantListItem } from "@/types"

interface VariantManagerProps {
  publicVoiceId: string
}

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

function mergeModelsWithVariants(
  models: { id: string; name: string }[],
  variants: VariantListItem[],
) {
  const variantMap = new Map(variants.map((v) => [v.model_id, v]))
  return models.map((model) => ({
    ...model,
    variant: variantMap.get(model.id) ?? null,
  }))
}

export function VariantManager({ publicVoiceId }: VariantManagerProps) {
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

  const rebuildMut = useMutation({
    mutationFn: (modelId: string) => rebuildVariant(publicVoiceId, modelId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["voice-variants", publicVoiceId] })
      queryClient.invalidateQueries({ queryKey: ["variant-summary"] })
    },
  })

  const loading = modelsQ.isLoading || variantsQ.isLoading
  const models = modelsQ.data ?? []
  const variants = variantsQ.data ?? []
  const rows = mergeModelsWithVariants(models, variants)

  if (loading) {
    return (
      <div className="flex items-center justify-center py-4">
        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (rows.length === 0) {
    return null
  }

  return (
    <div className="space-y-1">
      <p className="text-caption uppercase tracking-wide">Model variants</p>
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
            {rows.map((row) => {
              const StatusIcon = row.variant
                ? STATUS_ICONS[row.variant.status] ?? Clock
                : Clock
              const statusColor = row.variant
                ? STATUS_COLORS[row.variant.status] ?? "text-muted-foreground"
                : "text-muted-foreground"
              const statusLabel = row.variant
                ? STATUS_LABELS[row.variant.status] ?? row.variant.status
                : "Not built"
              const busy = buildMut.isPending || rebuildMut.isPending
              const thisBusy = (buildMut.isPending && buildMut.variables === row.id) ||
                (rebuildMut.isPending && rebuildMut.variables === row.id)

              return (
                <tr key={row.id} className="text-sm hover:bg-surface/50">
                  <td className="px-3 py-2.5 font-medium truncate max-w-[160px]">{row.name}</td>
                  <td className="px-3 py-2.5">
                    <span className={`inline-flex items-center gap-1.5 ${statusColor}`}>
                      <StatusIcon
                        className={`h-3.5 w-3.5 ${row.variant?.status === "building" ? "animate-spin" : ""}`}
                      />
                      <span>{statusLabel}</span>
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-muted-foreground hidden sm:table-cell text-xs">
                    {row.variant?.realization_type ? (
                      <code className="text-xs">{row.variant.realization_type}</code>
                    ) : (
                      <span className="italic">&mdash;</span>
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-right">
                    {row.variant?.active_artifact_version != null
                      ? <span className="font-mono text-xs">v{row.variant.active_artifact_version}</span>
                      : <span className="text-muted-foreground">&mdash;</span>}
                  </td>
                  <td className="px-3 py-2.5 text-right">
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
                    ) : (
                      <div className="flex items-center justify-end gap-1.5">
                        {row.variant?.status === "failed" && row.variant.error_message && (
                          <span
                            className="text-xs text-error max-w-[100px] truncate hidden lg:inline"
                            title={row.variant.error_message}
                          >
                            {row.variant.error_message}
                          </span>
                        )}
                        {row.variant.active_artifact_version != null && (
                          <span className="text-xs text-muted-foreground hidden sm:inline font-mono">
                            v{row.variant.active_artifact_version}
                          </span>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 gap-1.5 text-xs"
                          disabled={busy}
                          onClick={() => rebuildMut.mutate(row.id)}
                          title="Rebuild variant"
                        >
                          {thisBusy
                            ? <Loader2 className="h-3 w-3 animate-spin" />
                            : <RefreshCw className="h-3 w-3" />}
                          <span className="hidden sm:inline">Rebuild</span>
                        </Button>
                      </div>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
