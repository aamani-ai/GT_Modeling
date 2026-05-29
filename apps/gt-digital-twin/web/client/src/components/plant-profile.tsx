/**
 * PlantProfile — §02 of the dashboard.
 *
 * The structural anchor: what plant the engine is modeling. The §01 P&L numbers
 * are an answer for a specific machine, not a generic CCGT — this section
 * makes that machine visible.
 *
 * Three nested anchors, top-down:
 *   1. Identity strip (top KPI band) — name, vintage, ISO zone, configuration
 *   2. Capability envelope (left half) — what duties the plant is qualified for
 *   3. Realized operating profile (right half) — what duties it actually exercises
 *
 * Honest about scope: ADR-005 §4 names forward conditioning on the realized
 * profile as the v2 payoff. v1 uses these YAMLs as the asset anchor + audit
 * cross-check, not as live conditioning inputs to dispatch. The header
 * carries that disclosure inline.
 *
 * UI principles applied (renewablesinfo_org/docs/principles/ui_design.md):
 *  - Data leads, chrome disappears — no decorative dividers, no "Plant" labels
 *    above the obvious plant fields
 *  - Specificity over approximation — 221.3 MW, 9.7% CF, 720 min start, not
 *    "~221 MW" / "~10%" / "very slow"
 *  - Provenance everywhere — every fact carries the status badge from its YAML
 *  - Bloomberg-Terminal density — mono tabular numbers, eyebrow micro-labels,
 *    inline status pills, no animation
 */
import { Precomputed, PlantProfile as PP, fmtNumber } from "@/lib/data";
import { StatusBadge } from "./status-badge";

const SECTION_INDEX = "§02";

const DUTY_LABEL: Record<string, string> = {
  cogen: "Cogen",
  mid_merit: "Mid-merit",
  baseload: "Baseload",
  peaker: "Peaker",
  frequency_regulation: "Frequency reg.",
  must_run_eligible: "Must-run eligible",
};

// One-line evidence sub-tag per duty — a single decisive observation, not the
// full YAML evidence sentence. Bloomberg-style: the data leads, the badge
// gives provenance, the sub-tag gives just enough context.
const DUTY_SUBTAG: Record<string, string> = {
  cogen: "DHTS + EIA CHP=Yes · host GM Harrison Radiator (PURPA)",
  mid_merit: "3×1 CCGT · HR 8.9–10.4 kBtu/kWh · ramp ~20 MW/min",
  baseload: "Hardware-capable but latent — current CF 9.7%, far below 70%",
  peaker: "EIA time-to-full-load = 720 min (12 hr) — physically too slow",
  frequency_regulation: "NYISO AGC qualification not publicly retrievable (D2)",
  must_run_eligible: "Active steam-host obligation + PURPA QF structure",
};

const SEASON_DATES: Record<"winter" | "shoulder" | "summer", string> = {
  winter: "Dec · Jan · Feb",
  shoulder: "Mar–May · Sep–Nov",
  summer: "Jun · Jul · Aug",
};

const SEASON_LABEL: Record<"winter" | "shoulder" | "summer", string> = {
  winter: "Winter",
  shoulder: "Shoulder",
  summer: "Summer",
};

export function PlantProfile({ data }: { data: Precomputed }) {
  const p = data.plant_profile;
  if (!p) {
    return (
      <section className="text-[12.5px] text-muted-foreground">
        Plant profile unavailable — regenerate precomputed.json
        (<span className="font-mono">python apps/gt-digital-twin/scripts/precompute.py</span>).
      </section>
    );
  }

  const id = p.identity;
  const eng = p.engineering;
  const cap = p.capability_envelope;
  const rop = p.realized_operating_profile;

  const onlineYear = parseInt(id.cts_operating_since.slice(0, 4), 10);
  const ageYears = new Date().getFullYear() - onlineYear;

  return (
    <section data-testid="section-plant-profile">
      <Header
        onlineYear={onlineYear}
        ageYears={ageYears}
        nameplate={eng.total_nameplate_mw}
        regimeNote={p.regime_note}
      />

      <IdentityStrip identity={id} engineering={eng} ageYears={ageYears} onlineYear={onlineYear} />

      <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
        <CapabilityEnvelopeBlock cap={cap} />
        <RealizedProfileBlock rop={rop} />
      </div>

      <SubsetCheckFooter cap={cap} rop={rop} />
    </section>
  );
}

/* ────────────────────────────────────────────────────────────────────────
   Header
   ──────────────────────────────────────────────────────────────────────── */

function Header({
  onlineYear,
  ageYears,
  nameplate,
  regimeNote,
}: {
  onlineYear: number;
  ageYears: number;
  nameplate: number;
  regimeNote: string;
}) {
  return (
    <header className="mb-7 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      <div className="lg:col-span-7">
        <p className="eyebrow mb-2">{SECTION_INDEX} · Plant profile</p>
        <h2 className="display text-3xl md:text-4xl tracking-[-0.02em] leading-[1.05]">
          What plant the engine is modeling.
        </h2>
        <p className="mt-3 text-[13.5px] text-foreground/75 leading-[1.6]">
          The §01 P&amp;L is an answer for a specific machine — a {ageYears}-year-old{" "}
          {fmtNumber(nameplate, 1)} MW 3-on-1 CCGT cogeneration plant in NYISO Zone A, online since {onlineYear}.
          Three nested anchors define it: <span className="text-foreground/95">identity</span> (who and where),
          {" "}<span className="text-foreground/95">capability envelope</span> (what it CAN do), and
          {" "}<span className="text-foreground/95">realized operating profile</span> (what it IS doing).
        </p>
      </div>

      {/* Honest scope disclosure — the regime stack is v1-built, v2-consumed. */}
      <aside className="lg:col-span-5 border border-card-border bg-card/60 rounded-sm p-4">
        <p className="eyebrow mb-2 text-foreground/70">Scope</p>
        <p className="text-[12px] text-foreground/80 leading-[1.55]">{regimeNote}</p>
        <p className="mt-2 font-mono text-[10.5px] text-muted-foreground">
          ADR-003 · ADR-004 · ADR-005
        </p>
      </aside>
    </header>
  );
}

/* ────────────────────────────────────────────────────────────────────────
   Identity strip — 4 KPI cards
   ──────────────────────────────────────────────────────────────────────── */

function IdentityStrip({
  identity,
  engineering,
  ageYears,
  onlineYear,
}: {
  identity: PP["identity"];
  engineering: PP["engineering"];
  ageYears: number;
  onlineYear: number;
}) {
  return (
    <div className="card-clean">
      <div className="grid grid-cols-2 md:grid-cols-4 divide-y md:divide-y-0 md:divide-x divide-card-border">
        <KpiCell
          eyebrow="Nameplate"
          value={`${fmtNumber(engineering.total_nameplate_mw, 1)} MW`}
          sub={`Net summer ${fmtNumber(engineering.total_net_summer_mw, 0)} · winter ${fmtNumber(engineering.total_net_winter_mw, 0)}`}
        />
        <KpiCell
          eyebrow="Vintage"
          value={`${ageYears} yrs`}
          sub={`Online ${identity.cts_operating_since} (F-class)`}
        />
        <KpiCell
          eyebrow="Market"
          value={identity.iso_zone}
          sub={`${identity.location.county} County · ${identity.location.state}`}
        />
        <KpiCell
          eyebrow="Configuration"
          value="3-on-1 CCGT"
          sub={`${engineering.hrsg_count}× HRSG · cogen · dual-fuel`}
        />
      </div>

      <div className="border-t border-card-border px-5 py-3 flex flex-wrap items-center gap-x-5 gap-y-1.5 text-[11px] text-foreground/75">
        <span><span className="text-muted-foreground">Name</span> <span className="font-medium text-foreground">{identity.name}</span></span>
        <span><span className="text-muted-foreground">Sector</span> <span className="font-mono">{identity.sector}</span></span>
        <span><span className="text-muted-foreground">Operator</span> {identity.operator === identity.name ? "same as plant" : identity.operator}</span>
        <span><span className="text-muted-foreground">Owner</span> {identity.sole_owner}</span>
        <span><span className="text-muted-foreground">Regulatory</span> <span className="font-mono">{identity.regulatory}</span> (merchant)</span>
        <span className="ml-auto font-mono text-[10.5px] text-muted-foreground">ORISPL {identity.orispl} · {identity.location.address}</span>
      </div>
    </div>
  );
}

function KpiCell({ eyebrow, value, sub }: { eyebrow: string; value: string; sub: string }) {
  return (
    <div className="px-5 py-4">
      <p className="eyebrow mb-1.5">{eyebrow}</p>
      <p className="num-pro text-[1.4rem] leading-[1.1] font-medium text-foreground">{value}</p>
      <p className="mt-1.5 text-[11px] text-muted-foreground leading-snug">{sub}</p>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────────────────
   Capability envelope — duty table + modifiers
   ──────────────────────────────────────────────────────────────────────── */

function CapabilityEnvelopeBlock({ cap }: { cap: PP["capability_envelope"] }) {
  const duties = ["cogen", "mid_merit", "baseload", "peaker", "must_run_eligible", "frequency_regulation"];

  return (
    <div>
      <BlockHeader
        eyebrow="Capability envelope"
        title="What this plant CAN be."
        sub="Per-duty qualification — physical hardware + contracts + certifications. Cadence: years (event-driven refresh)."
        meta={`as of ${cap.as_of}`}
      />

      <div className="card-clean overflow-hidden">
        <div className="grid grid-cols-12 px-4 py-2 border-b border-card-border bg-secondary/30 text-[10px] eyebrow">
          <div className="col-span-4">Duty</div>
          <div className="col-span-2 text-center">Qual</div>
          <div className="col-span-2">Conf.</div>
          <div className="col-span-4">Status</div>
        </div>
        <ul>
          {duties.map((d, i) => {
            const block = cap.per_duty[d];
            return (
              <li
                key={d}
                className={`grid grid-cols-12 gap-2 px-4 py-2.5 items-center ${
                  i < duties.length - 1 ? "border-b border-card-border" : ""
                }`}
              >
                <div className="col-span-4">
                  <p className="text-[12.5px] font-medium tracking-tight">{DUTY_LABEL[d]}</p>
                  <p className="mt-0.5 text-[10.5px] text-muted-foreground leading-snug">{DUTY_SUBTAG[d]}</p>
                </div>
                <div className="col-span-2 text-center">
                  <QualifiedGlyph value={block.qualified} />
                </div>
                <div className="col-span-2">
                  <ConfidencePill confidence={block.confidence} />
                </div>
                <div className="col-span-4">
                  <StatusBadge status={block.status} size="xs" />
                </div>
              </li>
            );
          })}
        </ul>
      </div>

      <ModifiersStrip mods={cap.modifiers} />
    </div>
  );
}

function QualifiedGlyph({ value }: { value: boolean | null }) {
  if (value === true) {
    return <span className="text-[hsl(var(--status-real))] font-mono text-[13px]" title="qualified">✓</span>;
  }
  if (value === false) {
    return <span className="text-[hsl(var(--status-placeholder))] font-mono text-[13px]" title="disqualified">✗</span>;
  }
  return <span className="font-mono text-[12px] text-muted-foreground" title="open / D2 needed">?</span>;
}

function ConfidencePill({ confidence }: { confidence: string | null }) {
  if (!confidence) return <span className="font-mono text-[10px] text-muted-foreground">—</span>;
  const color =
    confidence === "HIGH"
      ? "text-foreground/90"
      : confidence === "MEDIUM"
      ? "text-foreground/65"
      : "text-foreground/45";
  return <span className={`font-mono text-[10px] tracking-wider ${color}`}>{confidence}</span>;
}

function ModifiersStrip({ mods }: { mods: PP["capability_envelope"]["modifiers"] }) {
  return (
    <div className="mt-4 border border-card-border rounded-sm bg-card/40">
      <p className="eyebrow px-4 pt-3 pb-1.5">Capability modifiers</p>
      <ul className="px-4 pb-3 grid grid-cols-1 sm:grid-cols-2 gap-x-5 gap-y-1.5 text-[11px]">
        <li className="flex items-baseline justify-between gap-3">
          <span className="text-foreground/85">Fuel switching</span>
          <span className="font-mono text-foreground/70">
            gas → {mods.fuel_switching.secondary_fuel} in {mods.fuel_switching.switch_time_hr.toFixed(1)} hr
          </span>
        </li>
        <li className="flex items-baseline justify-between gap-3">
          <span className="text-foreground/85">Simple cycle</span>
          <span className="font-mono text-foreground/70">CT can bypass HRSG</span>
        </li>
        <li className="flex items-baseline justify-between gap-3">
          <span className="text-foreground/85">Supplemental firing</span>
          <span className="font-mono text-foreground/70">duct burners on CA</span>
        </li>
        <li className="flex items-baseline justify-between gap-3">
          <span className="text-foreground/85">Load turndown</span>
          <span className="font-mono text-foreground/70">
            CT {(mods.load_turndown.ct_min_load_pct * 100).toFixed(0)}% · CA{" "}
            {(mods.load_turndown.ca_min_load_pct * 100).toFixed(0)}%
          </span>
        </li>
      </ul>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────────────────
   Realized operating profile — seasonal triptych + per-year trend
   ──────────────────────────────────────────────────────────────────────── */

function RealizedProfileBlock({ rop }: { rop: PP["realized_operating_profile"] }) {
  const seasons: Array<"winter" | "shoulder" | "summer"> = ["winter", "shoulder", "summer"];
  const years = Object.entries(rop.per_year_cf_pct).sort(([a], [b]) => +a - +b);
  const maxCfYear = Math.max(...Object.values(rop.per_year_cf_pct));

  return (
    <div>
      <BlockHeader
        eyebrow="Realized operating profile"
        title="What this plant IS doing."
        sub="Per-season classification + per-year trend, from 5-yr MOR. Cadence: seasons to years."
        meta={`as of ${rop.as_of} · ${rop.horizon}`}
      />

      <div className="card-clean overflow-hidden">
        {/* Overall CF + realized duties summary */}
        <div className="grid grid-cols-3 divide-x divide-card-border border-b border-card-border">
          <div className="px-4 py-3">
            <p className="eyebrow mb-1">Overall CF</p>
            <p className="num-pro text-[1.4rem] leading-[1.05] font-medium">{rop.overall_cf_pct.toFixed(1)}%</p>
            <p className="mt-1 text-[10.5px] text-muted-foreground">5-yr avg, all hours</p>
          </div>
          <div className="px-4 py-3 col-span-2">
            <p className="eyebrow mb-1.5">Realized duties</p>
            <div className="flex flex-wrap gap-1.5">
              {rop.realized_duties.map((d) => (
                <span key={d} className="font-mono text-[10.5px] px-1.5 py-0.5 border border-card-border rounded-sm bg-[hsl(var(--status-real)/0.10)] text-[hsl(var(--status-real))]">
                  {d}
                </span>
              ))}
              {rop.not_realized_but_capable.map((d) => (
                <span key={d} className="font-mono text-[10.5px] px-1.5 py-0.5 border border-card-border rounded-sm text-muted-foreground" title="capability-qualified but never realized">
                  {d} (latent)
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Seasonal triptych */}
        <div className="grid grid-cols-3 divide-x divide-card-border">
          {seasons.map((s) => {
            const b = rop.per_season[s];
            return (
              <div key={s} className="px-4 py-3.5">
                <div className="flex items-baseline justify-between gap-2">
                  <p className="text-[11.5px] font-medium tracking-tight text-foreground">{SEASON_LABEL[s]}</p>
                  <p className="font-mono text-[10px] text-muted-foreground">{SEASON_DATES[s]}</p>
                </div>
                <p className="mt-2 num-pro text-[1.1rem] leading-[1.1] font-medium">{b.cf_pct.toFixed(1)}%</p>
                <p className="text-[10.5px] text-muted-foreground">CF · mean {b.mean_ambient_f.toFixed(0)}°F amb.</p>

                <ul className="mt-2.5 space-y-0.5 text-[10.5px] font-mono text-foreground/80">
                  <li className="flex justify-between gap-2"><span className="text-muted-foreground">operating</span> {b.operating_days} d</li>
                  <li className="flex justify-between gap-2"><span className="text-muted-foreground">steam-only</span> {b.steam_only_days} d</li>
                  <li className="flex justify-between gap-2"><span className="text-muted-foreground">offline</span> {b.offline_days} d</li>
                </ul>

                <p className="mt-2.5 text-[11px] text-foreground/85 leading-snug border-t border-card-border pt-2">
                  {b.label}
                </p>
              </div>
            );
          })}
        </div>

        {/* Per-year CF trend — micro bar list */}
        <div className="border-t border-card-border px-4 py-3">
          <div className="flex items-baseline justify-between gap-3 mb-2">
            <p className="eyebrow">Per-year CF trend</p>
            <p className="font-mono text-[10px] text-muted-foreground">2021 → 2025</p>
          </div>
          <ul className="space-y-1">
            {years.map(([yr, cf]) => (
              <li key={yr} className="grid grid-cols-12 gap-2 items-center text-[11px] font-mono">
                <span className="col-span-1 text-muted-foreground">{yr}</span>
                <div className="col-span-9 h-2 bg-muted/30 rounded-sm overflow-hidden">
                  <div
                    className="h-full bg-[hsl(var(--signal))]"
                    style={{ width: `${(cf / maxCfYear) * 100}%` }}
                  />
                </div>
                <span className="col-span-2 text-right tabular-nums text-foreground/85">{cf.toFixed(1)}%</span>
              </li>
            ))}
          </ul>
          <p className="mt-2.5 text-[11px] text-foreground/75 leading-snug">
            {rop.trend_interpretation}
          </p>
        </div>
      </div>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────────────────
   Shared sub-block helpers
   ──────────────────────────────────────────────────────────────────────── */

function BlockHeader({
  eyebrow,
  title,
  sub,
  meta,
}: {
  eyebrow: string;
  title: string;
  sub: string;
  meta: string;
}) {
  return (
    <div className="mb-3">
      <div className="flex items-baseline justify-between gap-3">
        <p className="eyebrow">{eyebrow}</p>
        <p className="font-mono text-[10px] text-muted-foreground">{meta}</p>
      </div>
      <h3 className="mt-1 display-sm text-[18px] tracking-[-0.01em] leading-[1.2]">{title}</h3>
      <p className="mt-1 text-[11.5px] text-foreground/65 leading-snug">{sub}</p>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────────────────
   Footer — the validation cross-check that came out of this stack
   ──────────────────────────────────────────────────────────────────────── */

function SubsetCheckFooter({
  cap,
  rop,
}: {
  cap: PP["capability_envelope"];
  rop: PP["realized_operating_profile"];
}) {
  // Subset check: every realized duty should be in the qualified set
  const qualified = new Set([...cap.qualified_duties]);
  // The realized profile uses "must_run" (short) where capability uses "must_run_eligible"
  const realizedMapped = rop.realized_duties.map((d) => (d === "must_run" ? "must_run_eligible" : d));
  const violations = realizedMapped.filter((d) => !qualified.has(d));
  const passes = violations.length === 0;

  return (
    <div className="mt-7 border-t border-card-border pt-4 grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
      <div>
        <p className="eyebrow mb-1.5">Validation</p>
        <p className="text-[12px] text-foreground/85 leading-[1.5]">
          <span className="font-mono text-foreground">Realized ⊆ Capability</span> —{" "}
          {passes ? (
            <>
              every realized duty (<span className="font-mono">{rop.realized_duties.join(", ")}</span>) is qualified
              in the envelope. {" "}<span className="text-foreground/65">Cross-check from <span className="font-mono">realized_profile_classify.py</span> against <span className="font-mono">operating_profile.yaml</span> matched the steam-only day count exactly (ADR-005 §6).</span>
            </>
          ) : (
            <span className="text-[hsl(var(--status-placeholder))]">
              Violations: {violations.join(", ")} — realized duty not in envelope. Investigate.
            </span>
          )}
        </p>
      </div>
      <div className="md:text-right">
        <p className="eyebrow mb-1.5">How this feeds the engine chain</p>
        <p className="text-[12px] text-foreground/75 leading-[1.5]">
          The capability envelope bounds what dispatch can choose; the realized
          profile bounds <span className="text-foreground/90">what we believe</span> the operator chooses.
          See <span className="font-mono">§00</span> diagram — Box <span className="font-mono">00 · Asset</span> is the static pre-step
          to Box 01 Inputs.
        </p>
      </div>
    </div>
  );
}
