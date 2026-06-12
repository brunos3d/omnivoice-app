import { PageHeader } from "@/components/shell/PageHeader"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { CodeTabs } from "@/components/api/CodeTabs"
import {
  listVoicesExamples,
  listModelsExamples,
  capabilitiesExamples,
  variantsExamples,
  compatibleModelsExamples,
  ttsExamples,
  ttsExtendedExamples,
} from "@/lib/api-examples"

const GENERATION = [
  { method: "POST", path: "/api/v1/text-to-speech", desc: "Generate speech. Voice-first: voiceId + text. Returns audio or a download URL." },
]

const VOICES = [
  { method: "GET", path: "/api/v1/voices", desc: "List voices (cursor-paginated)." },
  { method: "GET", path: "/api/v1/voices/{voiceId}", desc: "Get a voice by its public Voice ID." },
  { method: "POST", path: "/api/v1/voices", desc: "Create a voice (multipart; ≤10s reference audio)." },
  { method: "DELETE", path: "/api/v1/voices/{voiceId}", desc: "Delete a voice." },
  { method: "GET", path: "/api/v1/voices/{voiceId}/compatible-models", desc: "Models that can serve this voice." },
  { method: "GET", path: "/api/v1/voices/{voiceId}/compatible-variants", desc: "RuntimeVariants that can serve this voice." },
]

const DISCOVERY = [
  { method: "GET", path: "/api/v1/models", desc: "List models available in this edition." },
  { method: "GET", path: "/api/v1/models/{modelId}", desc: "Model detail: capabilities, settings schema, variants." },
  { method: "GET", path: "/api/v1/models/{modelId}/capabilities", desc: "The model's declared capability contract." },
  { method: "GET", path: "/api/v1/models/{modelId}/variants", desc: "RuntimeVariants (base / singing / pt-br …)." },
  { method: "GET", path: "/api/v1/models/{modelId}/variants/{variantId}", desc: "A single RuntimeVariant." },
]

const IDENTIFIERS = [
  { id: "voiceId", example: "voice_8JXQ29K4L3", body: "Permanent, public Voice ID. Stable across models, editions, and rebuilds — your durable handle to a voice." },
  { id: "modelId", example: "omnivoice-base", body: "Stable, human-readable model id. Independent of runtime internals. Discover via GET /models." },
  { id: "variantId", example: "base · singing", body: "A RuntimeVariant — a model variation. Independent of checkpoints and filesystem layout. Omit to use the model default." },
]

const METHOD_TONE: Record<string, string> = {
  GET: "text-success",
  POST: "text-primary",
  DELETE: "text-error",
}

function EndpointTable({ rows }: { rows: { method: string; path: string; desc: string }[] }) {
  return (
    <CardContent className="divide-y divide-border">
      {rows.map((e) => (
        <div key={`${e.method} ${e.path}`} className="flex items-center gap-3 py-2 text-sm">
          <span className={`w-16 shrink-0 font-mono text-xs font-semibold ${METHOD_TONE[e.method]}`}>{e.method}</span>
          <code className="font-mono text-xs">{e.path}</code>
          <span className="ml-auto hidden max-w-[45%] text-right text-caption sm:block">{e.desc}</span>
        </div>
      ))}
    </CardContent>
  )
}

export default function VoiceApiDocsPage() {
  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        title="API reference"
        description="A voice-first, model-agnostic REST API. Generate speech with a Voice ID and text; select models, RuntimeVariants, and settings when you need them."
      />

      <div className="mt-6 space-y-6">
        {/* Identifiers */}
        <Card>
          <CardHeader>
            <CardTitle>Identifiers</CardTitle>
            <CardDescription>Three stable, public identifiers. None of them expose model internals.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {IDENTIFIERS.map((i) => (
              <div key={i.id} className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:gap-3">
                <code className="w-24 shrink-0 font-mono text-xs font-semibold text-primary">{i.id}</code>
                <code className="shrink-0 rounded bg-surface-2 px-1.5 py-0.5 font-mono text-xs">{i.example}</code>
                <span className="text-caption">{i.body}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Auth */}
        <Card>
          <CardHeader>
            <CardTitle>Authentication</CardTitle>
            <CardDescription>Send your key as a bearer token or an X-API-Key header. Keys are created on the API Keys page.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <code className="block rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm font-mono">
              Authorization: Bearer ov_live_…
            </code>
            <code className="block rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm font-mono">
              X-API-Key: ov_live_…
            </code>
          </CardContent>
        </Card>

        {/* Endpoints */}
        <Card>
          <CardHeader>
            <CardTitle>Generation</CardTitle>
            <CardDescription>The core endpoint. Everything else is discovery.</CardDescription>
          </CardHeader>
          <EndpointTable rows={GENERATION} />
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Voices</CardTitle>
            <CardDescription>Manage voices and discover what can serve them.</CardDescription>
          </CardHeader>
          <EndpointTable rows={VOICES} />
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">Discovery <Badge variant="secondary">models &amp; variants</Badge></CardTitle>
            <CardDescription>List models, read their capabilities, and enumerate RuntimeVariants — no source reading required.</CardDescription>
          </CardHeader>
          <EndpointTable rows={DISCOVERY} />
        </Card>

        {/* Minimal generate */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">Generate speech <Badge variant="secondary">voice-first</Badge></CardTitle>
            <CardDescription>The minimal request is a voiceId and text. Formats: wav, mp3.</CardDescription>
          </CardHeader>
          <CardContent>
            <CodeTabs examples={ttsExamples("voice_XXXXXXXXXX")} />
          </CardContent>
        </Card>

        {/* Extended generate */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">Advanced generation <Badge variant="secondary">model · variant · settings</Badge></CardTitle>
            <CardDescription>
              All fields below are optional and additive. <code className="font-mono text-xs">generationSettings</code> are
              platform-level (validated against the model&apos;s declared schema);{" "}
              <code className="font-mono text-xs">providerSettings</code> are a flexible, model-specific pass-through.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <CodeTabs examples={ttsExtendedExamples("voice_XXXXXXXXXX")} />
          </CardContent>
        </Card>

        {/* Discovery examples */}
        <Card>
          <CardHeader>
            <CardTitle>List voices</CardTitle>
          </CardHeader>
          <CardContent>
            <CodeTabs examples={listVoicesExamples()} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>List models</CardTitle>
            <CardDescription>Each model carries an id, capabilities, and a default RuntimeVariant.</CardDescription>
          </CardHeader>
          <CardContent>
            <CodeTabs examples={listModelsExamples()} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Inspect capabilities</CardTitle>
            <CardDescription>Branch on declared capabilities (supports_singing, supports_reference_audio, …) — never on a model id.</CardDescription>
          </CardHeader>
          <CardContent>
            <CodeTabs examples={capabilitiesExamples()} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>List RuntimeVariants</CardTitle>
          </CardHeader>
          <CardContent>
            <CodeTabs examples={variantsExamples()} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Check voice compatibility</CardTitle>
            <CardDescription>Which models can serve a given voice, computed from declared capabilities.</CardDescription>
          </CardHeader>
          <CardContent>
            <CodeTabs examples={compatibleModelsExamples()} />
          </CardContent>
        </Card>

        {/* Responses + errors */}
        <Card>
          <CardHeader>
            <CardTitle>Responses &amp; errors</CardTitle>
            <CardDescription>JSON bodies use camelCase. Errors carry a stable, parseable shape.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <p className="text-caption uppercase tracking-wide">Model (GET /models/&#123;modelId&#125;)</p>
              <pre className="overflow-x-auto rounded-lg border border-border bg-surface-2 p-4 text-xs leading-relaxed"><code>{`{
  "modelId": "omnivoice-base",
  "name": "OmniVoice",
  "isDefault": true,
  "defaultVariantId": "base",
  "capabilities": { "supports_reference_audio": true, "supports_multilingual": true },
  "settingsSchema": { "properties": { "speed": { "type": "number" } } },
  "variants": [ { "variantId": "base", "isDefault": true, "trust": "verified" } ]
}`}</code></pre>
            </div>
            <div className="space-y-1.5">
              <p className="text-caption uppercase tracking-wide">Error</p>
              <pre className="overflow-x-auto rounded-lg border border-border bg-surface-2 p-4 text-xs leading-relaxed"><code>{`{
  "detail": {
    "message": "Variant 'singing' not found for model 'omnivoice-base'",
    "category": "not_found",
    "request_id": "a1b2c3d4e5f6",
    "timestamp": "2026-06-11T20:00:00Z"
  }
}`}</code></pre>
            </div>
            <p className="text-caption">
              Common statuses: <code className="font-mono text-xs">401</code> missing/invalid key ·
              <code className="font-mono text-xs"> 404</code> unknown voice/model/variant ·
              <code className="font-mono text-xs"> 409</code> model not available ·
              <code className="font-mono text-xs"> 422</code> unsupported generation setting.
            </p>
          </CardContent>
        </Card>

        <p className="text-caption">
          The full machine-readable schema is generated by the backend at{" "}
          <code className="font-mono text-xs">/openapi.json</code> (interactive docs at{" "}
          <code className="font-mono text-xs">/docs</code>).
        </p>
      </div>
    </div>
  )
}
