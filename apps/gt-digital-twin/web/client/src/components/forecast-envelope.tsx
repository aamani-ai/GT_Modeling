import { GridCell, Precomputed, fmtMoneyM, fmtNumber } from "@/lib/data";
import { InfoPopover } from "./info-popover";

interface Props {
  data: Precomputed;
  cell: GridCell | null;
  policy: string;
  initState: string;
  gasMult: number;
}

// Marquee forecast envelope — the repo's signature artifact.
// Uses the precomputed forecast_trajectories.png as the centerpiece, surrounded by
// a P10/P50/P90 ribbon strip per metric so the artifact is interpretable at a glance.
export function ForecastEnvelope({ data, cell, policy, initState, gasMult }: Props) {
  if (!cell) return null;
  const q = cell.quantiles;

  return (
    <section className="space-y-6">
      <header className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
        <div className="max-w-2xl">
          <p className="eyebrow mb-2">§02 · Forward forecast envelope</p>
          <h2 className="display text-3xl md:text-4xl tracking-[-0.02em] leading-[1.05] text-foreground">
            The distribution is the story.
          </h2>
          <p className="mt-3 text-[13.5px] text-foreground/75 leading-[1.6]">
            One year forward, six panels — net P&amp;L, spark margin, LTSA owner cost, generation, fired hours.
            Each shows the probability-weighted envelope across 25 SEAS5-conditioned analog windows.
            A single number would lie about how wide this asset's outcome cone actually is.
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Ribbon q={q.net_pl_usd} label="Net P&amp;L" />
          <InfoPopover
            title="Forward forecast envelope"
            status="real_observed"
            source="src/forward.run_forward(basis='RT', aged_start=True). 25 Apr→Mar analog windows scored against SEAS5 ensemble → softmax → probability weights."
            whyV1="Captures multiple gas regimes including 2022 highs. Spread reflects scenario uncertainty with engine seed fixed."
            upgrade="Add per-month engine output (currently engine writes annual aggregates); joint price/gas conditioning; outage-RNG Monte Carlo over each window."
            value={`Policy ${policy} · gas ${gasMult}× · ${initState} · ${data.n_scenarios} paths`}
          />
        </div>
      </header>

      {/* The big artifact */}
      <figure className="card-clean overflow-hidden">
        <div className="border-b border-card-border px-6 py-3 flex items-center justify-between flex-wrap gap-3 bg-secondary/30">
          <p className="text-[12px] font-medium tracking-tight">Cumulative trajectory — six metrics, one year</p>
          <p className="text-[10.5px] font-mono text-muted-foreground tracking-wide">
            Apr 2026 → Mar 2027 · {data.n_scenarios} paths · seed 42
          </p>
        </div>
        <div className="p-4 lg:p-6 bg-background">
          <img
            src={import.meta.env.BASE_URL + "img/forecast_trajectories.png"}
            alt="Forward forecast envelope across six engine metrics"
            className="w-full h-auto block"
            loading="eager"
          />
        </div>
        <figcaption className="border-t border-card-border px-6 py-3 text-[10.5px] text-muted-foreground font-mono leading-relaxed flex flex-wrap items-center justify-between gap-3">
          <span>
            Endpoints = real <span className="text-foreground/85">run_forward</span> output · within-year shape = idealized monthly seasonality for visual continuity
          </span>
          <span className="text-foreground/70">
            P50 Net P&amp;L · {fmtMoneyM(q.net_pl_usd.P50, 1)}
          </span>
        </figcaption>
      </figure>

      {/* Quantile strip — five metrics side by side */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        <MetricStrip label="Net P&amp;L" p10={fmtMoneyM(q.net_pl_usd.P10,1)} p50={fmtMoneyM(q.net_pl_usd.P50,1)} p90={fmtMoneyM(q.net_pl_usd.P90,1)} />
        <MetricStrip label="Spark margin" p10={fmtMoneyM(q.spark_margin_usd.P10,1)} p50={fmtMoneyM(q.spark_margin_usd.P50,1)} p90={fmtMoneyM(q.spark_margin_usd.P90,1)} />
        <MetricStrip label="LTSA owner cost" p10={fmtMoneyM(q.ltsa_owner_usd.P10,1)} p50={fmtMoneyM(q.ltsa_owner_usd.P50,1)} p90={fmtMoneyM(q.ltsa_owner_usd.P90,1)} />
        <MetricStrip label="Generation" p10={`${fmtNumber(q.total_mwh.P10/1000,0)}k`} p50={`${fmtNumber(q.total_mwh.P50/1000,0)}k`} p90={`${fmtNumber(q.total_mwh.P90/1000,0)}k`} unit="MWh" />
        <MetricStrip label="Fired hours" p10={fmtNumber(q.fired_hours.P10,0)} p50={fmtNumber(q.fired_hours.P50,0)} p90={fmtNumber(q.fired_hours.P90,0)} unit="h" />
      </div>
    </section>
  );
}

function Ribbon({ q, label }: { q: { P10: number; P50: number; P90: number }; label: string }) {
  return (
    <div className="hidden lg:flex items-stretch gap-0 border border-card-border rounded-md overflow-hidden bg-card">
      <Cell label={`${label} P10`} value={fmtMoneyM(q.P10, 1)} dim />
      <Cell label="P50" value={fmtMoneyM(q.P50, 1)} primary />
      <Cell label="P90" value={fmtMoneyM(q.P90, 1)} dim />
    </div>
  );
}

function Cell({ label, value, primary, dim }: { label: string; value: string; primary?: boolean; dim?: boolean }) {
  return (
    <div className={`px-3.5 py-2 ${primary ? "bg-primary/10" : ""} ${dim ? "opacity-80" : ""} border-r border-card-border last:border-r-0 text-center`}>
      <p className="eyebrow text-[9px] mb-0.5">{label}</p>
      <p className={`font-mono text-[11.5px] tracking-tight ${primary ? "text-primary font-medium" : "text-foreground/80"}`} dangerouslySetInnerHTML={{ __html: value }} />
    </div>
  );
}

function MetricStrip({ label, p10, p50, p90, unit }: { label: string; p10: string; p50: string; p90: string; unit?: string }) {
  return (
    <div className="card-clean p-4">
      <p className="eyebrow mb-2">{label}{unit ? ` · ${unit}` : ""}</p>
      <p className="tabular text-lg font-medium tracking-[-0.01em] text-foreground">{p50}</p>
      <p className="font-mono text-[10.5px] text-muted-foreground mt-1.5">
        <span className="text-foreground/60">P10</span> {p10}
        <span className="mx-1.5 text-muted-foreground/40">·</span>
        <span className="text-foreground/60">P90</span> {p90}
      </p>
    </div>
  );
}
