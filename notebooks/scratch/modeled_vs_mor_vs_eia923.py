"""Compare N4 modeled generation vs real MOR data (from diligence-extractor)
   vs EIA Form 923 (federal). MOR is the ground truth; EIA-923 is the
   public-data approximation; modeled is what v1 says."""
from __future__ import annotations
import calendar, re
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

REPO = Path("/Users/divy/code/work/infrasure_git_codes/gt_models")
OUT_DIR = REPO / "notebooks" / "scratch"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MOR_DIR = Path("/Users/divy/code/personal/diligence-extractor/data/lockport/3.0 Lockport/3.4 O&M Reports/3.4.20 Monthly Operating Reports")
EIA_PARQUET = Path("/Users/divy/code/personal/renewablesinfo_org/data/sources/eia_generation/eia_generation_monthly.parquet")

MONTH_NAMES = ["January","February","March","April","May","June","July","August","September","October","November","December"]

# Column index → semantic name (verified consistent across years per the diligence-extractor notebook)
COLS = {
    1:  "ambient_temp_f",
    2:  "net_output_mwh",
    3:  "gross_output_mwh",
    6:  "net_station_output",
    7:  "dhts_steam_load_mmbtu",
    9:  "dhts_net_thermal_mmbtu",
    11: "ctg1_mwh",
    12: "ctg2_mwh",
    14: "ctg3_mwh",
    15: "stg_mwh",
    16: "plant_run_time_hrs",
    17: "total_gas_mmbtu",
}

# === Parse MOR workbooks ===
def parse_sheet(path: Path, year: int, month_name: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=month_name, header=None)
    month_num = MONTH_NAMES.index(month_name) + 1
    days = calendar.monthrange(year, month_num)[1]
    rows = []
    for i in range(5, min(40, len(df))):
        day_val = df.iloc[i, 0]
        if pd.isna(day_val):
            continue
        try:
            day = int(day_val)
        except (ValueError, TypeError):
            continue
        if not (1 <= day <= days):
            continue
        rec = {"date": pd.Timestamp(year=year, month=month_num, day=day)}
        for col_idx, name in COLS.items():
            try:
                v = df.iloc[i, col_idx]
                rec[name] = float(v) if pd.notna(v) else None
            except (ValueError, TypeError, IndexError):
                rec[name] = None
        rows.append(rec)
    return pd.DataFrame(rows)

year_files = {}
for year_dir in sorted(MOR_DIR.glob("3.4.20.* 20*")):
    m = re.search(r"20\d{2}", year_dir.name)
    if not m:
        continue
    year = int(m.group())
    candidates = list(year_dir.glob("*monthly_report_data*.xls*"))
    if candidates:
        year_files[year] = candidates[0]
print(f"MOR workbooks: {sorted(year_files)}")

all_rows = []
for year, f in sorted(year_files.items()):
    sheets = set(pd.ExcelFile(f).sheet_names)
    for m_name in MONTH_NAMES:
        if m_name not in sheets:
            continue
        d = parse_sheet(f, year, m_name)
        all_rows.append(d)
mor_daily = pd.concat(all_rows, ignore_index=True).sort_values("date").reset_index(drop=True)
print(f"MOR daily rows: {len(mor_daily)}")
print(f"Date range: {mor_daily['date'].min().date()} to {mor_daily['date'].max().date()}")

# Save MOR daily parquet for reuse
mor_parquet = REPO / "data" / "paths" / "lockport" / "mor_daily.parquet"
mor_daily.to_parquet(mor_parquet, index=False)
print(f"Saved MOR daily parquet: {mor_parquet}")

# Aggregate MOR to monthly
mor_daily["month"] = mor_daily["date"].dt.to_period("M").dt.to_timestamp()
mor_monthly = mor_daily.groupby("month").agg(
    mwh_mor=("net_output_mwh", "sum"),
    gross_mwh_mor=("gross_output_mwh", "sum"),
    dhts_thermal_mmbtu=("dhts_net_thermal_mmbtu", "sum"),
    gas_mmbtu=("total_gas_mmbtu", "sum"),
    run_hours=("plant_run_time_hrs", "sum"),
).reset_index()
print(f"\nMOR monthly totals (first 6 rows):")
print(mor_monthly.head(6).to_string())

# === Pull EIA-923 monthly ===
eia = pd.read_parquet(EIA_PARQUET)
eia_lp = eia[(eia['plantCode'] == '54041') & (eia['energy_source_code'] == 'ALL') & (eia['prime_mover_code'] == 'ALL')].copy()
eia_lp['month'] = pd.to_datetime(eia_lp['period'])
eia_lp = eia_lp[['month', 'generation']].rename(columns={'generation': 'mwh_eia923'}).reset_index(drop=True)

# === Pull modeled monthly from latest N4 ===
runs_dir = REPO / "data" / "outputs" / "lockport" / "runs"
latest_run = sorted([d for d in runs_dir.iterdir() if d.name.startswith("notebook4_")])[-1]
print(f"\nUsing model run: {latest_run.name}")

modeled = {}
for mode in ['a', 'b', 'c']:
    d = pd.read_parquet(latest_run / f"daily_summary_mode_{mode}.parquet")
    d['date'] = pd.to_datetime(d['date'])
    d['month'] = d['date'].dt.to_period('M').dt.to_timestamp()
    monthly = d.groupby('month')['mwh_degraded'].sum().reset_index().rename(columns={'mwh_degraded': f'mwh_mode_{mode}'})
    modeled[mode] = monthly
mod = modeled['a'].merge(modeled['b'], on='month').merge(modeled['c'], on='month')

# === Combine ===
combined = mod.merge(mor_monthly[['month', 'mwh_mor']], on='month', how='left')\
              .merge(eia_lp[['month', 'mwh_eia923']], on='month', how='left')
# Restrict to range where we have MOR coverage
combined = combined[combined['month'].dt.year.between(2021, 2025)].reset_index(drop=True)
print(f"\nComparison range: {combined['month'].min().date()} to {combined['month'].max().date()}")
print(f"Months: {len(combined)}")
combined['year'] = combined['month'].dt.year

# Annual aggregates
annual = combined.groupby('year').agg(
    mwh_mor=('mwh_mor', 'sum'),
    mwh_mode_a=('mwh_mode_a', 'sum'),
    mwh_mode_b=('mwh_mode_b', 'sum'),
    mwh_mode_c=('mwh_mode_c', 'sum'),
    mwh_eia923=('mwh_eia923', 'sum'),
).reset_index()
annual['ratio_a_over_mor'] = annual['mwh_mode_a'] / annual['mwh_mor'].replace(0, np.nan)
annual['ratio_eia_over_mor'] = annual['mwh_eia923'] / annual['mwh_mor'].replace(0, np.nan)
print("\nAnnual comparison (2021-2025):")
print(annual.to_string(index=False))

# === Plots ===
fig, axes = plt.subplots(4, 1, figsize=(14, 14))

# Panel 1: monthly time series
ax = axes[0]
ax.plot(combined['month'], combined['mwh_mor']/1000, color='black', linewidth=2,
        label='Real (MOR — daily from data room)', marker='o', markersize=4, alpha=0.85)
ax.plot(combined['month'], combined['mwh_mode_a']/1000, color='tab:red', linewidth=1.5,
        label='Modeled — Policy A (v1)', alpha=0.85)
ax.plot(combined['month'], combined['mwh_eia923']/1000, color='tab:blue', linewidth=1.2,
        label='EIA Form 923 (federal)', linestyle='--', alpha=0.7)
ax.set_ylabel('Monthly generation (GWh)')
ax.set_title('Lockport — Monthly generation: MOR (truth) vs Modeled (Policy A) vs EIA-923 (federal)', fontsize=11)
ax.legend(loc='upper right', fontsize=9)
ax.grid(alpha=0.3)
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

# Panel 2: annual bars
ax = axes[1]
years = annual['year'].values
width = 0.16
x = np.arange(len(years))
ax.bar(x - 2*width, annual['mwh_mor']/1000, width, label='Real (MOR)', color='black', alpha=0.85)
ax.bar(x - 1*width, annual['mwh_mode_a']/1000, width, label='Mode A', color='tab:red', alpha=0.85)
ax.bar(x + 0*width, annual['mwh_mode_b']/1000, width, label='Mode B', color='tab:orange', alpha=0.85)
ax.bar(x + 1*width, annual['mwh_mode_c']/1000, width, label='Mode C', color='tab:green', alpha=0.85)
ax.bar(x + 2*width, annual['mwh_eia923']/1000, width, label='EIA-923', color='tab:blue', alpha=0.85)
ax.set_xticks(x); ax.set_xticklabels(years)
ax.set_ylabel('Annual generation (GWh)')
ax.set_title('Annual generation: Real (MOR) vs Modeled (3 policy modes) vs EIA-923')
ax.legend(loc='upper right', fontsize=9)
ax.grid(alpha=0.3, axis='y')
# Ratio annotations
for i, yr in enumerate(years):
    r = annual.iloc[i]
    if pd.notna(r['ratio_a_over_mor']):
        ax.text(i - 1*width, r['mwh_mode_a']/1000 + 8,
                f'{r["ratio_a_over_mor"]:.1f}×', ha='center', fontsize=8, color='red')

# Panel 3: cumulative
ax = axes[2]
ax.plot(combined['month'], (combined['mwh_mor']/1000).cumsum(), color='black',
        linewidth=2.5, label=f"MOR — final {combined['mwh_mor'].sum()/1000:,.0f} GWh", alpha=0.9)
ax.plot(combined['month'], (combined['mwh_mode_a']/1000).cumsum(), color='tab:red',
        linewidth=2, label=f"Mode A — final {combined['mwh_mode_a'].sum()/1000:,.0f} GWh")
ax.plot(combined['month'], (combined['mwh_mode_b']/1000).cumsum(), color='tab:orange',
        linewidth=2, label=f"Mode B — final {combined['mwh_mode_b'].sum()/1000:,.0f} GWh")
ax.plot(combined['month'], (combined['mwh_mode_c']/1000).cumsum(), color='tab:green',
        linewidth=2, label=f"Mode C — final {combined['mwh_mode_c'].sum()/1000:,.0f} GWh")
ax.plot(combined['month'], (combined['mwh_eia923']/1000).cumsum(), color='tab:blue',
        linewidth=1.5, linestyle='--', label=f"EIA-923 — final {combined['mwh_eia923'].sum()/1000:,.0f} GWh", alpha=0.7)
ax.set_xlabel('Date'); ax.set_ylabel('Cumulative GWh')
ax.set_title('Cumulative generation, 2021-2025')
ax.legend(loc='upper left', fontsize=9)
ax.grid(alpha=0.3)
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

# Panel 4: EIA-923 vs MOR data quality check
ax = axes[3]
mor_eia = combined.dropna(subset=['mwh_mor', 'mwh_eia923']).copy()
mor_eia['eia_minus_mor'] = mor_eia['mwh_eia923'] - mor_eia['mwh_mor']
ax.bar(mor_eia['month'], mor_eia['eia_minus_mor']/1000, width=20, color='tab:purple', alpha=0.7)
ax.axhline(0, color='black', linewidth=0.8)
ax.set_xlabel('Date'); ax.set_ylabel('EIA-923 − MOR (GWh, monthly)')
ax.set_title('Data-quality check: EIA Form 923 vs MOR-reported (zero = federal data matches plant filings)')
ax.grid(alpha=0.3)
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

plt.tight_layout()
plot_path = OUT_DIR / "modeled_vs_mor_vs_eia923.png"
plt.savefig(plot_path, dpi=120, bbox_inches='tight')
print(f"\nPlot saved to: {plot_path}")

# Save combined comparison parquet
combined.to_parquet(OUT_DIR / "monthly_comparison_2021_2025.parquet", index=False)
print(f"Comparison data saved to: {OUT_DIR / 'monthly_comparison_2021_2025.parquet'}")

# === Headlines ===
print("\n=== Headlines (2021-2025, 5-year period with MOR coverage) ===")
tot_mor = annual['mwh_mor'].sum()
tot_a = annual['mwh_mode_a'].sum()
tot_eia = annual['mwh_eia923'].sum()
n_yrs = len(annual)
print(f"MOR (truth):     {tot_mor/1000:>8,.0f} GWh   ({tot_mor/n_yrs/1000:>6,.0f} GWh/yr avg)")
print(f"Mode A:          {tot_a/1000:>8,.0f} GWh   ({tot_a/n_yrs/1000:>6,.0f} GWh/yr avg)")
print(f"EIA-923:         {tot_eia/1000:>8,.0f} GWh   ({tot_eia/n_yrs/1000:>6,.0f} GWh/yr avg)")
print(f"\nMode A / MOR over-commit:  {tot_a/tot_mor:.2f}×")
print(f"EIA-923 / MOR data lag:    {tot_eia/tot_mor:.2f}×")
