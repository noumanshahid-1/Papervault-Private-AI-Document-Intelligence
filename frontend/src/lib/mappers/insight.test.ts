import { describe, expect, it } from "vitest";
import type { ApiDocumentInsight } from "../api/contracts";
import { mapInsight } from "./insight";

const rawInsight: ApiDocumentInsight = {
  classification: {
    document_type: "government notice",
    confidence: "high",
    evidence: ["Government Gazette"],
  },
  confidence: "high",
  diagnostics: {
    confidence_score: 0.9,
    classification_confidence: "high",
    extracted_signal_count: 4,
    grounded_field_count: 4,
    reasons: ["Four structured fields were grounded."],
  },
  summary: "A revenue authority notification assigns tax payment liability.",
  action_items: ["Ensure timely collection and payment of sales tax."],
  contact_information: [],
  fees_or_amounts: [{ value: "Rs. 3,000/- per goods declaration" }],
  important_dates: [{ value: "16 July 2025" }],
  limitations: [],
  missing_information: [],
  required_documents: [],
  risks: [],
  official_notice: {
    issuing_authority: "Khyber Pakhtunkhwa Revenue Authority",
    notice_type: "notification",
    notice_number: "KPRA/ADMN/GN/2025/3337",
    gazette_date: "16 JULY, 2025",
    issue_date: "16 June, 2025",
    legal_basis: "Section 10 read with section 14-A",
    subject: "Sales tax liability for specified services",
    effective_timing: "immediate effect",
    payment_timing: "not later than the 15 day of the following tax period",
    table_rows: [
      {
        service: "Custom House Agents",
        heading: "9806.3000",
        liable_party: "Pakistan Single Window",
        rate_or_amount: "Rs. 3,000/- per goods declaration",
        source_snippet: "Custom House Agents Pakistan Single Window",
      },
    ],
    compliance_duties: ["Ensure timely collection and payment of sales tax."],
    consequences: ["Penalty and default surcharge may apply."],
    confidence: "high",
    limitations: ["Verify the scanned table against the gazette."],
  },
};

describe("mapInsight", () => {
  it("preserves the complete official-notice contract", () => {
    const insight = mapInsight(rawInsight, "notice.pdf");

    expect(insight.official_notice).toMatchObject({
      issuing_authority: "Khyber Pakhtunkhwa Revenue Authority",
      notice_type: "notification",
      notice_number: "KPRA/ADMN/GN/2025/3337",
      issue_date: "16 June, 2025",
      effective_timing: "immediate effect",
      payment_timing: "not later than the 15 day of the following tax period",
      confidence: "high",
    });
    expect(insight.official_notice?.table_rows[0]).toEqual({
      service: "Custom House Agents",
      heading: "9806.3000",
      liable_party: "Pakistan Single Window",
      rate_or_amount: "Rs. 3,000/- per goods declaration",
      source_snippet: "Custom House Agents Pakistan Single Window",
    });
    expect(insight.official_notice?.compliance_duties).toHaveLength(1);
    expect(insight.official_notice?.consequences).toHaveLength(1);
    expect(insight.official_notice?.limitations).toHaveLength(1);
  });

  it("keeps non-notice documents free of an empty notice shell", () => {
    const insight = mapInsight(
      { ...rawInsight, official_notice: null },
      "letter.pdf",
    );

    expect(insight.official_notice).toBeNull();
  });
});
