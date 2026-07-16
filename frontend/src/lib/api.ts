import type {
  ApiAnalyzeRequest,
  ApiAskRequest,
  ApiChecklistResult,
  ApiDocumentInsight,
  ApiExtractionResult,
  ApiIntelligenceRuntimeResponse,
  ApiQuestionAnswer,
  ApiSavedSession,
  ApiSaveSessionRequest,
  ApiSessionCreatedResponse,
  ApiSessionMetadata,
  ApiSessionsClearedResponse,
} from "./api/contracts";
import { request } from "./api/client";
import { mapChecklist } from "./mappers/checklist";
import { mapExtraction } from "./mappers/extraction";
import { mapInsight } from "./mappers/insight";
import { mapQA } from "./mappers/qa";
import {
  mapSavedSession,
  mapSessionMetadata,
  type RestoredSession,
} from "./mappers/session";
import type {
  ChecklistResult,
  DocumentInsight,
  IntelligenceRuntime,
  QuestionAnswer,
  SessionMetadata,
} from "./types";

export async function extractDocument(file: File) {
  const form = new FormData();
  form.append("file", file);
  const raw = await request<ApiExtractionResult>("/api/extract", {
    method: "POST",
    body: form,
  });
  return mapExtraction(raw, file);
}

export async function analyzeDocument(
  text: string,
  filename: string,
): Promise<{ insight: DocumentInsight; raw: ApiDocumentInsight }> {
  const body: ApiAnalyzeRequest = { text, filename };
  const raw = await request<ApiDocumentInsight>("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return { insight: mapInsight(raw, filename, text), raw };
}

export async function buildChecklist(
  text: string,
  filename: string,
): Promise<{ checklist: ChecklistResult; raw: ApiChecklistResult }> {
  const body: ApiAnalyzeRequest = { text, filename };
  const raw = await request<ApiChecklistResult>("/api/checklist", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return { checklist: mapChecklist(raw, filename), raw };
}

export async function askDocument(
  text: string,
  question: string,
  filename: string,
  options?: {
    answerMode?: "auto" | "extractive" | "local_llm";
    model?: string | null;
    topK?: number;
  },
): Promise<QuestionAnswer> {
  const body: ApiAskRequest = {
    text,
    question,
    filename,
    top_k: options?.topK ?? 5,
    answer_mode: options?.answerMode ?? "auto",
    model: options?.model ?? null,
  };
  const raw = await request<ApiQuestionAnswer>("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return mapQA(raw, question);
}

export async function getIntelligenceRuntime(): Promise<IntelligenceRuntime> {
  const raw = await request<ApiIntelligenceRuntimeResponse>(
    "/api/intelligence/runtime",
  );
  return {
    local_llm_enabled: raw.local_llm_enabled,
    ollama_available: raw.ollama_available,
    configured_model: raw.configured_model,
    available_models: (raw.available_models ?? []).map((model) => ({
      name: model.name,
      size_bytes: model.size_bytes ?? null,
      modified_at: model.modified_at ?? null,
    })),
    embedding_provider: raw.embedding_provider,
    embedding_model: raw.embedding_model ?? null,
    vector_backend: raw.vector_backend,
    status_message: raw.status_message,
  };
}

export async function saveSession(
  data: ApiSaveSessionRequest,
): Promise<ApiSessionCreatedResponse> {
  return request<ApiSessionCreatedResponse>("/api/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function clearSessions(): Promise<ApiSessionsClearedResponse> {
  return request<ApiSessionsClearedResponse>("/api/sessions", {
    method: "DELETE",
  });
}

export async function listSessions(): Promise<SessionMetadata[]> {
  const raw = await request<ApiSessionMetadata[]>("/api/sessions");
  return raw.map(mapSessionMetadata);
}

export async function getSession(id: string): Promise<RestoredSession> {
  const raw = await request<ApiSavedSession>(
    `/api/sessions/${encodeURIComponent(id)}`,
  );
  return mapSavedSession(raw);
}
