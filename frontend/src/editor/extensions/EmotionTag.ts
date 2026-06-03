import { Node, mergeAttributes } from "@tiptap/core";

export interface EmotionTagAttrs {
  tagId: string;
  modelId: string;
  invalid?: boolean;
}

declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    emotionTag: {
      setEmotionTag: (attrs: EmotionTagAttrs) => ReturnType;
    };
  }
}

export const EmotionTag = Node.create<Record<string, never>>({
  name: "emotionTag",

  group: "inline",

  inline: true,

  atom: true,

  selectable: true,

  draggable: false,

  addAttributes() {
    return {
      tagId: { default: null },
      modelId: { default: null },
      invalid: { default: false },
    };
  },

  parseHTML() {
    return [{ tag: "span[data-emotion-tag]" }];
  },

  renderHTML({ node, HTMLAttributes }) {
    const attrs = node.attrs as unknown as EmotionTagAttrs;
    return [
      "span",
      mergeAttributes(HTMLAttributes, {
        "data-emotion-tag": attrs.tagId,
        "data-model-id": attrs.modelId,
        "data-invalid": attrs.invalid ? "true" : undefined,
        class: attrs.invalid
          ? "inline-flex items-center rounded-md bg-error/15 px-1.5 py-0.5 text-sm font-medium text-error"
          : "inline-flex items-center rounded-md bg-primary/10 px-1.5 py-0.5 text-sm font-medium text-primary",
        contenteditable: "false",
      }),
      `[${attrs.tagId}]`,
    ];
  },

  addCommands() {
    return {
      setEmotionTag:
        (attrs: EmotionTagAttrs) =>
        ({ commands }) => {
          return commands.insertContent({
            type: this.name,
            attrs,
          });
        },
    };
  },
});
