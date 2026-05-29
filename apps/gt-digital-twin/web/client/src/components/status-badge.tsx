// Status badge mapped to the parameter calibration register status taxonomy
export type StatusKey = "real_observed" | "real_reported" | "assumed_industry" | "assumed_vendor" | "assumed_derived" | "placeholder" | "modeling_convention" | "deferred";

const map: Record<string, { label: string; color: string; dot: string; bg: string }> = {
  real_observed:        { label: "Real · observed",        color: "hsl(var(--status-real))",        dot: "bg-[hsl(var(--status-real))]",        bg: "bg-[hsl(var(--status-real)/0.10)]" },
  real_reported:        { label: "Real · reported",        color: "hsl(var(--status-real))",        dot: "bg-[hsl(var(--status-real))]",        bg: "bg-[hsl(var(--status-real)/0.10)]" },
  assumed_industry:     { label: "Assumed · industry",     color: "hsl(var(--status-assumed))",     dot: "bg-[hsl(var(--status-assumed))]",     bg: "bg-[hsl(var(--status-assumed)/0.10)]" },
  assumed_vendor:       { label: "Assumed · vendor",       color: "hsl(var(--status-assumed))",     dot: "bg-[hsl(var(--status-assumed))]",     bg: "bg-[hsl(var(--status-assumed)/0.10)]" },
  assumed_derived:      { label: "Assumed · derived",      color: "hsl(var(--status-assumed))",     dot: "bg-[hsl(var(--status-assumed))]",     bg: "bg-[hsl(var(--status-assumed)/0.10)]" },
  placeholder:          { label: "Placeholder",            color: "hsl(var(--status-placeholder))", dot: "bg-[hsl(var(--status-placeholder))]", bg: "bg-[hsl(var(--status-placeholder)/0.10)]" },
  modeling_convention:  { label: "Modeling convention",    color: "hsl(var(--status-convention))",  dot: "bg-[hsl(var(--status-convention))]",  bg: "bg-[hsl(var(--status-convention)/0.10)]" },
  deferred:             { label: "Deferred · roadmap",     color: "hsl(var(--status-deferred))",    dot: "bg-[hsl(var(--status-deferred))]",    bg: "bg-[hsl(var(--status-deferred)/0.10)]" },
};

export function StatusBadge({ status, size = "sm" }: { status: string; size?: "xs" | "sm" }) {
  const entry = map[status] ?? map.placeholder;
  const sizing = size === "xs"
    ? "text-[10px] px-1.5 py-0.5"
    : "text-[10.5px] px-2 py-0.5";
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border border-card-border ${entry.bg} ${sizing} font-medium tracking-wide`}
          style={{ color: entry.color }}>
      <span className={`w-1.5 h-1.5 rounded-full ${entry.dot}`} />
      {entry.label}
    </span>
  );
}
