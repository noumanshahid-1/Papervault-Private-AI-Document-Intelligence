import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowRight,
  CalendarDays,
  ChevronRight,
  Clock3,
  FilePlus2,
  FileText,
  HardDrive,
  Inbox,
  Loader2,
  RefreshCw,
  ShieldCheck,
  Trash2,
} from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { clearSessions, getSession, listSessions } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useWorkspaceStore } from "@/store/workspaceStore";
import { cn } from "@/lib/utils";

const DOC_TYPE_LABELS: Record<string, string> = {
  university_admission: "University admission",
  scholarship: "Scholarship",
  scholarship_document: "Scholarship",
  visa: "Visa",
  government_form: "Government form",
  government_notice: "Government notice",
  contract: "Contract",
  unknown: "Document",
};

export function HistoryPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const loadWorkspace = useWorkspaceStore((state) => state.loadWorkspace);
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [confirmingClear, setConfirmingClear] = useState(false);
  const [clearing, setClearing] = useState(false);

  const {
    data: sessions = [],
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["sessions"],
    queryFn: listSessions,
  });

  const handleOpen = async (id: string) => {
    if (loadingId || clearing) return;
    setLoadingId(id);
    setLoadError(null);
    try {
      const session = await getSession(id);
      loadWorkspace(session.extraction, session.insight, session.checklist);
      navigate("/workspace");
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "Failed to load session");
      setLoadingId(null);
    }
  };

  const handleClearConfirmed = async () => {
    setClearing(true);
    setLoadError(null);
    try {
      await clearSessions();
      await queryClient.invalidateQueries({ queryKey: ["sessions"] });
      setConfirmingClear(false);
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "Failed to clear history");
    } finally {
      setClearing(false);
    }
  };

  const contentStoredCount = sessions.filter((session) => session.content_stored).length;

  return (
    <div className="page-shell">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div className="max-w-2xl">
          <p className="eyebrow">Local archive</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-[-0.035em] sm:text-4xl">
            Review history
          </h1>
          <p className="mt-3 text-sm leading-6 text-muted-foreground sm:text-base">
            Reopen structured findings and checklists saved on this machine. Source
            text remains private unless retention is explicitly enabled.
          </p>
        </div>
        <Button asChild className="w-full sm:w-auto">
          <Link to="/">
            <FilePlus2 />
            New review
          </Link>
        </Button>
      </div>

      {!isLoading && !isError && sessions.length > 0 && (
        <div className="mt-7 grid gap-3 sm:grid-cols-3">
          <HistoryStat
            icon={<FileText size={17} />}
            value={sessions.length}
            label={sessions.length === 1 ? "Saved review" : "Saved reviews"}
            tone="text-accent bg-accent/10"
          />
          <HistoryStat
            icon={<ShieldCheck size={17} />}
            value={sessions.length - contentStoredCount}
            label="Summary-only records"
            tone="text-emerald-600 bg-emerald-500/10"
          />
          <HistoryStat
            icon={<HardDrive size={17} />}
            value={contentStoredCount}
            label="Reviews retaining text"
            tone="text-amber-600 bg-amber-500/10"
          />
        </div>
      )}

      <section className="mt-7">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-foreground">Saved reviews</h2>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Most recent documents appear first.
            </p>
          </div>
          {sessions.length > 0 && !confirmingClear && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setConfirmingClear(true)}
              disabled={clearing || loadingId !== null}
              className="text-muted-foreground"
            >
              <Trash2 />
              Clear history
            </Button>
          )}
        </div>

        {confirmingClear && (
          <div className="mb-4 rounded-2xl border border-destructive/20 bg-destructive/[0.055] p-4 sm:p-5">
            <div className="flex items-start gap-3">
              <span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-destructive/10 text-destructive">
                <Trash2 size={17} />
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-foreground">
                  Delete {sessions.length} saved{" "}
                  {sessions.length === 1 ? "review" : "reviews"}?
                </p>
                <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                  This permanently removes saved findings, checklists, metadata, and
                  any retained content. This action cannot be undone.
                </p>
                <div className="mt-4 flex flex-col-reverse gap-2 sm:flex-row">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setConfirmingClear(false)}
                    disabled={clearing}
                  >
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={handleClearConfirmed}
                    disabled={clearing}
                  >
                    {clearing ? (
                      <>
                        <Loader2 className="animate-spin" />
                        Clearing history
                      </>
                    ) : (
                      <>
                        <Trash2 />
                        Delete all reviews
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        {loadError && (
          <div
            role="alert"
            className="mb-4 flex items-start justify-between gap-3 rounded-xl border border-destructive/20 bg-destructive/[0.05] p-4"
          >
            <div>
              <p className="text-sm font-medium text-foreground">Review could not be opened</p>
              <p className="mt-1 text-xs text-muted-foreground">{loadError}</p>
            </div>
            <button
              type="button"
              onClick={() => setLoadError(null)}
              className="text-xs font-medium text-destructive hover:underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {isLoading ? (
          <HistorySkeleton />
        ) : isError ? (
          <StatePanel
            icon={<RefreshCw size={23} />}
            title="History is temporarily unavailable"
            description="Papervault could not reach the local service. Start the backend and try again."
            action={
              <Button variant="outline" onClick={() => refetch()}>
                <RefreshCw />
                Try again
              </Button>
            }
          />
        ) : sessions.length === 0 ? (
          <StatePanel
            icon={<Inbox size={24} />}
            title="No saved reviews yet"
            description="Analyze your first document and its structured findings will appear here."
            action={
              <Button asChild>
                <Link to="/">
                  Start a review
                  <ArrowRight />
                </Link>
              </Button>
            }
          />
        ) : (
          <div className="surface-panel overflow-hidden">
            <div className="hidden grid-cols-[minmax(0,1.4fr)_minmax(9rem,0.55fr)_minmax(10rem,0.55fr)_2rem] gap-4 border-b border-border/70 bg-muted/35 px-5 py-3 text-[0.65rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground md:grid">
              <span>Document</span>
              <span>Type</span>
              <span>Saved</span>
              <span className="sr-only">Open</span>
            </div>

            <div className="divide-y divide-border/70">
              {sessions.map((session) => {
                const busy = loadingId === session.id;
                const disabled =
                  busy || clearing || (loadingId !== null && loadingId !== session.id);

                return (
                  <button
                    type="button"
                    key={session.id}
                    onClick={() => handleOpen(session.id)}
                    disabled={disabled}
                    className="group relative grid w-full gap-3 px-4 py-4 text-left transition-colors hover:bg-muted/35 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-60 md:grid-cols-[minmax(0,1.4fr)_minmax(9rem,0.55fr)_minmax(10rem,0.55fr)_2rem] md:items-center md:gap-4 md:px-5"
                  >
                    <div className="flex min-w-0 items-start gap-3">
                      <span className="flex size-10 shrink-0 items-center justify-center rounded-xl border border-border/70 bg-background text-muted-foreground transition-colors group-hover:border-accent/30 group-hover:text-accent">
                        <FileText size={18} />
                      </span>
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-foreground">
                          {session.filename}
                        </p>
                        <p className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground md:hidden">
                          <CalendarDays size={12} />
                          {formatDate(session.created_at)}
                        </p>
                        <div className="mt-2 flex flex-wrap items-center gap-2 md:mt-1">
                          <Badge variant="secondary" className="text-[0.65rem] md:hidden">
                            {DOC_TYPE_LABELS[session.document_type] ?? session.document_type}
                          </Badge>
                          <span
                            className={cn(
                              "inline-flex items-center gap-1.5 rounded-full px-2 py-1 text-[0.65rem] font-medium",
                              session.content_stored
                                ? "bg-amber-500/10 text-amber-700 dark:text-amber-400"
                                : "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
                            )}
                          >
                            {session.content_stored ? <HardDrive size={11} /> : <ShieldCheck size={11} />}
                            {session.content_stored ? "Content retained" : "Summary only"}
                          </span>
                        </div>
                      </div>
                    </div>

                    <Badge
                      variant="secondary"
                      className="hidden w-fit text-xs md:inline-flex"
                    >
                      {DOC_TYPE_LABELS[session.document_type] ?? session.document_type}
                    </Badge>

                    <div className="hidden text-xs text-muted-foreground md:block">
                      <p>{formatDate(session.created_at)}</p>
                      <p className="mt-0.5 flex items-center gap-1">
                        <Clock3 size={11} />
                        {formatTime(session.created_at)}
                      </p>
                    </div>

                    <span className="absolute right-4 mt-1 md:static md:mt-0">
                      {busy ? (
                        <Loader2 size={16} className="animate-spin text-accent" />
                      ) : (
                        <ChevronRight
                          size={17}
                          className="text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-accent"
                        />
                      )}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

function HistoryStat({
  icon,
  value,
  label,
  tone,
}: {
  icon: React.ReactNode;
  value: number;
  label: string;
  tone: string;
}) {
  return (
    <div className="surface-panel flex items-center gap-3 p-4">
      <span className={cn("flex size-10 items-center justify-center rounded-xl", tone)}>
        {icon}
      </span>
      <div>
        <p className="text-xl font-semibold tracking-tight text-foreground">{value}</p>
        <p className="text-xs text-muted-foreground">{label}</p>
      </div>
    </div>
  );
}

function HistorySkeleton() {
  return (
    <div className="surface-panel divide-y divide-border/70 overflow-hidden" aria-label="Loading history">
      {[0, 1, 2].map((item) => (
        <div key={item} className="flex items-center gap-3 p-4 sm:p-5">
          <div className="size-10 animate-pulse rounded-xl bg-muted" />
          <div className="flex-1">
            <div className="h-3.5 w-2/5 animate-pulse rounded bg-muted" />
            <div className="mt-2 h-3 w-1/4 animate-pulse rounded bg-muted" />
          </div>
          <div className="h-7 w-24 animate-pulse rounded-full bg-muted" />
        </div>
      ))}
    </div>
  );
}

function StatePanel({
  icon,
  title,
  description,
  action,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  action: React.ReactNode;
}) {
  return (
    <div className="surface-panel flex min-h-80 flex-col items-center justify-center px-6 py-12 text-center">
      <span className="flex size-14 items-center justify-center rounded-2xl border border-border bg-muted/45 text-muted-foreground">
        {icon}
      </span>
      <h2 className="mt-5 text-lg font-semibold text-foreground">{title}</h2>
      <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">{description}</p>
      <div className="mt-6">{action}</div>
    </div>
  );
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function formatTime(value: string) {
  return new Date(value).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}
