import { useCallback, useState } from "react";
import { type FileRejection, useDropzone } from "react-dropzone";
import { useNavigate } from "react-router-dom";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  CalendarDays,
  Check,
  CheckCircle2,
  CloudOff,
  FileCheck2,
  FileText,
  FileType2,
  Image,
  ListChecks,
  Loader2,
  LockKeyhole,
  ScanText,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useWorkspaceStore } from "@/store/workspaceStore";
import { analyzeDocument, buildChecklist, extractDocument, saveSession } from "@/lib/api";
import type { ChecklistResult, DocumentInsight } from "@/lib/types";
import {
  FIXTURE_CHECKLIST,
  FIXTURE_EXTRACTION,
  FIXTURE_INSIGHT,
} from "@/lib/fixtures";

const ACCEPTED_TYPES: Record<string, string[]> = {
  "application/pdf": [".pdf"],
  "image/png": [".png"],
  "image/jpeg": [".jpg", ".jpeg"],
  "text/plain": [".txt"],
  "text/markdown": [".md"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
};

type Step = "idle" | "extracting" | "analyzing" | "building" | "done";

const STEPS: { key: Exclude<Step, "idle" | "done">; label: string; detail: string }[] = [
  {
    key: "extracting",
    label: "Extracting content",
    detail: "Reading text, pages, and document structure",
  },
  {
    key: "analyzing",
    label: "Finding key details",
    detail: "Identifying dates, fees, duties, and risks",
  },
  {
    key: "building",
    label: "Creating your action plan",
    detail: "Turning findings into a prioritized checklist",
  },
];

function stepIndex(step: Step) {
  return STEPS.findIndex((item) => item.key === step);
}

export function IntakePage() {
  const navigate = useNavigate();
  const {
    setPhase,
    setExtraction,
    setInsight,
    setChecklist,
    setError,
  } = useWorkspaceStore();
  const [file, setFile] = useState<File | null>(null);
  const [step, setStep] = useState<Step>("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [doneInsight, setDoneInsight] = useState<DocumentInsight | null>(null);
  const [doneChecklist, setDoneChecklist] = useState<ChecklistResult | null>(null);

  const resetLocalReview = useCallback(() => {
    setFile(null);
    setStep("idle");
    setErrorMsg(null);
    setDoneInsight(null);
    setDoneChecklist(null);
    setPhase("idle");
    setError(null);
  }, [setError, setPhase]);

  const onDrop = useCallback(
    (accepted: File[]) => {
      if (!accepted[0]) return;
      setFile(accepted[0]);
      setErrorMsg(null);
      setDoneInsight(null);
      setDoneChecklist(null);
      setStep("idle");
      setPhase("idle");
      setError(null);
    },
    [setError, setPhase],
  );

  const onDropRejected = useCallback((rejections: FileRejection[]) => {
    const code = rejections[0]?.errors[0]?.code;
    setErrorMsg(
      code === "file-too-large"
        ? "This file is larger than 25 MB. Choose a smaller document."
        : "This file type is not supported. Use PDF, DOCX, TXT, MD, PNG, or JPG.",
    );
  }, []);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    onDropRejected,
    accept: ACCEPTED_TYPES,
    maxFiles: 1,
    maxSize: 25 * 1024 * 1024,
    useFsAccessApi: false,
    disabled: step !== "idle",
  });

  const handleProcess = async () => {
    if (!file) return;

    setStep("extracting");
    setPhase("extracting");
    setErrorMsg(null);
    setDoneInsight(null);
    setDoneChecklist(null);

    try {
      const extraction = await extractDocument(file);
      setExtraction(extraction);
      setStep("analyzing");
      setPhase("analyzing");

      const [analyzeResult, checklistResult] = await Promise.all([
        analyzeDocument(extraction.extracted_text, extraction.filename),
        buildChecklist(extraction.extracted_text, extraction.filename),
      ]);

      setInsight(analyzeResult.insight);
      setStep("building");
      setPhase("building");
      setChecklist(checklistResult.checklist);
      setDoneInsight(analyzeResult.insight);
      setDoneChecklist(checklistResult.checklist);
      setStep("done");
      setPhase("ready");
      setError(null);

      saveSession({
        filename: extraction.filename,
        document_type: analyzeResult.insight.document_type,
        extracted_text: extraction.extracted_text,
        insight: analyzeResult.raw,
        checklist: checklistResult.raw,
      }).catch(() => undefined);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Processing failed";
      setPhase("error");
      setError(message);
      setErrorMsg(message);
      setStep("idle");
    }
  };

  const isProcessing = step !== "idle" && step !== "done";
  const showSummary = step === "done" && doneInsight && doneChecklist;

  return (
    <div className="page-shell">
      <div className="grid items-start gap-8 lg:grid-cols-[minmax(0,0.9fr)_minmax(30rem,1.1fr)] lg:gap-12 xl:gap-16">
        <section className="pt-3 lg:sticky lg:top-10 lg:pt-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-accent/20 bg-accent/[0.07] px-3 py-1.5 text-xs font-medium text-accent">
            <Sparkles size={13} />
            Private document intelligence
          </div>

          <h1 className="mt-6 max-w-2xl text-balance text-4xl font-semibold tracking-[-0.045em] text-foreground sm:text-5xl lg:text-[3.45rem] lg:leading-[1.03]">
            Turn dense documents into clear next steps.
          </h1>
          <p className="mt-5 max-w-xl text-base leading-7 text-muted-foreground sm:text-lg">
            Papervault reads documents locally, surfaces deadlines and risks, and
            builds a practical checklist without sending your files to a cloud API.
          </p>

          <div className="mt-8 grid gap-3 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
            <TrustItem
              icon={<CloudOff size={17} />}
              title="No cloud upload"
              detail="Files stay on this device"
            />
            <TrustItem
              icon={<ScanText size={17} />}
              title="Structured findings"
              detail="Dates, fees, duties, risks"
            />
            <TrustItem
              icon={<ListChecks size={17} />}
              title="Action-ready"
              detail="Prioritized review checklist"
            />
          </div>

          <div className="mt-10 hidden rounded-2xl border border-border/70 bg-card/55 p-5 lg:block">
            <p className="eyebrow">Designed for real paperwork</p>
            <div className="mt-4 space-y-3">
              {[
                "Official notices and government forms",
                "University offers and scholarship letters",
                "Visa documents, contracts, and supporting records",
              ].map((item) => (
                <div key={item} className="flex items-center gap-3 text-sm text-foreground">
                  <span className="flex size-6 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                    <Check size={13} />
                  </span>
                  {item}
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="surface-panel overflow-hidden">
          <div className="border-b border-border/70 bg-gradient-to-br from-primary/[0.06] via-card to-accent/[0.05] px-5 py-5 sm:px-7 sm:py-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="eyebrow">New review</p>
                <h2 className="mt-2 text-xl font-semibold tracking-tight sm:text-2xl">
                  Analyze a document
                </h2>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                  Add one file and Papervault will create a private review workspace.
                </p>
              </div>
              <div className="flex size-11 shrink-0 items-center justify-center rounded-xl border border-accent/15 bg-accent/10 text-accent">
                <LockKeyhole size={20} />
              </div>
            </div>
          </div>

          <div className="p-5 sm:p-7">
            {showSummary ? (
              <CompletionSummary
                filename={file?.name ?? doneInsight.filename}
                insight={doneInsight}
                checklist={doneChecklist}
                onOpen={() => {
                  setInsight(doneInsight);
                  setChecklist(doneChecklist);
                  setPhase("ready");
                  setError(null);
                  navigate("/workspace");
                }}
                onReset={resetLocalReview}
              />
            ) : (
              <div className="space-y-5">
                <div
                  {...getRootProps()}
                  className={cn(
                    "group relative flex min-h-64 cursor-pointer flex-col items-center justify-center overflow-hidden rounded-2xl border border-dashed px-5 py-9 text-center transition-all duration-200 sm:min-h-72 sm:px-8",
                    isDragActive && !isDragReject
                      ? "scale-[1.01] border-accent bg-accent/[0.06] shadow-[0_18px_45px_-28px_hsl(var(--accent))]"
                      : file
                        ? "border-primary/35 bg-primary/[0.045]"
                        : "border-border bg-muted/20 hover:border-accent/45 hover:bg-accent/[0.035]",
                    isDragReject && "border-destructive bg-destructive/[0.05]",
                    isProcessing && "cursor-wait",
                  )}
                >
                  <input {...getInputProps()} aria-label="Choose a document to analyze" />
                  <div className="absolute inset-x-8 top-0 h-px bg-gradient-to-r from-transparent via-accent/35 to-transparent" />

                  <FilePreview file={file} isDragActive={isDragActive} />
                </div>

                {isProcessing && <ProcessingTimeline step={step} />}

                {errorMsg && (
                  <div
                    role="alert"
                    className="flex items-start gap-3 rounded-xl border border-destructive/20 bg-destructive/[0.055] p-4"
                  >
                    <AlertCircle size={17} className="mt-0.5 shrink-0 text-destructive" />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-foreground">
                        We couldn’t complete this review
                      </p>
                      <p className="mt-1 break-words text-xs leading-relaxed text-muted-foreground">
                        {errorMsg}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setErrorMsg(null)}
                      className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
                      aria-label="Dismiss error"
                    >
                      <X size={14} />
                    </button>
                  </div>
                )}

                <Button
                  onClick={handleProcess}
                  disabled={!file || isProcessing}
                  className="h-12 w-full text-sm"
                  size="lg"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="animate-spin" />
                      Processing locally
                    </>
                  ) : (
                    <>
                      Analyze document
                      <ArrowRight />
                    </>
                  )}
                </Button>

                <div className="flex flex-col gap-3 border-t border-border/70 pt-4 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
                  <span className="flex items-center gap-2">
                    <ShieldCheck size={14} className="text-emerald-600 dark:text-emerald-400" />
                    PDF, DOCX, TXT, MD, PNG, JPG
                  </span>
                  <span>Maximum file size: 25 MB</span>
                </div>

                {import.meta.env.DEV && (
                  <button
                    type="button"
                    onClick={async () => {
                      setErrorMsg(null);
                      setStep("extracting");
                      setPhase("extracting");
                      await new Promise((resolve) => setTimeout(resolve, 350));
                      setExtraction(FIXTURE_EXTRACTION);
                      setStep("analyzing");
                      setPhase("analyzing");
                      await new Promise((resolve) => setTimeout(resolve, 450));
                      setInsight(FIXTURE_INSIGHT);
                      setStep("building");
                      setPhase("building");
                      await new Promise((resolve) => setTimeout(resolve, 350));
                      setChecklist(FIXTURE_CHECKLIST);
                      setError(null);
                      setPhase("ready");
                      setDoneInsight(FIXTURE_INSIGHT);
                      setDoneChecklist(FIXTURE_CHECKLIST);
                      setStep("done");
                    }}
                    disabled={isProcessing}
                    className="w-full rounded-xl border border-dashed border-border px-3 py-2.5 text-xs text-muted-foreground transition-colors hover:border-accent/35 hover:bg-muted/40 hover:text-foreground disabled:opacity-50"
                  >
                    Load a sample document for interface testing
                  </button>
                )}
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

function FilePreview({
  file,
  isDragActive,
}: {
  file: File | null;
  isDragActive: boolean;
}) {
  if (file) {
    const Icon = file.type.startsWith("image/")
      ? Image
      : file.type === "application/pdf"
        ? FileType2
        : FileText;

    return (
      <>
        <div className="flex size-16 items-center justify-center rounded-2xl border border-accent/15 bg-accent/10 text-accent shadow-sm">
          <Icon size={28} />
        </div>
        <p className="mt-5 max-w-full truncate text-sm font-semibold text-foreground">
          {file.name}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          {formatFileSize(file.size)} · click or drop another file to replace
        </p>
        <div className="mt-5 inline-flex items-center gap-2 rounded-full bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-700 dark:text-emerald-400">
          <CheckCircle2 size={13} />
          Ready for local analysis
        </div>
      </>
    );
  }

  return (
    <>
      <div className="flex size-16 items-center justify-center rounded-2xl border border-border bg-card text-muted-foreground shadow-sm transition-all group-hover:-translate-y-1 group-hover:border-accent/30 group-hover:text-accent">
        <UploadCloud size={28} />
      </div>
      <p className="mt-5 text-base font-semibold text-foreground">
        {isDragActive ? "Drop your document here" : "Drag and drop a document"}
      </p>
      <p className="mt-1.5 text-sm text-muted-foreground">
        or click to choose a file from this device
      </p>
      <span className="mt-5 rounded-full border border-border bg-card px-3 py-1.5 text-[0.7rem] font-medium text-muted-foreground">
        Your file never leaves this machine
      </span>
    </>
  );
}

function ProcessingTimeline({ step }: { step: Step }) {
  const current = stepIndex(step);

  return (
    <div
      className="rounded-2xl border border-accent/15 bg-accent/[0.04] p-4 sm:p-5"
      aria-live="polite"
    >
      <div className="mb-4 flex items-center justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-foreground">Processing locally</p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Keep this page open while the review is prepared.
          </p>
        </div>
        <Loader2 size={18} className="shrink-0 animate-spin text-accent" />
      </div>

      <div className="space-y-3">
        {STEPS.map((item, index) => {
          const complete = index < current;
          const active = index === current;
          return (
            <div key={item.key} className="flex items-start gap-3">
              <span
                className={cn(
                  "mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full border text-xs",
                  complete && "border-emerald-500/30 bg-emerald-500/10 text-emerald-600",
                  active && "border-accent/30 bg-accent/10 text-accent",
                  !complete && !active && "border-border bg-background text-muted-foreground",
                )}
              >
                {complete ? <Check size={13} /> : active ? <Loader2 size={12} className="animate-spin" /> : index + 1}
              </span>
              <div>
                <p
                  className={cn(
                    "text-xs font-medium",
                    complete || active ? "text-foreground" : "text-muted-foreground",
                  )}
                >
                  {item.label}
                </p>
                <p className="mt-0.5 text-[0.7rem] text-muted-foreground">
                  {item.detail}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CompletionSummary({
  filename,
  insight,
  checklist,
  onOpen,
  onReset,
}: {
  filename: string;
  insight: DocumentInsight;
  checklist: ChecklistResult;
  onOpen: () => void;
  onReset: () => void;
}) {
  const metrics = [
    {
      label: "Action items",
      value: checklist.items.length,
      icon: ListChecks,
      tone: "text-accent bg-accent/10",
    },
    {
      label: "High priority",
      value: checklist.items.filter((item) => item.priority === "high").length,
      icon: AlertTriangle,
      tone: "text-amber-600 bg-amber-500/10",
    },
    {
      label: "Risks flagged",
      value: insight.risks.length,
      icon: AlertCircle,
      tone: "text-destructive bg-destructive/10",
    },
    {
      label: "Key dates",
      value: insight.important_dates.length,
      icon: CalendarDays,
      tone: "text-emerald-600 bg-emerald-500/10",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-start gap-3">
        <span className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
          <FileCheck2 size={21} />
        </span>
        <div className="min-w-0 flex-1">
          <p className="eyebrow text-emerald-600 dark:text-emerald-400">Review ready</p>
          <h3 className="mt-1 text-lg font-semibold text-foreground">Analysis complete</h3>
          <p className="mt-1 truncate text-xs text-muted-foreground">
            {filename} · {insight.document_type.replace(/_/g, " ")}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {metrics.map(({ label, value, icon: Icon, tone }) => (
          <div key={label} className="rounded-xl border border-border/70 bg-muted/25 p-3.5">
            <span className={cn("flex size-8 items-center justify-center rounded-lg", tone)}>
              <Icon size={15} />
            </span>
            <p className="mt-3 text-xl font-semibold tracking-tight text-foreground">{value}</p>
            <p className="mt-0.5 text-xs text-muted-foreground">{label}</p>
          </div>
        ))}
      </div>

      {insight.summary && (
        <div className="rounded-xl border border-border/70 bg-muted/25 p-4">
          <p className="eyebrow text-muted-foreground">At a glance</p>
          <p className="mt-2 text-sm leading-6 text-foreground">
            {insight.summary.length > 300
              ? `${insight.summary.slice(0, 300)}…`
              : insight.summary}
          </p>
        </div>
      )}

      <div className="flex flex-col-reverse gap-2 sm:flex-row">
        <Button variant="outline" onClick={onReset} className="sm:w-auto">
          Review another file
        </Button>
        <Button onClick={onOpen} className="flex-1">
          Open review workspace
          <ArrowRight />
        </Button>
      </div>
    </div>
  );
}

function TrustItem({
  icon,
  title,
  detail,
}: {
  icon: React.ReactNode;
  title: string;
  detail: string;
}) {
  return (
    <div className="rounded-xl border border-border/70 bg-card/70 p-3.5 backdrop-blur">
      <span className="flex size-8 items-center justify-center rounded-lg bg-accent/10 text-accent">
        {icon}
      </span>
      <p className="mt-3 text-xs font-semibold text-foreground">{title}</p>
      <p className="mt-1 text-[0.7rem] leading-relaxed text-muted-foreground">{detail}</p>
    </div>
  );
}

function formatFileSize(bytes: number) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
