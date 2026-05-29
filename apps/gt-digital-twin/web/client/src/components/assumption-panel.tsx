import { CalibrationEntry } from "@/lib/data";
import { StatusBadge } from "./status-badge";
import { InfoPopover } from "./info-popover";

const PRETTY: Record<string, string> = {
  policy: "Dispatch policy (A/B/C)",
  gas_price: "Gas price",
  init_state: "Initial plant state",
  scenario: "Scenario ensemble",
  capacity_revenue: "Capacity revenue (ICAP)",
  steam_revenue: "Steam revenue (host)",
  ltsa_deeper: "Deeper LTSA terms",
  multi_year: "Multi-year horizon",
  wear_constants: "Wear / aging constants",
};

export function AssumptionPanel({ register }: { register: Record<string, CalibrationEntry> }) {
  const items = Object.entries(register);

  // Group by status family
  const families = [
    { key: "real_observed", label: "Real · observed" },
    { key: "assumed_industry", label: "Assumed · industry" },
    { key: "modeling_convention", label: "Modeling · convention" },
    { key: "placeholder", label: "Placeholder" },
    { key: "deferred_roadmap", label: "Deferred · roadmap" },
  ];
  const counts = families.map((f) => ({
    ...f,
    count: items.filter(([, e]) => e.status === f.key).length,
  }));

  return (
    <section>
      <header className="mb-6 max-w-2xl">
        <p className="eyebrow mb-2">§03 · Assumptions &amp; provenance</p>
        <h2 className="display text-3xl md:text-4xl tracking-[-0.02em] leading-[1.05]">
          What's real. What's a placeholder. What's deferred.
        </h2>
        <p className="mt-3 text-[13.5px] text-foreground/75 leading-[1.6]">
          Every active control and every roadmap item carries a status badge from
          <span className="font-mono text-foreground/85"> docs/assumptions/parameter_calibration_register.md</span>.
          This is the v1 contract.
        </p>
      </header>

      {/* Status legend strip */}
      <div className="flex flex-wrap gap-2.5 mb-4">
        {counts.filter((c) => c.count > 0).map((c) => (
          <div key={c.key} className="inline-flex items-center gap-2 px-3 py-1.5 border border-card-border rounded-sm bg-card">
            <StatusBadge status={c.key} size="xs" />
            <span className="font-mono text-[10.5px] text-foreground/80">{c.count}</span>
          </div>
        ))}
      </div>

      <div className="card-clean overflow-hidden">
        <div className="grid grid-cols-12 px-5 py-2.5 border-b border-card-border bg-secondary/30 text-[10px] eyebrow">
          <div className="col-span-3">Assumption</div>
          <div className="col-span-2">Status</div>
          <div className="col-span-3">Source</div>
          <div className="col-span-2">Why v1 acceptable</div>
          <div className="col-span-2">What would upgrade it</div>
        </div>
        <ul>
          {items.map(([key, e], i) => (
            <li key={i} className={`grid grid-cols-12 gap-4 px-5 py-4 ${i < items.length - 1 ? "border-b border-card-border" : ""} hover:bg-secondary/15 transition-colors`}>
              <div className="col-span-12 md:col-span-3 text-[12px] font-medium tracking-tight flex items-center gap-1.5">
                {PRETTY[key] ?? key}
                <InfoPopover title={PRETTY[key] ?? key} status={e.status} source={e.source} whyV1={e.why_v1} upgrade={e.upgrade} />
              </div>
              <div className="col-span-12 md:col-span-2">
                <StatusBadge status={e.status} size="xs" />
              </div>
              <div className="col-span-12 md:col-span-3 text-[11px] text-muted-foreground leading-relaxed font-mono">{e.source}</div>
              <div className="col-span-12 md:col-span-2 text-[11px] text-muted-foreground/90 leading-relaxed">{e.why_v1}</div>
              <div className="col-span-12 md:col-span-2 text-[11px] text-muted-foreground/90 leading-relaxed">{e.upgrade}</div>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
