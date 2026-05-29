import { GridCell, Precomputed, fmtMoneyM, fmtNumber } from "@/lib/data";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";

interface Props {
  cell: GridCell | null;
  data: Precomputed;
  policy: string;
  initState: string;
  gasMult: number;
}

export function Headline({ cell, data, policy, initState, gasMult }: Props) {
  if (!cell) return <div className="card-clean p-6 text-sm text-muted-foreground">Scenario not precomputed.</div>;
  const q = cell.quantiles.net_pl_usd;
  const mwh = cell.quantiles.total_mwh;
  const spark = cell.quantiles.spark_margin_usd;
  const ltsa = cell.quantiles.ltsa_owner_usd;
  const aged = data.aged_state_summary[policy];

  return (
    <section aria-label="Headline" className="space-y-5">
      <div className="flex items-baseline justify-between gap-4 flex-wrap">
        <div>
          <p className="eyebrow mb-1.5">Net P&L · 1-yr forward · energy-only</p>
          <div className="flex items-baseline gap-3 flex-wrap">
            <span className="num-xl text-foreground tabular">{fmtMoneyM(q.P50, 2)}</span>
            <span className="text-xs text-muted-foreground tracking-wide">P50</span>
            <span className="text-[11px] text-muted-foreground/70 ml-2 font-mono">
              P10 <span className="text-foreground/80">{fmtMoneyM(q.P10, 1)}</span>
              <span className="mx-2">·</span>
              P90 <span className="text-foreground/80">{fmtMoneyM(q.P90, 1)}</span>
            </span>
          </div>
        </div>
        <div className="text-right text-[11px] text-muted-foreground font-mono leading-tight">
          <p>Policy <span className="text-foreground/80">{policy}</span> · gas {gasMult}× · {initState}</p>
          {initState === "aged" && aged && (
            <p className="mt-1">Aged EOH <span className="text-foreground/80">{fmtNumber(aged.eoh)}</span> · rotor <span className="text-foreground/80">{aged.rotor_life.toFixed(3)}</span> · insp_done {aged.insp_done}</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-4 pt-4 border-t border-border">
        <Kpi label="Spark margin P50" value={fmtMoneyM(spark.P50, 1)} sub={`P10 ${fmtMoneyM(spark.P10, 1)} · P90 ${fmtMoneyM(spark.P90, 1)}`} positive={spark.P50 >= 0} />
        <Kpi label="LTSA owner P50" value={fmtMoneyM(ltsa.P50, 1)} sub={`P10 ${fmtMoneyM(ltsa.P10, 1)} · P90 ${fmtMoneyM(ltsa.P90, 1)}`} positive={false} />
        <Kpi label="Generation P50" value={`${fmtNumber(mwh.P50 / 1000, 0)}k MWh`} sub={`P10 ${fmtNumber(mwh.P10 / 1000, 0)}k · P90 ${fmtNumber(mwh.P90 / 1000, 0)}k`} />
        <Kpi label="Fired hours P50" value={fmtNumber(cell.quantiles.fired_hours.P50, 0)} sub={`P10 ${fmtNumber(cell.quantiles.fired_hours.P10, 0)} · P90 ${fmtNumber(cell.quantiles.fired_hours.P90, 0)}`} />
      </div>
    </section>
  );
}

function Kpi({ label, value, sub, positive }: { label: string; value: string; sub: string; positive?: boolean }) {
  return (
    <div>
      <p className="eyebrow mb-1.5">{label}</p>
      <p className={`num-md tabular ${positive === undefined ? "text-foreground" : positive ? "text-[hsl(var(--status-real))]" : "text-foreground"}`}>{value}</p>
      <p className="text-[10.5px] text-muted-foreground/80 font-mono mt-1">{sub}</p>
    </div>
  );
}
