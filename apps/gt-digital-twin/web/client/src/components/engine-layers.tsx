import { Precomputed, fmtNumber } from "@/lib/data";
import { Cpu, Activity, FileText } from "lucide-react";

// Three engine layer cards + the infrasure pipeline image as the architectural anchor.
export function EngineLayers({ data, policy, initState }: { data: Precomputed; policy: string; initState: string }) {
  const aged = data.aged_state_summary[policy];
  const c = data.constants;
  const eohThresh = 48000;
  const headroom = aged ? eohThresh - aged.eoh : null;

  return (
    <section className="space-y-7">
      <header className="max-w-2xl">
        <p className="eyebrow mb-2">§08 · Engine mechanics</p>
        <h2 className="display text-3xl md:text-4xl tracking-[-0.02em] leading-[1.05]">
          Three layers, one engine.
        </h2>
        <p className="mt-3 text-[13.5px] text-foreground/75 leading-[1.6]">
          The simulation isn't a black box. Engineering state, hourly dispatch, and the LTSA contract layer
          run as three independent modules whose outputs compose into the headline distribution.
        </p>
      </header>

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-12 lg:col-span-7 card-clean overflow-hidden">
          <div className="px-5 py-3 border-b border-card-border bg-secondary/30 flex items-center justify-between flex-wrap gap-2">
            <p className="text-[12px] font-medium tracking-tight">Pipeline architecture</p>
            <p className="font-mono text-[10.5px] text-muted-foreground">img/infrasure_pipeline.png</p>
          </div>
          <div className="p-4 lg:p-5 bg-background flex items-center justify-center">
            <img
              src={import.meta.env.BASE_URL + "img/infrasure_pipeline.png"}
              alt="Infrasure engine pipeline"
              className="w-full h-auto max-h-[440px] object-contain"
            />
          </div>
        </div>

        <div className="col-span-12 lg:col-span-5 grid grid-cols-1 gap-3">
          <LayerCard
            icon={<Cpu className="w-4 h-4" />}
            n="L1"
            title="Engineering state"
            body={`Equivalent operating hours (EOH), rotor life consumed, inspection counters. Aged ${policy}: EOH ${aged ? fmtNumber(aged.eoh) : "—"} · headroom to MI ${headroom ? `${fmtNumber(headroom)}h` : "—"}.`}
            facts={[
              ["MI threshold", `${fmtNumber(eohThresh)} h`],
              ["Rotor life used", aged ? `${(aged.rotor_life * 100).toFixed(1)}%` : "—"],
            ]}
          />
          <LayerCard
            icon={<Activity className="w-4 h-4" />}
            n="L2"
            title="Hourly dispatch"
            body="Hourly spark-margin decisions across 3×CC / 2×CC / 1×CC operating modes. Policy A/B/C modulate the wear-penalty hurdle as EOH headroom shrinks."
            facts={[
              ["Modes", `${c.MODE_3xCC_MW.toFixed(0)} / ${c.MODE_2xCC_MW.toFixed(0)} / ${c.MODE_1xCC_MW.toFixed(0)} MW`],
              ["Heat rates", `${fmtNumber(c.HR_3xCC)} / ${fmtNumber(c.HR_2xCC)} / ${fmtNumber(c.HR_1xCC)}`],
            ]}
          />
          <LayerCard
            icon={<FileText className="w-4 h-4" />}
            n="L3"
            title="LTSA / contract layer"
            body="Long-term service agreement: daily fixed fee, EOH-banked reserve, inspection events tied to engineering counters. Owner cost is the L1+L2 byproduct."
            facts={[
              ["Fixed fee", `$${(c.LTSA_FIXED_DAILY * 365 / 1e6).toFixed(2)}M/yr`],
              ["EOH reserve", `$${c.LTSA_EOH_RESERVE_USD_PER_EOH.toFixed(0)}/EOH`],
            ]}
          />
        </div>
      </div>
    </section>
  );
}

function LayerCard({ icon, n, title, body, facts }: { icon: React.ReactNode; n: string; title: string; body: string; facts: [string, string][] }) {
  return (
    <article className="card-clean p-5">
      <div className="flex items-center gap-2.5 mb-2.5">
        <span className="w-7 h-7 rounded-md border border-primary/30 bg-primary/8 flex items-center justify-center text-primary">
          {icon}
        </span>
        <span className="font-mono text-[10.5px] text-muted-foreground tracking-wider">{n}</span>
        <h3 className="text-[13px] font-medium tracking-tight">{title}</h3>
      </div>
      <p className="text-[11.5px] text-muted-foreground leading-[1.6] mb-3">{body}</p>
      <div className="grid grid-cols-2 gap-3 pt-3 border-t border-card-border">
        {facts.map(([k, v], i) => (
          <div key={i}>
            <p className="eyebrow text-[9px] mb-0.5">{k}</p>
            <p className="font-mono text-[11.5px] text-foreground/90">{v}</p>
          </div>
        ))}
      </div>
    </article>
  );
}
