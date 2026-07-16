import type {
  ApiSavedSession,
  ApiSessionMetadata,
} from "../api/contracts";
import type {
  ChecklistResult,
  DocumentInsight,
  ExtractionResult,
  SessionMetadata,
} from "../types";
import { mapChecklist } from "./checklist";
import { mapInsight } from "./insight";

export interface RestoredSession {
  extraction: ExtractionResult;
  insight: DocumentInsight;
  checklist: ChecklistResult;
}

export function mapSessionMetadata(
  raw: ApiSessionMetadata,
): SessionMetadata {
  return {
    id: raw.session_id,
    filename: raw.filename,
    document_type: raw.document_type,
    created_at: raw.created_at,
    text_hash: raw.extracted_text_hash,
    content_stored: raw.content_stored,
  };
}

export function mapSavedSession(raw: ApiSavedSession): RestoredSession {
  const text = raw.extracted_text ?? "";
  return {
    extraction: {
      filename: raw.filename,
      content_type: "",
      extracted_text: text,
      page_count: null,
      word_count: text.split(/\s+/).filter(Boolean).length,
      char_count: text.length,
      extraction_method: "restored",
      warnings: [],
      extracted_text_hash: raw.extracted_text_hash,
      content_available: raw.content_stored && text.length > 0,
      diagnostics: {
        engine: "restored",
        confidence: text.length > 0 ? "medium" : "low",
        confidence_score: text.length > 0 ? 0.6 : 0,
        is_ocr: false,
        ocr_engine: null,
        ocr_mean_confidence: null,
        word_count: text.split(/\s+/).filter(Boolean).length,
        character_count: text.length,
        readable_character_ratio: text.length > 0 ? 1 : 0,
        suspicious_character_ratio: 0,
        page_text_coverage: null,
        signals: text.length > 0 ? ["Restored retained source text."] : [],
        recommendations:
          text.length > 0
            ? []
            : ["Re-upload the source to assess extraction quality."],
      },
    },
    insight: mapInsight(raw.insight, raw.filename, text),
    checklist: mapChecklist(raw.checklist, raw.filename),
  };
}
