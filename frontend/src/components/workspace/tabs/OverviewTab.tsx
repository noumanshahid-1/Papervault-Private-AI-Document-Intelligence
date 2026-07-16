import {
  AlertTriangle,
  CalendarDays,
  DollarSign,
  FileCheck2,
  ListChecks,
  Sparkles,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ChecklistResult, DocumentInsight } from "@/lib/types";
import { cn } from "@/lib/utils";

interface Props {
  insight: DocumentInsight;
  checklist: ChecklistResult;
}

export function OverviewTab({ insight, checklist }: Props) {
  const panels = [
    {
      icon: CalendarDays,
      title: "Key dates",
      items: insight.important_dates,
      emptyText: "No dates were identified.",
      tone: "text-accent bg-accent/10",
    },
    {
      icon: FileCheck2,
      title: "Required documents",
      items: insight.required_documents,
      emptyText: "No supporting documents were listed.",
      tone: "text-violet-600 bg-violet-500/10",
    },
    {
      icon: DollarSign,
      title: "Fees and amounts",
      items: insight.fees_and_amounts,
      emptyText: "No amounts were identified.",
      tone: "text-amber-600 bg-amber-500/10",
    },
    {
      icon: AlertTriangle,
      title: "High-priority actions",
      items: checklist.items
        .filter((item) => item.priority === "high")
        .map((item) => item.task),
      emptyText: "No high-priority actions were identified.",
      tone: "text-destructive bg-destructive/10",
    },
  ];

  return (
    <div className="space-y-4">
      <Card className="overflow-hidden border-accent/15">
        <div className="h-1 bg-gradient-to-r from-accent via-sky-400 to-emerald-400" />
        <CardContent className="p-5 sm:p-6">
          <div className="flex items-start gap-3">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-accent/10 text-accent">
              <Sparkles size={18} />
            </span>
            <div>
              <p className="eyebrow">Document summary</p>
              <p className="mt-3 text-sm leading-7 text-foreground sm:text-[0.95rem]">
                {insight.summary}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {panels.map((panel) => (
          <QuickPanel key={panel.title} {...panel} />
        ))}
      </div>

      <Card className="border-primary/15 bg-primary/[0.035]">
        <CardContent className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <ListChecks size={18} />
            </span>
            <div>
              <p className="text-sm font-semibold text-foreground">Review plan prepared</p>
              <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                {checklist.total} tasks were organized by urgency, including{" "}
                {checklist.high_priority_count} high-priority{" "}
                {checklist.high_priority_count === 1 ? "item" : "items"}.
              </p>
            </div>
          </div>
          <span className="w-fit rounded-full border border-primary/15 bg-background/70 px-3 py-1.5 text-xs font-medium text-primary">
            {insight.confidence} confidence
          </span>
        </CardContent>
      </Card>
    </div>
  );
}

function QuickPanel({
  icon: Icon,
  title,
  items,
  emptyText,
  tone,
}: {
  icon: React.ElementType;
  title: string;
  items: string[];
  emptyText: string;
  tone: string;
}) {
  return (
    <Card className="min-w-0">
      <CardHeader className="flex-row items-center justify-between space-y-0 px-5 pb-2 pt-5">
        <div className="flex items-center gap-3">
          <span className={cn("flex size-9 items-center justify-center rounded-lg", tone)}>
            <Icon size={16} />
          </span>
          <CardTitle className="text-sm font-semibold">{title}</CardTitle>
        </div>
        <span className="rounded-full bg-muted px-2 py-1 text-[0.65rem] font-medium text-muted-foreground">
          {items.length}
        </span>
      </CardHeader>
      <CardContent className="px-5 pb-5 pt-2">
        {items.length === 0 ? (
          <p className="rounded-xl border border-dashed border-border bg-muted/20 px-3 py-4 text-xs text-muted-foreground">
            {emptyText}
          </p>
        ) : (
          <ul className="space-y-2.5">
            {items.slice(0, 5).map((item) => (
              <li key={item} className="flex items-start gap-2.5 text-xs leading-5 text-foreground">
                <span className="mt-2 size-1.5 shrink-0 rounded-full bg-accent/70" />
                <span className="min-w-0 break-words">{item}</span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
