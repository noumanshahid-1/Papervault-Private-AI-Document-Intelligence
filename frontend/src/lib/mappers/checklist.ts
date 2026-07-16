import type { ApiChecklistResult } from "../api/contracts";
import { extractTimeHint, isTimeSensitive } from "../documentSignals";
import type { ChecklistResult } from "../types";
import { asChecklistStatus, asPriority } from "./shared";

export function mapChecklist(
  raw: ApiChecklistResult,
  filename: string,
): ChecklistResult {
  const items = (raw.items ?? []).map((item, index) => {
    const haystack = `${item.title} ${item.reason} ${item.source_snippet ?? ""}`;
    const priority = isTimeSensitive(haystack)
      ? "high"
      : asPriority(item.priority);
    return {
      id: `cl-${index + 1}`,
      task: item.title,
      reason: item.reason,
      priority,
      status: asChecklistStatus(item.status),
      due_hint: item.due_date ?? extractTimeHint(haystack),
      source_snippet: item.source_snippet ?? null,
    };
  });

  return {
    filename,
    items,
    total: items.length,
    high_priority_count: items.filter((item) => item.priority === "high").length,
  };
}
