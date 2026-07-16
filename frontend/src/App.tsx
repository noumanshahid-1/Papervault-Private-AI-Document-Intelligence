import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Sidebar } from "./components/layout/Sidebar";
import { useWorkspaceStore } from "./store/workspaceStore";

const IntakePage = lazy(() =>
  import("./pages/IntakePage").then((module) => ({ default: module.IntakePage })),
);
const WorkspacePage = lazy(() =>
  import("./pages/WorkspacePage").then((module) => ({ default: module.WorkspacePage })),
);
const HistoryPage = lazy(() =>
  import("./pages/HistoryPage").then((module) => ({ default: module.HistoryPage })),
);

function WorkspaceGuard() {
  const phase = useWorkspaceStore((s) => s.phase);
  if (phase !== "ready") return <Navigate to="/" replace />;
  return <WorkspacePage />;
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen overflow-x-hidden bg-background text-foreground">
        <div className="pointer-events-none fixed inset-x-0 top-0 -z-10 h-[34rem] bg-[radial-gradient(circle_at_top_left,hsl(var(--accent)/0.13),transparent_38%),radial-gradient(circle_at_75%_0%,hsl(var(--primary)/0.1),transparent_34%)]" />
        <Sidebar />
        <main className="min-w-0 pt-16 lg:pl-72 lg:pt-0">
          <Suspense fallback={<RouteLoading />}>
            <Routes>
              <Route path="/" element={<IntakePage />} />
              <Route path="/workspace" element={<WorkspaceGuard />} />
              <Route path="/history" element={<HistoryPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </BrowserRouter>
  );
}

function RouteLoading() {
  return (
    <div className="page-shell" aria-label="Loading page">
      <div className="animate-pulse">
        <div className="h-3 w-28 rounded bg-muted" />
        <div className="mt-4 h-9 w-72 max-w-full rounded-lg bg-muted" />
        <div className="mt-3 h-4 w-[32rem] max-w-full rounded bg-muted" />
        <div className="mt-8 grid gap-4 md:grid-cols-2">
          <div className="h-72 rounded-2xl border border-border bg-card" />
          <div className="h-72 rounded-2xl border border-border bg-card" />
        </div>
      </div>
    </div>
  );
}
