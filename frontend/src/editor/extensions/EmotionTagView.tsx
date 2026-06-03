"use client";

import { NodeViewWrapper, type NodeViewProps } from "@tiptap/react";
import { cn } from "@/lib/utils";
import { tagById } from "@/editor/tags";

export function EmotionTagView({ node }: NodeViewProps) {
  const attrs = node.attrs as { tagId: string; invalid?: boolean };
  const tag = tagById(attrs.tagId);
  const label = tag ? `${tag.emoji} ${tag.label}` : attrs.tagId;
  const invalid = attrs.invalid ?? false;

  return (
    <NodeViewWrapper
      as="span"
      contenteditable="false"
      data-emotion-tag={attrs.tagId}
      data-invalid={invalid ? "true" : undefined}
      draggable="false"
      className={cn(
        "inline-flex cursor-default items-center gap-1 rounded-md px-1.5 py-0.5 text-sm font-medium select-none",
        "transition-colors duration-150",
        invalid
          ? "bg-error/15 text-error"
          : "bg-primary/10 text-primary hover:bg-primary/15",
      )}
      title={tag?.description ?? attrs.tagId}
    >
      {label}
    </NodeViewWrapper>
  );
}
