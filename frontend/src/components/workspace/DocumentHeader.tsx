import { Link } from "react-router-dom";
import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  FilePlus2,
  FileText,
  ShieldCheck,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type {
  ChecklistResult,
  DocumentInsight,
  ExtractionResult,
} from "@/lib/types";

interface Props {
  extraction: ExtractionResult;
  insight: DocumentInsight;
  checklist: ChecklistResult;
  onSelectActions?: () => void;
  onSelectHighPriority?: () => void;
  onSelectRisks?: () => void;
  onSelectDates?: () => void;
}

const CONFIDENCE_STYLES = {
  high: "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
  medium: "border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-400",
  low: "border-destructive/20 bg-destructive/10 text-destructive",
};

export function DocumentHeader({
  extraction,
  insight,
  checklist,
  onSelectActions,
  onSelectHighPriority,
  onSelectRisks,
  onSelectDates,
}: Props) {
  return (
    <header className="border-b border-border/70 bg-card/72 backdrop-blur">
      <div className="mx-auto w-full max-w-7xl px-4 py-5 sm:px-6 sm:py-6 lg:px-10">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex min-w-0 items-start gap-3.5">
            <span className="flex size-11 shrink-0 items-center justify-center rounded-xl border border-accent/15 bg-accent/10 text-accent">
              <FileText size={20} />
            </span>
            <div className="min-w-0">
              <p className="eyebrow">Active review</p>
              <h1 className="mt-1.5 truncate text-lg font-semibold tracking-tight text-foreground sm:text-xl">
                {extraction.filename}
              </h1>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <Badge variant="secondary" className="capitalize">
                  {insight.document_type.replace(/_/g, " ")}
                </Badge>
                {extraction.page_count ? (
                  <span className="text-xs text-muted-foreground">
                    {extraction.page_count} {extraction.page_count === 1 ? "page" : "pages"}
                  </span>
                ) : null}
                <span className="text-xs text-muted-foreground">
                  {extraction.content_available
                    ? `${extraction.word_count.toLocaleString()} words`
                    : "Source text not retained"}
                </span>
                <Badge
                  variant="outline"
                  className={cn("capitalize", CONFIDENCE_STYLES[insight.confidence])}
                >
                  Analysis: {insight.confidence}
                </Badge>
                <Badge
                  variant="outline"
                  className={cn(
                    "capitalize",
                    CONFIDENCE_STYLES[extraction.diagnostics.confidence],
                  )}
                >
                  Extraction: {extraction.diagnostics.confidence}
                </Badge>
              </div>
            </div>
          </div>

          <Button asChild variant="outline" size="sm" className="w-full sm:w-auto">
            <Link to="/">
              <FilePlus2 />
              New review
            </Link>
          </Button>
        </div>

        <div className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Metric
            icon={<CheckCircle2 size={16} />}
            value={checklist.total}
            label="Action items"
            detail="Open full checklist"
            tone="text-emerald-600 bg-emerald-500/10"
            onClick={onSelectActions}
          />
          <Metric
            icon={<AlertTriangle size={16} />}
            value={checklist.high_priority_count}
            label="High priority"
            detail="Needs attention first"
            tone="text-amber-600 bg-amber-500/10"
            onClick={onSelectHighPriority}
          />
          <Metric
            icon={<ShieldCheck size={16} />}
            value={insight.risks.length}
            label="Risks flagged"
            detail="Review verification steps"
            tone="text-destructive bg-destructive/10"
            onClick={onSelectRisks}
          />
          <Metric
            icon={<CalendarDays size={16} />}
            value={insight.important_dates.length}
            label="Key dates"
            detail="See timing details"
            tone="text-accent bg-accent/10"
            onClick={onSelectDates}
          />
        </div>
      </div>
    </header>
  );
}

function Metric({
  icon,
  value,
  label,
  detail,
  tone,
  onClick,
}: {
  icon: React.ReactNode;
  value: number;
  label: string;
  detail: string;
  tone: string;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!onClick}
      className="group flex min-w-0 items-center gap-3 rounded-xl border border-border/70 bg-background/65 p-3 text-left transition-all hover:-translate-y-0.5 hover:border-accent/25 hover:bg-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-default sm:p-3.5"
    >
      <span className={cn("flex size-9 shrink-0 items-center justify-center rounded-lg", tone)}>
        {icon}
      </span>
      <span className="min-w-0">
        <span className="flex items-baseline gap-2">
          <span className="text-lg font-semibold tracking-tight text-foreground">{value}</span>
          <span className="truncate text-xs font-medium text-foreground">{label}</span>
        </span>
        <span className="mt-0.5 hidden truncate text-[0.68rem] text-muted-foreground sm:block">
          {detail}
        </span>
      </span>
    </button>
  );
}
