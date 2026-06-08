import { Download, PauseCircle, PlayCircle, RefreshCw, Trash2, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { RuntimePhase } from "@/types"
import type { RuntimeLifecycleAction } from "@/hooks/use-runtimes"

type PendingPhase = "Pulling" | "Starting" | "Stopping" | "Updating"

const OPERATIONS_BY_PHASE: Record<RuntimePhase, RuntimeLifecycleAction[]> = {
  NotInstalled: ["install"],
  Pulling: [],
  Installed: ["start", "remove"],
  Starting: [],
  Active: ["stop", "update", "remove"],
  Stopping: [],
  Stopped: ["start", "remove"],
  Failed: ["remove"],
  Updating: [],
}

const PENDING_LABELS: Record<PendingPhase, string> = {
  Pulling: "Pulling image...",
  Starting: "Starting container...",
  Stopping: "Stopping container...",
  Updating: "Updating image...",
}

const ACTION_ICON: Record<RuntimeLifecycleAction, typeof Download> = {
  install: Download,
  start: PlayCircle,
  stop: PauseCircle,
  update: RefreshCw,
  remove: Trash2,
}

const ACTION_VARIANT: Record<RuntimeLifecycleAction, "default" | "outline" | "destructive"> = {
  install: "default",
  start: "default",
  stop: "outline",
  update: "outline",
  remove: "destructive",
}

function isPendingPhase(phase: RuntimePhase): phase is PendingPhase {
  return phase === "Pulling" || phase === "Starting" || phase === "Stopping" || phase === "Updating"
}

export function OperationsRow({
  phase,
  pending,
  onAction,
}: {
  phase: RuntimePhase
  pending: boolean
  onAction: (action: RuntimeLifecycleAction) => void
}) {
  if (isPendingPhase(phase)) {
    return (
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        {PENDING_LABELS[phase]}
      </div>
    )
  }

  const actions = OPERATIONS_BY_PHASE[phase]
  if (actions.length === 0) return null

  return (
    <div className="flex flex-wrap gap-1.5 pt-1">
      {actions.map((action) => {
        const Icon = ACTION_ICON[action]
        const variant = ACTION_VARIANT[action]
        const isRemoveBlockedDuringActive = action === "remove" && phase === "Active"
        return (
          <Button
            key={action}
            size="sm"
            variant={variant}
            disabled={pending || isRemoveBlockedDuringActive}
            onClick={() => onAction(action)}
            className={cn(action === "remove" && "gap-1")}
          >
            <Icon className="mr-1 h-3 w-3" />
            {action[0].toUpperCase() + action.slice(1)}
          </Button>
        )
      })}
    </div>
  )
}
