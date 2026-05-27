# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
# ---

# %% [markdown]
# # Notebook 6 — Forward Scenarios (Stream A / Phase 6, v1)
#
# Turns the v1 historical-replay model into a **forward, SEAS5-conditioned, scenario-based
# valuation**. The engine is `src/gt_engine`; the scenario logic is `src/forward`
# (select -> build -> run). See [`docs/plans/forward_engine_plan.md`](../docs/plans/forward_engine_plan.md)
# and [`docs/methodology/flowcharts.md`](../docs/methodology/flowcharts.md).
#
# **v1 scope**: RT basis (~25 analog windows, 1999-2026, multi gas-regime), raw historical
# price levels (no forward-curve anchoring), temperature-only conditioning, scenario-driven
# spread at a fixed seed. Set `BASIS = "DA"` for the recent-only (~8 window) comparison.
# **Remaining follow-ups**: forward-price anchoring; outage-RNG Monte Carlo; behavioral output (#3).
#
# > ⚠️ Like the historical model, absolute Net P&L is **not representative** (energy-only
# > revenue + placeholder Athens LTSA). The deliverable here is the *working forward
# > distribution* + the *scenario spread*, not the level.

# %%
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path("..").resolve() / "src"))

from forward.select import select
from forward.run import run_forward

MODE = "A"
BASIS = "RT"   # RT -> ~25 windows (1999-2026, multi gas-regime); DA -> ~8 (2017+). Plan §6.

# %% [markdown]
# ## 1. The conditioning signal (SEAS5 temperature anomaly)
# Apr-Oct have >=80% SEAS5 coverage and drive the analog score; other months are neutral.

# %%
sel = select(basis=BASIS)
print(f"SEAS5 init: {sel.seas5_init}   valid months: {sel.valid_months}")
print(sel.month_scores[["month", "coverage", "forecast_mean_c", "mu_c", "z_s2s",
                        "used_for_weighting"]].to_string(index=False))
print("\nWindow probabilities:")
print(sel.window_weights.to_string(index=False))

# %% [markdown]
# ## 2. Run the forward ensemble + probability-weighted P10/P50/P90

# %%
res = run_forward(MODE, seed=42, basis=BASIS, save=True, return_paths=True)
pp = res["per_path"].sort_values("net_pl_usd").reset_index(drop=True)
q = res["quantiles"]["net_pl_usd"]
out_dir = Path(res["out_dir"])

print("Per-scenario 1-year economics ($M):")
disp = pp.copy()
for c in ["spark_margin_usd", "ltsa_owner_usd", "net_pl_usd"]:
    disp[c] = (disp[c] / 1e6).round(2)
print(disp[["source_window_id", "probability", "spark_margin_usd",
            "ltsa_owner_usd", "net_pl_usd", "fired_hours"]].to_string(index=False))
print(f"\nNet P&L distribution ($M): P10={q['P10']/1e6:.2f}  P50={q['P50']/1e6:.2f}  "
      f"P90={q['P90']/1e6:.2f}  mean={q['prob_weighted_mean']/1e6:.2f}")

# %% [markdown]
# ## 3. Charts — conditioning, probabilities, scenario P&L, distribution

# %%
fig, ax = plt.subplots(2, 2, figsize=(13, 9))

# (a) SEAS5 monthly temperature anomaly (the conditioning signal)
ms = sel.month_scores
colors = ["#cccccc" if not u else ("#c0392b" if z > 0 else "#2980b9")
          for z, u in zip(ms["z_s2s"], ms["used_for_weighting"])]
ax[0, 0].bar(ms["month"], ms["z_s2s"], color=colors)
ax[0, 0].axhline(0, color="k", lw=0.8)
ax[0, 0].set_title("SEAS5 temperature anomaly by month (z vs climatology)\ngray = not used (low coverage)")
ax[0, 0].set_xlabel("month"); ax[0, 0].set_ylabel("z_s2s  (warm > 0)")

# (b) Window selection probabilities
ww = sel.window_weights.sort_values("probability")
ax[0, 1].barh(ww["window_id"], ww["probability"], color="#16a085")
ax[0, 1].set_title("Analog window probabilities\n(closest temperature analog = highest)")
ax[0, 1].set_xlabel("probability")

# (c) Per-scenario Net P&L (sorted), bar width ~ probability
ax[1, 0].bar(pp["source_window_id"], pp["net_pl_usd"] / 1e6,
             color=["#27ae60" if v > 0 else "#c0392b" for v in pp["net_pl_usd"]])
ax[1, 0].axhline(0, color="k", lw=0.8)
ax[1, 0].set_title("Net P&L by analog scenario ($M)")
ax[1, 0].set_xlabel("analog window"); ax[1, 0].set_ylabel("Net P&L ($M)")
ax[1, 0].tick_params(axis="x", rotation=45)

# (d) Probability-weighted distribution (weighted CDF + P10/P50/P90)
vals = pp["net_pl_usd"].values / 1e6
wts = pp["probability"].values
cum = (np.cumsum(wts) - 0.5 * wts) / wts.sum()
ax[1, 1].step(vals, cum, where="mid", color="#2c3e50", marker="o")
for label, qq, col in [("P10", q["P10"], "#e67e22"), ("P50", q["P50"], "#2980b9"),
                       ("P90", q["P90"], "#27ae60")]:
    ax[1, 1].axvline(qq / 1e6, color=col, ls="--", label=f"{label} {qq/1e6:.1f}")
ax[1, 1].set_title("Probability-weighted Net P&L distribution")
ax[1, 1].set_xlabel("Net P&L ($M)"); ax[1, 1].set_ylabel("cumulative probability")
ax[1, 1].legend(fontsize=8)

fig.suptitle(f"Lockport forward scenarios — Mode {MODE}, {BASIS}, raw levels "
             f"(SEAS5 {sel.seas5_init[:10]}, {len(pp)} analog years)", fontsize=12)
fig.tight_layout()
fig.savefig(out_dir / "forward_summary.png", dpi=110, bbox_inches="tight")
print(f"Saved charts -> {out_dir / 'forward_summary.png'}")

# %% [markdown]
# ## 4. Forward model card

# %%
def _fmt(v):
    return f"{v/1e6:+.2f}"

card = f"""# Forward Model Card — Lockport (Mode {MODE}, v1)

- **Generated**: {out_dir.name}
- **SEAS5 forecast init**: {sel.seas5_init}  |  **conditioning months**: {sel.valid_months} (Apr-Oct)
- **Basis**: {BASIS}  |  **Anchoring**: raw historical levels  |  **Paths**: {len(pp)} analog Apr-Mar windows
- **Seed**: 42 (scenario-driven spread; outage-RNG Monte Carlo is a later layer)

## Probability-weighted Net P&L ($M)

| P10 | P50 | P90 | prob-weighted mean |
|---:|---:|---:|---:|
| {_fmt(q['P10'])} | {_fmt(q['P50'])} | {_fmt(q['P90'])} | {_fmt(q['prob_weighted_mean'])} |

## Per-scenario (analog year) 1-year economics ($M)

| Analog window | Prob | Spark | LTSA | Net P&L | Fired hrs |
|---|---:|---:|---:|---:|---:|
""" + "\n".join(
    f"| {r.source_window_id} | {r.probability:.3f} | {r.spark_margin_usd/1e6:.2f} | "
    f"{r.ltsa_owner_usd/1e6:.2f} | {r.net_pl_usd/1e6:.2f} | {r.fired_hours} |"
    for r in pp.itertuples(index=False)
) + f"""

## Caveats (v1)

- **Not representative absolute level**: energy-only revenue + placeholder Athens LTSA
  (no capacity / steam / ancillary). Inherited from the historical model; closing the
  revenue-stack gaps is what makes the level real.
- **Scenario-driven spread, fixed seed** — reflects *which future* (price/gas/weather
  analog), not outage-draw noise.
- **Pool**: {len(pp)} analog windows. RT (1999-2026) spans multiple gas regimes and
  captures high-gas-year downside (2005-2009) that a DA-only 2017+ pool excludes.
- **Fresh-state 1-yr runs** — start from the v1 initial state, not the current 2026 plant
  state (a documented simplification).

See [`docs/plans/forward_engine_plan.md`](../../../../docs/plans/forward_engine_plan.md).
"""
(out_dir / "forward_model_card.md").write_text(card)
print(card)
print(f"\nSaved -> {out_dir / 'forward_model_card.md'}")

# %% [markdown]
# ## 5. Forecast trajectories — what we're projecting
# The charts above show the *outcome* (Net P&L distribution). These show **what we're
# forecasting over the horizon**: projected weather, LMP, gas, and the resulting generation
# and gross margin across the analog scenarios — as **monthly P10/P50/P90 fans**
# (probability-weighted across scenarios), in Apr→Mar order.

# %%
import json
import pandas as pd
from forward.run import weighted_quantile

paths = res["paths"]
probs = [p["probability"] for p in paths]
MONTH_ORDER = [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3]
MONTH_LABEL = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]


def _scn_monthly_series(s, agg):           # s: Series indexed by datetime
    g = s.groupby(pd.DatetimeIndex(s.index).month).agg(agg)
    return {int(k): float(v) for k, v in g.items()}


def _scn_monthly_df(df, col, agg):          # df: engine daily with 'date' col
    d = df.copy(); d["m"] = pd.to_datetime(d["date"]).dt.month
    g = d.groupby("m")[col].agg(agg)
    return {int(k): float(v) for k, v in g.items()}


def _fan(per_scn):                          # per_scn: list of {month: value}
    P = {0.1: [], 0.5: [], 0.9: []}
    for mo in MONTH_ORDER:
        vals = np.array([d.get(mo, np.nan) for d in per_scn], float)
        w = np.array(probs, float); mask = ~np.isnan(vals)
        for qq in P:
            P[qq].append(weighted_quantile(vals[mask], w[mask], qq) if mask.sum() else np.nan)
    return np.array(P[0.1]), np.array(P[0.5]), np.array(P[0.9])


lmp_m = [_scn_monthly_series(p["lmp_daily"], "mean") for p in paths]
gas_m = [_scn_monthly_series(p["gas_daily"], "mean") for p in paths]
mwh_m = [_scn_monthly_df(p["daily"], "mwh_degraded", "sum") for p in paths]
marg_m = [_scn_monthly_df(p["daily"], "margin_degraded", "sum") for p in paths]

# SEAS5 temperature ensemble (the forecast we condition on)
seas5 = json.loads((Path("..").resolve() / "data" / "paths" / "lockport"
                    / "weather_forecast_seas5.json").read_text())
_var = seas5["data"]["temperature_2m"]
_times = pd.to_datetime(_var["time"])
_arr = np.array([_var["data"][0]["values"][k] for k in _var["data"][0]["values"]], float) * 9 / 5 + 32

# %%
fig, ax = plt.subplots(2, 3, figsize=(16, 9))
x = np.arange(len(MONTH_LABEL))


def fan_panel(a, per_scn, title, ylab, scale=1.0):
    p10, p50, p90 = _fan(per_scn)
    a.fill_between(x, p10 / scale, p90 / scale, alpha=0.22, color="#16a085", label="P10–P90")
    a.plot(x, p50 / scale, "-o", color="#0e6655", ms=3, label="P50")
    a.set_xticks(x); a.set_xticklabels(MONTH_LABEL, rotation=45, fontsize=8)
    a.set_title(title); a.set_ylabel(ylab); a.axhline(0, color="k", lw=0.5)


# (a) SEAS5 temperature ensemble fan over the forecast horizon
ax[0, 0].fill_between(_times, np.nanpercentile(_arr, 10, axis=0), np.nanpercentile(_arr, 90, axis=0),
                      alpha=0.22, color="#c0392b")
ax[0, 0].plot(_times, np.nanpercentile(_arr, 50, axis=0), color="#922b21", lw=1)
ax[0, 0].set_title("SEAS5 temperature FORECAST (°F)\n51-member ensemble P10–P90 (the conditioning signal)")
ax[0, 0].set_ylabel("°F"); ax[0, 0].tick_params(axis="x", rotation=45, labelsize=7)

fan_panel(ax[0, 1], lmp_m,  "Forward LMP (monthly mean)", "$/MWh")
fan_panel(ax[0, 2], gas_m,  "Forward Henry Hub gas (monthly mean)", "$/MMBtu")
fan_panel(ax[1, 0], mwh_m,  "Forward generation (monthly MWh)", "MWh")
fan_panel(ax[1, 1], marg_m, "Forward gross margin (monthly $M)", "$M", scale=1e6)

# (f) Net P&L scenario distribution
vals = pp["net_pl_usd"].values / 1e6; wts = pp["probability"].values
cum = (np.cumsum(wts) - 0.5 * wts) / wts.sum()
ax[1, 2].step(vals, cum, where="mid", color="#2c3e50", marker="o", ms=3)
for lab, qq, c in [("P10", q["P10"], "#e67e22"), ("P50", q["P50"], "#2980b9"), ("P90", q["P90"], "#27ae60")]:
    ax[1, 2].axvline(qq / 1e6, color=c, ls="--", label=f"{lab} {qq/1e6:.1f}")
ax[1, 2].set_title("Net P&L distribution ($M)"); ax[1, 2].set_xlabel("$M")
ax[1, 2].set_ylabel("cumulative probability"); ax[1, 2].legend(fontsize=7)

fig.suptitle(f"Lockport forward FORECAST trajectories — {BASIS}, {len(paths)} analog scenarios, "
             f"SEAS5 {sel.seas5_init[:10]} — monthly P10/P50/P90 (prob-weighted)", fontsize=12)
fig.tight_layout()
fig.savefig(out_dir / "forecast_trajectories.png", dpi=110, bbox_inches="tight")
print(f"Saved charts -> {out_dir / 'forecast_trajectories.png'}")
