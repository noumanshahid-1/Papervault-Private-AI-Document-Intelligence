import type { ApiExtractionResult } from "../api/contracts";
import type { ExtractionResult } from "../types";

export function mapExtraction(
  raw: ApiExtractionResult,
  file: File,
): ExtractionResult {
  const text = raw.text ?? "";
  const diagnostics = raw.diagnostics;
  return {
    filename: raw.filename,
    content_type: file.type,
    extracted_text: text,
    page_count: raw.page_count ?? null,
    word_count: text.split(/\s+/).filter(Boolean).length,
    char_count: text.length,
    extraction_method: raw.diagnostics?.engine ?? "local",
    warnings: raw.warnings ?? [],
    extracted_text_hash: "",
    content_available: true,
    diagnostics: {
      engine: diagnostics?.engine ?? String(raw.metadata?.engine ?? "local"),
      confidence:
        diagnostics?.confidence === "high" ||
        diagnostics?.confidence === "low"
          ? diagnostics.confidence
          : "medium",
      confidence_score: diagnostics?.confidence_score ?? (text ? 0.6 : 0),
      is_ocr: diagnostics?.is_ocr ?? false,
      ocr_engine: diagnostics?.ocr_engine ?? null,
      ocr_mean_confidence: diagnostics?.ocr_mean_confidence ?? null,
      word_count: diagnostics?.word_count ?? text.split(/\s+/).filter(Boolean).length,
      character_count: diagnostics?.character_count ?? text.length,
      readable_character_ratio: diagnostics?.readable_character_ratio ?? (text ? 1 : 0),
      suspicious_character_ratio: diagnostics?.suspicious_character_ratio ?? 0,
      page_text_coverage: diagnostics?.page_text_coverage ?? null,
      signals: diagnostics?.signals ?? [],
      recommendations: diagnostics?.recommendations ?? [],
    },
  };
}
