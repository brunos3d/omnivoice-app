/**
 * Centralized API error model.
 *
 * The backend may return errors in a few shapes:
 *   - { detail: "string" } (FastAPI default)
 *   - { detail: { message, ..., category, request_id, timestamp } } (rich)
 *   - A thrown TypeError (network / abort)
 *
 * parseApiError normalises all of them into a single ``ApiError`` so every
 * generation / voice mutation flows through the same display layer.
 */

export type ApiErrorCategory =
  | "network"
  | "validation"
  | "not_found"
  | "unauthorized"
  | "conflict"
  | "gpu_unavailable"
  | "cuda_out_of_memory"
  | "model_loading"
  | "voice_not_found"
  | "generation_timeout"
  | "backend_unavailable"
  | "rate_limited"
  | "internal_server"
  | "unknown"

export interface ApiError {
  /** Stable category used to drive the user-facing remediation copy. */
  category: ApiErrorCategory
  /** HTTP status (0 means the request never produced a response). */
  status: number
  /** Backend-provided human-readable summary. */
  message: string
  /** Optional secondary detail (e.g. unsupported_tags, model_id). */
  detail?: Record<string, unknown>
  /** Backend request id (for support / log correlation). */
  requestId?: string
  /** ISO-8601 timestamp captured at error-parse time. */
  timestamp: string
  /** Raw response body for development-mode diagnostics. */
  raw?: unknown
  /** Original Error object if the failure was a thrown exception. */
  cause?: unknown
}

/**
 * Map an HTTP status + a hint string (e.g. detail) to an ApiErrorCategory.
 * Pure function — no DOM / React. Reused by tests.
 */
export function categorizeError(status: number, hint: string): ApiErrorCategory {
  const lower = hint.toLowerCase()
  if (status === 0) return "network"
  if (status === 401 || status === 403) return "unauthorized"
  if (status === 404) {
    if (lower.includes("voice")) return "voice_not_found"
    if (lower.includes("model") || lower.includes("model_id")) return "model_loading"
    return "not_found"
  }
  if (status === 409) {
    if (lower.includes("variant")) return "model_loading"
    if (lower.includes("cuda") || lower.includes("out of memory") || lower.includes("oom")) {
      return "cuda_out_of_memory"
    }
    if (lower.includes("loading")) return "model_loading"
    if (lower.includes("gpu")) return "gpu_unavailable"
    return "conflict"
  }
  if (status === 422) return "validation"
  if (status === 429) return "rate_limited"
  if (status === 503) {
    if (lower.includes("loading")) return "model_loading"
    if (lower.includes("unavailable")) return "backend_unavailable"
    return "backend_unavailable"
  }
  if (status === 504) return "generation_timeout"
  if (status >= 500) {
    if (lower.includes("cuda") || lower.includes("out of memory") || lower.includes("oom")) {
      return "cuda_out_of_memory"
    }
    if (lower.includes("model")) return "model_loading"
    if (lower.includes("voice")) return "voice_not_found"
    return "internal_server"
  }
  return "unknown"
}

/**
 * User-facing copy per category. Production-safe (no stack traces, no
 * request ids, no internal terminology). Single source of truth.
 */
export const USER_REMEDIATION: Record<ApiErrorCategory, { title: string; body: string }> = {
  network: {
    title: "Can't reach the server",
    body: "Check your internet connection and try again.",
  },
  validation: {
    title: "We couldn't process that request",
    body: "Double-check your input and try again.",
  },
  not_found: {
    title: "Not found",
    body: "That item no longer exists. Refresh the page and try again.",
  },
  unauthorized: {
    title: "You don't have access",
    body: "Sign in again or contact your administrator.",
  },
  conflict: {
    title: "Action couldn't be completed",
    body: "Another action is in progress. Wait a moment and try again.",
  },
  gpu_unavailable: {
    title: "GPU isn't ready",
    body: "The graphics processor is busy or unavailable. Wait a few seconds and try again.",
  },
  cuda_out_of_memory: {
    title: "GPU ran out of memory",
    body: "Free up resources by switching to a smaller model, or wait a moment and try again.",
  },
  model_loading: {
    title: "Model is still loading",
    body: "The model is being prepared. Wait a moment and try again.",
  },
  voice_not_found: {
    title: "Voice not found",
    body: "This voice may have been removed. Pick another voice from the library.",
  },
  generation_timeout: {
    title: "Generation took too long",
    body: "Try a shorter text or switch to a smaller model.",
  },
  backend_unavailable: {
    title: "Server is temporarily unavailable",
    body: "Try again in a moment. If the problem persists, restart the server.",
  },
  rate_limited: {
    title: "Too many requests",
    body: "Slow down and try again in a moment.",
  },
  internal_server: {
    title: "Something went wrong",
    body: "An unexpected error occurred. Please try again.",
  },
  unknown: {
    title: "Something went wrong",
    body: "An unexpected error occurred. Please try again.",
  },
}

export function getRemediation(category: ApiErrorCategory) {
  return USER_REMEDIATION[category]
}

interface ApiErrorPayload {
  detail?: string | { message?: string; category?: ApiErrorCategory; request_id?: string; timestamp?: string; [k: string]: unknown }
  [k: string]: unknown
}

/**
 * Parse a fetch Response (or thrown Error) into a structured ApiError.
 */
export function parseApiError(
  response: Response | null,
  thrown: unknown,
  requestUrl?: string,
): ApiError {
  const timestamp = new Date().toISOString()
  if (thrown) {
    // Network / abort / CORS / JSON parse failure.
    const message =
      thrown instanceof Error
        ? thrown.message
        : typeof thrown === "string"
          ? thrown
          : "Request failed"
    return {
      category: "network",
      status: 0,
      message,
      timestamp,
      requestId: undefined,
      raw: thrown,
      cause: thrown,
    }
  }
  if (!response) {
    return {
      category: "unknown",
      status: 0,
      message: "No response received",
      timestamp,
    }
  }
  const status = response.status
  // Read the body as text first; FastAPI usually returns JSON, but we want to
  // capture the raw text too for the dev-mode panel.
  return response
    .clone()
    .text()
    .then((text) => {
      let payload: ApiErrorPayload = {}
      if (text) {
        try {
          payload = JSON.parse(text) as ApiErrorPayload
        } catch {
          // Non-JSON body — keep the text as the message.
          return {
            category: categorizeError(status, text),
            status,
            message: text.slice(0, 500),
            timestamp,
            requestId: response.headers.get("x-request-id") ?? undefined,
            raw: { url: requestUrl, status, body: text },
          } satisfies ApiError
        }
      }
      const detail = payload?.detail
      const detailMessage =
        typeof detail === "string"
          ? detail
          : detail && typeof detail === "object" && "message" in detail
            ? String((detail as { message?: unknown }).message ?? "")
            : ""
      const category: ApiErrorCategory =
        (detail && typeof detail === "object" && "category" in detail
          ? (detail as { category?: ApiErrorCategory }).category
          : undefined) ?? categorizeError(status, detailMessage)
      const requestId =
        (detail && typeof detail === "object" && "request_id" in detail
          ? String((detail as { request_id?: unknown }).request_id ?? "")
          : undefined) || response.headers.get("x-request-id") || undefined
      const detailObj =
        detail && typeof detail === "object" ? (detail as Record<string, unknown>) : undefined
      return {
        category,
        status,
        message: detailMessage || `Request failed with status ${status}`,
        detail: detailObj,
        requestId: requestId || undefined,
        timestamp,
        raw: { url: requestUrl, status, body: payload },
      } satisfies ApiError
    }) as unknown as ApiError
}
