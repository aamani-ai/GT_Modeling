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
import { TwinLayers } from "@/components/twin-layers";
import { PlantProfile } from "@/components/plant-profile";
import { ReferencesContext } from "@/components/info-popover";
import { TwinConfiguration } from "@/components/twin-configuration";

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
    <ReferencesContext.Provider value={data.references ?? {}}>
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
          data={data}
        />

        {/* ─────────────────────────────────────────────────────────────
            Section order — high-level story open by default,
            technical sections collapsed.

            History:
              2026-05-29 (PM): P&L moved above the forecast — lead with economics
              2026-05-29 (PM): inserted §02 Plant Profile between P&L and forecast;
                               renumbered downstream sections by +1

              §01  P&L decomposition + distribution ── open
              §02  Plant profile (identity · capability · realization) ── open
              §03  Forecast (interactive 6-panel) ── open
              §04  Assumptions & provenance ── open
              §05  Conditioning flow ── collapsed
              §06  Analog scenario table ── collapsed
              §07  Model vs. observed ── collapsed
              §08  Engine mechanics ── collapsed
              §09  What matters most ── open
              §10  Twin configuration deep-dive (every knob, sourced) ── open
            ─────────────────────────────────────────────────────────── */}
        {/* Methodology block — collapsed by default; sits ABOVE §01 so the
            reader knows it's there but isn't forced through it. Mirrors the
            "How the twin composes" diagram the fork places open at the top. */}
        <div className="pt-10">
          <CollapsibleSection
            index="00"
            title="How the twin composes"
            hint="Five engine modules · inputs → state → dispatch → wear → distribution"
            meta="methodology · explainer"
            testId="section-methodology"
          >
            <TwinLayers />
          </CollapsibleSection>
        </div>

        <div className="space-y-20 pt-14">
          {/* §01 — P&L decomposition + forward distribution */}
          <PnlDecomposition
            data={data}
            cell={cell}
            policy={policy}
            gasMult={gasMult}
            initState={initState}
            comparePolicies={comparePolicies}
            setComparePolicies={setComparePolicies}
          />

          {/* §02 — Plant profile: identity + capability envelope + realized operating profile.
              Answers "what plant produced the §01 P&L?" before the §03 forecast.
              Structural anchor only; v1 engine output does not condition on it (see ADR-005 §4 — v2 payoff). */}
          <PlantProfile data={data} />

          {/* §03 — Interactive forecast envelope */}
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

          {/* §04 — Assumptions & provenance */}
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
            index="05"
            title="Conditioning flow"
            hint="SEAS5 ensemble → analog softmax → probability weights"
            meta="real · explainer"
            testId="section-conditioning"
          >
            <ConditioningFlow data={data} />
          </CollapsibleSection>

          <CollapsibleSection
            index="06"
            title="Analog scenario table"
            hint={`25 SEAS5-conditioned analog windows · sorted by weight`}
            meta="real · per-path"
            testId="section-analog"
          >
            <AnalogTable cell={cell} policy={policy} initState={initState} gasMult={gasMult} />
          </CollapsibleSection>

          <CollapsibleSection
            index="07"
            title="Model vs. observed backtest"
            hint="MOR · EIA-923 · modeled — three-way reconciliation"
            meta="real · static"
            testId="section-backtest"
          >
            <BacktestStrip />
          </CollapsibleSection>

          <CollapsibleSection
            index="08"
            title="Engine mechanics"
            hint="Dispatch · wear · LTSA layers across 12-cell knob grid"
            meta="real · grid"
            testId="section-engine"
          >
            <EngineLayers data={data} policy={policy} initState={initState} />
          </CollapsibleSection>
        </div>

        {/* §09 — What matters most (kept open as closing story) */}
        <div className="mt-20">
          <WhatMattersMost ranks={data.sensitivity_ranks} />
        </div>

        {/* §10 — Twin configuration deep-dive: every knob in the engine, sourced.
            The natural home for the [KEY] citation links (Saturday-Isaiah, GER-3620,
            Kumar 2012, NERC-GADS) since the per-constant rows live here. */}
        <div className="mt-20">
          <TwinConfiguration data={data} policy={policy} gasMult={gasMult} initState={initState} />
        </div>

        <Footer data={data} />
      </main>
    </div>
    </ReferencesContext.Provider>
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
    </footer>
  );
}
