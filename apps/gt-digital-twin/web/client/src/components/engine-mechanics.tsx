import { Precomputed, fmtNumber } from "@/lib/data";

// Small "engine mechanics" panel — a calm baseline/interpretation strip that
// gives diligence viewers a one-look anchor into the simulated asset.
export function EngineMechanics({ data, policy, initState }: { data: Precomputed; policy: string; initState: string }) {
  const aged = data.aged_state_summary[policy];
  const c = data.constants;
  const eohThresh = 48000;
  const headroom = aged ? eohThresh - aged.eoh : null;

  return (
    <section className="card-clean p-5 lg:p-6">
      <header className="flex items-baseline justify-between gap-4 mb-4 flex-wrap">
        <div>
          <h2 className="text-sm font-medium tracking-tight">Engine baseline</h2>
          <p className="text-[11.5px] text-muted-foreground mt-0.5 leading-relaxed">
            Fixed asset constants and where this policy's aged state sits in the wear cycle.
          </p>
        </div>
      </header>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-5 text-[11.5px]">
        <Field label="Operating modes" value={`3×CC ${c.MODE_3xCC_MW.toFixed(1)} MW · 2×CC ${c.MODE_2xCC_MW.toFixed(1)} MW · 1×CC ${c.MODE_1xCC_MW.toFixed(1)} MW`} />
        <Field label="Heat rates (Btu/kWh)" value={`${fmtNumber(c.HR_3xCC)} · ${fmtNumber(c.HR_2xCC)} · ${fmtNumber(c.HR_1xCC)}`} />
        <Field label="VOM (cogen markup)" value={`$${c.VOM_USD_PER_MWH.toFixed(2)}/MWh`} />
        <Field label="LTSA fixed fee" value={`$${(c.LTSA_FIXED_DAILY * 365 / 1e6).toFixed(2)}M /yr · $${c.LTSA_EOH_RESERVE_USD_PER_EOH.toFixed(0)}/EOH reserve`} />
        {aged && initState === "aged" && (
          <>
            <Field label={`Aged EOH — policy ${policy}`} value={`${fmtNumber(aged.eoh)} h`} mono />
            <Field label="MI threshold" value={`${fmtNumber(eohThresh)} h`} mono />
            <Field label="Headroom to MI" value={headroom ? `${fmtNumber(headroom)} h` : "—"} mono accent={headroom && headroom < 4000} />
            <Field label="Rotor life used" value={`${(aged.rotor_life * 100).toFixed(1)}%`} mono />
          </>
        )}
      </div>
    </section>
  );
}

function Field({ label, value, mono, accent }: { label: string; value: string; mono?: boolean; accent?: boolean }) {
  return (
    <div>
      <p className="eyebrow mb-1.5">{label}</p>
      <p className={`${mono ? "font-mono" : ""} text-[12px] leading-tight ${accent ? "text-[hsl(var(--status-assumed))]" : "text-foreground/90"}`}>{value}</p>
    </div>
  );
}
