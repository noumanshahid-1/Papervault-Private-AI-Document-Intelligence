import { afterEach, describe, expect, it } from "vitest";
import {
  FIXTURE_CHECKLIST,
  FIXTURE_EXTRACTION,
  FIXTURE_INSIGHT,
} from "@/lib/fixtures";
import { useWorkspaceStore } from "./workspaceStore";

describe("workspace restoration", () => {
  afterEach(() => {
    useWorkspaceStore.getState().reset();
  });

  it("loads a saved review into one ready workspace state", () => {
    useWorkspaceStore.getState().setError("previous failure");
    useWorkspaceStore.getState().addQA({
      question: "Old question",
      answer: "Old answer",
      grounded: true,
      confidence: "high",
      source_snippets: [],
      mode: "extractive",
      retrieval: {
        embedding_provider: "hashing",
        embedding_model: "hashing-384",
        vector_backend: "python",
        requested_top_k: 0,
        retrieved_count: 0,
        relevant_count: 0,
        top_score: 0,
        mean_score: 0,
        score_spread: 0,
        query_terms: [],
        matched_terms: [],
        warnings: [],
      },
      generation: {
        requested_mode: "auto",
        actual_mode: "extractive",
        configured_model: null,
        model_used: null,
        local_llm_enabled: false,
        fallback_reason: null,
      },
      explanation: {
        strategy: "no_answer",
        confidence_reasons: [],
        limitations: [],
      },
    });

    useWorkspaceStore
      .getState()
      .loadWorkspace(FIXTURE_EXTRACTION, FIXTURE_INSIGHT, FIXTURE_CHECKLIST);

    const state = useWorkspaceStore.getState();
    expect(state.phase).toBe("ready");
    expect(state.error).toBeNull();
    expect(state.extraction).toBe(FIXTURE_EXTRACTION);
    expect(state.insight).toBe(FIXTURE_INSIGHT);
    expect(state.checklist).toBe(FIXTURE_CHECKLIST);
    expect(state.qaHistory).toEqual([]);
  });
});
