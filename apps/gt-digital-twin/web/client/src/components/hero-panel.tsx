import { useContext } from "react";
import { Precomputed, GridCell, Reference, fmtMoneyM, fmtNumber } from "@/lib/data";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { TermInfo } from "./term-info";
import { ReferencesContext, renderCitations } from "./info-popover";

interface Props {
  data: Precomputed;
  cell: GridCell | null;
  policy: string;
  initState: string;
  gasMult: number;
}

// Composed two-column hero. Left = product positioning. Right = live KPI card.
// Replaces the rejected v1 hero that had a large empty right gap and offered
// no forecast anchor up top.
export function HeroPanel({ data, cell, policy, initState, gasMult }: Props) {
  const aged = data.aged_state_summary[policy];
  const computed = new Date(data.generated_at);

  return (
    <section className="grid grid-cols-12 gap-6 lg:gap-8 pt-12 pb-12 border-b border-border">
      {/* LEFT — product positioning */}
      <div className="col-span-12 lg:col-span-6 flex flex-col justify-between">
        <div>
          <div className="flex items-center gap-2 mb-5">
            <span className="inline-flex items-center gap-1.5 text-[10.5px] tracking-[0.18em] uppercase font-medium text-primary">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-primary" aria-hidden />
              GT Digital Twin · v1
            </span>
            <span className="text-muted-foreground/40 text-xs">/</span>
            <span className="text-[10.5px] tracking-[0.18em] uppercase font-medium text-muted-foreground">
              Lockport Energy Associates
            </span>
          </div>

          <h1 className="display text-[clamp(2.2rem,4.5vw,3.2rem)] leading-[1.05] tracking-[-0.02em] text-foreground">
            Asset risk-twin engine.
          </h1>
          <p className="mt-2 font-mono text-[12px] text-muted-foreground tracking-tight">
            Lockport Energy Associates · 1992 · 3-on-1 CCGT · 221 MW · NYISO Zone A
          </p>

          <p className="mt-6 text-[14px] text-foreground/80 leading-[1.6]">
            Built so the decisions an owner-operator runs — acquisition · diligence ·
            monitoring · exit — can compose on a transparent, sourced engine. v1 ships the
            engineering layer (wear · dispatch · LTSA · forward distribution); the risk-output
            layer (EBITDA-at-risk, outage exposure, capacity / market sensitivity, DSCR,
            insurance gap, exit-value haircut) is the roadmap.
          </p>

          <ul className="mt-7 space-y-2.5">
            <Proof
              n="01"
              title="Engineering layer, sourced."
              body="Every constant carries a status badge linked to its citation — [GER-3620], [Kumar2012], [NERC-GADS], [Saturday-Isaiah-2018]."
            />
            <Proof
              n="02"
              title="Decision-relevant, not descriptive."
              body="Distribution + provenance inspectable in minutes via §03 assumptions, §08 what-matters-most, §09 twin configuration."
            />
            <Proof
              n="03"
              title="Energy-only by design."
              body="Capacity, steam, ancillary deliberately excluded. The headline is the engine output, not a valuation."
              termKeys={["energy_only"]}
            />
          </ul>
        </div>

        <div className="mt-10 flex items-center gap-8 text-[10.5px] tracking-[0.15em] uppercase text-muted-foreground/80">
          <span className="font-mono">v1.2</span>
          <span className="font-mono">RT basis</span>
          <span className="font-mono">25 paths</span>
          <span className="font-mono">{computed.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}</span>
        </div>
      </div>

      {/* RIGHT — live KPI card / forecast anchor */}
      <div className="col-span-12 lg:col-span-6">
        <KpiCard data={data} cell={cell} policy={policy} initState={initState} gasMult={gasMult} aged={aged} />
      </div>
    </section>
  );
}

function Proof({ n, title, body, termKeys }: { n: string; title: string; body: string; termKeys?: any[] }) {
  const refs = useContext(ReferencesContext) as Record<string, Reference>;
  return (
    <li className="flex gap-4">
      <span className="font-mono text-[10.5px] text-muted-foreground/70 pt-1 tracking-wider">{n}</span>
      <div>
        <p className="text-[13.5px] font-medium tracking-tight text-foreground inline-flex items-center gap-1.5">
          <span>{title}</span>
          {termKeys?.map((k) => (
            <TermInfo key={k} termKey={k} side="top" />
          ))}
        </p>
        <p className="text-[12.5px] text-muted-foreground leading-[1.55] mt-0.5">
          {renderCitations(body, refs)}
        </p>
      </div>
    </li>
  );
}

function KpiCard({ data, cell, policy, initState, gasMult, aged }: Props & { aged: any }) {
  if (!cell) {
    return (
      <div className="card-clean p-6 text-sm text-muted-foreground h-full flex items-center justify-center">
        Scenario not precomputed.
      </div>
    );
  }
  const q = cell.quantiles.net_pl_usd;
  const sparkP50 = cell.quantiles.spark_margin_usd.P50;
  const ltsa = cell.quantiles.ltsa_owner_usd.P50;
  const mwh = cell.quantiles.total_mwh;
  const fh = cell.quantiles.fired_hours;
  const negative = q.P50 < 0;

  // P10..P90 mini distribution bar
  const span = Math.max(Math.abs(q.P10), Math.abs(q.P90), 1);
  const zeroPos = 50; // centered conceptually; we'll plot relative to local domain
  const allVals = [q.P10, q.P50, q.P90, 0];
  const lo = Math.min(...allVals);
  const hi = Math.max(...allVals);
  const total = hi - lo || 1;
  const pos = (v: number) => ((v - lo) / total) * 100;

  return (
    <div className="card-clean overflow-hidden h-full flex flex-col">
      {/* Card head */}
      <div className="px-6 pt-5 pb-4 border-b border-card-border flex items-center justify-between bg-secondary/30">
        <div className="flex items-center gap-2">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-primary animate-pulse" aria-hidden />
          <p className="eyebrow">Forward outlook · 1 year · energy-only</p>
        </div>
        <p className="font-mono text-[10.5px] text-muted-foreground tracking-wide">
          Policy {policy} · gas {gasMult.toFixed(2).replace(/\.?0+$/, "") || gasMult}× · {initState}
        </p>
      </div>

      {/* Headline numeric */}
      <div className="px-6 pt-6 pb-5">
        <p className="eyebrow mb-1.5 inline-flex items-center gap-1">
          <span>Net P&amp;L · P50</span>
          <TermInfo termKey="net_pl" side="bottom" />
        </p>
        <div className="flex items-baseline gap-3 flex-wrap">
          <span className={`tabular font-medium text-[2.75rem] leading-[1.05] tracking-[-0.02em] ${negative ? "text-foreground" : "text-[hsl(var(--status-real))]"}`}>
            {fmtMoneyM(q.P50, 2)}
          </span>
          <span className="text-xs text-muted-foreground inline-flex items-center gap-1">
            {negative ? <ArrowDownRight className="w-3 h-3" /> : <ArrowUpRight className="w-3 h-3" />}
            Median across 25 paths
          </span>
        </div>

        {/* Mini distribution bar with P10/P50/P90 */}
        <div className="mt-5 relative h-2 rounded-full bg-secondary/60 overflow-visible">
          <div className="absolute inset-0 rounded-full" style={{
            left: `${pos(q.P10)}%`,
            right: `${100 - pos(q.P90)}%`,
            background: "hsl(var(--primary) / 0.30)"
          }} />
          {/* Zero line */}
          {lo < 0 && hi > 0 && (
            <div className="absolute top-[-6px] bottom-[-6px] w-px bg-foreground/40" style={{ left: `${pos(0)}%` }} />
          )}
          {/* P10 marker */}
          <Marker pos={pos(q.P10)} color="hsl(var(--primary))" opacity={0.55} />
          {/* P50 marker */}
          <Marker pos={pos(q.P50)} color="hsl(var(--primary))" opacity={1} thick />
          {/* P90 marker */}
          <Marker pos={pos(q.P90)} color="hsl(var(--primary))" opacity={0.55} />
        </div>
        <div className="mt-2 grid grid-cols-3 text-[10.5px] font-mono text-muted-foreground">
          <span>P10 <span className="text-foreground/80">{fmtMoneyM(q.P10, 1)}</span></span>
          <span className="text-center">P50 <span className="text-foreground">{fmtMoneyM(q.P50, 1)}</span></span>
          <span className="text-right">P90 <span className="text-foreground/80">{fmtMoneyM(q.P90, 1)}</span></span>
        </div>
        <p className="mt-2 text-[10px] text-muted-foreground/80 inline-flex items-center gap-1">
          <span>Energy-only basis</span>
          <TermInfo termKey="energy_only" size="xs" side="bottom" />
        </p>
      </div>

      {/* Sub KPIs */}
      <div className="grid grid-cols-2 border-t border-card-border">
        <SubKpi label="Spark margin P50" value={fmtMoneyM(sparkP50, 1)} sub="Energy − fuel − VOM" termKey="spark_margin" />
        <SubKpi label="LTSA owner P50" value={fmtMoneyM(ltsa, 1)} sub="Fee + EOH + inspections" termKey="ltsa_owner" border />
        <SubKpi label="Generation P50" value={`${fmtNumber(mwh.P50 / 1000, 0)}k MWh`} sub={`${fmtNumber(mwh.P10/1000,0)}k – ${fmtNumber(mwh.P90/1000,0)}k`} termKey="generation_mwh" topBorder />
        <SubKpi label="Fired hours P50" value={fmtNumber(fh.P50, 0)} sub={`${fmtNumber(fh.P10,0)} – ${fmtNumber(fh.P90,0)}`} termKey="fired_hours" border topBorder />
      </div>

      {/* Asset metadata footer */}
      <div className="mt-auto px-6 py-4 border-t border-card-border bg-secondary/20 text-[10.5px] leading-relaxed font-mono text-muted-foreground space-y-1">
        <div className="flex justify-between gap-3">
          <span>Asset</span>
          <span className="text-foreground/80">Lockport Energy · 3-on-1 F-class · 221 MW</span>
        </div>
        {aged && initState === "aged" && (
          <div className="flex justify-between gap-3 items-center">
            <span className="inline-flex items-center gap-1">
              <span>Aged state · {policy}</span>
              <TermInfo termKey="initial_state" size="xs" side="top" />
            </span>
            <span className="text-foreground/80 inline-flex items-center gap-1">
              <span>EOH {fmtNumber(aged.eoh)}</span>
              <TermInfo termKey="eoh" size="xs" side="top" align="end" />
              <span>· rotor {(aged.rotor_life*100).toFixed(1)}%</span>
              <TermInfo termKey="rotor_life" size="xs" side="top" align="end" />
            </span>
          </div>
        )}
        <div className="flex justify-between gap-3 items-center">
          <span>Scenario set</span>
          <span className="text-foreground/80 inline-flex items-center gap-1">
            <span>{data.n_scenarios} SEAS5 analog windows · {data.basis} basis</span>
            <TermInfo termKey="analog_scenarios" size="xs" side="top" align="end" />
          </span>
        </div>
      </div>
    </div>
  );
}

function SubKpi({ label, value, sub, border, topBorder, termKey }: { label: string; value: string; sub: string; border?: boolean; topBorder?: boolean; termKey?: any }) {
  return (
    <div className={`px-6 py-4 ${border ? "border-l border-card-border" : ""} ${topBorder ? "border-t border-card-border" : ""}`}>
      <p className="eyebrow mb-1 inline-flex items-center gap-1">
        <span>{label}</span>
        {termKey && <TermInfo termKey={termKey} side="top" />}
      </p>
      <p className="tabular text-lg tracking-tight font-medium text-foreground">{value}</p>
      <p className="text-[10.5px] text-muted-foreground/80 font-mono mt-1">{sub}</p>
    </div>
  );
}

function Marker({ pos, color, opacity, thick }: { pos: number; color: string; opacity: number; thick?: boolean }) {
  return (
    <div
      className="absolute top-[-3px] bottom-[-3px]"
      style={{
        left: `calc(${pos}% - ${thick ? 1.5 : 1}px)`,
        width: thick ? 3 : 2,
        background: color,
        opacity,
        borderRadius: 2,
      }}
    />
  );
}
