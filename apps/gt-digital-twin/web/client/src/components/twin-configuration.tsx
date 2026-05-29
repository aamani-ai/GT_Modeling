import { useContext } from "react";
import { Precomputed, fmtNumber } from "@/lib/data";
import { StatusBadge } from "./status-badge";
import { InfoPopover, ReferencesContext, renderCitations } from "./info-popover";
import { TermInfo, TERMS } from "./term-info";
import { DossierCell } from "./pnl-decomposition";
import {
  Cpu,
  TrendingUp,
  Thermometer,
  Wrench,
  AlertTriangle,
  FileSignature,
  Coins,
} from "lucide-react";

/**
 * TwinConfiguration — methodology-driven deep dive.
 *
 * Seven grouped configuration cards covering every knob the engine
 * currently exposes plus the deferred / roadmap knobs the digital-twin
 * product surface is being designed around.
 *
 * Design rules:
 *  - Active controls (policy, gas, init_state) link back to the live
 *    scenario anchor at the top of the page — we do not duplicate the
 *    controls themselves here, we just document their current value.
 *  - Roadmap / deferred controls render inside `.control-disabled`
 *    affordance (dashed + diagonal stripes) so it is visually obvious
 *    they are previews of intent, not interactive surfaces.
 *  - Every value is sourced. The StatusBadge tags the provenance
 *    taxonomy; InfoPopover carries source/why-v1/upgrade copy.
 *  - No fabrication: values come from `data.constants`,
 *    `data.calibration_register`, `data.aged_state_summary`, or the
 *    YAML/methodology copy that the docs already commit to (which we
 *    mirror verbatim in UI copy, never invented).
 */
export function TwinConfiguration({
  data,
  policy,
  gasMult,
  initState,
}: {
  data: Precomputed;
  policy: string;
  gasMult: number;
  initState: string;
}) {
  const c = data.constants;
  const reg = data.calibration_register;
  const aged = data.aged_state_summary[policy];

  return (
    <section className="space-y-7" data-testid="twin-configuration">
      <header className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
        <div className="max-w-2xl">
          <p className="eyebrow mb-2">§10 · Twin configuration</p>
          <h2 className="display text-3xl md:text-4xl tracking-[-0.02em] leading-[1.05]">
            Every knob in the engine, sourced.
          </h2>
          <p className="mt-3 text-[13.5px] text-foreground/75 leading-[1.6]">
            The simulation has roughly seven configuration surfaces. Three are wired to the scenario anchor at the
            top of the page; the remainder are either fixed modeling constants we have evidence for, or deferred
            controls the cockpit will expose once we have the underlying data. Each card states the current value,
            its provenance, and what would turn a placeholder into an instrument.
          </p>
        </div>
        {/* Right-side: deep-dive scope at a glance. */}
        <dl className="grid grid-cols-2 gap-x-5 gap-y-2 text-right shrink-0">
          <DossierCell label="Cards" value="7 surfaces" />
          <DossierCell label="Active controls" value="3 (policy · gas · init)" />
          <DossierCell label="Reference sources" value={`${Object.keys(data.references ?? {}).length} cited`} />
          <DossierCell label="Roadmap items" value="marked · dashed" />
        </dl>
      </header>

      <div className="grid grid-cols-12 gap-4">
        {/* 01 — Asset state */}
        <ConfigCard
          n="01"
          icon={<Cpu className="w-3.5 h-3.5" />}
          title="Asset state"
          subtitle="What the engine starts knowing about the plant."
          colSpan="col-span-12 lg:col-span-6"
        >
          <Row
            label="Initial state preset"
            value={initState === "aged" ? "Aged · per-mode historical end-state" : "Fresh · EOH 24,000 default"}
            badge={reg.init_state.status}
            active
            info={
              <InfoPopover
                title="Initial plant state"
                status={reg.init_state.status}
                source={reg.init_state.source}
                whyV1={reg.init_state.why_v1}
                upgrade={reg.init_state.upgrade}
                value={`aged: each mode's historical end-state\nfresh: EOH 24k modeling default`}
              />
            }
          />
          <Row
            label="Equivalent operating hours (EOH)"
            termKey="eoh"
            value={aged ? `${fmtNumber(aged.eoh)} h` : "—"}
            sub={`Policy ${policy} aged window · MI threshold 48,000 h`}
            info={<InfoPopover
              title="Aged-state EOH (start of forward window)"
              status="real_computed"
              source="Computed: run_mode(policy) returns state.eoh at sim end. Each policy's history accrued differently — A took its MI in-history; B/C deferred. ADR-009 wires this as init_state_override into the forward."
              whyV1="Starting EOH is the first-order driver of WHEN the next MI fires. Aged init = realistic continuation from 2017–2025 history; fresh init = modeling default (24k)."
              upgrade="Tier-1 measured: data-room accrued-EOH at sim start (1992 vintage history). Register §3.12."
            />} />
          <Row
            label="Rotor life consumed"
            termKey="rotor_life"
            value={aged ? `${(aged.rotor_life * 100).toFixed(1)}%` : "—"}
            sub="Cumulative creep + fatigue, normalized 0–100%"
            info={<InfoPopover
              title="state.rotor_life"
              status="real_computed"
              source="Engine-computed accumulator: ROTOR_LIFE_PER_FIRED_HOUR × fired_hours + per-start increment, partially replenished at CI (×0.5) and reset at MI. Initial value 0.35 (mid-life convention)."
              whyV1="Slow accumulator — for low-CF Lockport it stays well below 1.0 over the 9-year history. Not a near-term gating constraint."
              upgrade="Initial 0.35 should come from data-room rotor inspection records. Register §3.13."
            />} />
          <Row
            label="Inspections completed"
            value={aged ? `${aged.insp_done}` : "—"}
            sub="CI events triggered in the aged window"
            info={<InfoPopover
              title="Inspections completed (CI + MI)"
              status="real_computed"
              source="Counter: number of CI/MI events that fired during the historical replay for this policy. A=1 (took its MI in 2025); B/C=0 (deferred past sim end)."
              whyV1="Distinguishes the aged-start condition: A enters the forward freshly overhauled, B/C carry the deferred MI. This drives most of A's forward edge — not in-forward policy."
              upgrade="Tier-1 measured: actual contract inspection history from the data-room would replace the simulated counter."
            />} />
          <RoadmapRow
            label="Per-generator state"
            preview="Independent CT1 / CT2 / CT3 / ST timers, fouling, dc/df/tbc_time"
            why="Engine refactor — currently rolled into a plant-level state vector"
          />
        </ConfigCard>

        {/* 02 — Market & dispatch */}
        <ConfigCard
          n="02"
          icon={<TrendingUp className="w-3.5 h-3.5" />}
          title="Market & dispatch"
          subtitle="How the plant decides when to run."
          colSpan="col-span-12 lg:col-span-6"
        >
          <Row
            label="Dispatch policy"
            value={
              policy === "A" ? "A · myopic merchant (1.0× wear hurdle)"
              : policy === "B" ? "B · NPV-rational (clamps at 2.5×, headroom ≤ 1k EOH)"
              : "C · risk-averse (ramps to 4.0×, headroom ≤ 0)"
            }
            badge={reg.policy.status}
            active
            info={
              <InfoPopover
                title="A/B/C dispatch policy"
                status={reg.policy.status}
                source={reg.policy.source}
                whyV1={reg.policy.why_v1}
                upgrade={reg.policy.upgrade}
                value={`A = myopic merchant (1.0×)\nB = NPV-rational (2.5× cap)\nC = risk-averse (4.0× cap)`}
              />
            }
          />
          <Row
            label="Gas price multiplier"
            value={gasMult === 1.0 ? "Base (1.0× Henry Hub)" : `${gasMult}× Henry Hub`}
            badge={reg.gas_price.status}
            active
            info={
              <InfoPopover
                title="Henry Hub multiplier"
                status={reg.gas_price.status}
                source={reg.gas_price.source}
                whyV1={reg.gas_price.why_v1}
                upgrade={reg.gas_price.upgrade}
                value="Uniform multiplier on Henry Hub series"
              />
            }
          />
          <Row
            label="Variable O&M"
            termKey="energy_only"
            value={`$${c.VOM_USD_PER_MWH.toFixed(3)} / MWh`}
            sub="Fixed in v1 — energy-only basis"
            badge="modeling_convention"
            info={<InfoPopover
              title="VOM_USD_PER_MWH"
              status="modeling_convention"
              source="Athens-prototype VOM placeholder. Energy-only basis — does not include capacity, steam, or ancillary revenue offsets. Hardcoded in engine config."
              whyV1="Small relative to fuel + LTSA on the cost side; placeholder is acceptable for the showcase scope. The 'energy-only' framing is the bigger statement."
              upgrade="Data-room O&M actuals (NAES operating-cost reports if available); split out the cogen-specific variable cost component."
            />}
          />
          <Row
            label="Operating modes"
            value={`3×CC ${c.MODE_3xCC_MW.toFixed(0)} · 2×CC ${c.MODE_2xCC_MW.toFixed(0)} · 1×CC ${c.MODE_1xCC_MW.toFixed(0)} MW`}
            sub={`Heat rates ${fmtNumber(c.HR_3xCC)} · ${fmtNumber(c.HR_2xCC)} · ${fmtNumber(c.HR_1xCC)} Btu/kWh`}
            badge="real_observed"
            info={<InfoPopover
              title="Operating modes — capacity & heat rate"
              status="real_observed"
              source="EIA-860 thermal_enriched + MOR-extracted heat rates per mode (see operating_profile.yaml). 3×CC = all three CTs + ST; 2×CC = two CTs + ST (currently dispatch blind spot); 1×CC = one CT + ST. Heat rate is MODE-only in v1 — does NOT vary with ambient temperature (gaps_and_priorities #10)."
              whyV1="Tier-1 measured; the most defensible operational constants in the engine."
              upgrade="Add ambient T → heat-rate curve (priority #10 in gaps_and_priorities). Per-generator state vector would unlock 2×CC dispatch behavior (gap #4)."
            />}
          />
          <RoadmapRow
            label="LMP basis · DA vs RT toggle"
            termKeys={["lmp", "rt_basis"]}
            preview="Day-Ahead and Real-Time basis selectable, with Algonquin basis on the gas side"
            why="Requires DA series + Algonquin basis ingestion (deferred)"
          />
          <RoadmapRow
            label="Minimum-run hours override"
            preview={`Engine constant MIN_RUN_HOURS = 6 (un-exposed)`}
            why="Engine refactor — currently a literal in the dispatch loop"
          />
          <RoadmapRow
            label="Policy strategy workbench"
            preview="Design and compare candidate dispatch / wear policies — custom wear hurdles, headroom rules, start-cost weights — against the same Monte-Carlo engine that drives A·B·C today"
            why="v1 only compares the fixed A / B / C postures; custom policy optimization and parameter sweeps are not active yet"
          />
        </ConfigCard>

        {/* 03 — Thermal / weather */}
        <ConfigCard
          n="03"
          icon={<Thermometer className="w-3.5 h-3.5" />}
          title="Thermal & weather effects"
          subtitle="How ambient temperature deforms output, heat rate, and wear."
          colSpan="col-span-12 lg:col-span-6"
        >
          <Row
            label="Ambient wear sensitivity"
            value="0.004 / °F"
            sub="Linear creep + fatigue uplift, referenced to 34.3 °F. Cross-check flag: [Saturday-Isaiah-2018] measures 6.85 %/°F on LM2500+ (~17× higher); heavy-duty F-class caveat — see register §3.7."
            badge="assumed_industry"
            info={<InfoPopover
              title="AMBIENT_WEAR_SENS_PER_F"
              status="assumed_industry"
              source="Literature default for hot-section ambient sensitivity (ADR-006). [Saturday-Isaiah-2018] measures 12.33 %/°C ≈ 6.85 %/°F creep-life decrease on LM2500+ aero-derivative — ~17× higher than our current 0.4 %/°F. Heavy-duty F-class vs aero-derivative likely explains some, not all."
              whyV1="Lockport's realized fired-hour-weighted mean ambient ≈ 34.3 °F → modest swing in the current calibration. The mechanism is wired (ADR-006); only the magnitude is in question."
              upgrade="Sensitivity sweep across 0.004 → 0.07 /°F to bound the heavy-duty correction factor; calibrate target via MOR EOH-vs-inspection timing — register §3.7."
              value="0.004 per °F · clamped factor ∈ [0.70, 1.40]"
            />}
          />
          <Row
            label="Summer derate"
            value="−3.5% capacity"
            sub="From engineering.yaml summer envelope"
            badge="real_reported"
            info={<InfoPopover
              title="Summer ambient derate"
              status="real_reported"
              source="EIA-860 thermal_enriched envelope + plant-reported summer DMNC. Encoded in [data/assets/lockport/engineering.yaml]."
              whyV1="Capacity drops with hot ambient — directly observed for this asset class, real_reported tier."
              upgrade="Per-hour temperature-dependent derate curve (replacing the two-season step) when EIA-923 hourly + LMSPP correlation is wired."
            />}
          />
          <Row
            label="Winter boost"
            value="+2.7% capacity"
            sub="From engineering.yaml winter envelope"
            badge="real_reported"
            info={<InfoPopover
              title="Winter ambient boost"
              status="real_reported"
              source="EIA-860 thermal_enriched envelope + plant-reported winter DMNC. Encoded in [data/assets/lockport/engineering.yaml]."
              whyV1="GT output rises with cold ambient (denser intake air); ST condenser efficiency also gains in summer (caveat — see engineering.yaml §7)."
              upgrade="Per-hour temperature curve as above; document the ST-side counter-effect that partially offsets the GT-side seasonality."
            />}
          />
          <Row
            label="Reference ambient"
            value="34.3 °F"
            sub="Mean annual NYISO Zone A — wear calibration anchor"
            badge="modeling_convention"
            info={<InfoPopover
              title="AMBIENT_WEAR_REF_F"
              status="modeling_convention"
              source="Realized fired-hour-weighted mean ambient on the Lockport simulation path. Re-anchor point for the wear factor (see ADR-006); not a free parameter — derived from data."
              whyV1="Centering the factor on the fired-hour-weighted mean keeps total calibrated wear preserved (anchor ratio ≈ 1.0); only the time-distribution of wear shifts toward hot hours."
              upgrade="Recompute per asset when extending beyond Lockport. The mechanism generalizes; this number is asset-specific."
            />}
          />
          <RoadmapRow
            label="Weather source override"
            preview="Choose SEAS5 ensemble · ERA5 reanalysis · historical analog"
            why="Cockpit exposure pending — engine accepts the data but UI does not"
          />
        </ConfigCard>

        {/* 04 — Wear & maintenance */}
        <ConfigCard
          n="04"
          icon={<Wrench className="w-3.5 h-3.5" />}
          title="Wear & maintenance"
          subtitle="The nine stress accumulators that drive EOH and inspections."
          colSpan="col-span-12 lg:col-span-6"
        >
          <Row label="EOH baseline · CI threshold · MI threshold"
               value="24,000 · 24,000 · 48,000 h"
               sub="[GER-3620] standard CI/MI intervals + equivalent-hours convention. CI replenishes 25% rotor, MI replenishes 100%."
               badge="assumed_industry"
               info={<InfoPopover
                 title="Inspection intervals (CI / MI)"
                 status="assumed_industry"
                 source="[GER-3620] standard GE 7FA.03 CI/MI intervals (Athens default). Initial EOH baseline 24,000 is a modeling convention ('post-HGP mid-clock'); register §3.12 + §3.14 + §3.15."
                 whyV1="MI fires ~2025 in the historical replay only because EOH starts at 24k and accrues to the 48k threshold — i.e., the initial-EOH assumption is first-order on MI timing."
                 upgrade="Tier-1 from data-room: actual contract CI/MI intervals + accrued-EOH history at sim start. See parameter_calibration_register §3.12–§3.15."
                 value="CI threshold 24,000 h · MI threshold 48,000 h · start EOH 24,000 h"
               />} />
          <Row label="Compressor fouling"
               value="τ = 2,000 h · asymptote 2.5%"
               sub="Exponential approach to fouled-state heat-rate uplift — industry rule-of-thumb, register §3.6."
               badge="assumed_industry"
               info={<InfoPopover
                 title="FOULING_TAU_HRS / asymptote"
                 status="assumed_industry"
                 source="Compressor-fouling exponential approach (industry rule-of-thumb). Not directly cited; sits between vendor specs and field experience. Register §3.6 / §4.1."
                 whyV1="Tier-2 placeholder; the exponential shape is well-accepted, the magnitudes (τ, asymptote) are Athens-prototype defaults. Phase-L tornado top driver."
                 upgrade="Calibrate τ, asymptote to MOR heat-rate-vs-EOH trajectory (Tier-3 calibrate-to-MOR). OEM compressor-wash recovery data would tighten the asymptote."
                 value="τ = 2,000 h · asymptote 2.5% · AQI proxy = 1.0 (no scaling, v1)"
               />} />
          <Row label="TBC coating life (Weibull)"
               value="β = 3 · η = 28,000 h"
               sub="Standard TBC oxidation Weibull fit per F-class coating literature [GER-3620]; not addressed by [Saturday-Isaiah-2018] (creep-only paper) — register §3.5."
               badge="assumed_industry"
               info={<InfoPopover
                 title="TBC_WEIBULL_BETA / TBC_WEIBULL_ETA"
                 status="assumed_industry"
                 source="Standard thermal-barrier-coating oxidation Weibull fit; F-class coating-life literature [GER-3620]. Not addressed by [Saturday-Isaiah-2018] (creep-only paper). Register §3.5."
                 whyV1="Tier-2 cited at framework level. For Lockport's low-CF cogen, tbc_time stays well below η — the TBC channel is sub-threshold (latent)."
                 upgrade="Vendor-specific β/η for the actual coating chemistry used on Lockport's hot section; would replace [GER-3620] defaults with OEM-spec values."
                 value="β = 3 · η = 28,000 h"
               />} />
          <Row label="Creep rate · fatigue per start"
               value="5×10⁻⁶ / h · cold 1×10⁻³ · warm 5×10⁻⁴ · hot 2×10⁻⁴"
               sub="Robinson cumulative-damage proxy ([GER-3620]) + Miner's-rule per-cycle damage. Load × ambient creep coupling has analog evidence in [Saturday-Isaiah-2018] (Larson-Miller, MLRI)."
               badge="assumed_industry"
               info={<InfoPopover
                 title="CREEP_RATE_PER_FIRED_HOUR / FATIGUE_PER_*_START"
                 status="assumed_industry"
                 source="Creep: Robinson cumulative-damage proxy; F-class hot-section creep [GER-3620]. Analog evidence for load × ambient creep coupling in [Saturday-Isaiah-2018] (LM2500+ Cranfield-PYTHIA + Larson-Miller, MLRI 0.2451/°C ambient · 0.1466/% power). Fatigue: Miner's-rule per-cycle damage; F-class fatigue literature [GER-3620]. Register §3.2 / §3.3."
                 whyV1="Tier-2 cited at framework level. Mechanisms wired (creep → P_creep hazard ADR-007; fatigue → df accumulator). Magnitudes are F-class defaults — Phase-L tornado top driver."
                 upgrade="Calibrate creep rate to MOR EOH→MI timing; vendor spec for fatigue-per-cold-start. Re-evaluate against [Saturday-Isaiah-2018] coefficients once heavy-duty correction is bounded — register §3.2 cross-check."
                 value="creep 5×10⁻⁶ /h · fatigue cold 1×10⁻³ /warm 5×10⁻⁴ /hot 2×10⁻⁴"
               />} />
          <Row label="Start C&M cost"
               value="$79 / $55 / $35 per MW (cold / warm / hot)"
               sub="[Kumar2012] Table 1-1 Gas-CC F-class start-mode cost basis (2011 USD)."
               badge="assumed_industry"
               info={<InfoPopover
                 title="START_CM_USD_PER_MW"
                 status="assumed_industry"
                 source="[Kumar2012] Table 1-1 'Gas-CC' start C&M (2011 USD). Drives the start hurdle in dispatch + the wear-fraction (0.42) of start damage attributed to GT-side."
                 whyV1="Tier-2 cited — the most defensible monetary constant in the wear stack. Multiplied by the policy A/B/C wear hurdle to gate marginal starts."
                 upgrade="Escalate 2011 USD to today's dollars (CPI / IHS Markit power-gen escalation index); OEM-specific values from data-room would be Tier-1."
                 value="cold $79 · warm $55 · hot $35 (per MW capacity, 2011 USD)"
               />} />
          <Row label="Trip wear factor"
               value="8 × cold-start equivalent"
               sub="[GER-3620] trip-from-load factored-start convention (ADR-007). Unplanned trip adds 8× the cold-start fatigue increment."
               badge="assumed_industry"
               info={<InfoPopover
                 title="TRIP_MAINTENANCE_FACTOR"
                 status="assumed_industry"
                 source="[GER-3620] trip-from-load factored-start convention — full-load trip ≈ 8 factored starts of hot-section damage. Wired into forced-outage → wear coupling per ADR-007. [Saturday-Isaiah-2018] is creep-only and doesn't constrain this magnitude."
                 whyV1="Tier-2 cited at framework level. For Mode A historical, 7 of 35 forced outages were trips → +1,120 EOH → +$0.24M LTSA reserve. Active and material."
                 upgrade="OEM-specific factored-start data (vendor-specific maintenance manual) would replace the generic 8× with a measured value."
                 value="8.0 × cold-start damage (applies on forced outage from running state)"
               />} />
          <RoadmapRow
            label="Per-asset calibration override"
            preview="Adjust τ, η, creep rate against MOR EOH counters once reconciled"
            why="Requires MOR-vs-engine reconciliation (calibration pass)"
          />
        </ConfigCard>

        {/* 05 — Outage risk */}
        <ConfigCard
          n="05"
          icon={<AlertTriangle className="w-3.5 h-3.5" />}
          title="Outage risk"
          subtitle="Per-day forced-outage probabilities and duration shape."
          colSpan="col-span-12 lg:col-span-6"
        >
          <Row label="HRSG forced-outage probability"
               value="0.75% / day"
               sub="Per-unit independent draw — industry CCGT HRSG baseline. Cross-check vs [NERC-GADS] Class CC."
               badge="assumed_industry"
               info={<InfoPopover
                 title="HRSG_BASE_PROB_PER_DAY"
                 status="assumed_industry"
                 source="Industry CCGT HRSG forced-outage baseline. Cross-check to [NERC-GADS] Class CC availability statistics. Register §3.8."
                 whyV1="Dominant outage driver for low-CF Lockport (HRSG/BG events outnumber GT mechanical events). Phase-L tornado co-dominant with BG."
                 upgrade="Tier-3 calibrate: tune to MOR-observed EFOR + [NERC-GADS] class CC distribution. Asset-specific baseline from GADS would replace the industry default."
                 value="0.0075 per day · age-multiplied up to 1.5× over plant life"
               />} />
          <Row label="BG (balance-of-plant) probability"
               value="0.40% / day"
               sub="Per-unit independent draw — [NERC-GADS] Class CC balance-of-plant baseline."
               badge="assumed_industry"
               info={<InfoPopover
                 title="BG_BASE_PROB_PER_DAY"
                 status="assumed_industry"
                 source="Balance-of-plant forced-outage baseline; [NERC-GADS] Class CC. Register §3.9."
                 whyV1="Co-dominant with HRSG for low-CF Lockport outage profile. Aging multiplier (BG_AGE_MULT_MAX = 1.5×) is a separate Phase-L tornado #1 driver."
                 upgrade="Same as HRSG: tune to MOR + [NERC-GADS]. Aging-multiplier curve is NOT addressed by [Saturday-Isaiah-2018] (creep-only); needs separate literature — register §3.10."
                 value="0.0040 per day · age-multiplied up to 1.5× over plant life"
               />} />
          <Row label="Outage duration"
               value="Lognormal · σ = 0.5"
               sub="Median centered on event class — GT 8d / HRSG 12d / BG 5d; σ fixed across classes."
               badge="modeling_convention"
               info={<InfoPopover
                 title="OUTAGE_DURATION_DAYS / SIGMA"
                 status="modeling_convention"
                 source="Athens-prototype lognormal medians: gt 8d, hrsg 12d, bg 5d. σ = 0.5 is a standard repair-time spread convention. Register §4.3."
                 whyV1="Captures the right shape (long-tail risk) without overfitting. Medians are class-typical, not asset-specific."
                 upgrade="Tier-3 calibrate medians + σ to MOR-observed outage durations once available; [NERC-GADS] Class CC distribution would tighten the σ assumption."
                 value="gt median 8 d · hrsg 12 d · bg 5 d · σ 0.5 (lognormal)"
               />} />
          <Row label="Trip → wear coupling"
               value="8× cold-start fatigue"
               sub="[GER-3620] trip-from-load factor — mirrors the Wear card; same constant, two faces."
               badge="assumed_industry"
               info={<InfoPopover
                 title="TRIP_MAINTENANCE_FACTOR (here: outage face)"
                 status="assumed_industry"
                 source="[GER-3620] trip-from-load factored-start convention (ADR-007). Wired in two places: outage event (here) adds 8× cold-start fatigue + EOH at the moment of trip; wear card lists the same constant from the wear side."
                 whyV1="ADR-007 closed the gap where forced outages from a running state were free of wear cost. For Mode A: 7 trips of 35 forced outages → +1,120 EOH, +$0.24M LTSA. Active channel."
                 upgrade="OEM-specific factored-start data; same upgrade path as the Wear-card row."
                 value="8.0 × cold-start damage on trip-from-load"
               />} />
          <RoadmapRow
            label="Forced-outage cost override"
            preview="Per-event $/MWh penalty separate from lost revenue"
            why="Pending insurance / parametric overlay design"
          />
        </ConfigCard>

        {/* 06 — Contract / LTSA */}
        <ConfigCard
          n="06"
          icon={<FileSignature className="w-3.5 h-3.5" />}
          title="Contract & LTSA"
          subtitle="Long-term service agreement terms feeding the L3 ledger."
          colSpan="col-span-12 lg:col-span-6"
        >
          <Row label="Fixed monthly fee"
               value="$850,000 / month"
               sub={`Modeled as $${c.LTSA_FIXED_DAILY.toFixed(0)} / day = $${(c.LTSA_FIXED_DAILY * 365 / 1e6).toFixed(2)}M / yr`}
               badge="placeholder"
               info={<InfoPopover
                 title="LTSA fixed fee"
                 status={reg.ltsa_deeper.status}
                 source={reg.ltsa_deeper.source}
                 whyV1={reg.ltsa_deeper.why_v1}
                 upgrade={reg.ltsa_deeper.upgrade}
                 value="$850k / mo · Athens-prototype value"
               />} />
          <Row label="EOH-banked reserve"
               value={`$${c.LTSA_EOH_RESERVE_USD_PER_EOH.toFixed(0)} / EOH`}
               sub="Accrued hourly; drawn against CI and MI events. Athens-prototype default."
               badge="placeholder"
               info={<InfoPopover
                 title="EOH reserve rate"
                 status="placeholder"
                 source="Athens-prototype LTSA term ($175 / EOH). Accrues per-fired-hour and is drawn against CI/MI event costs. Register §4.4."
                 whyV1="Structurally correct (one of 7 LTSA streams); the magnitude is placeholder. Phase-L tornado: meaningful relative to fuel + fixed fee."
                 upgrade="Tier-1 measured from data-room: actual contract EOH reserve $/EOH from the executed LTSA + amendments (PURPA-era contract)."
                 value="$175 per EOH · 3.5%/yr escalation"
               />} />
          <Row label="CI event"
               value="12 days · $3.75M total / $937k owner"
               sub="OEM coverage 75% · CI threshold 24,000 EOH. Athens-prototype default."
               badge="placeholder"
               info={<InfoPopover
                 title="Combustion Inspection (CI)"
                 status="placeholder"
                 source="Athens-prototype LTSA: $3.75M total, OEM-covered 75%, 12-day outage. CI threshold 24k EOH from [GER-3620] convention. Register §3.14 / §4.4."
                 whyV1="Structurally correct. OEM coverage fraction is the dominant lever on owner-uncovered cost. Currently NOT firing in the 9-yr historical (EOH headroom math)."
                 upgrade="Real Lockport LTSA: $ total + OEM-covered fraction + actual outage duration. Likely Tier-1 within v2."
                 value="duration 12 d · $3.75M total · OEM 75% · owner $937k"
               />} />
          <Row label="MI event"
               value="52 days · $30M total / $10.5M owner"
               sub="OEM coverage 65% · MI threshold 48,000 EOH. Largest single LTSA event — #1 v2 priority."
               badge="placeholder"
               info={<InfoPopover
                 title="Major Inspection (MI)"
                 status="placeholder"
                 source="Athens-prototype LTSA: $30M total, OEM-covered 65%, 52-day outage. MI threshold 48k EOH from [GER-3620]. Register §3.15 / §3.16 / §4.4 — single largest LTSA stream."
                 whyV1="Phase-L tornado: highest-impact LTSA constant. Mode A historical incurred the MI in 2025; B/C deferred. ~$10.5M owner cost is the gap between A and B/C historical Net P&L."
                 upgrade="Tier-1 measured: contract MI cost + OEM-covered fraction. Gap #1 in gaps_and_priorities — replacing this placeholder alone moves Net by +$5–9M/yr."
                 value="duration 52 d · $30M total · OEM 65% · owner $10.5M"
               />} />
          <Row label="Availability guarantee"
               value="95% annual"
               sub="HR tolerance ±2% — both Athens-prototype defaults"
               badge="placeholder"
               info={<InfoPopover
                 title="Availability + heat-rate guarantee"
                 status="placeholder"
                 source="Athens-prototype LTSA: 95% annual availability guarantee + 2% HR tolerance. Penalty stream wired (monthly_fee/12 × shortfall × 10). Register §4.4."
                 whyV1="Structurally correct; magnitudes are placeholder. Penalty rarely fires in v1 because modeled availability ≈ 95%."
                 upgrade="Tier-1 from data-room: actual guarantee % + tolerance + penalty formula from contract."
                 value="95% availability · ±2% HR tolerance"
               />} />
          <RoadmapRow
            label="Data-room contract terms"
            preview="Replace every placeholder above with the executed LTSA schedule"
            why="Requires data-room access · highest-leverage v2 upgrade"
          />
        </ConfigCard>

        {/* 07 — Revenue modules */}
        <ConfigCard
          n="07"
          icon={<Coins className="w-3.5 h-3.5" />}
          title="Revenue modules"
          subtitle="Which dollar streams are switched on for the showcase."
          colSpan="col-span-12 lg:col-span-12"
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <ModuleTile
              status="active"
              title="Energy"
              body="NYISO Zone A LBMP × dispatched MWh, less fuel × heat rate × MMBtu, less VOM."
              note="The full showcase P&L runs on this module."
              badge="real_observed"
            />
            <ModuleTile
              status="roadmap"
              title="Capacity"
              termKey="capacity_revenue"
              body="NYISO ICAP Zone A pricing × DMNC-derated MW × locational capability factor."
              note={reg.capacity_revenue.why_v1}
              badge={reg.capacity_revenue.status}
              info={<InfoPopover
                title="Capacity revenue"
                status={reg.capacity_revenue.status}
                source={reg.capacity_revenue.source}
                whyV1={reg.capacity_revenue.why_v1}
                upgrade={reg.capacity_revenue.upgrade}
              />}
            />
            <ModuleTile
              status="roadmap"
              title="Steam"
              termKey="steam_revenue"
              body="Host-contract steam offtake × delivered MMBtu (cogen duty qualified)."
              note={reg.steam_revenue.why_v1}
              badge={reg.steam_revenue.status}
              info={<InfoPopover
                title="Steam revenue"
                status={reg.steam_revenue.status}
                source={reg.steam_revenue.source}
                whyV1={reg.steam_revenue.why_v1}
                upgrade={reg.steam_revenue.upgrade}
              />}
            />
          </div>
        </ConfigCard>
      </div>

    </section>
  );
}

function ConfigCard({
  n,
  icon,
  title,
  subtitle,
  colSpan,
  children,
}: {
  n: string;
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  colSpan: string;
  children: React.ReactNode;
}) {
  return (
    <article className={`${colSpan} panel overflow-hidden`}>
      <div className="px-5 py-3 border-b border-card-border flex items-start justify-between gap-3 bg-secondary/20">
        <div className="flex items-center gap-2.5 min-w-0">
          <span className="w-6 h-6 rounded border border-card-border bg-card flex items-center justify-center text-primary shrink-0">
            {icon}
          </span>
          <div className="min-w-0">
            <p className="text-[13px] font-medium tracking-tight leading-tight">{title}</p>
            <p className="text-[11px] text-muted-foreground leading-tight mt-0.5">{subtitle}</p>
          </div>
        </div>
        <span className="font-mono text-[10px] text-muted-foreground/70 shrink-0 pt-0.5">{n}</span>
      </div>
      <div className="p-4 space-y-3">{children}</div>
    </article>
  );
}

function Row({
  label,
  value,
  sub,
  badge,
  active,
  info,
  termKey,
}: {
  label: string;
  value: string;
  sub?: string;
  badge?: string;
  active?: boolean;
  info?: React.ReactNode;
  termKey?: keyof typeof TERMS;
}) {
  // Parse [KEY] markers in sub through the shared references map so citations
  // (e.g. [GER-3620], [Kumar2012], [Saturday-Isaiah-2018]) become clickable
  // links to the underlying paper / spec.
  const refs = useContext(ReferencesContext);
  return (
    <div className="flex items-start gap-3 py-1.5 border-b border-card-border/60 last:border-b-0">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 mb-0.5">
          <p className="text-[11px] uppercase tracking-[0.08em] font-medium text-foreground/80">{label}</p>
          {termKey && <TermInfo termKey={termKey} side="top" />}
          {active && (
            <span className="inline-flex items-center gap-1 text-[9.5px] uppercase tracking-[0.14em] text-primary font-medium">
              <span className="w-1.5 h-1.5 rounded-full signal-dot" />
              live
            </span>
          )}
          {info}
        </div>
        <p className="num-pro text-[13px] text-foreground leading-tight">{value}</p>
        {sub && <p className="text-[11px] text-muted-foreground mt-1 leading-snug">{renderCitations(sub, refs)}</p>}
      </div>
      {badge && (
        <div className="shrink-0 pt-0.5">
          <StatusBadge status={badge} size="xs" />
        </div>
      )}
    </div>
  );
}

function RoadmapRow({
  label,
  preview,
  why,
  termKeys,
}: {
  label: string;
  preview: string;
  why: string;
  termKeys?: (keyof typeof TERMS)[];
}) {
  return (
    <div
      className="control-disabled rounded-md px-3 py-2.5 flex items-start gap-3 mt-1"
      aria-disabled="true"
      role="group"
      aria-label={`Roadmap: ${label}`}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <p className="text-[11px] uppercase tracking-[0.08em] font-medium text-foreground/70">{label}</p>
          {termKeys?.map((k) => (
            <TermInfo key={k as string} termKey={k} size="xs" side="top" />
          ))}
          <span className="text-[9px] uppercase tracking-[0.18em] font-semibold text-muted-foreground border border-card-border bg-card/70 px-1.5 py-[1px] rounded">
            roadmap
          </span>
        </div>
        <p className="text-[11.5px] text-foreground/70 leading-snug">{preview}</p>
        <p className="text-[10.5px] text-muted-foreground mt-1 leading-snug italic">{why}</p>
      </div>
    </div>
  );
}

function ModuleTile({
  status,
  title,
  body,
  note,
  badge,
  info,
  termKey,
}: {
  status: "active" | "roadmap";
  title: string;
  body: string;
  note: string;
  badge: string;
  info?: React.ReactNode;
  termKey?: keyof typeof TERMS;
}) {
  const isActive = status === "active";
  return (
    <div className={`${isActive ? "card-clean p-4" : "control-disabled rounded-md p-4"}`}>
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <p className="text-[12.5px] font-medium tracking-tight">{title}</p>
          {termKey && <TermInfo termKey={termKey} side="top" />}
          {isActive && (
            <span className="inline-flex items-center gap-1 text-[9.5px] uppercase tracking-[0.14em] text-primary font-medium">
              <span className="w-1.5 h-1.5 rounded-full signal-dot" />
              live
            </span>
          )}
          {!isActive && (
            <span className="text-[9px] uppercase tracking-[0.18em] font-semibold text-muted-foreground border border-card-border bg-card/70 px-1.5 py-[1px] rounded">
              roadmap
            </span>
          )}
          {info}
        </div>
        <StatusBadge status={badge} size="xs" />
      </div>
      <p className="text-[12px] text-foreground/80 leading-snug mb-2">{body}</p>
      <p className="text-[10.5px] text-muted-foreground italic leading-snug">{note}</p>
    </div>
  );
}
