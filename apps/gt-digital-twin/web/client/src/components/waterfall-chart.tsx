import { Precomputed, fmtMoneyM } from "@/lib/data";
import { InfoPopover } from "./info-popover";

// Custom SVG waterfall — no recharts dependency for this one, gives full control.
export function WaterfallChart({ data, policy }: { data: Precomputed; policy: string }) {
  const d = data.historical_decomp[policy];
  if (!d) return null;

  // Build waterfall segments. Note: this is the historical 9yr run decomposition
  // (the only place we have full per-stream attribution from final_ltsa).
  // It's labeled clearly as historical mechanism — not the forward headline above.
  const items: { label: string; value: number; kind: "start" | "pos" | "neg" | "subtotal" | "net" }[] = [
    { label: "Energy revenue", value: d.gross_revenue, kind: "start" },
    { label: "Fuel cost", value: d.fuel_cost, kind: "neg" },
    { label: "VOM", value: d.vom_cost, kind: "neg" },
    { label: "Spark subtotal", value: 0, kind: "subtotal" },
    { label: "LTSA fixed fee", value: d.ltsa_fixed_fee, kind: "neg" },
    { label: "LTSA EOH reserve", value: d.ltsa_eoh_reserve, kind: "neg" },
    { label: "LTSA inspections", value: d.ltsa_inspections, kind: "neg" },
    { label: "LTSA other", value: d.ltsa_other, kind: "neg" },
    { label: "Net P&L", value: 0, kind: "net" },
  ];

  // Compute running totals
  let running = 0;
  const bars = items.map((it) => {
    if (it.kind === "start") {
      const start = 0;
      running = it.value;
      return { ...it, start, end: running };
    }
    if (it.kind === "subtotal") {
      const v = running;
      return { ...it, start: 0, end: v, value: v };
    }
    if (it.kind === "net") {
      const v = running;
      return { ...it, start: 0, end: v, value: v };
    }
    const start = running;
    running += it.value; // value is negative for neg bars
    return { ...it, start, end: running };
  });

  // Find min/max to scale
  const allValues = bars.flatMap((b) => [b.start, b.end]).concat([0]);
  const min = Math.min(...allValues);
  const max = Math.max(...allValues);
  const pad = (max - min) * 0.06;
  const yMin = Math.floor((min - pad) / 1e7) * 1e7;
  const yMax = Math.ceil((max + pad) / 1e7) * 1e7;

  // SVG dims
  const W = 700;
  const H = 320;
  const Mtop = 24;
  const Mbot = 60;
  const Mleft = 56;
  const Mright = 16;
  const innerW = W - Mleft - Mright;
  const innerH = H - Mtop - Mbot;
  const barW = innerW / bars.length * 0.62;
  const stepX = innerW / bars.length;

  const yScale = (v: number) => Mtop + (yMax - v) / (yMax - yMin) * innerH;

  // Y ticks
  const tickCount = 5;
  const ticks = Array.from({ length: tickCount }, (_, i) => yMin + (i * (yMax - yMin) / (tickCount - 1)));

  return (
    <section className="card-clean p-5 lg:p-6">
      <header className="flex items-start justify-between gap-4 mb-1">
        <div>
          <h2 className="text-sm font-medium tracking-tight">P&L decomposition</h2>
          <p className="text-[11.5px] text-muted-foreground mt-0.5 leading-relaxed">
            Where each dollar comes from and where it goes. Energy-only — capacity and steam revenue are excluded by design.
          </p>
        </div>
        <InfoPopover
          title="P&L decomposition"
          status="real_observed"
          source="Mode-A historical replay 2017–2025 (notebook 04 / src/gt_engine.run_mode). Spark = LMP × MWh − fuel − VOM; LTSA streams from final_ltsa accumulators."
          whyV1="Decomposes the historical 9-yr run — the only window where we have full per-stream attribution. The forward headline above is a separate 1-yr distribution."
          upgrade="Per-scenario forward decomposition (currently the engine only writes spark + total LTSA per path); add ICAP + steam columns when those streams exist."
          value={`Historical · Mode ${policy} · 2017–2025`}
        />
      </header>

      <div className="mt-4 -mx-2 overflow-x-auto">
        <svg viewBox={`0 0 ${W} ${H}`} width="100%" preserveAspectRatio="xMidYMid meet" className="block" style={{ minWidth: 640 }}>
          {/* axis grid */}
          {ticks.map((t, i) => (
            <g key={i}>
              <line x1={Mleft} y1={yScale(t)} x2={W - Mright} y2={yScale(t)} stroke="hsl(var(--border))" strokeWidth="0.5" strokeDasharray={t === 0 ? "" : "2 3"} opacity={t === 0 ? 0.8 : 0.5} />
              <text x={Mleft - 8} y={yScale(t)} dy="0.32em" textAnchor="end" className="fill-muted-foreground" style={{ fontFamily: "var(--font-mono)", fontSize: 10 }}>
                {`${t < 0 ? "−" : ""}$${Math.abs(t / 1e6).toFixed(0)}M`}
              </text>
            </g>
          ))}

          {/* bars */}
          {bars.map((b, i) => {
            const x = Mleft + i * stepX + (stepX - barW) / 2;
            const y0 = yScale(b.start);
            const y1 = yScale(b.end);
            const top = Math.min(y0, y1);
            const h = Math.max(2, Math.abs(y1 - y0));
            let fill = "hsl(var(--chart-1))";
            if (b.kind === "neg") fill = "hsl(var(--chart-2))";
            if (b.kind === "subtotal") fill = "hsl(var(--chart-3))";
            if (b.kind === "net") fill = b.end < 0 ? "hsl(var(--destructive))" : "hsl(var(--chart-1))";

            // dotted connector from previous bar's end to current's start
            const conn = i > 0 ? (
              <line
                x1={Mleft + (i - 1) * stepX + (stepX + barW) / 2}
                x2={x}
                y1={yScale(bars[i - 1].end)}
                y2={yScale(b.start)}
                stroke="hsl(var(--border))"
                strokeWidth="1"
                strokeDasharray="2 2"
              />
            ) : null;

            return (
              <g key={i}>
                {conn}
                <rect x={x} y={top} width={barW} height={h} fill={fill} rx={1.5} opacity={b.kind === "subtotal" || b.kind === "net" ? 0.95 : 0.85} />
                {/* value label */}
                <text x={x + barW / 2} y={top - 6} textAnchor="middle" className="fill-foreground" style={{ fontFamily: "var(--font-mono)", fontSize: 10, fontWeight: 500 }}>
                  {b.kind === "net" || b.kind === "subtotal" ? fmtMoneyM(b.value, 0) : (b.value >= 0 ? `+${fmtMoneyM(b.value, 0)}` : fmtMoneyM(b.value, 0))}
                </text>
                {/* x-label */}
                <text x={x + barW / 2} y={H - Mbot + 16} textAnchor="middle" className="fill-muted-foreground" style={{ fontSize: 10 }}>
                  {b.label.split(" ").slice(0, 2).join(" ")}
                </text>
                {b.label.split(" ").length > 2 && (
                  <text x={x + barW / 2} y={H - Mbot + 30} textAnchor="middle" className="fill-muted-foreground" style={{ fontSize: 10 }}>
                    {b.label.split(" ").slice(2).join(" ")}
                  </text>
                )}
              </g>
            );
          })}

          {/* baseline 0 emphasis */}
          <line x1={Mleft} y1={yScale(0)} x2={W - Mright} y2={yScale(0)} stroke="hsl(var(--foreground))" strokeWidth="0.75" opacity="0.5" />
        </svg>
      </div>

      <footer className="mt-4 pt-3 border-t border-card-border flex items-center justify-between text-[10.5px] text-muted-foreground font-mono">
        <span>Mode {policy} · 9-yr historical replay · {Math.round(d.total_mwh / 1000).toLocaleString()}k MWh · {Math.round(d.fired_hours).toLocaleString()} fired hrs</span>
        <span>Energy-only · ICAP + steam excluded</span>
      </footer>
    </section>
  );
}
