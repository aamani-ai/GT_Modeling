# dashboard/ — Pointer to the active dashboard app

> **The active dashboard app now lives at [`apps/gt-digital-twin/`](../apps/gt-digital-twin/).**
> This folder remains as a stable pointer; do not put new code here.

## Where the app is

```
apps/gt-digital-twin/
├── README.md                       ← app overview + run instructions
├── V1.2_HANDOFF.md                 ← v1.2 corrections handoff (typography, sections, 6-panel)
├── scripts/
│   ├── precompute.py                ← runs the REAL engine over the knob grid
│   ├── build_monthly_forecast_panel.py  ← REAL-DATA monthly export consumed by §01
│   └── build_monthly_trajectories.py    ← DEPRECATED (illustrative monthly shape)
└── web/                            ← Vite + React + Tailwind + shadcn webapp
    ├── client/src/                 ← React source
    └── client/public/              ← precomputed.json + monthly_forecast_panel.json + img/
```

## Quick run

```bash
# (One-time) precompute the engine grid — ~16–22 min
cd /path/to/GT_Modeling
python apps/gt-digital-twin/scripts/precompute.py

# (One-time) build the real-data monthly panel for §01 (forward 6-panel)
python apps/gt-digital-twin/scripts/build_monthly_forecast_panel.py

# Dev server
cd apps/gt-digital-twin/web
npm install
npm run dev                         # http://localhost:5000

# Static build
npm run build                       # → dist/public
```

See [`apps/gt-digital-twin/README.md`](../apps/gt-digital-twin/README.md) for the full architecture, design decisions, status taxonomy, and honest limitations.

## Why this pointer file exists

`dashboard/` was originally reserved as a future-scope placeholder (sibling to `docs/`, `data/`, `src/`, `notebooks/`). v1 of the dashboard ended up under `apps/gt-digital-twin/` to keep the app self-contained — its own `scripts/`, `web/`, lockfile, and build pipeline don't need to live at the repo root. This file leaves a breadcrumb so anyone landing in `dashboard/` finds the real app.

## See also

- [`apps/gt-digital-twin/README.md`](../apps/gt-digital-twin/README.md) — app entry point
- [`apps/gt-digital-twin/V1.2_HANDOFF.md`](../apps/gt-digital-twin/V1.2_HANDOFF.md) — v1.2 corrections handoff
- [consolidation plan §4.4](../docs/plans/consolidation_plan.md#44-dashboard--future-scope-new-placeholder-only)
