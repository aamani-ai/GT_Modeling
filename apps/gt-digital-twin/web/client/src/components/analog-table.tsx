import { GridCell, fmtMoneyM, fmtNumber } from "@/lib/data";
import { InfoPopover } from "./info-popover";

interface Props {
  cell: GridCell | null;
  policy: string;
  initState: string;
  gasMult: number;
}

// Full per-path table — window, probability, spark margin, net P&L, fired hours.
// Sorted by probability descending.
export function AnalogTable({ cell, policy, initState, gasMult }: Props) {
  if (!cell) return null;
  const paths = [...cell.per_path].sort((a, b) => b.probability - a.probability);
  const maxProb = Math.max(...paths.map((p) => p.probability));
  const allNetVals = paths.map((p) => p.net_pl_usd);
  const netMin = Math.min(...allNetVals);
  const netMax = Math.max(...allNetVals);
  const span = Math.max(netMax - netMin, 1);

  return (
    <section className="space-y-5">
      <header className="flex items-end justify-between gap-4 flex-wrap">
        <div className="max-w-2xl">
          <p className="eyebrow mb-2">§06 · Analog scenario table</p>
          <h2 className="display text-3xl md:text-4xl tracking-[-0.02em] leading-[1.05]">
            Every path is named.
          </h2>
          <p className="mt-3 text-[13.5px] text-foreground/75 leading-[1.6]">
            The {paths.length} analog windows that compose the forward ensemble — each one a real historical year.
            Outcomes are conditional on this anchor: policy {policy}, gas {gasMult}×, {initState}.
          </p>
        </div>
        <InfoPopover
          title="Analog scenario table"
          status="real_observed"
          source="src/forward.run_forward per_path output. Each row is one engine simulation against the named historical window's gas+power+temperature record."
          whyV1="Provenance per path — no synthetic time-series. Every dollar number is traceable to a specific historical window."
          upgrade="Add per-path P&L decomposition (currently the engine writes annual aggregates by stream); add per-path winter-month detail."
        />
      </header>

      <div className="card-clean overflow-hidden">
        {/* Header row */}
        <div className="grid grid-cols-[60px_110px_1fr_110px_1fr_100px_80px_80px] gap-3 px-5 py-3 border-b border-card-border bg-secondary/30 text-[10px] eyebrow items-center">
          <span>Path</span>
          <span>Window</span>
          <span>Probability</span>
          <span className="text-right">Spark margin</span>
          <span>Net P&amp;L · 1y</span>
          <span className="text-right">Net value</span>
          <span className="text-right">MWh</span>
          <span className="text-right">Fired h</span>
        </div>
        <ul className="max-h-[460px] overflow-y-auto">
          {paths.map((p, i) => {
            const netPos = ((p.net_pl_usd - netMin) / span) * 100;
            const isNeg = p.net_pl_usd < 0;
            // Zero position on the same scale
            const zeroPos = netMin < 0 && netMax > 0 ? ((0 - netMin) / span) * 100 : null;
            return (
              <li key={p.path_id} className={`grid grid-cols-[60px_110px_1fr_110px_1fr_100px_80px_80px] gap-3 px-5 py-2.5 items-center text-[11.5px] ${i < paths.length - 1 ? "border-b border-card-border" : ""} hover:bg-secondary/20 transition-colors`}>
                <span className="font-mono text-[10.5px] text-muted-foreground/70">#{String(p.path_id).padStart(2, "0")}</span>
                <span className="font-mono text-foreground/90">{p.window}</span>
                <div className="flex items-center gap-2 min-w-0">
                  <div className="relative h-1.5 flex-1 rounded-sm bg-secondary/40 overflow-hidden">
                    <div className="absolute inset-y-0 left-0 bg-primary/60" style={{ width: `${(p.probability / maxProb) * 100}%` }} />
                  </div>
                  <span className="font-mono text-[10.5px] text-foreground/80 tabular w-12 text-right">{(p.probability * 100).toFixed(1)}%</span>
                </div>
                <span className="font-mono text-right tabular text-foreground/85">{fmtMoneyM(p.spark_margin_usd, 1)}</span>
                <div className="relative h-5 flex items-center">
                  <div className="absolute inset-y-1 left-0 right-0 rounded-sm bg-secondary/30" />
                  {zeroPos !== null && (
                    <div className="absolute top-0 bottom-0 w-px bg-foreground/40 z-10" style={{ left: `${zeroPos}%` }} />
                  )}
                  <div
                    className={`absolute inset-y-1 rounded-sm ${isNeg ? "bg-[hsl(var(--chart-2)/0.6)]" : "bg-[hsl(var(--chart-1)/0.7)]"}`}
                    style={
                      isNeg
                        ? zeroPos !== null
                          ? { left: `${netPos}%`, width: `${zeroPos - netPos}%` }
                          : { left: 0, width: `${netPos}%` }
                        : zeroPos !== null
                          ? { left: `${zeroPos}%`, width: `${netPos - zeroPos}%` }
                          : { left: 0, width: `${netPos}%` }
                    }
                  />
                </div>
                <span className={`font-mono text-right tabular text-[11px] ${isNeg ? "text-[hsl(var(--chart-2))]" : "text-[hsl(var(--status-real))]"} font-medium`}>{fmtMoneyM(p.net_pl_usd, 1)}</span>
                <span className="font-mono text-right tabular text-foreground/80">{fmtNumber(p.total_mwh / 1000, 0)}k</span>
                <span className="font-mono text-right tabular text-foreground/80">{fmtNumber(p.fired_hours, 0)}</span>
              </li>
            );
          })}
        </ul>
        <footer className="px-5 py-3 border-t border-card-border bg-secondary/20 flex flex-wrap items-center justify-between gap-3 text-[10.5px] font-mono text-muted-foreground">
          <span>Sorted by probability · weights sum to 100% across all {paths.length} paths</span>
          <span className="text-foreground/70">Policy {policy} · gas {gasMult}× · {initState}</span>
        </footer>
      </div>
    </section>
  );
}
