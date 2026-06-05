export function Logo({ className }: { className?: string }) {
  return (
    <div className={"flex items-center gap-2.5 " + (className ?? "")}>
      <svg width="22" height="22" viewBox="0 0 32 32" fill="none" aria-hidden>
        <rect width="32" height="32" rx="8" fill="#5b5bd6" />
        <circle cx="16" cy="16" r="7.5" stroke="rgba(255,255,255,0.9)" strokeWidth="1.75" />
        <circle cx="16" cy="16" r="2.5" fill="white" />
      </svg>
      <div className="flex items-baseline gap-1.5">
        <span className="text-[14.5px] font-semibold tracking-tight text-fg">Sprint Zero</span>
        <span className="text-[11px] text-fg-subtle tracking-widest uppercase font-medium">presenter</span>
      </div>
    </div>
  );
}
