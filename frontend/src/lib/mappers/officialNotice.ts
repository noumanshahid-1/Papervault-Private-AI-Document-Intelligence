import type { ApiOfficialNoticeBreakdown } from "../api/contracts";
import type { OfficialNoticeBreakdown } from "../types";
import { asPriority } from "./shared";

export function mapOfficialNotice(
  raw: ApiOfficialNoticeBreakdown,
): OfficialNoticeBreakdown {
  return {
    issuing_authority: raw.issuing_authority ?? null,
    notice_type: raw.notice_type ?? null,
    notice_number: raw.notice_number ?? null,
    gazette_date: raw.gazette_date ?? null,
    issue_date: raw.issue_date ?? null,
    legal_basis: raw.legal_basis ?? null,
    subject: raw.subject ?? null,
    effective_timing: raw.effective_timing ?? null,
    payment_timing: raw.payment_timing ?? null,
    table_rows: (raw.table_rows ?? []).map((row) => ({
      service: row.service ?? null,
      heading: row.heading ?? null,
      liable_party: row.liable_party ?? null,
      rate_or_amount: row.rate_or_amount ?? null,
      source_snippet: row.source_snippet ?? null,
    })),
    compliance_duties: raw.compliance_duties ?? [],
    consequences: raw.consequences ?? [],
    confidence: asPriority(raw.confidence),
    limitations: raw.limitations ?? [],
  };
}
