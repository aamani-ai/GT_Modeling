"""Historical A/B/C policy-mode comparison chart.

Reads the latest notebook-4 run bundle (daily_summary_mode_{a,b,c} + inspection_events)
and plots the wear-vs-revenue tradeoff: spark/LTSA/Net by policy, cumulative Net over
time (where A diverges), and cumulative LTSA over time (the MI step-up). Saves a tracked
figure to docs/methodology/assets/ for dispatch_mechanics.md §3.5.

Run:  MPLBACKEND=Agg python notebooks/scratch/policy_mode_comparison.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RUNS = REPO / "data" / "outputs" / "lockport" / "runs"
ASSETS = REPO / "docs" / "methodology" / "assets"
LTSA = ["fixed_fee_cum", "eoh_reserve_cum", "ci_owner_cum", "mi_owner_cum",
        "overage_cum", "avail_penalty_cum", "hr_penalty_cum", "outage_forced_cum"]
COLORS = {"A": "#c0392b", "B": "#2980b9", "C": "#16a085"}

latest = sorted(RUNS.glob("notebook4_*"), key=lambda p: p.stat().st_mtime)[-1]
print(f"Using run: {latest.name}")

modes = {}
for m in "abc":
    d = pd.read_parquet(latest / f"daily_summary_mode_{m}.parquet").copy()
    d["dt"] = pd.to_datetime(d["date"])
    d["spark_cum"] = d["margin_degraded"].cumsum()
    d["ltsa_cum"] = d[LTSA].sum(axis=1)
    d["net_cum"] = d["spark_cum"] - d["ltsa_cum"]
    modes[m.upper()] = d

insp = pd.read_parquet(latest / "inspection_events.parquet")

# headline totals
tot = {M: {"spark": d["margin_degraded"].sum(),
           "ltsa": d["ltsa_cum"].iloc[-1],
           "net": d["spark_cum"].iloc[-1] - d["ltsa_cum"].iloc[-1]} for M, d in modes.items()}

fig, ax = plt.subplots(1, 3, figsize=(17, 5))

# (1) grouped bars: spark / LTSA / Net by policy
labels = ["A", "B", "C"]; x = np.arange(3); w = 0.26
ax[0].bar(x - w, [tot[M]["spark"] / 1e6 for M in labels], w, label="Spark margin", color="#27ae60")
ax[0].bar(x,     [-tot[M]["ltsa"] / 1e6 for M in labels], w, label="LTSA (cost, shown −)", color="#e67e22")
ax[0].bar(x + w, [tot[M]["net"] / 1e6 for M in labels], w, label="Net P&L", color="#2c3e50")
ax[0].axhline(0, color="k", lw=0.6); ax[0].set_xticks(x); ax[0].set_xticklabels([f"Policy {M}" for M in labels])
ax[0].set_ylabel("$M (9-yr)"); ax[0].set_title("Policy A/B/C — 9-year totals\n(A runs more spark but pays an MI → worse Net)")
ax[0].legend(fontsize=8)
for i, M in enumerate(labels):
    ax[0].annotate(f"{tot[M]['net']/1e6:.0f}", (i + w, tot[M]["net"] / 1e6), ha="center",
                   va="top" if tot[M]["net"] < 0 else "bottom", fontsize=8)

# (2) cumulative Net P&L over time
for M, d in modes.items():
    ax[1].plot(d["dt"], d["net_cum"] / 1e6, color=COLORS[M], label=f"Policy {M}", lw=1.3)
for _, r in insp.iterrows():
    ax[1].axvline(pd.to_datetime(r["date"]), color=COLORS.get(r["mode"], "k"), ls=":", lw=1)
    ax[1].annotate(f"{r['mode']} {r['type']}", (pd.to_datetime(r["date"]), ax[1].get_ylim()[0]),
                   rotation=90, va="bottom", fontsize=7, color=COLORS.get(r["mode"], "k"))
ax[1].set_title("Cumulative Net P&L ($M)\nA diverges when its MI fires (B/C defer past window)")
ax[1].set_ylabel("$M"); ax[1].legend(fontsize=8)

# (3) cumulative LTSA over time (the MI step-up)
for M, d in modes.items():
    ax[2].plot(d["dt"], d["ltsa_cum"] / 1e6, color=COLORS[M], label=f"Policy {M}", lw=1.3)
ax[2].set_title("Cumulative LTSA owner-cost ($M)\nA's step-up = the deferred-by-B/C Major Inspection")
ax[2].set_ylabel("$M"); ax[2].legend(fontsize=8)

fig.suptitle("Lockport policy-mode comparison (historical 9-yr). "
             "B=C (C's extra conservatism never bites at this CF). "
             "⚠ B/C's edge is partly a finite-horizon artifact — the MI just falls past 2026.",
             fontsize=11)
fig.tight_layout()
ASSETS.mkdir(parents=True, exist_ok=True)
out = ASSETS / "policy_mode_comparison.png"
fig.savefig(out, dpi=110, bbox_inches="tight")
print(f"Saved -> {out}")
print({M: {k: round(v / 1e6, 2) for k, v in tot[M].items()} for M in labels})
