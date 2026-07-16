import {
  AlarmClock,
  CalendarDays,
  CircleHelp,
  Contact,
  DollarSign,
  FileCheck2,
  SearchX,
  Zap,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { OfficialNoticePanel } from "@/components/workspace/OfficialNoticePanel";
import type { DocumentInsight } from "@/lib/types";
import { cn } from "@/lib/utils";

interface Props {
  insight: DocumentInsight;
}

export function FindingsTab({ insight }: Props) {
  const deadlines = insight.key_deadlines ?? [];
  const groups = [
    {
      icon: CalendarDays,
      title: "Important dates",
      items: insight.important_dates,
      tone: "text-accent bg-accent/10",
    },
    {
      icon: FileCheck2,
      title: "Required documents",
      items: insight.required_documents,
      tone: "text-violet-600 bg-violet-500/10",
    },
    {
      icon: Zap,
      title: "Action items",
      items: insight.action_items,
      tone: "text-orange-600 bg-orange-500/10",
    },
    {
      icon: DollarSign,
      title: "Fees and amounts",
      items: insight.fees_and_amounts,
      tone: "text-amber-600 bg-amber-500/10",
    },
    {
      icon: Contact,
      title: "Contact information",
      items: insight.contact_info,
      tone: "text-emerald-600 bg-emerald-500/10",
    },
    {
      icon: CircleHelp,
      title: "Missing information",
      items: insight.missing_information,
      tone: "text-muted-foreground bg-muted",
    },
  ].filter((group) => group.items.length > 0);

  const hasFindings = Boolean(insight.official_notice) || deadlines.length > 0 || groups.length > 0;

  if (!hasFindings) {
    return (
      <Card>
        <CardContent className="flex min-h-72 flex-col items-center justify-center px-6 py-12 text-center">
          <span className="flex size-14 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
            <SearchX size={24} />
          </span>
          <h2 className="mt-5 text-base font-semibold text-foreground">No structured findings</h2>
          <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">
            The document did not contain recognizable dates, fees, contacts, or
            required actions.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {insight.official_notice && <OfficialNoticePanel notice={insight.official_notice} />}

      {deadlines.length > 0 && (
        <Card className="border-destructive/20 bg-destructive/[0.035]">
          <CardHeader className="px-5 pb-2 pt-5">
            <CardTitle className="flex flex-wrap items-center gap-2 text-sm font-semibold">
              <span className="flex size-9 items-center justify-center rounded-lg bg-destructive/10 text-destructive">
                <AlarmClock size={16} />
              </span>
              Critical deadlines
              <span className="rounded-full bg-destructive/10 px-2 py-1 text-[0.65rem] font-medium text-destructive">
                {deadlines.length}
              </span>
            </CardTitle>
            <p className="pl-11 text-xs text-muted-foreground">
              Dates connected to deadline or mandatory-action language.
            </p>
          </CardHeader>
          <CardContent className="grid gap-3 px-5 pb-5 pt-2 md:grid-cols-2">
            {deadlines.map((deadline) => (
              <div
                key={`${deadline.text}-${deadline.context}`}
                className="rounded-xl border border-destructive/15 bg-background/75 p-3.5"
              >
                <p className="text-sm font-semibold text-destructive">{deadline.text}</p>
                <p className="mt-1.5 text-xs italic leading-5 text-muted-foreground">
                  “{deadline.context}”
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {groups.map(({ icon: Icon, title, items, tone }) => (
          <Card key={title} className="min-w-0">
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
              <ul className="space-y-2.5">
                {items.map((item) => (
                  <li key={item} className="flex items-start gap-2.5 text-xs leading-5 text-foreground">
                    <span className="mt-2 size-1.5 shrink-0 rounded-full bg-accent/70" />
                    <span className="min-w-0 break-words">{item}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
