import { HelpCircle } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

/**
 * TermInfo — lightweight definition popover for domain terms.
 *
 * Lighter sibling of InfoPopover. InfoPopover carries full provenance
 * (status badge + source + why-v1 + upgrade path) for *assumptions*.
 * TermInfo carries only a definition + how it's used in the dashboard,
 * so explanatory tooltips for things like "Gross margin", "EOH", or
 * "P50" don't clutter the UI with status chrome.
 *
 * Style: small circular question mark icon, subtle muted color, hover/
 * focus reveals the primary tint. Keyboard focusable; aria-label
 * describes the term.
 */

export interface TermDef {
  /** Display name, e.g. "Gross margin" */
  term: string;
  /** One-sentence definition. */
  definition: string;
  /** Optional formula or short example, monospaced. */
  formula?: string;
  /** Optional: how this term is used in *this* dashboard. */
  usage?: string;
}

/**
 * Centralized term glossary. Keep wording short; one definition + one
 * usage sentence is the target. Formula is optional and stays simple.
 */
export const TERMS: Record<string, TermDef> = {
  // ── Revenue / margin layers ────────────────────────────────────────
  gross_margin: {
    term: "Gross margin",
    definition:
      "Energy revenue minus fuel cost and variable O&M, before any LTSA, inspection, or owner-cost layers.",
    formula: "Gross margin = LMP × MWh − fuel × heat rate × MMBtu − VOM × MWh",
    usage:
      "Monthly sums shown in the forecast panel; rolls up into spark margin and then net P&L.",
  },
  spark_margin: {
    term: "Spark margin",
    definition:
      "Energy revenue minus fuel and variable operating costs — the engine's pre-LTSA contribution margin.",
    formula: "Spark margin = energy revenue − fuel − VOM",
    usage:
      "Equivalent to gross margin here; deducting LTSA / EOH / inspection costs from spark gives net P&L.",
  },
  net_pl: {
    term: "Net P&L",
    definition:
      "Spark margin less the full LTSA owner-cost stack (fixed fee, EOH reserve, inspections, other).",
    formula: "Net P&L = spark margin − LTSA owner cost",
    usage:
      "The dashboard's headline outcome. Energy-only basis — capacity and steam revenue are excluded by design.",
  },
  ltsa_owner: {
    term: "LTSA owner cost",
    definition:
      "Total long-term service agreement cost borne by the asset owner across a path: fixed daily fee, EOH-banked reserve accrual, and inspection draws.",
    formula:
      "LTSA owner = fixed fee + EOH reserve accrual + CI/MI inspections + other",
    usage:
      "Subtracted from spark margin to produce net P&L. Modeled with placeholder rates pending the executed schedule.",
  },
  energy_only: {
    term: "Energy-only basis",
    definition:
      "Outputs reflect energy market revenue and cost streams only — capacity payments and steam-host revenue are intentionally excluded.",
    usage:
      "Keeps the engine's wear / dispatch mechanics legible without entangling host-contract or ICAP assumptions.",
  },

  // ── Quantiles & distribution ──────────────────────────────────────
  p_quantiles: {
    term: "P10 · P50 · P90",
    definition:
      "Probability quantiles across the SEAS5-conditioned analog ensemble: P50 is the probability-weighted median; P10 / P90 bound the central 80%.",
    usage:
      "Every forward metric is shown as a P10–P90 envelope plus P50 point — never a single number.",
  },
  cdf: {
    term: "Net P&L CDF",
    definition:
      "Cumulative distribution function of annual net P&L across the analog ensemble — Pr(Net P&L ≤ x) on the y-axis.",
    usage:
      "Lets you read tail probabilities directly: where the curve crosses zero is Pr(negative year).",
  },

  // ── Physical / engineering counters ───────────────────────────────
  generation_mwh: {
    term: "Generation (MWh)",
    definition:
      "Megawatt-hours of electricity produced. Engine output uses degraded capacity (mwh_degraded) reflecting current rotor and fouling state.",
    usage:
      "Monthly sums in the forecast panel; annual totals in the KPI strip. Drives revenue and fuel burn.",
  },
  fired_hours: {
    term: "Fired hours",
    definition:
      "Hours the unit is online and producing — used as the volumetric basis for LTSA fixed-fee accrual and wear counters.",
    usage:
      "Aged-state windows start with non-zero fired-hour totals; fresh windows start from zero.",
  },
  eoh: {
    term: "Equivalent operating hours (EOH)",
    definition:
      "Wear counter that scales fired hours by stress factors (starts, ramps, peak firing) to estimate hot-section life consumption.",
    formula: "EOH ≈ fired hours + start penalties + load-factor penalties",
    usage:
      "CI (combustion inspection) triggers near 24,000 EOH; MI (major inspection) near 48,000 EOH.",
  },
  rotor_life: {
    term: "Rotor life",
    definition:
      "Remaining hot-section rotor life expressed as a percentage. Depletes with fired hours and stress; CI restores ~25%, MI restores 100%.",
    usage:
      "Aged-state initial conditions carry per-mode rotor life from the historical replay end-state.",
  },

  // ── Market / fuel inputs ──────────────────────────────────────────
  seas5: {
    term: "SEAS5",
    definition:
      "ECMWF's Seasonal Forecast System 5 — a ~25-member ensemble of seasonal weather forecasts used to condition the analog ensemble.",
    usage:
      "Daily temperature P10/P50/P90 are the SEAS5 ensemble directly. Each historical analog window is scored against the current SEAS5 forecast and softmaxed into a probability weight.",
  },
  analog_scenarios: {
    term: "Analog scenarios",
    definition:
      "25 historical Apr→Mar reanalysis windows (1999–2026) that serve as the forward sampling set. Each window contributes weather, LMP, and gas paths.",
    usage:
      "Each window receives a SEAS5-conditioned probability weight; outputs are weighted-quantile aggregates across the ensemble.",
  },
  henry_hub: {
    term: "Henry Hub gas",
    definition:
      "Henry Hub natural gas spot price — the U.S. benchmark used as the fuel-cost reference for this run.",
    usage:
      "Per-path daily Henry Hub from each analog window, multiplied by the user-selected gas multiplier; basis differentials (Iroquois / TGP) are not yet overlaid.",
  },
  lmp: {
    term: "LMP",
    definition:
      "Locational Marginal Price — NYISO Zone A LBMP, the wholesale electricity price the asset sells into.",
    usage:
      "Per-path daily LMP feeds dispatch decisions and energy revenue. Forecast panel shows monthly mean of daily LMP.",
  },
  rt_basis: {
    term: "RT basis",
    definition:
      "Real-time settlement — dispatch and revenue use 5-minute real-time LMP rather than day-ahead clearing prices.",
    usage:
      "Fixed at RT for v1. Day-ahead basis is wired in the engine but not surfaced in this preview.",
  },

  // ── Policy / state controls ───────────────────────────────────────
  policy_abc: {
    term: "Dispatch policy (A / B / C)",
    definition:
      "Three commit/dispatch postures that differ only in the wear hurdle applied to spark margin before committing.",
    formula:
      "A: 1.0× wear hurdle (myopic merchant)\nB: clamps at 2.5× (NPV-rational)\nC: ramps to 4.0× (risk-averse)",
    usage:
      "Same physics and prices across all three — only the hurdle changes — so differences isolate the policy effect on net P&L.",
  },
  initial_state: {
    term: "Initial state (aged vs fresh)",
    definition:
      "Where the forward run starts on the wear / EOH counters.",
    formula:
      "aged: each mode's historical end-state\nfresh: EOH = 24,000 modeling default",
    usage:
      "Aged isolates the carry-in effect of the 2017–2025 replay; fresh provides a clean comparison baseline.",
  },

  // ── Disabled / deferred modules ───────────────────────────────────
  capacity_revenue: {
    term: "Capacity revenue (disabled)",
    definition:
      "NYISO ICAP capacity-market payments based on unforced-capacity obligations.",
    usage:
      "Excluded from v1 net P&L — the dashboard is energy-only. Will be added once capacity terms are sourced.",
  },
  steam_revenue: {
    term: "Steam revenue (disabled)",
    definition:
      "Host-contract steam offtake revenue tied to cogeneration qualification.",
    usage:
      "Excluded from v1 net P&L. Host contract not yet modeled.",
  },
};

interface TermInfoProps {
  /** Key into TERMS, or an inline definition object. */
  termKey?: keyof typeof TERMS;
  /** Inline term override (for cases not in the central map). */
  def?: TermDef;
  /** Popover side. Default: top. */
  side?: "top" | "right" | "bottom" | "left";
  /** Popover align. Default: start. */
  align?: "start" | "center" | "end";
  /** Visual size: sm (12px icon, default) or xs (10px). */
  size?: "sm" | "xs";
  /** Optional className override. */
  className?: string;
}

export function TermInfo({
  termKey,
  def,
  side = "top",
  align = "start",
  size = "sm",
  className,
}: TermInfoProps) {
  const t = def ?? (termKey ? TERMS[termKey] : undefined);
  if (!t) return null;
  const iconSize = size === "xs" ? "w-2.5 h-2.5" : "w-3 h-3";
  const btnSize = size === "xs" ? "w-3.5 h-3.5" : "w-4 h-4";

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          aria-label={`What is ${t.term}?`}
          className={`inline-flex items-center justify-center ${btnSize} rounded-full text-muted-foreground/55 hover:text-primary hover:bg-accent focus-visible:text-primary focus-visible:bg-accent focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary/40 transition-colors align-middle ${
            className ?? ""
          }`}
          data-testid={`term-${t.term.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`}
        >
          <HelpCircle className={iconSize} strokeWidth={2} />
        </button>
      </PopoverTrigger>
      <PopoverContent
        side={side}
        align={align}
        className="w-[300px] text-xs leading-relaxed p-0 border border-popover-border"
      >
        <div className="px-4 pt-3.5 pb-2.5 border-b border-card-border">
          <p className="text-[12.5px] font-medium tracking-tight">{t.term}</p>
        </div>
        <div className="px-4 py-3 space-y-2.5">
          <p className="text-[11.5px] text-foreground/90 leading-[1.55]">
            {t.definition}
          </p>
          {t.formula && (
            <pre className="text-[10.5px] font-mono text-foreground/85 bg-secondary/40 border border-card-border rounded px-2 py-1.5 leading-[1.5] whitespace-pre-wrap">
              {t.formula}
            </pre>
          )}
          {t.usage && (
            <div>
              <p className="eyebrow mb-0.5 text-[9.5px]">In this dashboard</p>
              <p className="text-[11px] text-muted-foreground leading-[1.55]">
                {t.usage}
              </p>
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}
