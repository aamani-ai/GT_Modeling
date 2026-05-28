import { SensitivityRank, fmtMoneyM } from "@/lib/data";
import { StatusBadge } from "./status-badge";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";

// Premium ranked sensitivity cards — replaces a tornado chart with composed cards.
export function WhatMattersMost({ ranks }: { ranks: SensitivityRank[] }) {
  const maxAbs = Math.max(...ranks.map((r) => r.abs_max));

  return (
    <section>
      <header className="mb-6 max-w-2xl">
        <p className="eyebrow mb-2">§08 · What matters most</p>
        <h2 className="display text-3xl md:text-4xl tracking-[-0.02em] leading-[1.05]">
          Where the headline actually moves.
        </h2>
        <p className="mt-3 text-[13.5px] text-foreground/75 leading-[1.6]">
          Ranked by how much each v1 knob moves the P50 Net P&amp;L from the baseline
          (Mode A · gas 1.0× · aged). The bar is the swing range, signed.
        </p>
      </header>

      <ol className="space-y-3">
        {ranks.map((r, i) => (
          <li key={i}>
            <article className="card-clean p-5 lg:p-6 hover:border-primary/30 transition-colors">
              <div className="grid grid-cols-12 gap-5 items-start">
                <div className="col-span-12 lg:col-span-5">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="font-mono text-[10.5px] text-primary tracking-wider">{String(i + 1).padStart(2, "0")}</span>
                    <h3 className="text-[14px] font-medium tracking-tight">{r.knob}</h3>
                  </div>
                  <p className="text-[11.5px] text-muted-foreground leading-[1.6]">{r.rationale}</p>
                </div>

                <div className="col-span-12 lg:col-span-5">
                  <SwingBar low={r.delta_p50_low} high={r.delta_p50_high} max={maxAbs} />
                  <p className="mt-2 text-[10px] font-mono text-muted-foreground/70 leading-relaxed">{r.source}</p>
                </div>

                <div className="col-span-12 lg:col-span-2 flex lg:justify-end">
                  <StatusBadge status={r.status} size="xs" />
                </div>
              </div>
            </article>
          </li>
        ))}
      </ol>
    </section>
  );
}

function SwingBar({ low, high, max }: { low: number; high: number; max: number }) {
  const downside = Math.min(low, high, 0);
  const upside = Math.max(low, high, 0);
  const span = Math.max(max, 1e-9) * 1.05;
  const center = 50;
  const leftPct = Math.abs(downside) / span * 50;
  const rightPct = upside / span * 50;

  return (
    <div className="space-y-1.5">
      <div className="relative h-7 rounded-sm bg-secondary/40 overflow-hidden border border-card-border">
        <div className="absolute top-0 bottom-0 w-px bg-foreground/40 z-10" style={{ left: `${center}%` }} />
        {downside < 0 && (
          <div
            className="absolute top-0 bottom-0 bg-[hsl(var(--chart-2)/0.65)]"
            style={{ right: `${center}%`, width: `${leftPct}%` }}
          />
        )}
        {upside > 0 && (
          <div
            className="absolute top-0 bottom-0 bg-[hsl(var(--chart-1)/0.75)]"
            style={{ left: `${center}%`, width: `${rightPct}%` }}
          />
        )}
        {downside < 0 && (
          <span className="absolute top-1/2 -translate-y-1/2 text-[10px] font-mono text-foreground/95 font-medium px-1" style={{ right: `calc(${center}% + 4px)` }}>
            {fmtMoneyM(downside, 1)}
          </span>
        )}
        {upside > 0 && (
          <span className="absolute top-1/2 -translate-y-1/2 text-[10px] font-mono text-foreground/95 font-medium px-1" style={{ left: `calc(${center}% + 4px)` }}>
            +{fmtMoneyM(upside, 1)}
          </span>
        )}
        {downside === 0 && upside === 0 && (
          <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-[10px] font-mono text-muted-foreground">no swing</span>
        )}
      </div>
      <div className="flex justify-between text-[9.5px] text-muted-foreground/70 font-mono">
        <span className="inline-flex items-center gap-1"><ArrowDownRight className="w-2.5 h-2.5" /> worse than baseline</span>
        <span className="inline-flex items-center gap-1">better than baseline <ArrowUpRight className="w-2.5 h-2.5" /></span>
      </div>
    </div>
  );
}
