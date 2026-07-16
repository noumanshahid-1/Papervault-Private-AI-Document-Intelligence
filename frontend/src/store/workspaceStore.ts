import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ExtractionResult, DocumentInsight, ChecklistResult, QuestionAnswer } from "../lib/types";

export type WorkspacePhase = "idle" | "extracting" | "analyzing" | "building" | "ready" | "error";

interface WorkspaceState {
  phase: WorkspacePhase;
  error: string | null;
  extraction: ExtractionResult | null;
  insight: DocumentInsight | null;
  checklist: ChecklistResult | null;
  qaHistory: QuestionAnswer[];
  checklistCompletion: Record<string, boolean>;

  setPhase: (phase: WorkspacePhase) => void;
  setError: (error: string | null) => void;
  setExtraction: (result: ExtractionResult) => void;
  setInsight: (insight: DocumentInsight) => void;
  setChecklist: (checklist: ChecklistResult) => void;
  loadWorkspace: (
    extraction: ExtractionResult,
    insight: DocumentInsight,
    checklist: ChecklistResult,
  ) => void;
  addQA: (qa: QuestionAnswer) => void;
  toggleChecklist: (id: string) => void;
  reset: () => void;
}

const initialState = {
  phase: "idle" as WorkspacePhase,
  error: null,
  extraction: null,
  insight: null,
  checklist: null,
  qaHistory: [],
  checklistCompletion: {},
};

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set) => ({
      ...initialState,

      setPhase: (phase) => set({ phase }),
      setError: (error) => set((s) => ({
        error,
        // Only override phase to "error" when setting an error; clearing
        // an error must NOT reset the phase (would kick the user out of
        // a freshly-ready workspace).
        phase: error ? "error" : s.phase === "error" ? "idle" : s.phase,
      })),
      setExtraction: (extraction) => set({ extraction }),
      setInsight: (insight) => set({ insight }),
      setChecklist: (checklist) => set({ checklist }),
      loadWorkspace: (extraction, insight, checklist) =>
        set({
          extraction,
          insight,
          checklist,
          error: null,
          phase: "ready",
          qaHistory: [],
        }),
      addQA: (qa) => set((s) => ({ qaHistory: [...s.qaHistory, qa] })),
      toggleChecklist: (id) =>
        set((s) => ({
          checklistCompletion: {
            ...s.checklistCompletion,
            [id]: !s.checklistCompletion[id],
          },
        })),
      reset: () => set(initialState),
    }),
    {
      name: "papervault-workspace",
      partialize: (s) => ({ checklistCompletion: s.checklistCompletion }),
    }
  )
);
