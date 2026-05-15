"""Compare N4 modeled generation vs EIA Form 923 actual generation for Lockport, 2017-2023."""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

REPO = Path("/Users/divy/code/work/infrasure_git_codes/gt_models")
OUT_DIR = REPO / "notebooks" / "scratch"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# === Real Lockport generation from EIA Form 923 ===
eia_path = "/Users/divy/code/personal/renewablesinfo_org/data/sources/eia_generation/eia_generation_monthly.parquet"
df = pd.read_parquet(eia_path)
real = df[
    (df['plantCode'] == '54041')
    & (df['energy_source_code'] == 'ALL')
    & (df['prime_mover_code'] == 'ALL')
].copy()
real['period'] = pd.to_datetime(real['period'])
# 2024 EIA-923 data is incomplete (stale fetch); use 2017-2023
real = real[real['period'].dt.year.between(2017, 2023)].sort_values('period').reset_index(drop=True)
real = real.rename(columns={'generation': 'mwh_real', 'period': 'month'})[['month', 'mwh_real']]
print(f"Real (EIA-923): {len(real)} months from {real['month'].min().date()} to {real['month'].max().date()}")
print(f"Real total 2017-2023: {real['mwh_real'].sum():,.0f} MWh")

# === Modeled generation from latest N4 run ===
runs_dir = REPO / "data" / "outputs" / "lockport" / "runs"
latest_run = sorted([d for d in runs_dir.iterdir() if d.name.startswith("notebook4_")])[-1]
print(f"Using model run: {latest_run.name}")

modeled = {}
for mode in ['a', 'b', 'c']:
    d = pd.read_parquet(latest_run / f"daily_summary_mode_{mode}.parquet")
    d['date'] = pd.to_datetime(d['date'])
    d['month'] = d['date'].dt.to_period('M').dt.to_timestamp()
    monthly = d.groupby('month')['mwh_degraded'].sum().reset_index().rename(columns={'mwh_degraded': f'mwh_mode_{mode}'})
    modeled[mode] = monthly

# Merge all modes
mod = modeled['a'].merge(modeled['b'], on='month').merge(modeled['c'], on='month')
mod = mod[(mod['month'].dt.year >= 2017) & (mod['month'].dt.year <= 2023)]
print(f"Modeled: {len(mod)} months")

# Combine
combined = mod.merge(real, on='month', how='left')
combined['mwh_real'] = combined['mwh_real'].fillna(0)
print(f"\n{combined.head()}")

# === Annual aggregates ===
combined['year'] = combined['month'].dt.year
annual = combined.groupby('year').agg(
    mwh_real=('mwh_real', 'sum'),
    mwh_mode_a=('mwh_mode_a', 'sum'),
    mwh_mode_b=('mwh_mode_b', 'sum'),
    mwh_mode_c=('mwh_mode_c', 'sum'),
).reset_index()
annual['ratio_a_over_real'] = annual['mwh_mode_a'] / annual['mwh_real'].replace(0, np.nan)
print("\nAnnual comparison:")
print(annual.to_string(index=False))

# === Plot 1: Monthly time series (real + Mode A) ===
fig, axes = plt.subplots(3, 1, figsize=(13, 11))

# Panel 1: monthly comparison
ax = axes[0]
ax.plot(combined['month'], combined['mwh_mode_a'] / 1000, color='tab:red', linewidth=1.5,
        label='Modeled Mode A', alpha=0.85)
ax.plot(combined['month'], combined['mwh_real'] / 1000, color='black', linewidth=1.5,
        label='Real (EIA Form 923)', alpha=0.85)
ax.fill_between(combined['month'], combined['mwh_real'] / 1000, combined['mwh_mode_a'] / 1000,
                where=(combined['mwh_mode_a'] > combined['mwh_real']),
                alpha=0.20, color='red', label='Model over-commits')
ax.set_ylabel('Monthly generation (GWh)')
ax.set_title('Lockport — Monthly generation: Modeled (Mode A) vs Real (EIA Form 923), 2017-2023')
ax.legend(loc='upper right')
ax.grid(alpha=0.3)
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

# Panel 2: annual bars
ax = axes[1]
years = annual['year'].values
width = 0.20
x = np.arange(len(years))
ax.bar(x - 1.5*width, annual['mwh_real']/1000, width, label='Real (EIA-923)', color='black', alpha=0.85)
ax.bar(x - 0.5*width, annual['mwh_mode_a']/1000, width, label='Mode A', color='tab:red', alpha=0.85)
ax.bar(x + 0.5*width, annual['mwh_mode_b']/1000, width, label='Mode B', color='tab:orange', alpha=0.85)
ax.bar(x + 1.5*width, annual['mwh_mode_c']/1000, width, label='Mode C', color='tab:green', alpha=0.85)
ax.set_xticks(x)
ax.set_xticklabels(years)
ax.set_ylabel('Annual generation (GWh)')
ax.set_title('Annual generation: Modeled (Policy Modes A/B/C) vs Real')
ax.legend(loc='upper right')
ax.grid(alpha=0.3, axis='y')

# Annotate ratio
for i, yr in enumerate(years):
    r = annual.iloc[i]
    if r['mwh_real'] > 0:
        ratio = r['mwh_mode_a'] / r['mwh_real']
        ax.text(i, max(r['mwh_mode_a'], r['mwh_real'])/1000 + 15,
                f'{ratio:.1f}×', ha='center', fontsize=9, color='red')

# Panel 3: cumulative
ax = axes[2]
ax.plot(combined['month'], (combined['mwh_real']/1000).cumsum(), color='black',
        linewidth=2, label=f"Real (final {combined['mwh_real'].sum()/1000:,.0f} GWh)")
ax.plot(combined['month'], (combined['mwh_mode_a']/1000).cumsum(), color='tab:red',
        linewidth=2, label=f"Mode A (final {combined['mwh_mode_a'].sum()/1000:,.0f} GWh)")
ax.plot(combined['month'], (combined['mwh_mode_b']/1000).cumsum(), color='tab:orange',
        linewidth=2, label=f"Mode B (final {combined['mwh_mode_b'].sum()/1000:,.0f} GWh)")
ax.plot(combined['month'], (combined['mwh_mode_c']/1000).cumsum(), color='tab:green',
        linewidth=2, label=f"Mode C (final {combined['mwh_mode_c'].sum()/1000:,.0f} GWh)")
ax.set_xlabel('Date')
ax.set_ylabel('Cumulative GWh')
ax.set_title('Cumulative generation, 2017-2023')
ax.legend(loc='upper left')
ax.grid(alpha=0.3)
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

plt.tight_layout()
plot_path = OUT_DIR / "modeled_vs_actual_generation.png"
plt.savefig(plot_path, dpi=120, bbox_inches='tight')
print(f"\nPlot saved to: {plot_path}")

# === Headline numbers ===
print("\n=== Headline numbers (2017-2023) ===")
print(f"Real cumulative:    {real['mwh_real'].sum()/1000:>10,.0f} GWh  (avg {real['mwh_real'].sum()/7000:>5,.0f} GWh/yr)")
print(f"Mode A cumulative:  {mod['mwh_mode_a'].sum()/1000:>10,.0f} GWh  (avg {mod['mwh_mode_a'].sum()/7000:>5,.0f} GWh/yr)")
print(f"Mode B cumulative:  {mod['mwh_mode_b'].sum()/1000:>10,.0f} GWh  (avg {mod['mwh_mode_b'].sum()/7000:>5,.0f} GWh/yr)")
print(f"Mode C cumulative:  {mod['mwh_mode_c'].sum()/1000:>10,.0f} GWh  (avg {mod['mwh_mode_c'].sum()/7000:>5,.0f} GWh/yr)")
print(f"\nOver-commitment ratio (Mode A / Real): {mod['mwh_mode_a'].sum() / real['mwh_real'].sum():.2f}×")
