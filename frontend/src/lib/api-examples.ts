// Generates copy-pasteable request examples for the public /api/v1 API (ADR-0020).
// Used by the "Use in API" dialog and the developer portal documentation pages.
//
// PeakVox is voice-first: the minimal call is { voiceId, text }. Advanced users
// can additionally select a model, a RuntimeVariant, and pass generation /
// provider settings — without changing the integration shape.

import { getApiBaseUrl } from "@/lib/api"

export type ExampleLanguage =
  | "cURL"
  | "JavaScript"
  | "TypeScript"
  | "Python"
  | "Go"
  | "C#"

export interface CodeExample {
  language: ExampleLanguage
  code: string
}

const KEY_PLACEHOLDER = "$PEAKVOX_API_KEY"
const ENV = "PEAKVOX_API_KEY"

// ── Text-to-speech (voice-first showcase, 6 languages) ───────────────────────
/** Minimal text-to-speech examples for a given voice id ({ voiceId, text }). */
export function ttsExamples(voiceId: string, text = "Hello from PeakVox!"): CodeExample[] {
  const base = getApiBaseUrl()
  const body = `{"voiceId": "${voiceId}", "text": "${text}", "format": "mp3"}`
  return [
    {
      language: "cURL",
      code: `curl -X POST "${base}/api/v1/text-to-speech" \\
  -H "Authorization: Bearer ${KEY_PLACEHOLDER}" \\
  -H "Content-Type: application/json" \\
  -d '${body}' \\
  --output speech.mp3`,
    },
    {
      language: "JavaScript",
      code: `const res = await fetch("${base}/api/v1/text-to-speech", {
  method: "POST",
  headers: {
    Authorization: \`Bearer \${process.env.${ENV}}\`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ voiceId: "${voiceId}", text: "${text}", format: "mp3" }),
});
const audio = await res.arrayBuffer();`,
    },
    {
      language: "TypeScript",
      code: `const res: Response = await fetch("${base}/api/v1/text-to-speech", {
  method: "POST",
  headers: {
    Authorization: \`Bearer \${process.env.${ENV}}\`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ voiceId: "${voiceId}", text: "${text}", format: "mp3" }),
});
const audio: ArrayBuffer = await res.arrayBuffer();`,
    },
    {
      language: "Python",
      code: `import os, requests

res = requests.post(
    "${base}/api/v1/text-to-speech",
    headers={"Authorization": f"Bearer {os.environ['${ENV}']}"},
    json={"voiceId": "${voiceId}", "text": "${text}", "format": "mp3"},
)
with open("speech.mp3", "wb") as f:
    f.write(res.content)`,
    },
    {
      language: "Go",
      code: `package main

import (
	"bytes"
	"io"
	"net/http"
	"os"
)

func main() {
	body := bytes.NewBufferString(\`${body}\`)
	req, _ := http.NewRequest("POST", "${base}/api/v1/text-to-speech", body)
	req.Header.Set("Authorization", "Bearer "+os.Getenv("${ENV}"))
	req.Header.Set("Content-Type", "application/json")
	res, _ := http.DefaultClient.Do(req)
	defer res.Body.Close()
	out, _ := os.Create("speech.mp3")
	defer out.Close()
	io.Copy(out, res.Body)
}`,
    },
    {
      language: "C#",
      code: `using System.Net.Http.Headers;
using System.Text;

var key = Environment.GetEnvironmentVariable("${ENV}");
using var http = new HttpClient();
http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", key);
var json = "{\\"voiceId\\": \\"${voiceId}\\", \\"text\\": \\"${text}\\", \\"format\\": \\"mp3\\"}";
var content = new StringContent(json, Encoding.UTF8, "application/json");
var res = await http.PostAsync("${base}/api/v1/text-to-speech", content);
await File.WriteAllBytesAsync("speech.mp3", await res.Content.ReadAsByteArrayAsync());`,
    },
  ]
}

/** Extended text-to-speech: model + RuntimeVariant + generation/provider settings. */
export function ttsExtendedExamples(
  voiceId: string,
  modelId = "omnivoice-base",
  variantId = "base",
): CodeExample[] {
  const base = getApiBaseUrl()
  const payload = `{
    "voiceId": "${voiceId}",
    "text": "Hello from PeakVox!",
    "modelId": "${modelId}",
    "variantId": "${variantId}",
    "language": "en",
    "format": "wav",
    "generationSettings": { "speed": 1.1 },
    "providerSettings": { "cfg_scale": 2.0, "sampling_steps": 30 }
  }`
  return [
    {
      language: "cURL",
      code: `curl -X POST "${base}/api/v1/text-to-speech" \\
  -H "Authorization: Bearer ${KEY_PLACEHOLDER}" \\
  -H "Content-Type: application/json" \\
  -d '${payload.replace(/\n\s*/g, " ").trim()}' \\
  --output speech.wav`,
    },
    {
      language: "Python",
      code: `import os, requests

res = requests.post(
    "${base}/api/v1/text-to-speech",
    headers={"Authorization": f"Bearer {os.environ['${ENV}']}"},
    json={
        "voiceId": "${voiceId}",
        "text": "Hello from PeakVox!",
        "modelId": "${modelId}",
        "variantId": "${variantId}",
        "generationSettings": {"speed": 1.1},
        "providerSettings": {"cfg_scale": 2.0, "sampling_steps": 30},
    },
)
with open("speech.wav", "wb") as f:
    f.write(res.content)`,
    },
  ]
}

// ── Discovery (list voices / models / variants / capabilities) ───────────────
/** A GET discovery example in cURL / JavaScript / Python that reads one field. */
function getExamples(path: string, key: string): CodeExample[] {
  const base = getApiBaseUrl()
  return [
    {
      language: "cURL",
      code: `curl "${base}${path}" \\
  -H "Authorization: Bearer ${KEY_PLACEHOLDER}"`,
    },
    {
      language: "JavaScript",
      code: `const res = await fetch("${base}${path}", {
  headers: { Authorization: \`Bearer \${process.env.${ENV}}\` },
});
const data = await res.json();
console.log(data.${key});`,
    },
    {
      language: "Python",
      code: `import os, requests

res = requests.get(
    "${base}${path}",
    headers={"Authorization": f"Bearer {os.environ['${ENV}']}"},
)
print(res.json()["${key}"])`,
    },
  ]
}

/** List-voices examples (no specific voice). */
export function listVoicesExamples(): CodeExample[] {
  return getExamples("/api/v1/voices", "voices")
}

/** List-models examples (model discovery). */
export function listModelsExamples(): CodeExample[] {
  return getExamples("/api/v1/models", "models")
}

/** Model capabilities discovery. */
export function capabilitiesExamples(modelId = "omnivoice-base"): CodeExample[] {
  return getExamples(`/api/v1/models/${modelId}/capabilities`, "capabilities")
}

/** RuntimeVariant discovery for a model. */
export function variantsExamples(modelId = "omnivoice-base"): CodeExample[] {
  return getExamples(`/api/v1/models/${modelId}/variants`, "variants")
}

/** Voice ↔ model compatibility discovery. */
export function compatibleModelsExamples(voiceId = "voice_XXXXXXXXXX"): CodeExample[] {
  return getExamples(`/api/v1/voices/${voiceId}/compatible-models`, "models")
}
