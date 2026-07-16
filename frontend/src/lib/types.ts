// Frontend view models. Raw backend response shapes are mapped in lib/api.ts.

export interface HealthResponse {
  status: string;
  app: string;
}

export interface UploadedDocument {
  filename: string;
  content_type: string;
  size_bytes: number;
  supported: boolean;
}

export interface ExtractionDiagnostics {
  engine: string;
  confidence: "high" | "medium" | "low";
  confidence_score: number;
  is_ocr: boolean;
  ocr_engine: string | null;
  ocr_mean_confidence: number | null;
  word_count: number;
  character_count: number;
  readable_character_ratio: number;
  suspicious_character_ratio: number;
  page_text_coverage: number | null;
  signals: string[];
  recommendations: string[];
}

export interface ExtractionResult {
  filename: string;
  content_type: string;
  extracted_text: string;
  page_count: number | null;
  word_count: number;
  char_count: number;
  extraction_method: string;
  warnings: string[];
  extracted_text_hash: string;
  content_available: boolean;
  diagnostics: ExtractionDiagnostics;
}

export interface RiskInsight {
  issue: string;
  why_it_matters: string;
  verify_step: string;
  source_snippet: string;
  priority: "high" | "medium" | "low";
  // Human-readable reasons the priority was set (e.g. ["Deadline keyword: 'must submit'", "Date: '21 May 2026'"]).
  // Surfaced in the UI as "Why this priority" inside the expanded risk card.
  priority_flags?: string[];
}

export interface DatedEntry {
  text: string;          // canonical display string e.g. "21 May 2026"
  context: string;       // the sentence the date appeared in
  is_deadline: boolean;  // true iff the surrounding sentence has deadline keywords
}

export interface OfficialNoticeTableRow {
  service: string | null;
  heading: string | null;
  liable_party: string | null;
  rate_or_amount: string | null;
  source_snippet: string | null;
}

export interface OfficialNoticeBreakdown {
  issuing_authority: string | null;
  notice_type: string | null;
  notice_number: string | null;
  gazette_date: string | null;
  issue_date: string | null;
  legal_basis: string | null;
  subject: string | null;
  effective_timing: string | null;
  payment_timing: string | null;
  table_rows: OfficialNoticeTableRow[];
  compliance_duties: string[];
  consequences: string[];
  confidence: "high" | "medium" | "low";
  limitations: string[];
}

export interface DocumentInsight {
  filename: string;
  document_type: string;
  confidence: "high" | "medium" | "low";
  summary: string;
  important_dates: string[];
  // Subset of important_dates that have deadline context — for the
  // "Critical Deadlines" panel that separates true deadlines from
  // incidental dates mentioned in the body.
  key_deadlines: DatedEntry[];
  required_documents: string[];
  fees_and_amounts: string[];
  action_items: string[];
  risks: RiskInsight[];
  missing_information: string[];
  contact_info: string[];
  official_notice: OfficialNoticeBreakdown | null;
  analysis_diagnostics: {
    confidence_score: number;
    classification_confidence: "high" | "medium" | "low";
    extracted_signal_count: number;
    grounded_field_count: number;
    reasons: string[];
  };
  limitations: string[];
}

export type Priority = "high" | "medium" | "low";
export type ChecklistStatus = "pending" | "in_progress" | "done" | "na";

export interface ChecklistItem {
  id: string;
  task: string;
  reason: string;
  priority: Priority;
  status: ChecklistStatus;
  due_hint: string | null;
  source_snippet: string | null;
}

export interface ChecklistResult {
  filename: string;
  items: ChecklistItem[];
  total: number;
  high_priority_count: number;
}

export interface QuestionAnswer {
  question: string;
  answer: string;
  source_snippets: AnswerSource[];
  confidence: "high" | "medium" | "low";
  grounded: boolean;
  mode: string;
  retrieval: RetrievalDiagnostics;
  generation: GenerationDiagnostics;
  explanation: AnswerExplanation;
}

export interface AnswerSource {
  text: string;
  chunk_id: string;
  score: number;
  page_number: number | null;
  source_filename: string | null;
}

export interface RetrievalDiagnostics {
  embedding_provider: string;
  embedding_model: string | null;
  vector_backend: string;
  requested_top_k: number;
  retrieved_count: number;
  relevant_count: number;
  top_score: number;
  mean_score: number;
  score_spread: number;
  query_terms: string[];
  matched_terms: string[];
  warnings: string[];
}

export interface GenerationDiagnostics {
  requested_mode: string;
  actual_mode: string;
  configured_model: string | null;
  model_used: string | null;
  local_llm_enabled: boolean;
  fallback_reason: string | null;
}

export interface AnswerExplanation {
  strategy: string;
  confidence_reasons: string[];
  limitations: string[];
}

export interface LocalModelInfo {
  name: string;
  size_bytes: number | null;
  modified_at: string | null;
}

export interface IntelligenceRuntime {
  local_llm_enabled: boolean;
  ollama_available: boolean;
  configured_model: string;
  available_models: LocalModelInfo[];
  embedding_provider: string;
  embedding_model: string | null;
  vector_backend: string;
  status_message: string;
}

export interface SessionMetadata {
  id: string;
  filename: string;
  document_type: string;
  created_at: string;
  text_hash: string;
  content_stored: boolean;
}

export interface SaveSessionRequest {
  filename: string;
  document_type: string;
  text_hash: string;
  insight: DocumentInsight;
  checklist: ChecklistResult;
}

export interface AnalyzeRequest {
  text: string;
  filename: string;
}

export interface AskRequest {
  text: string;
  question: string;
  filename: string;
  top_k?: number;
  answer_mode?: "auto" | "extractive" | "local_llm";
  model?: string | null;
}
