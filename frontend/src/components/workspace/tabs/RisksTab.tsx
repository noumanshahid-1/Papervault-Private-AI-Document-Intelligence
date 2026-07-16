import { useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  CircleHelp,
  SearchCheck,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Priority, RiskInsight } from "@/lib/types";

const PRIORITY_STYLES: Record<
  Priority,
  { shell: string; icon: string; badge: string }
> = {
  high: {
    shell: "border-destructive/20 bg-destructive/[0.035]",
    icon: "bg-destructive/10 text-destructive",
    badge: "border-destructive/20 bg-destructive/10 text-destructive",
  },
  medium: {
    shell: "border-amber-500/20 bg-amber-500/[0.04]",
    icon: "bg-amber-500/10 text-amber-600",
    badge: "border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-400",
  },
  low: {
    shell: "border-emerald-500/20 bg-emerald-500/[0.04]",
    icon: "bg-emerald-500/10 text-emerald-600",
    badge: "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
  },
};

const PRIORITY_RUBRIC: Record<Priority, string> = {
  high: "A specific date or time appears with mandatory or deadline language.",
  medium: "The document signals urgency or timing, but not a firm blocking deadline.",
  low: "This is a routine instruction with no immediate time pressure detected.",
};

type Filter = "all" | Priority;

interface Props {
  risks: RiskInsight[];
  filter?: Filter;
  onFilterChange?: (filter: Filter) => void;
}

export function RisksTab({ risks, filter: controlledFilter, onFilterChange }: Props) {
  const [localFilter, setLocalFilter] = useState<Filter>("all");
  const filter = controlledFilter ?? localFilter;
  const setFilter = (value: Filter) =>
    onFilterChange ? onFilterChange(value) : setLocalFilter(value);
  const filtered = filter === "all" ? risks : risks.filter((risk) => risk.priority === filter);

  if (risks.length === 0) {
    return (
      <div className="surface-panel flex min-h-72 flex-col items-center justify-center px-6 py-12 text-center">
        <span className="flex size-14 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600">
          <CheckCircle2 size={24} />
        </span>
        <h2 className="mt-5 text-base font-semibold text-foreground">No risks were flagged</h2>
        <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">
          Papervault did not find deadline, payment, or compliance language requiring
          additional verification.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="surface-panel flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-foreground">Risk review</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Expand each item to see the reasoning and suggested verification step.
          </p>
        </div>
        <FilterPills filter={filter} onChange={setFilter} risks={risks} />
      </div>

      <div className="space-y-3">
        {filtered.map((risk, index) => (
          <RiskCard key={`${risk.issue}-${index}`} risk={risk} />
        ))}
        {filtered.length === 0 && (
          <div className="surface-panel flex min-h-48 flex-col items-center justify-center px-6 text-center">
            <SearchCheck size={22} className="text-muted-foreground" />
            <p className="mt-3 text-sm font-medium text-foreground">
              No {filter}-priority risks
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Choose another filter to view the remaining findings.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function FilterPills({
  filter,
  onChange,
  risks,
}: {
  filter: Filter;
  onChange: (filter: Filter) => void;
  risks: RiskInsight[];
}) {
  return (
    <div className="scrollbar-subtle -mx-1 flex max-w-full gap-1.5 overflow-x-auto px-1 pb-1 sm:pb-0">
      {(["all", "high", "medium", "low"] as Filter[]).map((item) => {
        const count =
          item === "all" ? risks.length : risks.filter((risk) => risk.priority === item).length;
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
            <span className={cn("text-[0.65rem]", filter === item ? "opacity-70" : "opacity-60")}>
              {count}
            </span>
          </button>
        );
      })}
    </div>
  );
}

function RiskCard({ risk }: { risk: RiskInsight }) {
  const [expanded, setExpanded] = useState(false);
  const styles = PRIORITY_STYLES[risk.priority];

  return (
    <article className={cn("overflow-hidden rounded-2xl border transition-colors", styles.shell)}>
      <button
        type="button"
        className="flex w-full items-start gap-3 p-4 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring sm:p-5"
        onClick={() => setExpanded((value) => !value)}
        aria-expanded={expanded}
      >
        <span className={cn("flex size-9 shrink-0 items-center justify-center rounded-xl", styles.icon)}>
          <AlertTriangle size={16} />
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold leading-5 text-foreground">{risk.issue}</span>
            <Badge variant="outline" className={cn("capitalize", styles.badge)}>
              {risk.priority}
            </Badge>
          </span>
          <span className="mt-1.5 block text-xs leading-5 text-muted-foreground">
            {risk.why_it_matters}
          </span>
        </span>
        {expanded ? (
          <ChevronUp size={16} className="mt-1 shrink-0 text-muted-foreground" />
        ) : (
          <ChevronDown size={16} className="mt-1 shrink-0 text-muted-foreground" />
        )}
      </button>

      {expanded && (
        <div className="grid gap-3 border-t border-current/10 px-4 pb-4 pt-4 sm:grid-cols-2 sm:px-5 sm:pb-5">
          <Detail
            icon={<CircleHelp size={14} />}
            title={`Why this is ${risk.priority} priority`}
          >
            <p>{PRIORITY_RUBRIC[risk.priority]}</p>
            {risk.priority_flags && risk.priority_flags.length > 0 && (
              <ul className="mt-2 space-y-1">
                {risk.priority_flags.map((flag) => (
                  <li key={flag} className="flex items-start gap-2">
                    <span className="mt-2 size-1 shrink-0 rounded-full bg-current opacity-50" />
                    {flag}
                  </li>
                ))}
              </ul>
            )}
          </Detail>
          <Detail icon={<SearchCheck size={14} />} title="How to verify">
            <p>{risk.verify_step}</p>
          </Detail>
          {risk.source_snippet && (
            <div className="rounded-xl border border-border/60 bg-background/65 p-3.5 sm:col-span-2">
              <p className="text-[0.65rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                Source evidence
              </p>
              <p className="mt-2 text-xs italic leading-5 text-foreground">
                “{risk.source_snippet}”
              </p>
            </div>
          )}
        </div>
      )}
    </article>
  );
}

function Detail({
  icon,
  title,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-border/60 bg-background/65 p-3.5">
      <p className="flex items-center gap-2 text-xs font-semibold text-foreground">
        {icon}
        {title}
      </p>
      <div className="mt-2 text-xs leading-5 text-muted-foreground">{children}</div>
    </div>
  );
}
