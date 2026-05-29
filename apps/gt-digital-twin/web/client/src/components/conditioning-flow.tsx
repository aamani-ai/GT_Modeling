import { Precomputed, fmtNumber } from "@/lib/data";

// Explains how SEAS5 forecast → monthly anomaly scoring → analog selection → weights
// Includes a flow stepper plus a top-windows probability mini-chart.
export function ConditioningFlow({ data }: { data: Precomputed }) {
  const meta = data.scenarios_meta.slice(0, 10);
  const maxProb = Math.max(...data.scenarios_meta.map((s) => s.probability));

  return (
    <section className="space-y-7">
      <header>
        <p className="eyebrow mb-2">§04 · How conditioning works</p>
        <h2 className="display text-3xl md:text-4xl tracking-[-0.02em] leading-[1.05]">
          From a seasonal forecast<br className="hidden sm:block" /> to a weighted scenario set.
        </h2>
        <p className="mt-3 text-[13.5px] text-foreground/75 leading-[1.6] max-w-2xl">
          The engine doesn't sample synthetic price paths. It re-ranks history. Every observed Apr→Mar window
          from 1999–2026 is a candidate forward — the SEAS5 ensemble decides which look most like next year.
        </p>
      </header>

      {/* Flow stepper */}
      <div className="relative">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
          <Step n="01" title="SEAS5 ensemble" body="ECMWF SEAS5 monthly forecast members for Apr 2026 → Mar 2027, temperature anomalies over the NYISO Zone A footprint." tag="Real · ECMWF" />
          <Step n="02" title="Monthly anomaly scoring" body="Each historical Apr→Mar window scored by mean monthly anomaly distance vs. the SEAS5 distribution." tag="Real · ERA5 reanalysis" />
          <Step n="03" title="Analog window selection" body={`Top ${data.n_scenarios} windows by anomaly proximity become the forward ensemble. Apr-anchored to preserve seasonal load shape.`} tag="Methodology" />
          <Step n="04" title="Softmax probability weights" body="Scores → softmax → probability mass. The engine runs each window once, then aggregates weighted distributions." tag="Real · softmax" />
        </div>
        {/* connector arrows overlaid */}
        <div className="hidden md:flex absolute inset-0 pointer-events-none">
          <div className="grid grid-cols-4 w-full">
            {[0,1,2,3].map(i => (
              <div key={i} className="relative">
                {i < 3 && (
                  <svg className="absolute -right-2.5 top-12 text-primary/45" width="22" height="14" viewBox="0 0 22 14" fill="none">
                    <path d="M2 7 H 18 M13 2 L 18 7 L 13 12" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Probability distribution mini-chart */}
      <div className="card-clean p-5 lg:p-6">
        <header className="flex items-baseline justify-between gap-4 flex-wrap mb-4">
          <div>
            <h3 className="text-sm font-medium tracking-tight">Top 10 analog windows by probability</h3>
            <p className="text-[11.5px] text-muted-foreground mt-0.5">
              The top window — <span className="text-foreground/90 font-mono">{meta[0]?.window}</span> — carries {(meta[0]?.probability * 100).toFixed(1)}% of the probability mass.
              No window dominates: this is calibrated diversification, not analog cherry-picking.
            </p>
          </div>
          <p className="font-mono text-[10.5px] text-muted-foreground tracking-wide">{data.n_scenarios} paths total</p>
        </header>
        <ul className="space-y-1.5">
          {meta.map((s, i) => (
            <li key={i} className="grid grid-cols-[40px_110px_1fr_70px] gap-3 items-center text-[11.5px]">
              <span className="font-mono text-[10px] text-muted-foreground/70">{String(i + 1).padStart(2, "0")}</span>
              <span className="font-mono text-foreground/85">{s.window}</span>
              <div className="relative h-2.5 rounded-sm bg-secondary/40 overflow-hidden">
                <div
                  className="absolute inset-y-0 left-0 bg-primary/60"
                  style={{ width: `${(s.probability / maxProb) * 100}%` }}
                />
              </div>
              <span className="font-mono text-right text-foreground/80">{(s.probability * 100).toFixed(1)}%</span>
            </li>
          ))}
        </ul>
        <p className="mt-4 pt-3 border-t border-card-border text-[10.5px] text-muted-foreground font-mono leading-relaxed">
          Source · ERA5 anomalies → SEAS5 softmax · seed 42 · all {data.n_scenarios} windows visible in the analog scenario table below
        </p>
      </div>
    </section>
  );
}

function Step({ n, title, body, tag }: { n: string; title: string; body: string; tag: string }) {
  return (
    <div className="card-clean p-5 relative">
      <p className="font-mono text-[10.5px] text-primary tracking-wider mb-2">{n}</p>
      <h3 className="text-[13.5px] font-medium tracking-tight text-foreground mb-2">{title}</h3>
      <p className="text-[11.5px] text-muted-foreground leading-[1.55]">{body}</p>
      <p className="mt-3 inline-flex items-center gap-1 text-[10px] font-mono uppercase tracking-wider text-muted-foreground/80 border border-card-border rounded-sm px-1.5 py-0.5">
        <span className="inline-block w-1 h-1 rounded-full bg-[hsl(var(--status-real))]" />
        {tag}
      </p>
    </div>
  );
}

