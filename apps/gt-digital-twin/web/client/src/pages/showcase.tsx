import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Precomputed, MonthlyForecastPanel, keyFor } from "@/lib/data";
import { Banner } from "@/components/banner";
import { Header } from "@/components/header";
import { ControlBar } from "@/components/control-bar";
import { HeroPanel } from "@/components/hero-panel";
import { ForecastEnvelope } from "@/components/forecast-envelope";
import { ForecastSixPanel } from "@/components/forecast-six-panel";
import { ConditioningFlow } from "@/components/conditioning-flow";
import { AnalogTable } from "@/components/analog-table";
import { PnlDecomposition } from "@/components/pnl-decomposition";
import { BacktestStrip } from "@/components/backtest-strip";
import { WhatMattersMost } from "@/components/what-matters-most";
import { EngineLayers } from "@/components/engine-layers";
import { AssumptionPanel } from "@/components/assumption-panel";
import { CollapsibleSection } from "@/components/collapsible-section";

export default function Showcase() {
  const [policy, setPolicy] = useState<string>("A");
  const [gasMult, setGasMult] = useState<number>(1.0);
  const [initState, setInitState] = useState<string>("aged");
  const [comparePolicies, setComparePolicies] = useState<boolean>(true);

  const { data, isLoading, isError } = useQuery<Precomputed>({
    queryKey: ["precomputed"],
    queryFn: async () => {
      const res = await fetch(import.meta.env.BASE_URL + "precomputed.json");
      if (!res.ok) throw new Error("Failed to load precomputed.json");
      return res.json();
    },
    staleTime: Infinity,
  });

  const { data: monthly } = useQuery<MonthlyForecastPanel>({
    queryKey: ["monthly_forecast_panel"],
    queryFn: async () => {
      const res = await fetch(import.meta.env.BASE_URL + "monthly_forecast_panel.json");
      if (!res.ok) throw new Error("Failed to load monthly_forecast_panel.json");
      return res.json();
    },
    staleTime: Infinity,
  });

  const cell = useMemo(() => {
    if (!data) return null;
    const key = keyFor(policy, gasMult, initState);
    return data.grid[key] ?? null;
  }, [data, policy, gasMult, initState]);

  const monthlyCell = useMemo(() => {
    if (!monthly) return null;
    const key = keyFor(policy, gasMult, initState);
    return monthly.grid[key] ?? null;
  }, [monthly, policy, gasMult, initState]);

  if (isLoading) return <LoadingShell />;
  if (isError || !data) return <ErrorShell />;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header generatedAt={data.generated_at} basis={data.basis} nScen={data.n_scenarios} />
      <Banner />

      <main className="max-w-[1480px] mx-auto px-6 lg:px-10 pb-24">
        {/* HERO — composed two-column, no empty right gap */}
        <HeroPanel data={data} cell={cell} policy={policy} initState={initState} gasMult={gasMult} />

        {/* Sticky scenario anchor controls */}
        <ControlBar
          policy={policy}
          setPolicy={setPolicy}
          gasMult={gasMult}
          setGasMult={setGasMult}
          initState={initState}
          setInitState={setInitState}
          comparePolicies={comparePolicies}
          setComparePolicies={setComparePolicies}
          data={data}
        />

        {/* ─────────────────────────────────────────────────────────────
            v1.2 section order — high-level story open by default,
            technical sections collapsed.

              §01  Forecast (interactive 6-panel) ── open
              §02  P&L decomposition + distribution ── open  (was §04)
              §03  Assumptions & provenance ── open  (was §08)
              §04  Conditioning flow ── collapsed  (was §02)
              §05  Analog scenario table ── collapsed  (was §03)
              §06  Model vs. observed ── collapsed  (was §05)
              §07  Engine mechanics ── collapsed  (was §06)
              §08  What matters most ── open  (was §07)
            ─────────────────────────────────────────────────────────── */}
        <div className="space-y-20 pt-14">
          {/* §01 — Interactive forecast envelope (the marquee) */}
          {monthly && monthlyCell && cell ? (
            <ForecastSixPanel
              data={data}
              monthly={monthly}
              monthlyCell={monthlyCell}
              cell={cell}
              policy={policy}
              initState={initState}
              gasMult={gasMult}
            />
          ) : (
            <ForecastEnvelope data={data} cell={cell} policy={policy} initState={initState} gasMult={gasMult} />
          )}

          {/* §02 — P&L decomposition + forward distribution (was §04) */}
          <PnlDecomposition
            data={data}
            cell={cell}
            policy={policy}
            gasMult={gasMult}
            initState={initState}
            comparePolicies={comparePolicies}
          />

          {/* §03 — Assumptions & provenance (was §08, moved up so reader sees what's real before going deeper) */}
          <AssumptionPanel register={data.calibration_register} />
        </div>

        {/* Detailed / technical sections — collapsed by default */}
        <div className="mt-20 space-y-3" data-testid="technical-sections">
          <div className="mb-4">
            <p className="eyebrow mb-1">Technical detail</p>
            <p className="text-[12.5px] text-muted-foreground leading-snug max-w-2xl">
              How the conditioning works, which analog windows drove the result, model-vs-observed checks,
              and engine layers. Collapsed by default so the story above stays readable; expand any section to dig in.
            </p>
          </div>

          <CollapsibleSection
            index="04"
            title="Conditioning flow"
            hint="SEAS5 ensemble → analog softmax → probability weights"
            meta="real · explainer"
            testId="section-conditioning"
          >
            <ConditioningFlow data={data} />
          </CollapsibleSection>

          <CollapsibleSection
            index="05"
            title="Analog scenario table"
            hint={`25 SEAS5-conditioned analog windows · sorted by weight`}
            meta="real · per-path"
            testId="section-analog"
          >
            <AnalogTable cell={cell} policy={policy} initState={initState} gasMult={gasMult} />
          </CollapsibleSection>

          <CollapsibleSection
            index="06"
            title="Model vs. observed backtest"
            hint="MOR · EIA-923 · modeled — three-way reconciliation"
            meta="real · static"
            testId="section-backtest"
          >
            <BacktestStrip />
          </CollapsibleSection>

          <CollapsibleSection
            index="07"
            title="Engine mechanics"
            hint="Dispatch · wear · LTSA layers across 12-cell knob grid"
            meta="real · grid"
            testId="section-engine"
          >
            <EngineLayers data={data} policy={policy} initState={initState} />
          </CollapsibleSection>
        </div>

        {/* §08 — What matters most (kept open as closing story) */}
        <div className="mt-20">
          <WhatMattersMost ranks={data.sensitivity_ranks} />
        </div>

        <Footer data={data} />
      </main>
    </div>
  );
}

function LoadingShell() {
  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
      <div className="text-center space-y-3">
        <div className="w-8 h-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin mx-auto"></div>
        <p className="eyebrow">Loading precomputed engine output</p>
      </div>
    </div>
  );
}

function ErrorShell() {
  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center px-8">
      <div className="max-w-md text-center space-y-3">
        <p className="eyebrow text-destructive">Failed to load</p>
        <p className="text-sm text-muted-foreground">
          precomputed.json was not found. Run <code className="font-mono text-xs px-1.5 py-0.5 bg-muted rounded">python apps/gt-digital-twin/scripts/precompute.py</code> from the repo root before serving the dashboard.
        </p>
      </div>
    </div>
  );
}

function Footer({ data }: { data: Precomputed }) {
  return (
    <footer className="mt-24 pt-8 border-t border-border text-xs text-muted-foreground">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <p className="eyebrow mb-2">Engine</p>
          <p className="font-mono text-[11px] leading-relaxed">{data.engine_version}</p>
        </div>
        <div>
          <p className="eyebrow mb-2">Basis</p>
          <p className="font-mono text-[11px]">{data.basis} · {data.n_scenarios} SEAS5-conditioned analog windows</p>
        </div>
        <div>
          <p className="eyebrow mb-2">Computed</p>
          <p className="font-mono text-[11px]">{new Date(data.generated_at).toUTCString()}</p>
        </div>
      </div>
      <p className="mt-8 text-[11px] leading-relaxed max-w-3xl">
        Data in this showcase comes from precomputed runs of <span className="font-mono">src/gt_engine.run_path</span> and <span className="font-mono">src/forward.run_forward</span> against a 12-cell knob matrix. Live recompute is intentionally off — <span className="font-mono">run_forward</span> is slow (~110s/mode) and v1 prioritizes a shareable preview over a live cockpit. See <span className="font-mono">apps/gt-digital-twin/README.md</span> for the live-integration handoff.
      </p>
    </footer>
  );
}
