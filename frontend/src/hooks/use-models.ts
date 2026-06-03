import { useQuery } from "@tanstack/react-query";
import { useAppStore } from "@/store/use-store";
import { fetchModels, fetchModel, fetchModelTags } from "@/lib/api";
import type { ModelTagMetadata } from "@/types";
import { FALLBACK_TAGS } from "@/editor/tags";

export function useModels() {
  return useQuery({
    queryKey: ["models"],
    queryFn: fetchModels,
    staleTime: 60_000,
  });
}

export function useModel(id: string | null) {
  return useQuery({
    queryKey: ["model", id],
    queryFn: () => fetchModel(id!),
    enabled: !!id,
  });
}

export function useModelTags(modelId: string | null) {
  return useQuery({
    queryKey: ["model-tags", modelId],
    queryFn: async (): Promise<ModelTagMetadata[]> => {
      if (!modelId) return [];
      const data = await fetchModelTags(modelId);
      return data.tags;
    },
    enabled: !!modelId,
    staleTime: 120_000,
    placeholderData: FALLBACK_TAGS,
  });
}

export function useActiveModel() {
  const selectedModelId = useAppStore((s) => s.selectedModelId);
  const { data: models } = useModels();

  const activeId = selectedModelId ?? models?.find((m) => m.is_default)?.id ?? null;
  const activeModel = models?.find((m) => m.id === activeId) ?? null;

  const { data: tags } = useModelTags(activeId);

  return {
    activeModel,
    activeModelId: activeId,
    tags: tags ?? FALLBACK_TAGS,
    isLoading: false,
  };
}
