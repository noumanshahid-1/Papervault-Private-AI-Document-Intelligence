import { useState } from "react";
import { CheckCircle2, Circle, ListChecks } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { useWorkspaceStore } from "@/store/workspaceStore";
import type { ChecklistResult, Priority } from "@/lib/types";

const PRIORITY_BADGE: Record<Priority, string> = {
  high: "border-destructive/20 bg-destructive/10 text-destructive",
  medium: "border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-400",
  low: "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
};

type Filter = "all" | Priority;

interface Props {
  checklist: ChecklistResult;
  filter?: Filter;
  onFilterChange?: (filter: Filter) => void;
}

export function ChecklistTab({
  checklist,
  filter: controlledFilter,
  onFilterChange,
}: Props) {
  const { checklistCompletion, toggleChecklist } = useWorkspaceStore();
  const [localFilter, setLocalFilter] = useState<Filter>("all");
  const filter = controlledFilter ?? localFilter;
  const setFilter = (value: Filter) =>
    onFilterChange ? onFilterChange(value) : setLocalFilter(value);
  const filtered =
    filter === "all"
      ? checklist.items
      : checklist.items.filter((item) => item.priority === filter);
  const completedCount = checklist.items.filter(
    (item) => checklistCompletion[item.id],
  ).length;
  const progress = checklist.total > 0 ? (completedCount / checklist.total) * 100 : 0;

  return (
    <div className="space-y-4">
      <div className="surface-panel p-4 sm:p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-start gap-3">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600">
              <ListChecks size={18} />
            </span>
            <div>
              <div className="flex items-baseline gap-2">
                <p className="text-sm font-semibold text-foreground">Action checklist</p>
                <span className="text-xs text-muted-foreground">
                  {completedCount} of {checklist.total} complete
                </span>
              </div>
              <Progress value={progress} className="mt-3 h-2 w-56 max-w-full" />
            </div>
          </div>
          <ChecklistFilters
            filter={filter}
            onChange={setFilter}
            checklist={checklist}
          />
        </div>
      </div>

      <div className="space-y-3">
        {filtered.map((item) => {
          const done = checklistCompletion[item.id] ?? false;
          return (
            <button
              type="button"
              key={item.id}
              onClick={() => toggleChecklist(item.id)}
              aria-pressed={done}
              className={cn(
                "group flex w-full items-start gap-3 rounded-2xl border p-4 text-left transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:p-5",
                done
                  ? "border-emerald-500/15 bg-emerald-500/[0.035]"
                  : "border-border/80 bg-card/92 shadow-[0_16px_40px_-34px_rgba(15,23,42,0.5)] hover:-translate-y-0.5 hover:border-accent/25",
              )}
            >
              {done ? (
                <CheckCircle2
                  size={19}
                  className="mt-0.5 shrink-0 text-emerald-600 dark:text-emerald-400"
                />
              ) : (
                <Circle
                  size={19}
                  className="mt-0.5 shrink-0 text-muted-foreground transition-colors group-hover:text-accent"
                />
              )}
              <span className="min-w-0 flex-1">
                <span className="flex flex-wrap items-center gap-2">
                  <span
                    className={cn(
                      "text-sm font-semibold leading-5 text-foreground",
                      done && "text-muted-foreground line-through",
                    )}
                  >
                    {item.task}
                  </span>
                  <Badge
                    variant="outline"
                    className={cn("capitalize", PRIORITY_BADGE[item.priority])}
                  >
                    {item.priority}
                  </Badge>
                </span>
                <span className="mt-1.5 block text-xs leading-5 text-muted-foreground">
                  {item.reason}
                </span>
                {item.due_hint && (
                  <span className="mt-2 inline-flex rounded-full bg-muted px-2.5 py-1 text-[0.68rem] font-medium text-muted-foreground">
                    Due: {item.due_hint}
                  </span>
                )}
              </span>
            </button>
          );
        })}

        {filtered.length === 0 && (
          <div className="surface-panel flex min-h-48 flex-col items-center justify-center px-6 text-center">
            <CheckCircle2 size={23} className="text-emerald-600" />
            <p className="mt-3 text-sm font-medium text-foreground">
              No {filter}-priority tasks
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Choose another filter to see the remaining checklist.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function ChecklistFilters({
  filter,
  onChange,
  checklist,
}: {
  filter: Filter;
  onChange: (filter: Filter) => void;
  checklist: ChecklistResult;
}) {
  return (
    <div className="scrollbar-subtle -mx-1 flex max-w-full gap-1.5 overflow-x-auto px-1 pb-1">
      {(["all", "high", "medium", "low"] as Filter[]).map((item) => {
        const count =
          item === "all"
            ? checklist.items.length
            : checklist.items.filter((entry) => entry.priority === item).length;
        return (
          <button
            type="button"
            key={item}
            onClick={() => onChange(item)}
            aria-pressed={filter === item}
            className={cn(
              "inline-flex h-8 shrink-0 items-center gap-1.5 rounded-full px-3 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              filter === item
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground hover:text-foreground",
            )}
          >
            {item === "all" ? "All" : item.charAt(0).toUpperCase() + item.slice(1)}
            <span className="text-[0.65rem] opacity-65">{count}</span>
          </button>
        );
      })}
    </div>
  );
}
