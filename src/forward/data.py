"""Forward data loader — builds the engine's market inputs over the FULL history.

The extracted engine pre-slices its price/weather to the historical sim window (2017-2025),
which is fine for the DA historical replay but too short for forward analog windows that
reach back to 1999 (RT). This module loads price/weather/gas over the full available range,
in exactly the schema gt_engine.run_path expects:

  lmp_window     : DataFrame[datetime_local (tz=US/Eastern, hourly), price]
  weather_window : DataFrame indexed by Eastern datetime, column temp_f (deg F)
  henry          : DataFrame[trade_date_dt (date), price_usd_per_mmbtu]

Price basis is selectable:
  - "DA": lmp_da_hourly  (2017+ -> ~8 analog windows)
  - "RT": lmp_rt_intervals aggregated to hourly  (1999+ -> ~24 windows)  [v1 target after the DA proof]
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]


def _paths_dir(asset: str = "lockport") -> Path:
    return REPO_ROOT / "data" / "paths" / asset


def load_price_hourly(basis: str = "RT", asset: str = "lockport") -> pd.DataFrame:
    """Hourly LMP as DataFrame[datetime_local (Eastern), price].

    Built from interval_start_utc -> Eastern -> hour, averaging within the hour
    (a no-op for already-hourly DA; collapses sub-hourly RT to hourly).
    """
    pd_dir = _paths_dir(asset)
    fname = "lmp_da_hourly.parquet" if basis.upper() == "DA" else "lmp_rt_intervals.parquet"
    df = pd.read_parquet(pd_dir / fname)
    # Floor in UTC (no DST ambiguity), then convert to Eastern.
    hour_utc = pd.to_datetime(df["interval_start_utc"], utc=True).dt.floor("h")
    hour = hour_utc.dt.tz_convert("US/Eastern")
    out = (pd.DataFrame({"datetime_local": hour, "price": df["price"].astype(float)})
           .dropna(subset=["price"])
           .groupby("datetime_local", as_index=False)["price"].mean()
           .sort_values("datetime_local").reset_index(drop=True))
    return out


def load_weather(asset: str = "lockport") -> pd.DataFrame:
    """Full historical hourly weather, Eastern-indexed, with temp_f (deg F)."""
    w = pd.read_parquet(_paths_dir(asset) / "weather_hourly.parquet").copy()
    w.index = pd.to_datetime(w.index, utc=True).tz_convert("US/Eastern")
    w["temp_f"] = w["temperature_2m"] * 9 / 5 + 32
    return w


def load_gas(asset: str = "lockport") -> pd.DataFrame:
    """Henry Hub gas with trade_date_dt (date)."""
    g = pd.read_parquet(_paths_dir(asset) / "gas_price_history.parquet")
    g = g[g["hub_name"] == "Henry Hub"].copy()
    g["trade_date_dt"] = pd.to_datetime(g["trade_date"]).dt.date
    return g


def load_market(basis: str = "RT", asset: str = "lockport"):
    """Returns (lmp_window, weather_window, henry) ready for gt_engine.run_path."""
    return load_price_hourly(basis, asset), load_weather(asset), load_gas(asset)
