import type { ApiQuestionAnswer } from "../api/contracts";
import type { QuestionAnswer } from "../types";
import { asPriority } from "./shared";

export function mapQA(
  raw: ApiQuestionAnswer,
  question: string,
): QuestionAnswer {
  const snippets = raw.source_snippets ?? [];
  const retrieval = raw.retrieval;
  const generation = raw.generation;
  const explanation = raw.explanation;
  return {
    question,
    answer: raw.answer,
    source_snippets: snippets.map((snippet) => ({
      text: snippet.text,
      chunk_id: snippet.chunk_id,
      score: snippet.score,
      page_number: snippet.page_number ?? null,
      source_filename: snippet.source_filename ?? null,
    })),
    confidence: asPriority(raw.confidence),
    grounded: snippets.length > 0,
    mode: raw.mode,
    retrieval: {
      embedding_provider: retrieval?.embedding_provider ?? "unknown",
      embedding_model: retrieval?.embedding_model ?? null,
      vector_backend: retrieval?.vector_backend ?? "python",
      requested_top_k: retrieval?.requested_top_k ?? 0,
      retrieved_count: retrieval?.retrieved_count ?? snippets.length,
      relevant_count: retrieval?.relevant_count ?? snippets.length,
      top_score: retrieval?.top_score ?? snippets[0]?.score ?? 0,
      mean_score: retrieval?.mean_score ?? 0,
      score_spread: retrieval?.score_spread ?? 0,
      query_terms: retrieval?.query_terms ?? [],
      matched_terms: retrieval?.matched_terms ?? [],
      warnings: retrieval?.warnings ?? [],
    },
    generation: {
      requested_mode: generation?.requested_mode ?? "auto",
      actual_mode: generation?.actual_mode ?? raw.mode,
      configured_model: generation?.configured_model ?? null,
      model_used: generation?.model_used ?? null,
      local_llm_enabled: generation?.local_llm_enabled ?? false,
      fallback_reason: generation?.fallback_reason ?? null,
    },
    explanation: {
      strategy: explanation?.strategy ?? "unknown",
      confidence_reasons: explanation?.confidence_reasons ?? [],
      limitations: explanation?.limitations ?? [],
    },
  };
}
