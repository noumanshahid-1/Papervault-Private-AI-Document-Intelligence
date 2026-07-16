import { describe, expect, it } from "vitest";
import type {
  ApiExtractionResult,
  ApiQuestionAnswer,
} from "../api/contracts";
import { mapExtraction } from "./extraction";
import { mapQA } from "./qa";

describe("diagnostic mappers", () => {
  it("preserves extraction and OCR quality signals", () => {
    const raw: ApiExtractionResult = {
      filename: "scan.png",
      document_type: "png",
      text: "Readable OCR text",
      diagnostics: {
        engine: "rapidocr",
        confidence: "medium",
        confidence_score: 0.68,
        is_ocr: true,
        ocr_engine: "rapidocr",
        ocr_mean_confidence: 0.71,
        word_count: 3,
        character_count: 17,
        readable_character_ratio: 0.98,
        suspicious_character_ratio: 0.01,
        page_text_coverage: null,
        signals: ["OCR mean confidence is 71%."],
        recommendations: ["Verify document codes."],
      },
    };

    const mapped = mapExtraction(raw, { type: "image/png" } as File);

    expect(mapped.diagnostics).toMatchObject({
      engine: "rapidocr",
      confidence: "medium",
      is_ocr: true,
      ocr_mean_confidence: 0.71,
    });
    expect(mapped.diagnostics.recommendations).toEqual(["Verify document codes."]);
  });

  it("preserves retrieval, generation, source, and explanation diagnostics", () => {
    const raw: ApiQuestionAnswer = {
      answer: "The deadline is 15 July 2026.",
      confidence: "medium",
      mode: "extractive",
      source_snippets: [
        {
          text: "You must respond by 15 July 2026.",
          chunk_id: "offer.pdf:1",
          score: 0.73,
          page_number: 1,
          source_filename: "offer.pdf",
        },
      ],
      retrieval: {
        embedding_provider: "hashing",
        embedding_model: "hashing-384",
        vector_backend: "faiss",
        requested_top_k: 5,
        retrieved_count: 5,
        relevant_count: 2,
        top_score: 0.73,
        mean_score: 0.32,
        score_spread: 0.61,
        query_terms: ["deadline"],
        matched_terms: ["deadline"],
        warnings: [],
      },
      generation: {
        requested_mode: "local_llm",
        actual_mode: "extractive",
        configured_model: "qwen2.5:7b",
        local_llm_enabled: true,
        fallback_reason: "Ollama was unavailable.",
      },
      explanation: {
        strategy: "direct_rule",
        confidence_reasons: ["A deadline rule matched."],
        limitations: ["Verify the source."],
      },
    };

    const mapped = mapQA(raw, "What is the deadline?");

    expect(mapped.source_snippets[0].score).toBe(0.73);
    expect(mapped.retrieval.vector_backend).toBe("faiss");
    expect(mapped.generation.configured_model).toBe("qwen2.5:7b");
    expect(mapped.generation.fallback_reason).toContain("unavailable");
    expect(mapped.explanation.strategy).toBe("direct_rule");
  });
});
