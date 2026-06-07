"use client";

import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  submitGeneration,
  fetchJob,
  fetchVoices,
  fetchVoicesPage,
  setVoiceFavorite,
  fetchModelStatus,
} from "@/lib/api";
import { parseApiError, type ApiError } from "@/lib/api-error";
import type {
  GenerationRequest,
  JobResponse,
  VoiceProfile,
  VoiceListPage,
  VoiceScope,
  SortField,
  VoiceQueryFilters,
  ModelStatus,
  SettingsSchema,
} from "@/types";
import { useAppStore } from "@/store/use-store";

/**
 * Filter settings to only include keys declared in the model's settings_schema.
 * Unknown params are stripped — the model adapter only receives what it understands.
 */
export function filterSettingsForModel(
  settings: Record<string, unknown>,
  schema: SettingsSchema | null | undefined,
): Record<string, unknown> {
  if (!schema?.properties) return {}
  const allowedKeys = new Set(Object.keys(schema.properties))
  return Object.fromEntries(
    Object.entries(settings).filter(([key]) => allowedKeys.has(key))
  )
}

/**
 * Initialize settings from a model's settings_schema defaults.
 * Returns an object populated with default values for each property.
 */
export function initializeSettingsFromSchema(
  schema: SettingsSchema | null | undefined,
): Record<string, unknown> {
  if (!schema?.properties) return {}
  return Object.fromEntries(
    Object.entries(schema.properties).map(([key, param]) => [key, param.default ?? null])
  )
}

export function useVoices() {
  const setVoices = useAppStore((s) => s.setVoices);

  return useQuery<VoiceProfile[]>({
    queryKey: ["voices"],
    queryFn: async () => {
      const data = await fetchVoices();
      setVoices(data);
      return data;
    },
    refetchInterval: 10000,
  });
}

/** Paginated/filtered/searchable listing that drives the Voice Library. */
export function useVoicesPage(
  scope: VoiceScope,
  search: string,
  filters: VoiceQueryFilters,
  sort_by?: SortField,
  sort_dir?: "asc" | "desc",
  creation_source?: string,
  recently_used?: string,
) {
  return useInfiniteQuery<VoiceListPage>({
    queryKey: ["voices-page", scope, search, filters, sort_by, sort_dir, creation_source, recently_used],
    queryFn: ({ pageParam }) =>
      fetchVoicesPage({
        scope,
        search,
        filters,
        cursor: pageParam as string | null,
        sort_by,
        sort_dir,
        creation_source,
        recently_used,
      }),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.next_cursor,
    enabled: scope === "mine" || scope === "recent",
  });
}

export function useToggleFavorite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, value }: { id: string; value: boolean }) =>
      setVoiceFavorite(id, value),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["voices-page"] });
      queryClient.invalidateQueries({ queryKey: ["voices"] });
    },
  });
}

export function useModelStatus() {
  return useQuery<ModelStatus>({
    queryKey: ["model-status"],
    queryFn: fetchModelStatus,
    refetchInterval: 5000,
  });
}

export function useSubmitGeneration() {
  const queryClient = useQueryClient();
  const setActiveJob = useAppStore((s) => s.setActiveJob);
  const setLastRequest = useAppStore((s) => s.setLastRequest);

  return useMutation<{ job_id: string }, ApiError, GenerationRequest>({
    mutationFn: async (data) => {
      try {
        return await submitGeneration(data)
      } catch (e) {
        // Re-throw as a structured ApiError so consumers can render it via
        // <ApiErrorDialog />. The fetch wrapper should already throw ApiError
        // for non-2xx; this is the network/abort fallback.
        throw await parseAsyncError(e, "/generate")
      }
    },
    onMutate: (data) => {
      setLastRequest(data);
    },
    onSuccess: (result) => {
      setActiveJob(result.job_id, "pending");
      queryClient.invalidateQueries({ queryKey: ["voices"] });
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}

async function parseAsyncError(e: unknown, url: string): Promise<ApiError> {
  // Response-based errors from the api wrapper already carry the parsed ApiError.
  if (e && typeof e === "object" && "category" in (e as Record<string, unknown>)) {
    return e as ApiError
  }
  // Fallback: treat as a thrown network/parse error.
  return await parseApiError(null, e, url)
}

export function useJobStatus(jobId: string | null) {
  const setActiveJobStatus = useAppStore((s) => s.setActiveJobStatus);
  const setActiveJob = useAppStore((s) => s.setActiveJob);

  return useQuery<JobResponse>({
    queryKey: ["job", jobId],
    queryFn: async () => {
      const data = await fetchJob(jobId!);
      setActiveJobStatus(data.status);
      if (data.status === "completed" || data.status === "failed") {
        // Capture the job ID at the time the query resolves. Only clear the
        // active-job state if this job is STILL the active one when the timer
        // fires. Without this guard, starting a new generation within the
        // 3-second window caused the old timer to wipe the new job's ID from
        // the store, stopping its poll and hiding its result.
        const completedJobId = jobId;
        setTimeout(() => {
          if (useAppStore.getState().activeJobId === completedJobId) {
            setActiveJob(null);
          }
        }, 3000);
      }
      return data;
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 1000;
      return data.status === "pending" || data.status === "processing"
        ? 1000
        : false;
    },
  });
}
