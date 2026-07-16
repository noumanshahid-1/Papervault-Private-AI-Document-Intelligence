import { Link, useLocation } from "react-router-dom";
import {
  Archive,
  FileSearch2,
  FileText,
  History,
  Menu,
  Moon,
  ShieldCheck,
  Sparkles,
  Sun,
} from "lucide-react";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { useWorkspaceStore } from "@/store/workspaceStore";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

const navItems = [
  {
    to: "/",
    label: "New review",
    description: "Analyze a local document",
    icon: FileSearch2,
  },
  {
    to: "/history",
    label: "Review history",
    description: "Reopen saved findings",
    icon: History,
  },
];

export function Sidebar() {
  const location = useLocation();
  const phase = useWorkspaceStore((s) => s.phase);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [dark, setDark] = useState(() => localStorage.getItem("pv-theme") === "dark");

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("pv-theme", dark ? "dark" : "light");
  }, [dark]);

  return (
    <>
      <header className="fixed inset-x-0 top-0 z-40 flex h-16 items-center justify-between border-b border-border/70 bg-background/85 px-4 backdrop-blur-xl lg:hidden">
        <Brand compact />
        <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
          <SheetTrigger asChild>
            <Button variant="outline" size="icon" aria-label="Open navigation">
              <Menu size={18} />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-[88vw] max-w-80 border-r-border/70 p-0">
            <SheetTitle className="sr-only">Papervault navigation</SheetTitle>
            <NavigationContent
              locationPath={location.pathname}
              phase={phase}
              dark={dark}
              onToggleTheme={() => setDark((value) => !value)}
              mobile
            />
          </SheetContent>
        </Sheet>
      </header>

      <aside className="fixed inset-y-0 left-0 z-40 hidden w-72 border-r border-border/70 bg-card/88 backdrop-blur-xl lg:flex lg:flex-col">
        <NavigationContent
          locationPath={location.pathname}
          phase={phase}
          dark={dark}
          onToggleTheme={() => setDark((value) => !value)}
        />
      </aside>
    </>
  );
}

function NavigationContent({
  locationPath,
  phase,
  dark,
  onToggleTheme,
  mobile = false,
}: {
  locationPath: string;
  phase: ReturnType<typeof useWorkspaceStore.getState>["phase"];
  dark: boolean;
  onToggleTheme: () => void;
  mobile?: boolean;
}) {
  const items = phase === "ready"
    ? [
        ...navItems,
        {
          to: "/workspace",
          label: "Active workspace",
          description: "Continue the current review",
          icon: FileText,
        },
      ]
    : navItems;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="border-b border-border/70 px-5 py-5">
        <Brand />
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-5">
        <p className="px-3 pb-2 text-[0.65rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Workspace
        </p>
        <nav className="space-y-1.5" aria-label="Primary navigation">
          {items.map(({ to, label, description, icon: Icon }) => {
            const active = locationPath === to;
            const link = (
              <Link
                key={to}
                to={to}
                className={cn(
                  "group flex items-center gap-3 rounded-xl px-3 py-3 transition-all",
                  active
                    ? "bg-primary text-primary-foreground shadow-[0_12px_30px_-18px_hsl(var(--primary))]"
                    : "text-muted-foreground hover:bg-muted/70 hover:text-foreground",
                )}
              >
                <span
                  className={cn(
                    "flex size-9 shrink-0 items-center justify-center rounded-lg border transition-colors",
                    active
                      ? "border-white/15 bg-white/10"
                      : "border-border/80 bg-background/60 group-hover:border-accent/30",
                  )}
                >
                  <Icon size={17} />
                </span>
                <span className="min-w-0">
                  <span className="block text-sm font-medium">{label}</span>
                  <span
                    className={cn(
                      "mt-0.5 block truncate text-[0.7rem]",
                      active ? "text-primary-foreground/65" : "text-muted-foreground",
                    )}
                  >
                    {description}
                  </span>
                </span>
              </Link>
            );

            return mobile ? (
              <SheetClose asChild key={to}>
                {link}
              </SheetClose>
            ) : (
              link
            );
          })}
        </nav>
      </div>

      <div className="space-y-3 border-t border-border/70 p-4">
        <div className="rounded-xl border border-emerald-500/15 bg-emerald-500/[0.06] p-3">
          <div className="flex items-start gap-2.5">
            <ShieldCheck
              size={16}
              className="mt-0.5 shrink-0 text-emerald-600 dark:text-emerald-400"
            />
            <div>
              <p className="text-xs font-medium text-foreground">Private by design</p>
              <p className="mt-1 text-[0.7rem] leading-relaxed text-muted-foreground">
                Documents stay on this machine. No cloud model calls.
              </p>
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={onToggleTheme}
          className="flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-sm text-muted-foreground transition-colors hover:bg-muted/70 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <span className="flex items-center gap-2.5">
            {dark ? <Sun size={15} /> : <Moon size={15} />}
            {dark ? "Light appearance" : "Dark appearance"}
          </span>
          <span className="text-[0.65rem] uppercase tracking-wider">
            {dark ? "Light" : "Dark"}
          </span>
        </button>
      </div>
    </div>
  );
}

function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <Link to="/" className="inline-flex items-center gap-3">
      <span className="relative flex size-10 items-center justify-center overflow-hidden rounded-xl bg-primary text-primary-foreground shadow-[0_12px_30px_-16px_hsl(var(--primary))]">
        <Archive size={19} />
        <Sparkles className="absolute right-1 top-1 size-2.5 text-sky-300" />
      </span>
      <span className={cn("min-w-0", compact && "sm:block")}>
        <span className="block text-base font-semibold tracking-tight text-foreground">
          Papervault
        </span>
        {!compact && (
          <span className="mt-0.5 block text-[0.68rem] uppercase tracking-[0.14em] text-muted-foreground">
            Document intelligence
          </span>
        )}
      </span>
    </Link>
  );
}
