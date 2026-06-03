export interface TagIssue {
  tagId: string;
  from: number;
  to: number;
  reason: "unsupported" | "unknown";
}

const TAG_RE = /\[([a-z0-9][a-z0-9-]*)\]/g;

export function validateTags(text: string, supportedTags: string[]): TagIssue[] {
  const issues: TagIssue[] = [];
  const allowed = new Set(supportedTags);
  let m: RegExpExecArray | null;
  TAG_RE.lastIndex = 0;
  while ((m = TAG_RE.exec(text)) !== null) {
    const tagId = m[1];
    if (!allowed.has(tagId)) {
      issues.push({
        tagId,
        from: m.index,
        to: m.index + m[0].length,
        reason: "unsupported",
      });
    }
  }
  return issues;
}
