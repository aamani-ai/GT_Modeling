import { GridCell, Precomputed, fmtMoneyM, keyFor } from "@/lib/data";
import { Switch } from "@/components/ui/switch";
import { InfoPopover } from "./info-popover";
import { TermInfo } from "./term-info";

interface Props {
  cell: GridCell | null;
  data: Precomputed;
  policy: string;
  gasMult: number;
  initState: string;
  comparePolicies: boolean;
  setComparePolicies: (v: boolean) => void;
}

// Forward Net P&L distribution rendered as a layered dotplot + P10/P50/P90 markers.
// When comparePolicies is on (aged), overlay A/B/C strips.
export function DistributionChart({ cell, data, policy, gasMult, initState, comparePolicies, setComparePolicies }: Props) {
  if (!cell) return null;

  const cells = comparePolicies
    ? data.modes.map((m) => ({ mode: m, cell: data.grid[keyFor(m, gasMult, initState)] }))
    : [{ mode: policy, cell }];

  // X domain across all visible cells
  const allValues = cells.flatMap((c) => (c.cell?.per_path ?? []).map((p) => p.net_pl_usd));
  const xMin = Math.floor(Math.min(...allValues) / 1e6) * 1e6;
  const xMax = Math.ceil(Math.max(...allValues) / 1e6) * 1e6;

  const W = 460;
  const rowH = comparePolicies ? 56 : 80;
  const H = 56 + rowH * cells.length;
  const Mleft = 18;
  const Mright = 16;
  const Mtop = 32;
  const innerW = W - Mleft - Mright;

  const xScale = (v: number) => Mleft + (v - xMin) / (xMax - xMin) * innerW;

  // ticks
  const tickStep = Math.ceil((xMax - xMin) / 4 / 5e6) * 5e6;
  const ticks: number[] = [];
  for (let t = Math.ceil(xMin / tickStep) * tickStep; t <= xMax; t += tickStep) ticks.push(t);

  return (
    <section className="card-clean p-5 lg:p-6 h-full flex flex-col">
      <header className="flex items-start justify-between gap-4 mb-1">
        <div>
          <h2 className="text-sm font-medium tracking-tight inline-flex items-center gap-1.5">
            <span>Forward Net P&L distribution</span>
            <TermInfo termKey="net_pl" side="top" />
          </h2>
          <p className="text-[11.5px] text-muted-foreground mt-0.5 leading-relaxed inline-flex items-center gap-1 flex-wrap">
            <span>25</span>
            <span className="inline-flex items-center gap-1">
              <span>SEAS5</span>
              <TermInfo termKey="seas5" size="xs" side="top" />
            </span>
            <span>-conditioned</span>
            <span className="inline-flex items-center gap-1">
              <span>analog windows</span>
              <TermInfo termKey="analog_scenarios" size="xs" side="top" />
            </span>
            <span>· probability-weighted</span>
            <span className="inline-flex items-center gap-1">
              <span>P10/P50/P90.</span>
              <TermInfo termKey="p_quantiles" size="xs" side="top" />
            </span>
          </p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          {/* Overlay toggle lives in the card header — it controls THIS chart,
              so it belongs anchored to it (not floating outside the card). */}
          <label htmlFor="overlay-abc" className="text-[11px] text-muted-foreground select-none cursor-pointer leading-tight whitespace-nowrap">
            Overlay A·B·C
          </label>
          <Switch checked={comparePolicies} onCheckedChange={setComparePolicies} data-testid="switch-compare" id="overlay-abc" />
          <InfoPopover
            title="Forward distribution"
            status="real_observed"
            source="src/forward.run_forward(basis='RT', aged_start=True). 25 Apr→Mar analog windows 1999–2026 scored against the SEAS5 ensemble, softmaxed → probability weights."
            whyV1="Captures multiple gas regimes including high-gas years (e.g. 2022). The spread is the policy/state-driven uncertainty, not outage RNG noise (seed fixed)."
            upgrade="Joint price/gas/regime conditioning; winter (Nov–Mar) climate-index conditioning; outage-RNG Monte Carlo over each window."
          />
        </div>
      </header>

      <div className="flex-1 mt-3 -mx-2">
        <svg viewBox={`0 0 ${W} ${H}`} width="100%" preserveAspectRatio="xMidYMid meet" className="block">
          {/* x axis */}
          {ticks.map((t, i) => (
            <g key={i}>
              <line x1={xScale(t)} y1={Mtop - 4} x2={xScale(t)} y2={H - 24} stroke="hsl(var(--border))" strokeWidth="0.5" strokeDasharray="2 4" opacity="0.5" />
              <text x={xScale(t)} y={H - 8} textAnchor="middle" className="fill-muted-foreground" style={{ fontFamily: "var(--font-mono)", fontSize: 9.5 }}>
                {fmtMoneyM(t, 0)}
              </text>
            </g>
          ))}

          {cells.map((c, ri) => {
            if (!c.cell) return null;
            const yTop = Mtop + ri * rowH;
            const yCenter = yTop + rowH / 2 - 6;
            const q = c.cell.quantiles.net_pl_usd;
            const fill = c.mode === policy ? "hsl(var(--primary))" : "hsl(var(--muted-foreground))";
            const accentOp = c.mode === policy ? 0.95 : 0.55;

            return (
              <g key={ri}>
                {/* row label */}
                <text x={Mleft} y={yTop - 4} className="fill-foreground" style={{ fontSize: 10.5, fontWeight: 500 }}>
                  Policy {c.mode}
                </text>
                <text x={W - Mright} y={yTop - 4} textAnchor="end" className="fill-muted-foreground" style={{ fontFamily: "var(--font-mono)", fontSize: 9.5 }}>
                  P50 {fmtMoneyM(q.P50, 1)}
                </text>

                {/* P10–P90 strip */}
                <line x1={xScale(q.P10)} y1={yCenter} x2={xScale(q.P90)} y2={yCenter} stroke={fill} strokeWidth="2" opacity={accentOp * 0.4} />
                {/* dots */}
                {c.cell.per_path.map((p, i) => (
                  <circle key={i} cx={xScale(p.net_pl_usd)} cy={yCenter + (i % 3 - 1) * 4} r={Math.max(1.5, Math.sqrt(p.probability * 800))} fill={fill} opacity={accentOp * 0.7} />
                ))}
                {/* P10 / P50 / P90 markers */}
                {([["P10", q.P10], ["P50", q.P50], ["P90", q.P90]] as const).map(([lbl, v], i) => (
                  <g key={i}>
                    <line x1={xScale(v)} y1={yCenter - 10} x2={xScale(v)} y2={yCenter + 10} stroke={fill} strokeWidth={lbl === "P50" ? 2 : 1} opacity={accentOp} />
                    {lbl === "P50" && (
                      <text x={xScale(v)} y={yCenter + 22} textAnchor="middle" className="fill-foreground" style={{ fontFamily: "var(--font-mono)", fontSize: 9.5, fontWeight: 500 }}>
                        {lbl}
                      </text>
                    )}
                  </g>
                ))}
              </g>
            );
          })}
        </svg>
      </div>

      <footer className="mt-3 pt-3 border-t border-card-border space-y-2.5">
        <p className="text-[10.5px] text-muted-foreground font-mono leading-relaxed">
          Dots are individual analog windows sized by probability. RT basis · 25 paths · seed 42.
        </p>
        <p className="text-[11px] leading-[1.55] text-muted-foreground">
          <span className="font-medium text-foreground/85">Why A·B·C P50s overlap.</span>{" "}
          A 1-yr horizon doesn't give the LTSA streams (fixed fee · EOH reserve · inspection events)
          room to compound differently — A/B/C's wear-hurdle differential only shifts the dispatch
          decision when EOH headroom approaches the next inspection threshold, and headroom stays
          well above that in a single year. Policy divergence emerges over multi-year horizons
          where inspection timing actually slides. Custom hurdle curves + longer horizons are on
          the workbench roadmap (next to A·B·C).
        </p>
      </footer>
    </section>
  );
}
