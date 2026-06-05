import { motion } from "motion/react";
import { Check, Loader2, Server, Monitor } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/cn";
import type { BuildState } from "@/lib/types";

interface BuildCardsProps {
  backend?: BuildState;
  frontend?: BuildState;
}

export function BuildCards({ backend = "idle", frontend = "idle" }: BuildCardsProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="h-full flex flex-col gap-4"
    >
      <Card className="p-6">
        <div className="flex items-start justify-between gap-3">
          <div>
            <Badge tone="accent">Parallel build</Badge>
            <h3 className="mt-3 text-[22px] font-semibold tracking-tight text-fg">
              Both engineers are building to the contract.
            </h3>
            <p className="mt-2 text-[14px] leading-relaxed text-fg-muted max-w-[620px]">
              Backend and frontend never speak to each other. They both read{" "}
              <code className="font-mono text-[12.5px] text-fg">docs/api-contract.md</code> and
              build in isolation. When they return, QA validates both against the same contract.
            </p>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-1">
        <BuildPanel
          icon={Server}
          label="backend-engineer"
          title="Express + Supabase"
          state={backend}
          steps={[
            "supabase client + JWT middleware",
            "migrations and idempotent seed",
            "routes per contract entity",
          ]}
        />
        <BuildPanel
          icon={Monitor}
          label="frontend-engineer"
          title="React + Vite + Supabase Auth"
          state={frontend}
          steps={[
            "session context + protected routes",
            "login, signup, marketing page",
            "product screens + api client",
          ]}
        />
      </div>
    </motion.div>
  );
}

function BuildPanel({
  icon: Icon,
  label,
  title,
  state,
  steps,
}: {
  icon: React.ComponentType<{ className?: string; strokeWidth?: number }>;
  label: string;
  title: string;
  state: BuildState;
  steps: string[];
}) {
  const isRunning = state === "running";
  const isDone = state === "done";

  return (
    <Card
      className={cn(
        "h-full transition-colors duration-300",
        isRunning && "border-[rgba(91,91,214,0.3)] bg-gradient-to-b from-[rgba(91,91,214,0.04)] to-transparent",
        isDone && "border-success/30"
      )}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div
              className={cn(
                "h-10 w-10 rounded-lg border flex items-center justify-center shrink-0 transition-colors",
                isRunning && "border-accent/40 bg-accent/[0.08]",
                isDone && "border-success/30 bg-success/10",
                state === "idle" && "border-border bg-surface-3"
              )}
            >
              <Icon
                className={cn(
                  "w-4.5 h-4.5 transition-colors",
                  isRunning && "text-accent",
                  isDone && "text-success",
                  state === "idle" && "text-fg-subtle"
                )}
                strokeWidth={1.5}
              />
            </div>
            <div>
              <code className="text-[12px] font-mono text-fg-subtle">{label}</code>
              <CardTitle className="mt-0.5">{title}</CardTitle>
              <CardDescription>
                {isRunning
                  ? "Building…"
                  : isDone
                    ? "Complete. All endpoints match the contract."
                    : state === "failed"
                      ? "Reported a failure."
                      : "Waiting for the build brief."}
              </CardDescription>
            </div>
          </div>
          <StateIcon state={state} />
        </div>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2.5">
          {steps.map((s, i) => (
            <li key={i} className="flex items-center gap-2.5 text-[13px]">
              <div
                className={cn(
                  "w-1.5 h-1.5 rounded-full shrink-0",
                  isDone ? "bg-success" : isRunning ? "bg-accent animate-pulse" : "bg-fg-subtle/40"
                )}
              />
              <span className={isRunning || isDone ? "text-fg-muted" : "text-fg-subtle"}>{s}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

function StateIcon({ state }: { state: BuildState }) {
  if (state === "running")
    return (
      <div className="h-7 w-7 rounded-full bg-accent/10 border border-accent/40 flex items-center justify-center">
        <Loader2 className="w-3.5 h-3.5 text-accent animate-spin" strokeWidth={2} />
      </div>
    );
  if (state === "done")
    return (
      <div className="h-7 w-7 rounded-full bg-success/15 border border-success/40 flex items-center justify-center">
        <Check className="w-3.5 h-3.5 text-success" strokeWidth={2.5} />
      </div>
    );
  if (state === "failed")
    return (
      <div className="h-7 w-7 rounded-full bg-danger/15 border border-danger/40 flex items-center justify-center">
        <span className="text-[10px] font-bold text-danger">!</span>
      </div>
    );
  return (
    <div className="h-7 w-7 rounded-full border border-border flex items-center justify-center">
      <span className="text-[10.5px] font-mono text-fg-subtle">idle</span>
    </div>
  );
}
