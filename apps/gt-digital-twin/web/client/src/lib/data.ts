// Precomputed engine data types and loader

export type Quantile = { P10: number; P50: number; P90: number; mean: number };

export interface PerPath {
  path_id: number;
  window: string;
  probability: number;
  spark_margin_usd: number;
  ltsa_owner_usd: number;
  net_pl_usd: number;
  total_mwh: number;
  fired_hours: number;
}

export interface GridCell {
  per_path: PerPath[];
  quantiles: {
    net_pl_usd: Quantile;
    spark_margin_usd: Quantile;
    ltsa_owner_usd: Quantile;
    total_mwh: Quantile;
    fired_hours: Quantile;
  };
  p50_path: PerPath;
  knobs: { policy: string; gas_mult: number; init_state: string };
}

export interface PnlDecomposition {
  gross_revenue: number;
  fuel_cost: number;       // negative
  vom_cost: number;        // negative
  wear_penalty_internal: number;
  ltsa_fixed_fee: number;  // negative
  ltsa_eoh_reserve: number;
  ltsa_inspections: number;
  ltsa_other: number;
  net_pl: number;
  total_mwh: number;
  fired_hours: number;
}

export interface SensitivityRank {
  knob: string;
  delta_p50_low: number;
  delta_p50_high: number;
  rationale: string;
  status: string;
  source: string;
  abs_max: number;
}

export interface CalibrationEntry {
  status: string;
  source: string;
  why_v1: string;
  upgrade: string;
}

/** External reference (e.g. GER-3620, Saturday-Isaiah-2018) from §9 of the
 *  calibration register. Keyed by the citation tag used inline in `source` /
 *  `upgrade` text via `[KEY]` brackets. */
export interface Reference {
  title: string;
  url: string;
}

export interface Precomputed {
  generated_at: string;
  engine_version: string;
  basis: string;
  n_scenarios: number;
  modes: string[];
  gas_multipliers: number[];
  init_presets: string[];
  aged_state_summary: Record<string, { eoh: number; rotor_life: number; insp_done: number }>;
  historical_decomp: Record<string, PnlDecomposition>;
  grid: Record<string, GridCell>;
  sensitivity_ranks: SensitivityRank[];
  scenarios_meta: { path_id: number; window: string; probability: number }[];
  constants: Record<string, number>;
  calibration_register: Record<string, CalibrationEntry>;
  /** §9 references from the calibration register, keyed by citation tag.
   *  Optional for back-compat with pre-references precomputed.json files. */
  references?: Record<string, Reference>;
}

// Format gas multiplier to match Python's str(float) semantics for JSON keys.
// Python: str(1.0) -> '1.0', str(0.75) -> '0.75', str(1.25) -> '1.25'.
// JS:     `${1.0}` -> '1'   ← this is the bug.
export function fmtGasMult(g: number): string {
  // If integer-valued, force one decimal place. Otherwise let toString handle it.
  return Number.isInteger(g) ? g.toFixed(1) : String(g);
}

export function keyFor(policy: string, gasMult: number, initState: string) {
  return `${policy}|gas${fmtGasMult(gasMult)}|${initState}`;
}

export function fmtMoneyM(usd: number, digits = 2): string {
  const m = usd / 1e6;
  const sign = m < 0 ? "−" : "";
  return `${sign}$${Math.abs(m).toFixed(digits)}M`;
}

export function fmtNumber(n: number, digits = 0): string {
  return n.toLocaleString("en-US", { maximumFractionDigits: digits, minimumFractionDigits: digits });
}

export function fmtPct(n: number, digits = 0): string {
  return `${(n * 100).toFixed(digits)}%`;
}

// ---------- v1.3 real monthly forecast panel (Section 01) ----------
// Every array below is derived from real run_forward(..., return_paths=True)
// per-path daily series, aggregated to monthly Apr->Mar using the SAME logic
// as notebooks/06_forward_scenarios.py §5. There is no illustrative shape.

export interface Envelope {
  P10: number[];
  P50: number[];
  P90: number[];
}

export interface CdfPoint {
  x: number;
  F: number;
  window: string;
  path_id: number;
}

export interface TemperatureDailyEnsemble {
  dates: string[];        // ISO date strings (one per SEAS5 day)
  P10: number[];
  P50: number[];
  P90: number[];
  n_members: number;
  source_file: string;
}

export interface MonthlyForecastGridCell {
  // Length-12 arrays in Apr->Mar order (notebook 06 MONTH_ORDER).
  lmp_usd_per_mwh_monthly_mean: Envelope;
  henry_hub_usd_per_mmbtu_monthly_mean: Envelope;
  generation_mwh_monthly_sum: Envelope;
  gross_margin_usd_monthly_sum: Envelope;
  net_pl_cdf: CdfPoint[];
  knobs: { policy: string; gas_mult: number; init_state: string };
}

export interface MonthlyForecastPanel {
  schema_version: string;
  generated_at: string;
  basis: string;
  seed: number;
  n_scenarios: number;
  seas5_init: string;
  month_labels: string[];     // length 12, Apr..Mar
  month_order: number[];      // [4,5,...,12,1,2,3]
  provenance: {
    engine: string;
    forward: string;
    weighted_quantile: string;
    weights: string;
    aggregation: Record<string, string>;
    notebook_mirror: string;
  };
  temperature_f_daily: TemperatureDailyEnsemble;
  grid: Record<string, MonthlyForecastGridCell>;
}
