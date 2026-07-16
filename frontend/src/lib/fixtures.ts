import type { ExtractionResult, DocumentInsight, ChecklistResult, QuestionAnswer, SessionMetadata } from "./types";

export const FIXTURE_EXTRACTION: ExtractionResult = {
  filename: "university_admission_offer.pdf",
  content_type: "application/pdf",
  extracted_text: "UNIVERSITY OF EXAMPLE — OFFER OF ADMISSION...",
  page_count: 4,
  word_count: 1240,
  char_count: 7450,
  extraction_method: "pymupdf",
  warnings: [],
  extracted_text_hash: "abc123demo",
  content_available: true,
  diagnostics: {
    engine: "pymupdf",
    confidence: "high",
    confidence_score: 0.94,
    is_ocr: false,
    ocr_engine: null,
    ocr_mean_confidence: null,
    word_count: 1240,
    character_count: 7450,
    readable_character_ratio: 0.99,
    suspicious_character_ratio: 0.001,
    page_text_coverage: 1,
    signals: [
      "Extracted 1,240 words.",
      "Meaningful text was detected on 100% of pages.",
    ],
    recommendations: [],
  },
};

export const FIXTURE_INSIGHT: DocumentInsight = {
  filename: "university_admission_offer.pdf",
  document_type: "university_admission",
  confidence: "high",
  summary:
    "This is a conditional offer of admission to the MSc Computer Science programme starting September 2025. You must confirm acceptance by 15 July 2025 and submit your final degree certificate before 1 August 2025. An enrollment deposit of £500 is required within 14 days of this offer.",
  important_dates: [
    "15 July 2025 — Acceptance deadline",
    "1 August 2025 — Final transcript submission",
    "15 September 2025 — Programme start date",
  ],
  required_documents: [
    "Certified copy of final degree certificate",
    "Official academic transcript",
    "Valid passport copy",
    "English language proficiency evidence (IELTS 7.0+)",
  ],
  fees_and_amounts: [
    "£500 enrollment deposit (due within 14 days)",
    "£18,500 annual tuition fee",
  ],
  action_items: [
    "Confirm acceptance via the student portal",
    "Pay £500 enrollment deposit",
    "Upload certified degree certificate",
    "Arrange certified English translation of documents if required",
  ],
  risks: [
    {
      issue: "Acceptance deadline in 23 days",
      why_it_matters: "Failure to confirm by 15 July voids this offer automatically.",
      verify_step: "Log in to the student portal and check the acceptance status.",
      source_snippet: "You must confirm your acceptance by 15 July 2025 to secure your place.",
      priority: "high",
    },
    {
      issue: "Conditional offer — degree certificate required",
      why_it_matters: "The offer is withdrawn if final results are not submitted by 1 August.",
      verify_step: "Contact your current institution about certificate issuance timelines.",
      source_snippet: "This offer is conditional upon receipt of your final degree certificate.",
      priority: "high",
    },
    {
      issue: "Enrollment deposit non-refundable",
      why_it_matters: "£500 cannot be recovered if you withdraw after payment.",
      verify_step: "Review the terms and conditions before paying the deposit.",
      source_snippet: "The enrollment deposit of £500 is non-refundable.",
      priority: "medium",
    },
  ],
  missing_information: [
    "Visa sponsorship details not specified",
    "Accommodation application process not mentioned",
  ],
  contact_info: [
    "admissions@example.ac.uk",
    "+44 (0)20 7946 0958",
  ],
  official_notice: null,
  analysis_diagnostics: {
    confidence_score: 0.92,
    classification_confidence: "high",
    extracted_signal_count: 13,
    grounded_field_count: 5,
    reasons: [
      "Classification confidence is high.",
      "13 structured signals were extracted.",
      "5 finding groups contain evidence.",
    ],
  },
  limitations: [
    "Insights are extracted with deterministic local rules and should be verified against the source document.",
  ],
  key_deadlines: [
    {
      text: "15 July 2025",
      context: "You must confirm your acceptance by 15 July 2025 to secure your place.",
      is_deadline: true,
    },
    {
      text: "1 August 2025",
      context: "This offer is conditional upon receipt of your final degree certificate by 1 August 2025.",
      is_deadline: true,
    },
  ],
};

export const FIXTURE_CHECKLIST: ChecklistResult = {
  filename: "university_admission_offer.pdf",
  items: [
    {
      id: "cl-1",
      task: "Confirm acceptance on the student portal",
      reason: "Required to secure your place before the 15 July deadline",
      priority: "high",
      status: "pending",
      due_hint: "15 July 2025",
      source_snippet: "You must confirm your acceptance by 15 July 2025.",
    },
    {
      id: "cl-2",
      task: "Pay £500 enrollment deposit",
      reason: "Required within 14 days of this offer letter",
      priority: "high",
      status: "pending",
      due_hint: "Within 14 days",
      source_snippet: "An enrollment deposit of £500 is required within 14 days.",
    },
    {
      id: "cl-3",
      task: "Upload certified final degree certificate",
      reason: "Offer is conditional on receiving your final certificate",
      priority: "high",
      status: "pending",
      due_hint: "1 August 2025",
      source_snippet: "This offer is conditional upon receipt of your final degree certificate.",
    },
    {
      id: "cl-4",
      task: "Submit official academic transcript",
      reason: "Required document listed in the offer conditions",
      priority: "medium",
      status: "pending",
      due_hint: null,
      source_snippet: null,
    },
    {
      id: "cl-5",
      task: "Arrange IELTS score submission (7.0+ required)",
      reason: "English proficiency evidence is a stated admission requirement",
      priority: "medium",
      status: "pending",
      due_hint: null,
      source_snippet: "English language proficiency evidence: IELTS 7.0 or equivalent.",
    },
    {
      id: "cl-6",
      task: "Confirm passport validity for programme duration",
      reason: "Passport copy required; visa may be needed",
      priority: "low",
      status: "pending",
      due_hint: null,
      source_snippet: null,
    },
  ],
  total: 6,
  high_priority_count: 3,
};

export const FIXTURE_QA: QuestionAnswer = {
  question: "What is the deadline to accept this offer?",
  answer: "You must confirm your acceptance by 15 July 2025 via the student portal to secure your place on the programme.",
  source_snippets: [
    {
      text: "You must confirm your acceptance by 15 July 2025 to secure your place.",
      chunk_id: "offer.pdf:1",
      score: 0.71,
      page_number: 1,
      source_filename: "university_admission_offer.pdf",
    },
    {
      text: "Failure to confirm acceptance by the stated date will result in automatic withdrawal of this offer.",
      chunk_id: "offer.pdf:2",
      score: 0.54,
      page_number: 1,
      source_filename: "university_admission_offer.pdf",
    },
  ],
  confidence: "high",
  grounded: true,
  mode: "extractive",
  retrieval: {
    embedding_provider: "hashing",
    embedding_model: "hashing-384",
    vector_backend: "faiss",
    requested_top_k: 5,
    retrieved_count: 5,
    relevant_count: 3,
    top_score: 0.71,
    mean_score: 0.38,
    score_spread: 0.55,
    query_terms: ["accept", "deadline", "offer"],
    matched_terms: ["accept", "deadline", "offer"],
    warnings: [],
  },
  generation: {
    requested_mode: "auto",
    actual_mode: "extractive",
    configured_model: "llama3.2",
    model_used: null,
    local_llm_enabled: false,
    fallback_reason: null,
  },
  explanation: {
    strategy: "direct_rule",
    confidence_reasons: [
      "A deterministic document rule found a directly relevant sentence.",
      "3 of 5 retrieved chunks met the relevance threshold.",
    ],
    limitations: [
      "Retrieval scores are relative indicators, not probabilities.",
    ],
  },
};

export const FIXTURE_SESSIONS: SessionMetadata[] = [
  {
    id: "sess-001",
    filename: "university_admission_offer.pdf",
    document_type: "university_admission",
    created_at: "2025-06-20T14:32:00Z",
    text_hash: "abc123demo",
    content_stored: false,
  },
  {
    id: "sess-002",
    filename: "scholarship_letter.pdf",
    document_type: "scholarship",
    created_at: "2025-06-18T09:15:00Z",
    text_hash: "def456demo",
    content_stored: false,
  },
];
