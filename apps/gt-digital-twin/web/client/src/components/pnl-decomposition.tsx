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
  setComparePolicies: (v: boolean) => void;
}

export function PnlDecomposition({ data, cell, policy, gasMult, initState, comparePolicies, setComparePolicies }: Props) {
  return (
    <section className="space-y-6">
      <header className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
        <div className="max-w-2xl">
          <p className="eyebrow mb-2">§01 · P&amp;L decomposition</p>
          <h2 className="display text-3xl md:text-4xl tracking-[-0.02em] leading-[1.05]">
            Where the dollars go.
          </h2>
          <p className="mt-3 text-[13.5px] text-foreground/75 leading-[1.6]">
            Historical replay attribution on the left — the only window where the engine writes
            per-stream attribution. Forward distribution on the right — the {data.n_scenarios}-path
            ensemble, with optional A/B/C overlay.
          </p>
        </div>
        {/* Right-side scenario dossier — orients the reader to which cell this section is showing. */}
        <dl className="shrink-0 grid grid-cols-2 gap-x-5 gap-y-2 text-right">
          <DossierCell label="Policy" value={policy} />
          <DossierCell label="Gas" value={gasMult === 1.0 ? "Base" : `${gasMult}×`} />
          <DossierCell label="Init state" value={initState} />
          <DossierCell label="Scenarios" value={`${data.n_scenarios} paths`} />
        </dl>
      </header>

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-5 items-stretch">
        <div className="xl:col-span-3">
          <WaterfallChart data={data} policy={policy} />
        </div>
        <div className="xl:col-span-2">
          {/* Toggle + "why A·B·C overlap" caption now live INSIDE DistributionChart,
              so left and right columns both render as single self-contained cards
              of matching structure. */}
          <DistributionChart cell={cell} data={data} policy={policy} gasMult={gasMult} initState={initState} comparePolicies={comparePolicies} setComparePolicies={setComparePolicies} />
        </div>
      </div>

      {comparePolicies && initState === "aged" && <BcExplanation data={data} gasMult={gasMult} />}
    </section>
  );
}


// Small "dossier" cell — eyebrow label + mono value, right-aligned. Used in
// section headers to surface scenario / data-source state without a heavy
// card or chart. Single source of truth for the look-and-feel; other sections
// can either reuse this via export or replicate the same pattern locally.
export function DossierCell({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <dt className="eyebrow text-[8.5px] tracking-[0.18em]">{label}</dt>
      <dd className="font-mono text-[11.5px] text-foreground/90 mt-0.5 leading-tight">{value}</dd>
    </div>
  );
}
