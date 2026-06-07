"use client"

import { useEffect, useState } from "react"
import { AlertCircle, Clipboard, ClipboardCheck, ExternalLink, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { ApiError } from "@/lib/api-error"
import { getRemediation } from "@/lib/api-error"

interface ApiErrorDialogProps {
  error: ApiError | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

/**
 * Renders a structured API error.
 *
 * Dev mode: full diagnostics — copy-to-clipboard, raw payload, request id,
 * timestamp, stack trace if available.
 *
 * Production: user-friendly title + remediation + retry/close.
 */
export function ApiErrorDialog({ error, open, onOpenChange }: ApiErrorDialogProps) {
  const isDev = process.env.NODE_ENV !== "production"
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!copied) return
    const t = setTimeout(() => setCopied(false), 2000)
    return () => clearTimeout(t)
  }, [copied])

  if (!error) return null
  const remediation = getRemediation(error.category)

  const diagnostics = buildDiagnostics(error)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(diagnostics)
      setCopied(true)
    } catch {
      // Clipboard not available — silently degrade.
    }
  }

  return (
    <div
      className={cn(
        "fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4",
        open ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0",
      )}
      aria-hidden={!open}
      onClick={(e) => {
        if (e.target === e.currentTarget) onOpenChange(false)
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Error details"
        className="w-full max-w-2xl rounded-lg border border-border bg-surface-1 shadow-2xl"
      >
        <header className="flex items-start justify-between gap-3 border-b border-border px-5 py-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-destructive" />
            <div>
              <h2 className="text-base font-semibold">
                {isDev ? `${remediation.title} (${error.category})` : remediation.title}
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">{remediation.body}</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onOpenChange(false)}
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </Button>
        </header>

        <div className="space-y-4 px-5 py-4 text-sm">
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              What happened
            </h3>
            <p className="mt-1 break-words text-foreground">{error.message}</p>
          </div>

          {error.detail && Object.keys(error.detail).length > 0 && (
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Detail
              </h3>
              <pre className="mt-1 max-h-40 overflow-auto rounded-md border border-border bg-surface-2 p-3 text-xs">
                {JSON.stringify(error.detail, null, 2)}
              </pre>
            </div>
          )}

          {isDev && (
            <>
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Diagnostics
                </h3>
                <dl className="mt-1 grid grid-cols-3 gap-x-3 gap-y-1 text-xs">
                  <dt className="text-muted-foreground">Category</dt>
                  <dd className="col-span-2 font-mono">{error.category}</dd>
                  <dt className="text-muted-foreground">Status</dt>
                  <dd className="col-span-2 font-mono">{error.status || "(no response)"}</dd>
                  <dt className="text-muted-foreground">Timestamp</dt>
                  <dd className="col-span-2 font-mono">{error.timestamp}</dd>
                  {error.requestId && (
                    <>
                      <dt className="text-muted-foreground">Request ID</dt>
                      <dd className="col-span-2 font-mono">{error.requestId}</dd>
                    </>
                  )}
                  {error.cause instanceof Error && (
                    <>
                      <dt className="text-muted-foreground">Error class</dt>
                      <dd className="col-span-2 font-mono">{error.cause.name}</dd>
                      {error.cause.stack && (
                        <>
                          <dt className="text-muted-foreground">Stack</dt>
                          <dd className="col-span-2">
                            <pre className="max-h-40 overflow-auto rounded-md border border-border bg-surface-2 p-2 text-[10px]">
                              {error.cause.stack}
                            </pre>
                          </dd>
                        </>
                      )}
                    </>
                  )}
                </dl>
              </div>

              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Raw response
                </h3>
                <pre className="mt-1 max-h-60 overflow-auto rounded-md border border-border bg-surface-2 p-3 text-[10px]">
                  {JSON.stringify(error.raw, null, 2)}
                </pre>
              </div>
            </>
          )}
        </div>

        <footer className="flex flex-wrap items-center justify-between gap-2 border-t border-border px-5 py-3">
          <div className="flex items-center gap-2">
            {isDev && (
              <Button
                size="sm"
                variant="outline"
                onClick={handleCopy}
                className="gap-1.5"
              >
                {copied ? (
                  <>
                    <ClipboardCheck className="h-3.5 w-3.5" />
                    Copied
                  </>
                ) : (
                  <>
                    <Clipboard className="h-3.5 w-3.5" />
                    Copy diagnostics
                  </>
                )}
              </Button>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button size="sm" variant="ghost" onClick={() => onOpenChange(false)}>
              Close
            </Button>
            {isDev && error.raw && (error.raw as { url?: string }).url ? (
              <Button size="sm" variant="outline" asChild className="gap-1.5">
                <a
                  href={(error.raw as { url: string }).url}
                  target="_blank"
                  rel="noreferrer"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  Open endpoint
                </a>
              </Button>
            ) : null}
          </div>
        </footer>
      </div>
    </div>
  )
}

function buildDiagnostics(error: ApiError): string {
  return [
    `[${error.timestamp}] ${error.category} (status ${error.status || "no-response"})`,
    `Message: ${error.message}`,
    error.requestId ? `Request ID: ${error.requestId}` : null,
    error.detail ? `Detail: ${JSON.stringify(error.detail, null, 2)}` : null,
    error.raw ? `Raw: ${JSON.stringify(error.raw, null, 2)}` : null,
    error.cause instanceof Error && error.cause.stack
      ? `Stack: ${error.cause.stack}`
      : null,
  ]
    .filter(Boolean)
    .join("\n\n")
}
