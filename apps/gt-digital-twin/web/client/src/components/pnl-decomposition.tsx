import { Precomputed, GridCell } from "@/lib/data";
import { WaterfallChart } from "./waterfall-chart";
import { DistributionChart } from "./distribution-chart";
import { BcExplanation } from "./bc-explanation";

interface Props {
  data: Precomputed;
  cell: GridCell | null;
  policy: string;
  gasMult: number;
  initState: string;
  comparePolicies: boolean;
}

export function PnlDecomposition({ data, cell, policy, gasMult, initState, comparePolicies }: Props) {
  return (
    <section className="space-y-6">
      <header className="max-w-2xl">
        <p className="eyebrow mb-2">§02 · P&amp;L decomposition</p>
        <h2 className="display text-3xl md:text-4xl tracking-[-0.02em] leading-[1.05]">
          Where the dollars go.
        </h2>
        <p className="mt-3 text-[13.5px] text-foreground/75 leading-[1.6]">
          Historical replay attribution on the left — the only window where the engine writes
          per-stream attribution. Forward distribution on the right — the {data.n_scenarios}-path
          ensemble, with optional A/B/C overlay.
        </p>
      </header>

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-5">
        <div className="xl:col-span-3">
          <WaterfallChart data={data} policy={policy} />
        </div>
        <div className="xl:col-span-2">
          <DistributionChart cell={cell} data={data} policy={policy} gasMult={gasMult} initState={initState} comparePolicies={comparePolicies} />
        </div>
      </div>

      {comparePolicies && initState === "aged" && <BcExplanation data={data} gasMult={gasMult} />}
    </section>
  );
}
