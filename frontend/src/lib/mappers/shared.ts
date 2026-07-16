import type { ChecklistStatus, Priority } from "../types";

export function asPriority(value: string): Priority {
  if (value === "high" || value === "low") return value;
  return "medium";
}

export function asChecklistStatus(value: string): ChecklistStatus {
  if (value === "in_progress" || value === "done" || value === "na") {
    return value;
  }
  return "pending";
}
