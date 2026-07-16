import { useState } from "react";
import {
  AlertTriangle,
  CheckSquare2,
  FileSearch,
  LayoutDashboard,
  MessageSquareText,
  SearchCheck,
} from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DocumentHeader } from "@/components/workspace/DocumentHeader";
import { ChecklistTab } from "@/components/workspace/tabs/ChecklistTab";
import { EvidenceTab } from "@/components/workspace/tabs/EvidenceTab";
import { FindingsTab } from "@/components/workspace/tabs/FindingsTab";
import { OverviewTab } from "@/components/workspace/tabs/OverviewTab";
import { QATab } from "@/components/workspace/tabs/QATab";
import { RisksTab } from "@/components/workspace/tabs/RisksTab";
import { useWorkspaceStore } from "@/store/workspaceStore";
import type { Priority } from "@/lib/types";

type TabKey = "overview" | "findings" | "risks" | "checklist" | "qa" | "evidence";
export type PriorityFilter = "all" | Priority;

const TAB_ITEMS = [
  { value: "overview", label: "Overview", icon: LayoutDashboard },
  { value: "findings", label: "Findings", icon: SearchCheck },
  { value: "risks", label: "Risks", icon: AlertTriangle },
  { value: "checklist", label: "Checklist", icon: CheckSquare2 },
  { value: "qa", label: "Ask document", icon: MessageSquareText },
  { value: "evidence", label: "Evidence", icon: FileSearch },
] as const;

export function WorkspacePage() {
  const { extraction, insight, checklist } = useWorkspaceStore();
  const [currentTab, setCurrentTab] = useState<TabKey>("overview");
  const [checklistFilter, setChecklistFilter] = useState<PriorityFilter>("all");
  const [risksFilter, setRisksFilter] = useState<PriorityFilter>("all");

  if (!extraction || !insight || !checklist) return null;

  const onSelectActions = () => {
    setChecklistFilter("all");
    setCurrentTab("checklist");
  };
  const onSelectHighPriority = () => {
    setChecklistFilter("high");
    setCurrentTab("checklist");
  };
  const onSelectRisks = () => {
    setRisksFilter("all");
    setCurrentTab("risks");
  };

  return (
    <div className="min-h-screen">
      <DocumentHeader
        extraction={extraction}
        insight={insight}
        checklist={checklist}
        onSelectActions={onSelectActions}
        onSelectHighPriority={onSelectHighPriority}
        onSelectRisks={onSelectRisks}
        onSelectDates={() => setCurrentTab("findings")}
      />

      <div className="mx-auto w-full max-w-7xl px-4 py-5 sm:px-6 sm:py-7 lg:px-10 lg:py-8">
        <Tabs
          value={currentTab}
          onValueChange={(value) => setCurrentTab(value as TabKey)}
          className="min-w-0"
        >
          <div className="scrollbar-subtle -mx-4 overflow-x-auto px-4 pb-1 sm:mx-0 sm:px-0">
            <TabsList className="flex w-max min-w-full justify-start gap-1">
              {TAB_ITEMS.map(({ value, label, icon: Icon }) => (
                <TabsTrigger key={value} value={value} className="gap-2 px-3.5">
                  <Icon size={14} />
                  {label}
                  {value === "risks" && insight.risks.length > 0 && (
                    <span className="rounded-full bg-destructive px-1.5 py-0.5 text-[0.65rem] leading-none text-destructive-foreground">
                      {insight.risks.length}
                    </span>
                  )}
                </TabsTrigger>
              ))}
            </TabsList>
          </div>

          <TabsContent value="overview" className="mt-5">
            <OverviewTab insight={insight} checklist={checklist} />
          </TabsContent>
          <TabsContent value="findings" className="mt-5">
            <FindingsTab insight={insight} />
          </TabsContent>
          <TabsContent value="risks" className="mt-5">
            <RisksTab
              risks={insight.risks}
              filter={risksFilter}
              onFilterChange={setRisksFilter}
            />
          </TabsContent>
          <TabsContent value="checklist" className="mt-5">
            <ChecklistTab
              checklist={checklist}
              filter={checklistFilter}
              onFilterChange={setChecklistFilter}
            />
          </TabsContent>
          <TabsContent value="qa" className="mt-5">
            <QATab />
          </TabsContent>
          <TabsContent value="evidence" className="mt-5">
            <EvidenceTab extraction={extraction} insight={insight} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
