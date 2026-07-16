import type { ApiDocumentInsight } from "../api/contracts";
import {
  buildKeyDeadlines,
  cleanList,
  dedupAndRankDates,
  explainPriority,
  extractAllHints,
  isLikelyContact,
  isTimeSensitive,
  splitSentences,
} from "../documentSignals";
import type { DocumentInsight, RiskInsight } from "../types";
import { mapOfficialNotice } from "./officialNotice";
import { asPriority } from "./shared";

export function mapInsight(
  raw: ApiDocumentInsight,
  filename: string,
  fullText = "",
): DocumentInsight {
  const rawRisks = raw.risks ?? [];
  const rawActions = raw.action_items ?? [];
  const diagnostics = raw.diagnostics;
  const baseRisks: RiskInsight[] = rawRisks.map((risk) => {
    const combined = `${risk.issue} ${risk.why_it_matters} ${risk.source_snippet ?? ""}`;
    const flags = explainPriority(combined);
    return {
      issue: risk.issue,
      why_it_matters: risk.why_it_matters,
      verify_step: risk.suggested_verification,
      source_snippet: risk.source_snippet ?? "",
      priority: asPriority(risk.confidence),
      priority_flags: flags.length ? flags : undefined,
    };
  });

  const seenIssues = new Set(baseRisks.map((risk) => risk.issue.toLowerCase()));
  const candidateIssues = rawActions.filter(isTimeSensitive);
  if (fullText) {
    candidateIssues.push(
      ...splitSentences(fullText).filter(isTimeSensitive),
    );
  }

  const seenCandidates = new Set<string>();
  const synthesized: RiskInsight[] = candidateIssues
    .filter((item) => {
      const key = item.toLowerCase().replace(/\s+/g, " ");
      if (seenIssues.has(key) || seenCandidates.has(key)) return false;
      seenCandidates.add(key);
      return true;
    })
    .map((item) => {
      const flags = explainPriority(item);
      return {
        issue: item,
        why_it_matters:
          "Time-sensitive instruction — missing the window may invalidate the action.",
        verify_step:
          "Confirm the exact time/deadline against the original document and prepare in advance.",
        source_snippet: item,
        priority: "high",
        priority_flags: flags.length ? flags : undefined,
      };
    });

  const explicitDates = (raw.important_dates ?? []).map((item) => item.value);
  const scanCorpus = [...rawActions, raw.summary, fullText].join("\n");
  const importantDates = dedupAndRankDates([
    ...explicitDates,
    ...extractAllHints(scanCorpus),
  ]);

  return {
    filename,
    document_type: raw.classification.document_type,
    confidence: asPriority(raw.confidence),
    summary: raw.summary,
    important_dates: importantDates,
    key_deadlines: buildKeyDeadlines(fullText),
    required_documents: cleanList(raw.required_documents ?? []),
    fees_and_amounts: cleanList(
      (raw.fees_or_amounts ?? []).map((item) => item.value),
    ),
    action_items: cleanList(rawActions),
    risks: [...baseRisks, ...synthesized],
    missing_information: cleanList(raw.missing_information ?? []),
    contact_info: cleanList(raw.contact_information ?? []).filter(
      isLikelyContact,
    ),
    official_notice: raw.official_notice
      ? mapOfficialNotice(raw.official_notice)
      : null,
    analysis_diagnostics: {
      confidence_score: diagnostics?.confidence_score ?? 0,
      classification_confidence: asPriority(
        diagnostics?.classification_confidence ?? raw.classification.confidence,
      ),
      extracted_signal_count: diagnostics?.extracted_signal_count ?? 0,
      grounded_field_count: diagnostics?.grounded_field_count ?? 0,
      reasons: diagnostics?.reasons ?? [],
    },
    limitations: raw.limitations ?? [],
  };
}
