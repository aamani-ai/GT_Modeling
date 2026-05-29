// v1.3 — Interactive 6-panel forecast chart, structurally mirroring the
// canonical forward run output (notebook 06 §5). Every series in this chart
// is computed from REAL run_forward(..., return_paths=True) per-path daily
// data (or the SEAS5 ensemble JSON for the temperature panel). No
// illustrative shapes.

import { useMemo } from "react";
import {
  ComposedChart,
  Area,
  Line,
  ReferenceLine,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  Envelope,
  MonthlyForecastGridCell,
  MonthlyForecastPanel,
  Precomputed,
  GridCell,
  TemperatureDailyEnsemble,
  fmtMoneyM,
  fmtNumber,
} from "@/lib/data";
import { InfoPopover } from "./info-popover";
import { TermInfo, TERMS } from "./term-info";
import { DossierCell } from "./pnl-decomposition";

interface Props {
  data: Precomputed;
  monthly: MonthlyForecastPanel;
  monthlyCell: MonthlyForecastGridCell;
  cell: GridCell;
  policy: string;
  initState: string;
  gasMult: number;
}

const TEAL = "hsl(var(--chart-1))";
const TEAL_FAINT = "hsl(var(--chart-1) / 0.18)";
const TEAL_MID = "hsl(var(--chart-1) / 0.32)";
const TERRA = "hsl(var(--chart-2))";
const TERRA_FAINT = "hsl(var(--chart-2) / 0.18)";
const TERRA_MID = "hsl(var(--chart-2) / 0.32)";
const GOLD = "hsl(var(--chart-4))";
const GOLD_FAINT = "hsl(var(--chart-4) / 0.18)";
const GOLD_MID = "hsl(var(--chart-4) / 0.32)";

const AXIS_TICK = { fill: "hsl(var(--muted-foreground))", fontSize: 10, fontFamily: "var(--font-mono)" };

// --- helpers -----------------------------------------------------------------

function envelopeRows(env: Envelope, labels: string[]) {
  return labels.map((label, i) => ({
    month: label,
    p10: env.P10[i],
    p50: env.P50[i],
    p90: env.P90[i],
    band_lo: env.P10[i],
    band_span: env.P90[i] - env.P10[i],
  }));
}

function temperatureRows(ens: TemperatureDailyEnsemble) {
  // Use month-day labels so the x-axis is interpretable without crowding.
  return ens.dates.map((iso, i) => {
    const d = new Date(iso);
    return {
      day: iso.slice(0, 10),
      tick: `${d.toLocaleString("en-US", { month: "short" })} ${d.getDate()}`,
      p10: ens.P10[i],
      p50: ens.P50[i],
      p90: ens.P90[i],
      band_lo: ens.P10[i],
      band_span: ens.P90[i] - ens.P10[i],
    };
  });
}

function fmtUsdShort(v: number) {
  if (Math.abs(v) >= 1e6) return `${v < 0 ? "−" : ""}$${(Math.abs(v) / 1e6).toFixed(1)}M`;
  if (Math.abs(v) >= 1e3) return `${v < 0 ? "−" : ""}$${(Math.abs(v) / 1e3).toFixed(0)}k`;
  return `${v < 0 ? "−" : ""}$${Math.abs(v).toFixed(0)}`;
}

function fmtMwh(v: number) {
  if (Math.abs(v) >= 1000) return `${(v / 1000).toFixed(0)}k`;
  return `${v.toFixed(0)}`;
}

// --- panels ------------------------------------------------------------------

function Panel({
  title,
  unit,
  caption,
  termKeys,
  children,
}: {
  title: string;
  unit: string;
  caption?: string;
  termKeys?: (keyof typeof TERMS)[];
  children: React.ReactNode;
}) {
  return (
    <div className="card-clean p-4 flex flex-col h-[300px]" data-testid={`panel-${title.toLowerCase().replace(/\s+/g, "-")}`}>
      <div className="flex items-start justify-between mb-2 gap-2">
        <div className="min-w-0">
          <p className="text-[12px] font-medium text-foreground leading-tight inline-flex items-center gap-1">
            <span>{title}</span>
            {termKeys?.map((k) => (
              <TermInfo key={k as string} termKey={k} side="top" />
            ))}
          </p>
          <p className="text-[10px] font-mono text-muted-foreground mt-0.5 tracking-tight">{unit}</p>
        </div>
        <span
          className="text-[9px] font-mono uppercase tracking-[0.08em] px-1.5 py-0.5 rounded-sm whitespace-nowrap bg-[hsl(var(--status-real)/0.12)] text-[hsl(var(--status-real))]"
        >
          real
        </span>
      </div>
      <div className="flex-1 min-h-0">{children}</div>
      {caption && <p className="text-[10px] text-muted-foreground mt-1.5 leading-snug">{caption}</p>}
    </div>
  );
}

function EnvelopeChart({
  rows,
  xKey = "month",
  yFormat,
  yDomain,
  color = TEAL,
  bandFaint = TEAL_FAINT,
  bandMid = TEAL_MID,
  zeroLine = false,
  tickInterval = 1,
}: {
  rows: any[];
  xKey?: string;
  yFormat: (v: number) => string;
  yDomain?: [number | "auto", number | "auto"];
  color?: string;
  bandFaint?: string;
  bandMid?: string;
  zeroLine?: boolean;
  tickInterval?: number | "preserveStartEnd";
}) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={rows} margin={{ top: 6, right: 8, bottom: 4, left: 8 }}>
        <CartesianGrid stroke="hsl(var(--border) / 0.5)" vertical={false} />
        <XAxis dataKey={xKey} tick={AXIS_TICK} axisLine={{ stroke: "hsl(var(--border))" }} tickLine={false} interval={tickInterval as any} />
        <YAxis
          tick={AXIS_TICK}
          axisLine={false}
          tickLine={false}
          width={48}
          domain={yDomain ?? ["auto", "auto"]}
          tickFormatter={yFormat}
        />
        {zeroLine && <ReferenceLine y={0} stroke="hsl(var(--border))" strokeWidth={1} />}
        <Area type="monotone" dataKey="band_lo" stackId="band" stroke="none" fill="transparent" isAnimationActive={false} />
        <Area type="monotone" dataKey="band_span" stackId="band" stroke="none" fill={bandFaint} isAnimationActive={false} />
        <Line type="monotone" dataKey="p50" stroke={color} strokeWidth={2} dot={false} isAnimationActive={false} />
        <Line type="monotone" dataKey="p10" stroke={color} strokeWidth={1} strokeDasharray="3 3" strokeOpacity={0.55} dot={false} isAnimationActive={false} />
        <Line type="monotone" dataKey="p90" stroke={color} strokeWidth={1} strokeDasharray="3 3" strokeOpacity={0.55} dot={false} isAnimationActive={false} />
        <Tooltip
          cursor={{ stroke: "hsl(var(--border))", strokeWidth: 1 }}
          contentStyle={{
            background: "hsl(var(--popover))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "6px",
            fontSize: "11px",
            fontFamily: "var(--font-mono)",
          }}
          labelStyle={{ color: "hsl(var(--foreground))", fontWeight: 500 }}
          formatter={(value: number, name: string) => {
            const label = name === "p50" ? "P50" : name === "p10" ? "P10" : name === "p90" ? "P90" : name;
            if (name === "band_lo" || name === "band_span") return [null, null] as any;
            return [yFormat(value), label];
          }}
        />
        {/* silence unused band mid */}
        <Area type="monotone" dataKey="_unused" stroke="none" fill={bandMid} hide />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

function CdfChart({
  points,
  median,
}: {
  points: { x: number; F: number; window: string }[];
  median: number;
}) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={points} margin={{ top: 6, right: 8, bottom: 4, left: 8 }}>
        <CartesianGrid stroke="hsl(var(--border) / 0.5)" vertical={false} />
        <XAxis
          dataKey="x"
          type="number"
          domain={["dataMin", "dataMax"]}
          tick={AXIS_TICK}
          axisLine={{ stroke: "hsl(var(--border))" }}
          tickLine={false}
          tickFormatter={fmtUsdShort}
        />
        <YAxis
          dataKey="F"
          type="number"
          domain={[0, 1]}
          tick={AXIS_TICK}
          axisLine={false}
          tickLine={false}
          width={36}
          tickFormatter={(v) => `${Math.round(v * 100)}%`}
        />
        <ReferenceLine x={0} stroke="hsl(var(--border))" strokeWidth={1} />
        <ReferenceLine
          x={median}
          stroke={TEAL}
          strokeDasharray="3 3"
          strokeWidth={1}
          label={{ value: "P50", position: "insideTopRight", fill: TEAL, fontSize: 9, fontFamily: "var(--font-mono)" }}
        />
        <Line
          type="stepAfter"
          dataKey="F"
          stroke={TEAL}
          strokeWidth={2}
          dot={{ r: 2.5, stroke: TEAL, strokeWidth: 1, fill: "hsl(var(--background))" }}
          isAnimationActive={false}
        />
        <Tooltip
          cursor={{ stroke: "hsl(var(--border))", strokeWidth: 1 }}
          contentStyle={{
            background: "hsl(var(--popover))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "6px",
            fontSize: "11px",
            fontFamily: "var(--font-mono)",
          }}
          formatter={(value: number, name: string, item: any) => {
            if (name === "F") {
              const w = item?.payload?.window;
              return [`${(value * 100).toFixed(0)}% · ${w}`, "cumul. prob"];
            }
            return [value, name];
          }}
          labelFormatter={(label: number) => `Net P&L ${fmtUsdShort(label)}`}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

// --- main --------------------------------------------------------------------

export function ForecastSixPanel({ data, monthly, monthlyCell, cell, policy, initState, gasMult }: Props) {
  const monthsOnly = monthly.month_labels;     // length 12 (Apr..Mar)

  const tempRows = useMemo(() => temperatureRows(monthly.temperature_f_daily), [monthly.temperature_f_daily]);
  const lmpRows = useMemo(
    () => envelopeRows(monthlyCell.lmp_usd_per_mwh_monthly_mean, monthsOnly),
    [monthlyCell.lmp_usd_per_mwh_monthly_mean, monthsOnly]
  );
  const gasRows = useMemo(
    () => envelopeRows(monthlyCell.henry_hub_usd_per_mmbtu_monthly_mean, monthsOnly),
    [monthlyCell.henry_hub_usd_per_mmbtu_monthly_mean, monthsOnly]
  );
  const genRows = useMemo(
    () => envelopeRows(monthlyCell.generation_mwh_monthly_sum, monthsOnly),
    [monthlyCell.generation_mwh_monthly_sum, monthsOnly]
  );
  const marginRows = useMemo(
    () => envelopeRows(monthlyCell.gross_margin_usd_monthly_sum, monthsOnly),
    [monthlyCell.gross_margin_usd_monthly_sum, monthsOnly]
  );
  const cdfPoints = monthlyCell.net_pl_cdf;
  const netP50 = cell.quantiles.net_pl_usd.P50;

  // Sparse tick interval for daily SEAS5 panel so labels don't crowd.
  const tempTickInterval = Math.max(1, Math.floor(tempRows.length / 8));

  return (
    <section className="space-y-6">
      <header className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="max-w-2xl">
          <p className="eyebrow mb-2">§02 · Forward forecast (interactive)</p>
          <h2 className="display text-3xl md:text-4xl tracking-[-0.015em] leading-[1.05] text-foreground">
            Six panels, one year forward.
          </h2>
          <p className="mt-3 text-[13.5px] text-foreground/75 leading-[1.6]">
            SEAS5 daily temperature ensemble → forward LMP → fuel cost → generation → gross margin → distribution of net P&L.
            Each metric panel shows the P10–P90 envelope across {data.n_scenarios} SEAS5-conditioned analog windows,
            aggregated from real per-path daily series — the same logic as the canonical six-panel chart in
            notebook 06 §5.
          </p>
        </div>
        {/* Right-side: data-sources tally — what powers the six panels. */}
        <div className="flex items-start gap-4 shrink-0">
          <dl className="grid grid-cols-2 gap-x-5 gap-y-2 text-right">
            <DossierCell label="Temperature" value={`SEAS5 · ${monthly.temperature_f_daily.n_members}-member`} />
            <DossierCell label="Power" value="NYISO RT LBMP" />
            <DossierCell label="Gas" value="Henry Hub spot" />
            <DossierCell label="Paths" value={`${data.n_scenarios} analog windows`} />
          </dl>
          <InfoPopover
            title="Forward forecast · six-panel interactive"
            status="real_observed"
            source={`src/forward.run_forward(basis='RT', return_paths=True). ${data.n_scenarios} SEAS5-conditioned analog windows; per-path daily LMP / gas / generation / margin aggregated to monthly (mean for LMP/gas, sum for MWh/margin); across-path P10/P50/P90 computed via forward.run.weighted_quantile with SEAS5 softmax weights. Temperature panel = daily P10/P50/P90 across the ${monthly.temperature_f_daily.n_members}-member SEAS5 ensemble in ${monthly.temperature_f_daily.source_file}.`}
            whyV1="Mirrors notebooks/06_forward_scenarios.py §5 verbatim. No illustrative seasonality, no climatology, no forward-curve representative shape — every series is real model output for this run."
            upgrade="Add basis-differential overlay (Iroquois/TGP) for delivered gas; extend horizon beyond Apr→Mar."
            value={`Policy ${policy} · gas ${gasMult}× · ${initState} · ${data.n_scenarios} paths`}
          />
        </div>
      </header>

      <figure className="card-clean overflow-hidden">
        <div className="border-b border-card-border px-6 py-3 flex items-center justify-between flex-wrap gap-3 bg-secondary/30">
          <p className="text-[12px] font-medium tracking-tight">Real forward envelope · six panels · {data.n_scenarios} paths</p>
          <p className="text-[10.5px] font-mono text-muted-foreground tracking-wide">
            Apr 2026 → Mar 2027 · seed {monthly.seed} · {monthly.basis}
          </p>
        </div>

        <div className="p-4 lg:p-6 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <Panel
            title="Ambient temperature · SEAS5"
            unit="°F · daily"
            termKeys={["seas5"]}
            caption={`${monthly.temperature_f_daily.n_members}-member SEAS5 ensemble · daily P10/P50/P90`}
          >
            <EnvelopeChart
              rows={tempRows}
              xKey="tick"
              yFormat={(v) => `${v.toFixed(0)}°`}
              color={TERRA}
              bandFaint={TERRA_FAINT}
              bandMid={TERRA_MID}
              tickInterval={tempTickInterval}
            />
          </Panel>

          <Panel
            title="Forward LMP · monthly mean"
            unit="$/MWh"
            termKeys={["lmp"]}
            caption="Monthly mean of per-path daily LMP · across-path P10/P50/P90"
          >
            <EnvelopeChart rows={lmpRows} yFormat={(v) => `$${v.toFixed(0)}`} color={GOLD} bandFaint={GOLD_FAINT} bandMid={GOLD_MID} />
          </Panel>

          <Panel
            title="Henry Hub natural gas · monthly mean"
            unit="$/MMBtu"
            termKeys={["henry_hub"]}
            caption="Monthly mean of per-path daily Henry Hub · across-path P10/P50/P90"
          >
            <EnvelopeChart rows={gasRows} yFormat={(v) => `$${v.toFixed(1)}`} color={TERRA} bandFaint={TERRA_FAINT} bandMid={TERRA_MID} />
          </Panel>

          <Panel
            title="Generation · monthly sum"
            unit="MWh"
            termKeys={["generation_mwh"]}
            caption="Monthly sum of engine mwh_degraded · across-path P10/P50/P90"
          >
            <EnvelopeChart rows={genRows} yFormat={fmtMwh} />
          </Panel>

          <Panel
            title="Gross margin · monthly sum"
            unit="USD"
            termKeys={["gross_margin"]}
            caption="Monthly sum of engine margin_degraded · across-path P10/P50/P90"
          >
            <EnvelopeChart rows={marginRows} yFormat={fmtUsdShort} zeroLine />
          </Panel>

          <Panel
            title="Net P&L distribution · annual"
            unit="CDF of annual USD"
            termKeys={["cdf"]}
            caption="Real per-path annual Net P&L · cumulative SEAS5 probability"
          >
            <CdfChart points={cdfPoints} median={netP50} />
          </Panel>
        </div>

        <figcaption className="border-t border-card-border px-6 py-3 text-[10.5px] text-muted-foreground font-mono leading-relaxed flex flex-wrap items-center justify-between gap-3">
          <span>
            All six panels are <span className="text-[hsl(var(--status-real))]">real</span> — derived from
            run_forward(return_paths=True) per-path daily series and the SEAS5 ensemble JSON. Mirrors notebook 06 §5.
          </span>
          <span className="text-foreground/70">
            P50 Net P&amp;L · {fmtMoneyM(netP50, 1)} · n={data.n_scenarios} paths
          </span>
        </figcaption>
      </figure>

      {/* Quantile strip — five metrics side by side */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        <MetricStrip label="Net P&L" termKey="net_pl" p10={fmtMoneyM(cell.quantiles.net_pl_usd.P10, 1)} p50={fmtMoneyM(cell.quantiles.net_pl_usd.P50, 1)} p90={fmtMoneyM(cell.quantiles.net_pl_usd.P90, 1)} />
        <MetricStrip label="Spark margin" termKey="spark_margin" p10={fmtMoneyM(cell.quantiles.spark_margin_usd.P10, 1)} p50={fmtMoneyM(cell.quantiles.spark_margin_usd.P50, 1)} p90={fmtMoneyM(cell.quantiles.spark_margin_usd.P90, 1)} />
        <MetricStrip label="LTSA owner cost" termKey="ltsa_owner" p10={fmtMoneyM(cell.quantiles.ltsa_owner_usd.P10, 1)} p50={fmtMoneyM(cell.quantiles.ltsa_owner_usd.P50, 1)} p90={fmtMoneyM(cell.quantiles.ltsa_owner_usd.P90, 1)} />
        <MetricStrip label="Generation" termKey="generation_mwh" p10={`${fmtNumber(cell.quantiles.total_mwh.P10 / 1000, 0)}k`} p50={`${fmtNumber(cell.quantiles.total_mwh.P50 / 1000, 0)}k`} p90={`${fmtNumber(cell.quantiles.total_mwh.P90 / 1000, 0)}k`} unit="MWh" />
        <MetricStrip label="Fired hours" termKey="fired_hours" p10={fmtNumber(cell.quantiles.fired_hours.P10, 0)} p50={fmtNumber(cell.quantiles.fired_hours.P50, 0)} p90={fmtNumber(cell.quantiles.fired_hours.P90, 0)} unit="h" />
      </div>
    </section>
  );
}

function MetricStrip({ label, p10, p50, p90, unit, termKey }: { label: string; p10: string; p50: string; p90: string; unit?: string; termKey?: keyof typeof TERMS }) {
  return (
    <div className="card-clean p-4">
      <p className="eyebrow mb-2 inline-flex items-center gap-1">
        <span>{label}{unit ? ` · ${unit}` : ""}</span>
        {termKey && <TermInfo termKey={termKey} side="top" />}
      </p>
      <p className="num-md text-foreground">{p50}</p>
      <p className="font-mono text-[10.5px] text-muted-foreground mt-1.5">
        <span className="text-foreground/60">P10</span> {p10}
        <span className="mx-1.5 text-muted-foreground/40">·</span>
        <span className="text-foreground/60">P90</span> {p90}
      </p>
    </div>
  );
}
