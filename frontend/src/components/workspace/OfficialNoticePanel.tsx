import {
  AlertTriangle,
  Building2,
  CalendarDays,
  Clock3,
  Landmark,
  Scale,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { OfficialNoticeBreakdown } from "@/lib/types";

interface Props {
  notice: OfficialNoticeBreakdown;
}

export function OfficialNoticePanel({ notice }: Props) {
  const metadata = [
    {
      label: "Issuing authority",
      value: notice.issuing_authority,
      icon: Building2,
    },
    { label: "Notice number", value: notice.notice_number, icon: Landmark },
    { label: "Gazette date", value: notice.gazette_date, icon: CalendarDays },
    { label: "Issue date", value: notice.issue_date, icon: CalendarDays },
    { label: "Legal basis", value: notice.legal_basis, icon: Scale },
    {
      label: "Effective timing",
      value: notice.effective_timing,
      icon: Clock3,
    },
    {
      label: "Payment timing",
      value: notice.payment_timing,
      icon: Clock3,
    },
  ].filter((item) => item.value);

  return (
    <Card className="overflow-hidden border-primary/20">
      <div className="h-1 bg-gradient-to-r from-primary via-accent to-sky-400" />
      <CardHeader className="px-5 pb-3 pt-5">
        <div className="flex flex-wrap items-center gap-2.5">
          <CardTitle className="flex items-center gap-2 text-sm font-semibold">
            <span className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Landmark size={16} />
            </span>
            Official Notice Breakdown
          </CardTitle>
          {notice.notice_type && (
            <Badge variant="secondary" className="capitalize">
              {notice.notice_type.replace(/_/g, " ")}
            </Badge>
          )}
          <Badge
            variant="outline"
            className="border-emerald-500/20 bg-emerald-500/10 capitalize text-emerald-700 sm:ml-auto dark:text-emerald-400"
          >
            {notice.confidence} confidence
          </Badge>
        </div>
        {notice.subject && (
          <p className="mt-2 text-sm leading-6 text-foreground">
            {notice.subject}
          </p>
        )}
      </CardHeader>

      <CardContent className="space-y-4 px-5 pb-5">
        {metadata.length > 0 && (
          <dl className="grid gap-3 sm:grid-cols-2">
            {metadata.map(({ label, value, icon: Icon }) => (
              <div
                key={label}
                className="min-w-0 rounded-xl border border-border/50 bg-muted/30 p-3.5"
              >
                <dt className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Icon size={12} />
                  {label}
                </dt>
                <dd className="mt-1.5 break-words text-xs font-medium leading-5 text-foreground">
                  {value}
                </dd>
              </div>
            ))}
          </dl>
        )}

        {notice.table_rows.length > 0 && (
          <div>
            <div className="space-y-3 sm:hidden">
              {notice.table_rows.map((row, index) => (
                <div
                  key={`${row.heading ?? "row"}-${index}`}
                  className="rounded-xl border border-border bg-muted/20 p-4"
                >
                  <p className="text-sm font-semibold text-foreground">
                    {row.service ?? "Unspecified service"}
                  </p>
                  <dl className="mt-3 grid gap-3">
                    <MobileField label="Heading" value={row.heading} />
                    <MobileField label="Liable party" value={row.liable_party} />
                    <MobileField label="Rate or amount" value={row.rate_or_amount} />
                  </dl>
                </div>
              ))}
            </div>

            <div className="hidden overflow-hidden rounded-xl border border-border sm:block">
              <table className="w-full table-fixed text-left text-xs">
                <thead className="bg-muted/50 text-muted-foreground">
                  <tr>
                    <th className="w-1/4 px-3 py-2.5 font-medium">Service</th>
                    <th className="w-[15%] px-3 py-2.5 font-medium">Heading</th>
                    <th className="w-1/4 px-3 py-2.5 font-medium">Liable party</th>
                    <th className="px-3 py-2.5 font-medium">Rate or amount</th>
                  </tr>
                </thead>
                <tbody>
                  {notice.table_rows.map((row, index) => (
                    <tr
                      key={`${row.heading ?? "row"}-${index}`}
                      className="border-t border-border"
                    >
                      <td className="break-words px-3 py-3">{row.service ?? "—"}</td>
                      <td className="break-words px-3 py-3">{row.heading ?? "—"}</td>
                      <td className="break-words px-3 py-3">{row.liable_party ?? "—"}</td>
                      <td className="break-words px-3 py-3">{row.rate_or_amount ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-2">
          <NoticeList
            title="Compliance duties"
            items={notice.compliance_duties}
            tone="default"
          />
          <NoticeList
            title="Possible consequences"
            items={notice.consequences}
            tone="warning"
          />
        </div>

        {notice.limitations.length > 0 && (
          <div className="rounded-xl border border-amber-500/20 bg-amber-500/[0.055] p-3.5">
            <p className="flex items-center gap-1.5 text-xs font-medium text-foreground">
              <AlertTriangle size={13} className="text-amber-600" />
              Extraction limitations
            </p>
            <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
              {notice.limitations.map((item) => (
                <li key={item}>• {item}</li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function NoticeList({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "default" | "warning";
}) {
  if (items.length === 0) return null;

  return (
    <div
      className={
        tone === "warning"
          ? "rounded-xl border border-destructive/20 bg-destructive/[0.045] p-3.5"
          : "rounded-xl border border-border bg-muted/20 p-3.5"
      }
    >
      <p className="text-xs font-medium text-foreground">{title}</p>
      <ul className="mt-2 space-y-1.5">
        {items.map((item) => (
          <li key={item} className="text-xs leading-relaxed text-muted-foreground">
            • {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

function MobileField({
  label,
  value,
}: {
  label: string;
  value: string | null;
}) {
  return (
    <div>
      <dt className="text-[0.65rem] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
        {label}
      </dt>
      <dd className="mt-1 break-words text-xs font-medium leading-5 text-foreground">
        {value ?? "—"}
      </dd>
    </div>
  );
}
