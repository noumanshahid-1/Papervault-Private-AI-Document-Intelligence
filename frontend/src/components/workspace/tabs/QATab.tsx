import { useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  BrainCircuit,
  CheckCircle2,
  Cpu,
  Database,
  FileQuestion,
  Gauge,
  Loader2,
  MessageSquareText,
  Send,
  Settings2,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { askDocument, getIntelligenceRuntime } from "@/lib/api";
import { useWorkspaceStore } from "@/store/workspaceStore";

const SUGGESTIONS = [
  "What is the most important deadline?",
  "Which documents do I need to submit?",
  "What do I need to pay and when?",
];

export function QATab() {
  const { qaHistory, addQA, extraction } = useWorkspaceStore();
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [answerMode, setAnswerMode] = useState<
    "auto" | "extractive" | "local_llm"
  >("auto");
  const [selectedModel, setSelectedModel] = useState("");
  const [topK, setTopK] = useState(5);
  const threadRef = useRef<HTMLDivElement>(null);
  const { data: runtime, isLoading: runtimeLoading } = useQuery({
    queryKey: ["intelligence-runtime"],
    queryFn: getIntelligenceRuntime,
    staleTime: 30_000,
    retry: 1,
  });

  useEffect(() => {
    const thread = threadRef.current;
    if (thread) {
      thread.scrollTo({ top: thread.scrollHeight, behavior: "smooth" });
    }
  }, [qaHistory]);

  if (extraction && !extraction.content_available) {
    return (
      <div className="surface-panel flex min-h-[28rem] items-center justify-center px-5 py-10">
        <div className="max-w-lg text-center">
          <span className="mx-auto flex size-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
            <ShieldCheck size={25} />
          </span>
          <p className="eyebrow mt-5">Privacy-protected history</p>
          <h2 className="mt-2 text-lg font-semibold text-foreground">
            Q&amp;A needs the original document
          </h2>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            This saved review contains structured findings, but its extracted text
            was not retained. Re-upload the source document to ask grounded questions.
          </p>
        </div>
      </div>
    );
  }

  const handleAsk = async (value: string) => {
    const trimmed = value.trim();
    if (!trimmed || loading || !extraction) return;
    setQuestion("");
    setLoading(true);
    setError(null);

    try {
      const answer = await askDocument(
        extraction.extracted_text,
        trimmed,
        extraction.filename,
        {
          answerMode,
          model: selectedModel || runtime?.configured_model || null,
          topK,
        },
      );
      addQA(answer);
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : "Failed to get an answer",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="surface-panel flex h-[42rem] min-h-0 flex-col overflow-hidden">
      <div className="border-b border-border/70 bg-muted/25 px-4 py-4 sm:px-5">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div className="flex items-start gap-3">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-accent/10 text-accent">
              <MessageSquareText size={18} />
            </span>
            <div>
              <p className="text-sm font-semibold text-foreground">Ask this document</p>
              <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                Answers include retrieval evidence, confidence reasons, and local
                generation diagnostics.
              </p>
            </div>
          </div>
          <RuntimeControls
            runtime={runtime}
            loading={runtimeLoading}
            answerMode={answerMode}
            onAnswerModeChange={setAnswerMode}
            selectedModel={selectedModel || runtime?.configured_model || ""}
            onModelChange={setSelectedModel}
            topK={topK}
            onTopKChange={setTopK}
          />
        </div>
      </div>

      <div
        ref={threadRef}
        className="scrollbar-subtle min-h-0 flex-1 space-y-5 overflow-y-auto p-4 sm:p-5"
      >
        {qaHistory.length === 0 && (
          <div className="flex min-h-[20rem] flex-col items-center justify-center text-center">
            <span className="flex size-14 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
              <FileQuestion size={24} />
            </span>
            <h2 className="mt-5 text-base font-semibold text-foreground">
              Start with a question
            </h2>
            <p className="mt-2 max-w-sm text-sm leading-6 text-muted-foreground">
              Ask about deadlines, required documents, fees, duties, or a specific
              statement in the source.
            </p>
            <div className="mt-6 flex max-w-xl flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((suggestion) => (
                <button
                  type="button"
                  key={suggestion}
                  onClick={() => handleAsk(suggestion)}
                  className="rounded-full border border-border bg-background px-3 py-2 text-xs text-muted-foreground transition-colors hover:border-accent/35 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {qaHistory.map((qa, index) => (
          <div key={`${qa.question}-${index}`} className="space-y-3">
            <div className="flex justify-end">
              <div className="max-w-[88%] rounded-2xl rounded-br-md bg-primary px-4 py-3 text-primary-foreground sm:max-w-[75%]">
                <p className="text-sm leading-6">{qa.question}</p>
              </div>
            </div>

            <div className="flex items-start gap-2.5">
              <span className="mt-1 flex size-8 shrink-0 items-center justify-center rounded-lg bg-accent/10 text-accent">
                <Sparkles size={14} />
              </span>
              <div className="max-w-[calc(100%_-_2.625rem)] rounded-2xl rounded-bl-md border border-border/70 bg-muted/35 px-4 py-3 sm:max-w-[82%]">
                <p className="text-sm leading-6 text-foreground">{qa.answer}</p>
                <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-border/60 pt-3">
                  <span className="inline-flex items-center gap-1.5 text-[0.68rem] text-muted-foreground">
                    {qa.grounded ? (
                      <CheckCircle2 size={12} className="text-emerald-600" />
                    ) : (
                      <AlertCircle size={12} className="text-amber-600" />
                    )}
                    {qa.grounded ? "Grounded answer" : "Limited evidence"}
                  </span>
                  <span className="text-[0.68rem] capitalize text-muted-foreground">
                    {qa.confidence} confidence
                  </span>
                  <span className="inline-flex items-center gap-1 text-[0.68rem] text-muted-foreground">
                    <BrainCircuit size={11} />
                    {qa.generation.actual_mode === "local_llm"
                      ? qa.generation.model_used ?? "Local model"
                      : "Extractive"}
                  </span>
                  <span className="inline-flex items-center gap-1 text-[0.68rem] text-muted-foreground">
                    <Gauge size={11} />
                    Top score {qa.retrieval.top_score.toFixed(3)}
                  </span>
                </div>

                {qa.source_snippets.length > 0 && (
                  <details className="mt-3 text-xs">
                    <summary className="cursor-pointer font-medium text-accent hover:underline">
                      View {qa.source_snippets.length} source
                      {qa.source_snippets.length > 1 ? "s" : ""}
                    </summary>
                    <ul className="mt-3 space-y-2 border-l-2 border-accent/20 pl-3">
                      {qa.source_snippets.map((snippet) => (
                        <li
                          key={snippet.chunk_id}
                          className="scrollbar-subtle max-h-48 overflow-y-auto break-words rounded-lg bg-background/70 p-2.5 leading-5 text-muted-foreground"
                        >
                          <span className="italic">“{snippet.text}”</span>
                          <span className="mt-1.5 flex flex-wrap gap-2 text-[0.62rem] not-italic text-muted-foreground/80">
                            <span>Score {snippet.score.toFixed(3)}</span>
                            {snippet.page_number && (
                              <span>Page {snippet.page_number}</span>
                            )}
                            <span>{snippet.chunk_id}</span>
                          </span>
                        </li>
                      ))}
                    </ul>
                  </details>
                )}

                <details className="mt-3 rounded-xl border border-border/60 bg-background/50 p-3 text-xs">
                  <summary className="cursor-pointer font-medium text-foreground">
                    Why this answer
                  </summary>
                  <div className="mt-3 grid gap-3 sm:grid-cols-2">
                    <DiagnosticList
                      title="Confidence basis"
                      icon={<Gauge size={13} />}
                      items={qa.explanation.confidence_reasons}
                    />
                    <DiagnosticList
                      title="Retrieval"
                      icon={<Database size={13} />}
                      items={[
                        `${qa.retrieval.relevant_count} of ${qa.retrieval.retrieved_count} chunks met the relevance threshold.`,
                        `Provider: ${qa.retrieval.embedding_provider}${qa.retrieval.embedding_model ? ` · ${qa.retrieval.embedding_model}` : ""}.`,
                        `Vector backend: ${qa.retrieval.vector_backend}.`,
                        ...(qa.retrieval.matched_terms.length
                          ? [`Matched terms: ${qa.retrieval.matched_terms.join(", ")}.`]
                          : []),
                      ]}
                    />
                    {qa.generation.fallback_reason && (
                      <DiagnosticList
                        title="Fallback"
                        icon={<AlertCircle size={13} />}
                        items={[qa.generation.fallback_reason]}
                      />
                    )}
                    <DiagnosticList
                      title="Limitations"
                      icon={<ShieldCheck size={13} />}
                      items={qa.explanation.limitations}
                    />
                  </div>
                </details>
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2.5" aria-live="polite">
            <span className="flex size-8 items-center justify-center rounded-lg bg-accent/10 text-accent">
              <Loader2 size={14} className="animate-spin" />
            </span>
            <div className="rounded-2xl rounded-bl-md bg-muted/45 px-4 py-3 text-xs text-muted-foreground">
              Searching the document…
            </div>
          </div>
        )}

        {error && (
          <div
            role="alert"
            className="flex items-start gap-2 rounded-xl border border-destructive/20 bg-destructive/[0.05] p-3 text-xs text-muted-foreground"
          >
            <AlertCircle size={14} className="mt-0.5 shrink-0 text-destructive" />
            {error}
          </div>
        )}
      </div>

      <div className="border-t border-border/70 bg-card p-3 sm:p-4">
        <label htmlFor="document-question" className="sr-only">
          Ask a question about this document
        </label>
        <div className="flex items-end gap-2">
          <textarea
            id="document-question"
            value={question}
            rows={1}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
                handleAsk(question);
              }
            }}
            placeholder="Ask about a deadline, payment, duty, or clause…"
            className={cn(
              "max-h-32 min-h-11 flex-1 resize-y rounded-xl border border-input bg-background px-3.5 py-3 text-sm",
              "placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring",
            )}
          />
          <Button
            onClick={() => handleAsk(question)}
            disabled={!question.trim() || loading}
            size="icon"
            className="size-11 shrink-0"
            aria-label="Send question"
          >
            <Send size={16} />
          </Button>
        </div>
        <p className="mt-2 text-center text-[0.68rem] text-muted-foreground">
          Ctrl or Command + Enter to send
        </p>
      </div>
    </div>
  );
}

function RuntimeControls({
  runtime,
  loading,
  answerMode,
  onAnswerModeChange,
  selectedModel,
  onModelChange,
  topK,
  onTopKChange,
}: {
  runtime: Awaited<ReturnType<typeof getIntelligenceRuntime>> | undefined;
  loading: boolean;
  answerMode: "auto" | "extractive" | "local_llm";
  onAnswerModeChange: (mode: "auto" | "extractive" | "local_llm") => void;
  selectedModel: string;
  onModelChange: (model: string) => void;
  topK: number;
  onTopKChange: (value: number) => void;
}) {
  const modelNames = runtime?.available_models.map((model) => model.name) ?? [];
  if (
    runtime?.configured_model &&
    !modelNames.includes(runtime.configured_model)
  ) {
    modelNames.unshift(runtime.configured_model);
  }
  const localModelReady =
    Boolean(runtime?.local_llm_enabled) && Boolean(runtime?.ollama_available);

  return (
    <div className="grid gap-2 sm:grid-cols-3 xl:min-w-[34rem]">
      <label className="text-[0.65rem] font-medium text-muted-foreground">
        Answer mode
        <span className="relative mt-1 block">
          <BrainCircuit className="pointer-events-none absolute left-2.5 top-2.5 size-3.5" />
          <select
            value={answerMode}
            onChange={(event) =>
              onAnswerModeChange(
                event.target.value as "auto" | "extractive" | "local_llm",
              )
            }
            className="h-9 w-full rounded-lg border border-input bg-background pl-8 pr-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="auto">Automatic</option>
            <option value="extractive">Extractive only</option>
            <option value="local_llm" disabled={!localModelReady}>
              Local Ollama
            </option>
          </select>
        </span>
      </label>

      <label className="text-[0.65rem] font-medium text-muted-foreground">
        Local model
        <span className="relative mt-1 block">
          <Cpu className="pointer-events-none absolute left-2.5 top-2.5 size-3.5" />
          <select
            value={selectedModel}
            onChange={(event) => onModelChange(event.target.value)}
            disabled={!localModelReady || modelNames.length === 0}
            className="h-9 w-full rounded-lg border border-input bg-background pl-8 pr-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-55"
          >
            {modelNames.length === 0 && <option value="">No model detected</option>}
            {modelNames.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
        </span>
      </label>

      <label className="text-[0.65rem] font-medium text-muted-foreground">
        Retrieval depth
        <span className="relative mt-1 block">
          <Settings2 className="pointer-events-none absolute left-2.5 top-2.5 size-3.5" />
          <select
            value={topK}
            onChange={(event) => onTopKChange(Number(event.target.value))}
            className="h-9 w-full rounded-lg border border-input bg-background pl-8 pr-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value={3}>3 chunks</option>
            <option value={5}>5 chunks</option>
            <option value={8}>8 chunks</option>
          </select>
        </span>
      </label>

      <p className="flex items-center gap-1.5 text-[0.65rem] leading-4 text-muted-foreground sm:col-span-3">
        {loading ? (
          <Loader2 size={11} className="animate-spin" />
        ) : localModelReady ? (
          <CheckCircle2 size={11} className="text-emerald-600" />
        ) : (
          <AlertCircle size={11} className="text-amber-600" />
        )}
        {runtime?.status_message ?? "Checking local intelligence runtime…"}
      </p>
    </div>
  );
}

function DiagnosticList({
  title,
  icon,
  items,
}: {
  title: string;
  icon: React.ReactNode;
  items: string[];
}) {
  if (items.length === 0) return null;
  return (
    <div>
      <p className="flex items-center gap-1.5 font-medium text-foreground">
        {icon}
        {title}
      </p>
      <ul className="mt-2 space-y-1.5 text-[0.68rem] leading-4 text-muted-foreground">
        {items.map((item) => (
          <li key={item} className="flex items-start gap-2">
            <span className="mt-1.5 size-1 shrink-0 rounded-full bg-accent" />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
