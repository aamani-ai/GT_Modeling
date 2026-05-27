"""Realized operating profile — classification methodology candidate (Phase 4).

Classifies Lockport's daily MOR record (2021-2025) into a *realized operating
profile*: what duty (cogen / mid-merit / baseload / must-run / idle) the plant
was actually playing, per season and per year.

This is the capability-side concept's complement (see ADR-003): capability =
what the plant *can* be (data/assets/lockport/capability_envelope.yaml);
realization = what it *is doing*, inferred from history (this script ->
data/assets/lockport/realized_operating_profile.yaml).

Status: INFORMAL classification methodology candidate. The thresholds here are
the proposal for the eventual graduation ADR-005, not a committed classifier.

Run:
    /Users/divy/code/personal/renewablesinfo_org/.venv/bin/python \
        notebooks/scratch/realized_profile_classify.py

Reads:  data/paths/lockport/mor_daily.parquet  (1,826 daily rows, 2021-2025)
Writes: nothing by default (prints summary). Pass --parquet to emit the
        per-month classification to notebooks/scratch/realized_profile_monthly.parquet
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
MOR = REPO / "data/paths/lockport/mor_daily.parquet"
NAMEPLATE_MW = 221.3  # plant total nameplate (engineering.yaml plant.total_nameplate_mw)

# --- classification thresholds (the methodology candidate; mirror operating_profile.yaml mode_classifier) ---
CT_ON_MWH = 5.0          # a CT counts as "on" above this daily MWh
GAS_FLOOR_MMBTU = 100.0  # min daily gas to distinguish steam-only from truly offline
DHTS_FLOOR_MMBTU = 100.0 # min daily net thermal to count as steam delivery
BASELOAD_CF = 0.70       # CF threshold for baseload-realized
MIDMERIT_CF = 0.30       # CF threshold for mid-merit-realized (vs low/idle)


def season(m: int) -> str:
    return "winter" if m in (12, 1, 2) else ("summer" if m in (6, 7, 8) else "shoulder")


def classify_days(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["season"] = df["month"].map(season)

    df["operating"] = df["net_output_mwh"] > 0
    df["steam_only"] = (
        (df["net_output_mwh"] <= 0)
        & (df["total_gas_mmbtu"] > GAS_FLOOR_MMBTU)
        & (df["dhts_net_thermal_mmbtu"] > DHTS_FLOOR_MMBTU)
    )
    df["offline"] = (~df["operating"]) & (~df["steam_only"])

    df["n_ct"] = (df[["ctg1_mwh", "ctg2_mwh", "ctg3_mwh"]] > CT_ON_MWH).sum(axis=1)
    df["mode"] = np.where(
        ~df["operating"],
        np.where(df["steam_only"], "steam_only", "offline"),
        np.where(df["n_ct"] >= 3, "3xCC", np.where(df["n_ct"] == 2, "2xCC", "1xCC")),
    )
    return df


def realized_label(cf: float, steam_only_share: float, offline_share: float,
                   dhts_per_day: float) -> str:
    """Map period aggregates -> a realized-duty label (the candidate rule)."""
    labels = []
    if cf >= BASELOAD_CF:
        labels.append("baseload")
    if steam_only_share > 0.20 or dhts_per_day > 200:
        labels.append("cogen+must-run")
    if MIDMERIT_CF <= cf < BASELOAD_CF or (cf >= 0.05 and dhts_per_day < 50):
        labels.append("mid-merit")
    if offline_share > 0.50 and cf < 0.05:
        labels.append("mostly-idle")
    return " / ".join(labels) if labels else "low-activity"


def summarize(df: pd.DataFrame, group: str) -> pd.DataFrame:
    rows = []
    for key, g in df.groupby(group):
        n = len(g)
        cf = g["net_output_mwh"].sum() / (NAMEPLATE_MW * 24 * n)
        rows.append({
            group: key,
            "days": n,
            "CF_pct": round(cf * 100, 1),
            "operating": int(g["operating"].sum()),
            "steam_only": int(g["steam_only"].sum()),
            "offline": int(g["offline"].sum()),
            "dhts_per_day": round(g["dhts_net_thermal_mmbtu"].mean()),
            "mean_T_F": round(g["ambient_temp_f"].mean()),
            "realized": realized_label(cf, g["steam_only"].mean(),
                                       g["offline"].mean(),
                                       g["dhts_net_thermal_mmbtu"].mean()),
        })
    return pd.DataFrame(rows)


def main() -> None:
    df = classify_days(pd.read_parquet(MOR))
    print(f"Coverage: {df['date'].min():%Y-%m-%d} -> {df['date'].max():%Y-%m-%d}  ({len(df)} days)")
    print(f"Overall CF 2021-2025: {df['net_output_mwh'].sum() / (NAMEPLATE_MW * 24 * len(df)) * 100:.1f}%\n")

    print("=== Per-season (pooled) ===")
    print(summarize(df, "season").to_string(index=False))
    print("\n=== Per-year (trend) ===")
    print(summarize(df, "year").to_string(index=False))

    print("\n=== Day-type mix ===")
    print(df["mode"].value_counts().to_string())

    # validation cross-check against operating_profile.yaml steam_only_mode.days_observed
    so = int(df["steam_only"].sum())
    print(f"\nVALIDATION: steam_only days = {so} (operating_profile.yaml expects 460) "
          f"-> {'MATCH' if so == 460 else 'MISMATCH — investigate'}")

    if "--parquet" in sys.argv:
        out = REPO / "notebooks/scratch/realized_profile_monthly.parquet"
        m = summarize(df.assign(ym=df["date"].dt.to_period("M").astype(str)), "ym")
        m.to_parquet(out)
        print(f"\nWrote per-month classification -> {out}")


if __name__ == "__main__":
    main()
