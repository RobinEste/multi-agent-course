import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { ArrowRight, ArrowLeft, CheckCircle2, Globe, Github, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input, Textarea, Label, FieldHint } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/cn";
import { submitScope } from "@/lib/status";
import type { ScopeLevel, Status } from "@/lib/types";

interface ScopeProps {
  onSubmitted: () => void;
  status: Status;
}

const LEVEL_OPTIONS: {
  value: ScopeLevel;
  title: string;
  tagline: string;
  body: string;
  recommended?: boolean;
}[] = [
  {
    value: "clickable",
    title: "Clickable",
    tagline: "Pitch-ready walkthrough",
    body: "Mock backend, fake data, no auth. Fastest path to something you can show.",
  },
  {
    value: "MVP",
    title: "MVP",
    tagline: "The idea actually works",
    body: "Real Supabase, real auth, one core loop end-to-end.",
    recommended: true,
  },
  {
    value: "Prod",
    title: "Prod",
    tagline: "Ready for real users",
    body: "MVP plus error states, validation, loading, and a Playwright error-path test.",
  },
];

export function Scope({ onSubmitted, status }: ScopeProps) {
  const [projectName, setProjectName] = useState("");
  const [companyUrl, setCompanyUrl] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [level, setLevel] = useState<ScopeLevel>("MVP");
  const [coreLoop, setCoreLoop] = useState("");
  const [excludes, setExcludes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Transition once the orchestrator has picked up scope.md.
  useEffect(() => {
    if (status.phase !== "idle" && status.phase !== "waiting-for-scope") {
      const t = setTimeout(onSubmitted, 300);
      return () => clearTimeout(t);
    }
  }, [status.phase, onSubmitted]);

  const canSubmit = companyUrl.trim() && coreLoop.trim() && !submitting;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    const result = await submitScope({
      projectName,
      companyUrl,
      repoUrl,
      level,
      coreLoop,
      excludes,
    });
    if (!result.ok) {
      setSubmitting(false);
      setError(result.error ?? "Could not submit");
    }
    // On success: leave submitting=true. The phase watcher above will transition.
  }

  return (
    <div className="pt-16 pb-8">
      <div className="max-w-[820px] mx-auto">
        {/* ------------------------ header ------------------------ */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Badge tone="accent" className="mb-5">
            Step 1 of 1
          </Badge>
          <h1 className="text-[44px] leading-[1.1] font-semibold tracking-[-0.02em] text-fg">
            Tell Sprint Zero what you want to build.
          </h1>
          <p className="mt-4 text-[16px] leading-relaxed text-fg-muted max-w-[620px]">
            Sprint Zero normally asks these questions in the terminal. The answers go
            straight into <code className="font-mono text-[13px] text-fg">docs/scope.md</code>,
            which every downstream agent reads.
          </p>
        </motion.div>

        {/* ------------------------ form ------------------------ */}
        <motion.form
          onSubmit={handleSubmit}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.06, duration: 0.3 }}
          className="mt-12 space-y-10"
        >
          {/* ---- identity ---- */}
          <section className="space-y-5">
            <SectionLabel num="01" title="Identify the run" />

            <Field>
              <Label htmlFor="projectName">Project name</Label>
              <Input
                id="projectName"
                placeholder="mini-crm"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
              />
              <FieldHint>A short slug used in the delivery summary. Optional.</FieldHint>
            </Field>

            <Field>
              <Label htmlFor="companyUrl">Reference product URL</Label>
              <div className="relative">
                <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-fg-subtle pointer-events-none" />
                <Input
                  id="companyUrl"
                  placeholder="https://twenty.com"
                  value={companyUrl}
                  onChange={(e) => setCompanyUrl(e.target.value)}
                  required
                  className="pl-9"
                />
              </div>
              <FieldHint>
                The product Sprint Zero will study to build something similar. Required.
              </FieldHint>
            </Field>

            <Field>
              <Label htmlFor="repoUrl">Repo URL</Label>
              <div className="relative">
                <Github className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-fg-subtle pointer-events-none" />
                <Input
                  id="repoUrl"
                  placeholder="https://github.com/twentyhq/twenty"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  className="pl-9"
                />
              </div>
              <FieldHint>
                Optional. Providing a repo lets the researcher read the source alongside the
                product site.
              </FieldHint>
            </Field>
          </section>

          {/* ---- level ---- */}
          <section className="space-y-5">
            <SectionLabel num="02" title="Pick a build level" />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {LEVEL_OPTIONS.map((opt) => {
                const selected = level === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setLevel(opt.value)}
                    className={cn(
                      "text-left p-5 rounded-xl border transition-all duration-150",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50",
                      selected
                        ? "border-[rgba(91,91,214,0.4)] bg-gradient-to-b from-[rgba(91,91,214,0.07)] to-transparent shadow-[var(--shadow-elev-2)]"
                        : "border-border bg-surface hover:border-border-strong hover:bg-surface-2"
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <div className="text-[11px] font-mono text-fg-subtle uppercase tracking-widest">
                        {opt.value}
                      </div>
                      {selected ? (
                        <CheckCircle2 className="w-4 h-4 text-accent" strokeWidth={2} />
                      ) : opt.recommended ? (
                        <Badge tone="accent">Default</Badge>
                      ) : null}
                    </div>
                    <div className="mt-3 text-[17px] font-semibold tracking-tight text-fg">
                      {opt.title}
                    </div>
                    <div className="mt-0.5 text-[12.5px] text-accent font-medium">{opt.tagline}</div>
                    <div className="mt-3 text-[13px] leading-relaxed text-fg-muted">{opt.body}</div>
                  </button>
                );
              })}
            </div>
          </section>

          {/* ---- core loop ---- */}
          <section className="space-y-5">
            <SectionLabel num="03" title="Name the core loop" />
            <Field>
              <Label htmlFor="coreLoop">The one user flow that must work</Label>
              <Textarea
                id="coreLoop"
                placeholder="User creates a contact (name, email, company), creates a deal linked to that contact, and moves the deal across pipeline stages (Lead → Qualified → Proposal → Closed Won / Closed Lost)."
                value={coreLoop}
                onChange={(e) => setCoreLoop(e.target.value)}
                required
                className="min-h-[120px]"
              />
              <FieldHint>
                If only one thing works end-to-end, what is it? Be specific — the agents follow
                this literally.
              </FieldHint>
            </Field>
          </section>

          {/* ---- excludes ---- */}
          <section className="space-y-5">
            <SectionLabel num="04" title="Name what to leave out" />
            <Field>
              <Label htmlFor="excludes">Anything to exclude</Label>
              <Textarea
                id="excludes"
                placeholder={
                  "Companies as a separate entity (roll into contacts)\nCustom fields\nEmail integration\nSearch and saved views"
                }
                value={excludes}
                onChange={(e) => setExcludes(e.target.value)}
                className="min-h-[120px]"
              />
              <FieldHint>
                One per line. The long and specific this list is, the tighter the build.
              </FieldHint>
            </Field>
          </section>

          {/* ---- submit ---- */}
          <section className="pt-2">
            <Card className="p-5 flex items-center justify-between bg-surface-2/60">
              <div className="flex items-center gap-3">
                <Button type="button" variant="ghost" size="md" onClick={() => history.back()}>
                  <ArrowLeft className="w-4 h-4" />
                  Back
                </Button>
                {error && (
                  <span className="text-[13px] text-danger">{error}</span>
                )}
              </div>
              <Button type="submit" size="lg" disabled={!canSubmit}>
                {submitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Waiting for Sprint Zero…
                  </>
                ) : (
                  <>
                    Start the run
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </Button>
            </Card>
          </section>
        </motion.form>
      </div>
    </div>
  );
}

function SectionLabel({ num, title }: { num: string; title: string }) {
  return (
    <div className="flex items-baseline gap-3 pb-2 border-b border-border/60">
      <span className="font-mono text-[11px] text-fg-subtle tracking-widest">{num}</span>
      <h2 className="text-[17px] font-semibold tracking-tight text-fg">{title}</h2>
    </div>
  );
}

function Field({ children }: { children: React.ReactNode }) {
  return <div className="space-y-2">{children}</div>;
}
