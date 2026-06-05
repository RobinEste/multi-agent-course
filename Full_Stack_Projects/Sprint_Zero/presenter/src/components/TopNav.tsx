import { Logo } from "./Logo";
import { cn } from "@/lib/cn";
import type { Status } from "@/lib/types";
import { Dot } from "./ui/badge";

type Section = "about" | "scope" | "live";

interface TopNavProps {
  section: Section;
  onChange: (next: Section) => void;
  status: Status;
}

export function TopNav({ section, onChange, status }: TopNavProps) {
  const runStarted = status.phase !== "idle" && status.phase !== "waiting-for-scope";
  const runFinished = status.phase === "done";
  const runFailed = status.phase === "failed";

  const links: { key: Section; label: string; disabled?: boolean }[] = [
    { key: "about", label: "About" },
    { key: "scope", label: "Start a run" },
    { key: "live", label: "Live", disabled: !runStarted },
  ];

  return (
    <header className="sticky top-0 z-20 bg-[rgba(248,248,252,0.85)] backdrop-blur-md border-b border-border">
      <div className="max-w-[1240px] mx-auto px-6 h-14 flex items-center justify-between">
        <Logo />
        <nav className="flex items-center gap-1">
          {links.map((l) => {
            const active = section === l.key;
            return (
              <button
                key={l.key}
                onClick={() => !l.disabled && onChange(l.key)}
                disabled={l.disabled}
                className={cn(
                  "h-8 px-3 rounded-md text-[13px] font-medium tracking-tight",
                  "transition-colors duration-150",
                  active
                    ? "bg-surface-2 text-fg border border-border"
                    : "text-fg-muted hover:text-fg hover:bg-surface-2 border border-transparent",
                  l.disabled && "opacity-40 cursor-not-allowed hover:bg-transparent hover:text-fg-muted"
                )}
              >
                {l.label}
              </button>
            );
          })}
        </nav>
        <div className="flex items-center gap-2 text-[12px] text-fg-muted">
          <Dot
            tone={
              runFailed ? "danger" : runFinished ? "success" : runStarted ? "accent" : "neutral"
            }
          />
          <span>
            {runFailed
              ? "failed"
              : runFinished
                ? "done"
                : runStarted
                  ? status.step || "running"
                  : "idle"}
          </span>
        </div>
      </div>
    </header>
  );
}
