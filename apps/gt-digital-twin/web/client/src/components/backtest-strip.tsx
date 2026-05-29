import { InfoPopover } from "./info-popover";

// Backtest + policy comparison panels — uses repo methodology figures.
export function BacktestStrip() {
  return (
    <section className="space-y-5">
      <header className="max-w-2xl">
        <p className="eyebrow mb-2">§07 · Model vs. observed</p>
        <h2 className="display text-3xl md:text-4xl tracking-[-0.02em] leading-[1.05]">
          Calibrated against the record.
        </h2>
        <p className="mt-3 text-[13.5px] text-foreground/75 leading-[1.6]">
          Two diligence anchors. The historical backtest aligns engine output against MOR
          dispatch and EIA-923 generation. The policy comparison decomposes A/B/C divergence
          across the 2017–2025 replay.
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <FigureCard
          title="Modeled vs. MOR vs. EIA-923"
          subtitle="9-year historical replay — Mode A"
          src="img/modeled_vs_mor_vs_eia923.png"
          info={
            <InfoPopover
              title="Backtest · modeled vs. observed"
              status="real_observed"
              source="docs/methodology/assets/modeled_vs_mor_vs_eia923.png · src/gt_engine.run_mode against NYISO MOR dispatch and EIA-923 monthly generation."
              whyV1="Anchors engine plausibility against two independent records: market dispatch (MOR) and reported generation (EIA-923)."
              upgrade="Per-month MAPE in a callout; add bid stack reconciliation."
            />
          }
        />
        <FigureCard
          title="Policy A vs B vs C — historical"
          subtitle="Replay decomposition · 2017–2025"
          src="img/policy_mode_comparison.png"
          info={
            <InfoPopover
              title="Policy mode comparison"
              status="real_observed"
              source="docs/methodology/assets/policy_mode_comparison.png · A/B/C dispatch posture run against the same 9-year historical record."
              whyV1="Shows where the policies actually diverge in history. The 1-year forward can't reach C's distinctive regime; the multi-year replay does."
              upgrade="Per-window MI timing animation; LTSA event marks on the timeline."
            />
          }
        />
      </div>
    </section>
  );
}

function FigureCard({ title, subtitle, src, info }: { title: string; subtitle: string; src: string; info: React.ReactNode }) {
  return (
    <figure className="card-clean overflow-hidden flex flex-col">
      <header className="px-5 py-3 border-b border-card-border bg-secondary/30 flex items-start justify-between gap-3">
        <div>
          <p className="text-[12.5px] font-medium tracking-tight">{title}</p>
          <p className="text-[10.5px] text-muted-foreground mt-0.5">{subtitle}</p>
        </div>
        {info}
      </header>
      <div className="p-4 lg:p-5 bg-background flex-1 flex items-center justify-center">
        <img src={import.meta.env.BASE_URL + src} alt={title} className="w-full h-auto max-h-[360px] object-contain" />
      </div>
    </figure>
  );
}
