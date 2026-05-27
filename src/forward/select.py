"""Forward scenario selection — temperature-conditioned continuous-window analog.

Ports the method from model-gpr's prototype
(`data_analytics_notebooks/lockport_gas_continuous_window/01_initial_prototype`),
adapted for gt_models (local data, DA price basis per the forward-engine plan §6).

The candidate unit is a full continuous Apr->Mar historical window. Each window is
scored by how closely its Apr-Oct standardized monthly temperature anomaly matches the
SEAS5 ensemble-mean anomaly, then turned into a probability via softmax + floor. Price
and gas do NOT enter the score (conditioning is temperature-only for v1, per the
prototype §7.8); they are carried at the BUILD step (src/forward/build.py).

DA-LMP only goes back to 2017, so the eligible window pool is naturally ~8 windows
(2017-2018 ... 2024-2025) — a small ensemble, which is the intended v1 scale.

⚠️ COMMITTED FOLLOW-UP (do not forget): switch this to RT after v1 is proven. DA's
~8 post-2017 windows are a shale-era-biased sample that excludes tail scenarios
(2022 gas spike, 2014 polar vortex); RT runs from 1999 -> ~24 windows across gas
regimes, which a forward valuation needs to bracket uncertainty. See
docs/plans/forward_engine_plan.md §6 decision 1.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # make src/ importable
from forward.data import load_price_hourly, load_weather, load_gas  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"

# Method constants (prototype defaults; Bucket-B-style, revisable)
TAU = 0.50                  # softmax temperature (smaller = sharper)
PROB_FLOOR = 0.02           # keeps low-ranked windows alive
COVERAGE_MIN = 0.99         # window eligibility on price / weather / gas
S2S_COVERAGE_MIN = 0.80     # a forecast month must cover >=80% of its calendar days
DEFAULT_BASIS = "RT"        # RT -> ~24 windows (1999+); DA -> ~8 (2017+). See plan §6.


@dataclass
class SelectionResult:
    window_weights: pd.DataFrame      # window_id, source_start_year, distance, probability
    month_scores: pd.DataFrame        # month, z_s2s, climatology mu/sigma, coverage, used
    contributions: pd.DataFrame       # window_id x month z_hist/z_s2s/z_diff/contribution
    valid_months: list[int]
    seas5_init: str


# ----------------------------------------------------------------------------- IO
def _paths_dir(asset: str = "lockport") -> Path:
    return DATA_DIR / "paths" / asset


def load_inputs(basis: str = DEFAULT_BASIS, asset: str = "lockport"):
    """Returns (weather, price_hourly, gas, seas5) for the chosen price basis."""
    weather = load_weather(asset)
    price = load_price_hourly(basis, asset)             # DataFrame[datetime_local, price]
    gas = load_gas(asset)                               # has trade_date_dt
    seas5 = json.loads((_paths_dir(asset) / "weather_forecast_seas5.json").read_text())
    return weather, price, gas, seas5


# --------------------------------------------------------------- temperature math
def daily_local_temp(weather: pd.DataFrame) -> pd.Series:
    """Local-date daily mean temperature (deg C). Two-step (hourly->daily) avoids DST bias."""
    return weather.groupby(weather.index.normalize().date)["temperature_2m"].mean()


def monthly_climatology(weather: pd.DataFrame):
    """Returns (T_hist[(year,month)], mu[month], sigma[month]) from historical weather."""
    t_daily = daily_local_temp(weather)
    idx = pd.to_datetime(pd.Series(list(t_daily.index)))
    df = pd.DataFrame({"t": t_daily.values, "year": idx.dt.year.values, "month": idx.dt.month.values})
    t_hist = df.groupby(["year", "month"])["t"].mean()
    mu = t_hist.groupby("month").mean()
    sigma = t_hist.groupby("month").std()
    return t_hist, mu, sigma


def s2s_monthly(seas5: dict, mu: pd.Series, sigma: pd.Series):
    """Ensemble-mean monthly forecast temp + coverage + standardized anomaly z_s2s[m]."""
    var = seas5["data"]["temperature_2m"]
    times = pd.to_datetime(var["time"])
    values = var["data"][0]["values"]            # {member_id: [..len(times)..]}
    members = list(values.keys())
    arr = np.array([values[m] for m in members], dtype=float)   # (n_members, n_days)
    member_mean_by_day = arr.mean(axis=0)                       # ensemble mean per day
    fdf = pd.DataFrame({"date": times, "f": member_mean_by_day})
    fdf["month"] = fdf["date"].dt.month
    cal_days = times.to_series().dt.month.value_counts()        # forecast days per month
    rows = []
    for month, grp in fdf.groupby("month"):
        n_days = pd.Timestamp(2026, month, 1).days_in_month
        coverage = len(grp) / n_days
        f_mean = grp["f"].mean()
        used = coverage >= S2S_COVERAGE_MIN
        z = (f_mean - mu[month]) / sigma[month] if month in mu.index else np.nan
        rows.append({"month": month, "forecast_days": len(grp), "calendar_days": n_days,
                     "coverage": coverage, "forecast_mean_c": f_mean,
                     "mu_c": mu.get(month, np.nan), "sigma_c": sigma.get(month, np.nan),
                     "z_s2s": z, "used_for_weighting": used})
    ms = pd.DataFrame(rows).sort_values("month").reset_index(drop=True)
    valid = ms.loc[ms["used_for_weighting"], "month"].tolist()
    return ms, valid


# ------------------------------------------------------------- candidate windows
def _source_year(window_start_year: int, month: int) -> int:
    """Apr-Mar window: Apr-Dec belong to start year, Jan-Mar to start+1."""
    return window_start_year if month >= 4 else window_start_year + 1


def candidate_windows(weather, price, gas, coverage_min: float = COVERAGE_MIN):
    """Eligible Apr->Mar window start-years where price + weather + gas all cover >= 99%.

    `price` is the hourly LMP DataFrame (datetime_local, price) for the chosen basis;
    its history start sets the pool size (RT 1999+ -> ~24 windows; DA 2017+ -> ~8).
    """
    price_dates = set(price["datetime_local"].dt.normalize().dt.date)
    wx_dates = set(weather.index.normalize().date)
    gas_dates = set(gas["trade_date_dt"])
    # Gas trades only on business days; it is forward-filled to calendar days (as the
    # prototype does). So a day is "gas-covered" if a gas trade exists on/before it
    # (a prior value is forward-fillable) — internal weekend/holiday gaps don't count.
    first_gas = min(gas_dates)
    last_gas = max(gas_dates)
    price_years = sorted({d.year for d in price_dates})
    rows = []
    for y in range(min(price_years), max(price_years) + 1):
        start = pd.Timestamp(y, 4, 1)
        end = pd.Timestamp(y + 1, 4, 1)
        days = pd.date_range(start, end - pd.Timedelta(days=1), freq="D").date
        n = len(days)
        price_cov = sum(d in price_dates for d in days) / n
        wx_cov = sum(d in wx_dates for d in days) / n
        gas_cov = sum(first_gas <= d <= last_gas for d in days) / n
        rows.append({"window_id": f"{y}_{y+1}", "source_start_year": y, "expected_days": n,
                     "price_coverage": price_cov, "weather_coverage": wx_cov, "gas_coverage": gas_cov,
                     "is_eligible": min(price_cov, wx_cov, gas_cov) >= coverage_min})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------- scoring
def score_windows(cw: pd.DataFrame, t_hist, mu, sigma, month_scores, valid_months,
                  tau: float = TAU, p_floor: float = PROB_FLOOR):
    elig = cw[cw["is_eligible"]].copy()
    if not valid_months:
        raise ValueError("No valid S2S months — cannot condition.")
    alpha = 1.0 / len(valid_months)
    z_s2s = month_scores.set_index("month")["z_s2s"]
    contribs = []
    distances = {}
    for _, w in elig.iterrows():
        y = int(w["source_start_year"]); wid = w["window_id"]
        ssq = 0.0
        for m in valid_months:
            sy = _source_year(y, m)
            th = t_hist.get((sy, m), np.nan)
            zh = (th - mu[m]) / sigma[m] if not np.isnan(th) else np.nan
            zd = zh - z_s2s[m]
            contribs.append({"window_id": wid, "month": m, "z_hist": zh,
                             "z_s2s": z_s2s[m], "z_diff": zd, "contribution": alpha * zd**2})
            ssq += alpha * (zd ** 2)
        distances[wid] = np.sqrt(ssq)
    elig["distance"] = elig["window_id"].map(distances)
    # softmax + floor + renormalize
    d = elig["distance"].values
    raw = np.exp(-d / tau); raw = raw / raw.sum()
    K = len(elig)
    floored = p_floor + (1 - K * p_floor) * raw
    elig["probability"] = floored / floored.sum()
    elig = elig.sort_values("probability", ascending=False).reset_index(drop=True)
    return elig[["window_id", "source_start_year", "distance", "probability"]], pd.DataFrame(contribs)


# ----------------------------------------------------------------------- entry
def select(basis: str = DEFAULT_BASIS, asset: str = "lockport",
           tau: float = TAU, p_floor: float = PROB_FLOOR) -> SelectionResult:
    weather, price, gas, seas5 = load_inputs(basis, asset)
    t_hist, mu, sigma = monthly_climatology(weather)
    month_scores, valid = s2s_monthly(seas5, mu, sigma)
    cw = candidate_windows(weather, price, gas)
    weights, contribs = score_windows(cw, t_hist, mu, sigma, month_scores, valid, tau, p_floor)
    init = seas5["data"]["temperature_2m"]["time"][0]
    return SelectionResult(window_weights=weights, month_scores=month_scores,
                           contributions=contribs, valid_months=valid, seas5_init=str(init))


if __name__ == "__main__":
    r = select()
    print(f"SEAS5 init: {r.seas5_init}")
    print(f"Valid (>=80% coverage) S2S months: {r.valid_months}")
    print("\nMonth scores (z_s2s = warm if >0):")
    print(r.month_scores[["month", "coverage", "forecast_mean_c", "mu_c", "z_s2s", "used_for_weighting"]].to_string(index=False))
    print(f"\nWindow probabilities ({len(r.window_weights)} eligible windows):")
    print(r.window_weights.to_string(index=False))
