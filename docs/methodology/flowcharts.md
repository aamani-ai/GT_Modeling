# Flow Charts — The gt_models Engine, End to End

> **Purpose**: a visual companion to [`architecture.md`](architecture.md). The big end-to-end chart shows how everything connects; the smaller charts zoom into the parts that are hard to hold in your head — the **daily feedback loop**, the **wear accumulation**, the **wear → failure** chain, the **creep-fatigue coupling**, and (chart 9) the **forward scenario engine**. All diagrams are [Mermaid](https://mermaid.js.org) (render on GitHub, VS Code, most Markdown viewers).
>
> **Where the prose lives**: [`architecture.md`](architecture.md) §2 (the three-layer loop) and §5 (the 12-step daily loop, state vector, forced-outage, inspections). This doc is the picture; that doc is the words.
>
> **Reflects**: [ADR-006](../decisions/006-ambient-weighted-wear.md) (ambient-weighted hot-section wear) and [ADR-007](../decisions/007-creep-wiring-and-trip-wear.md) (creep wired into `p_forced`; trip wear).

---

## 1. The big picture — one asset, one day, three layers, a clock

Everything in v1 is this loop, run once per day for 3,287 days × 3 policy modes. Read it as: *yesterday's state shapes today's dispatch → today's running consumes life → that drives failure risk, inspections, and cost → tomorrow inherits the new state.*

```mermaid
flowchart TD
    subgraph IN["INPUTS — data spine + asset profile"]
        LMP["LMP price path<br/>(NYISO node)"]
        GAS["Henry Hub gas<br/>+ RGGI carbon"]
        WX["Weather / ambient temp<br/>(hourly)"]
        CFG["Asset config:<br/>capability envelope,<br/>engineering, LTSA terms"]
    end

    subgraph ENG["ENGINEERING LAYER"]
        STATE["PLANT STATE VECTOR<br/>(wear accumulators,<br/>yesterday's close)"]
        PF["p_forced(state)<br/>failure hazard"]
    end

    subgraph DIS["DISPATCH LAYER"]
        DISP["Hourly mode pick<br/>3xCC / 2xCC / 1xCC / steam-only / off<br/>+ commitment + wear hurdle"]
    end

    subgraph CON["LTSA / CONTRACTS LAYER"]
        WEAR["update_stress:<br/>accumulate wear"]
        INSP["Inspection trigger<br/>(EOH or calendar)"]
        LTSA["LTSA cost streams<br/>+ forced-outage cost"]
    end

    PNL["Daily P/L<br/>cumulative model_card"]
    FWD["FORWARD ENGINE (src/forward — BUILT)<br/>re-runs THIS loop over SEAS5-conditioned<br/>RT analog windows → P10 / P50 / P90"]

    LMP --> DISP
    GAS --> DISP
    CFG --> DISP
    STATE -->|degraded heat rate<br/>+ wear hurdle near EOH limit| DISP
    WX -->|ambient weighting| WEAR
    DISP -->|fired hours, starts| WEAR
    WEAR -->|new accumulators| STATE
    STATE --> PF
    PF -->|daily outage draw<br/>+ trip wear| WEAR
    PF --> LTSA
    STATE -->|EOH| INSP
    INSP -->|reset accumulators| STATE
    INSP --> LTSA
    DISP --> PNL
    LTSA --> PNL
    PNL -.-> FWD

    classDef built fill:#e8f8f0,stroke:#16a085,stroke-width:2px;
    class FWD built;
```

**The one loop to remember**: `STATE → DISP → WEAR → STATE`. Everything else hangs off it. The **historical** run replays the actual 2017–2025 history once per mode. The **forward engine** (green box, now built — `src/forward/`) runs this *same* loop over SEAS5-conditioned RT analog windows to produce P10/P50/P90 — see **chart 9**. (The one remaining "future" piece is swapping the in-repo analog selection for the model-gpr scenario package.)

---

## 2. The daily loop (the 12 steps)

The procedural version of the engine — what actually executes each simulated day. Mirrors [`architecture.md` §5.2](architecture.md). **Steps [1]–[2] (the outage gates) are expanded with worked examples + an enlarged sub-flowchart in [`outage_mechanics.md`](outage_mechanics.md).**

```mermaid
flowchart TD
    A["Day N begins<br/>(state = close of day N-1)"] --> B{"In continuing<br/>outage?"}
    B -->|yes| B1["Accrue fixed LTSA fee,<br/>decrement outage days"] --> Z["Record day -> Day N+1"]
    B -->|no| C{"Forced-outage<br/>draw &lt; p_forced?"}
    C -->|yes| C1["Pick cause, sample duration,<br/>charge owner cost"]
    C1 --> C2{"Was the plant<br/>RUNNING?"}
    C2 -->|yes = trip from load| C3["TRIP WEAR (ADR-007):<br/>df += 8x cold-start,<br/>eoh += 8x cold-start"]
    C2 -->|no| C4["no trip wear"]
    C3 --> Z
    C4 --> Z
    C -->|no| D["Find next inspection;<br/>EOH headroom = threshold - eoh"]
    D --> E["Mode A/B/C wear-penalty<br/>multiplier from headroom"]
    E --> F["TWIN DISPATCH 24h<br/>(clean-HR and degraded-HR)<br/>see chart 5"]
    F --> G["Cold-start warming gas<br/>correction"]
    G --> H["Commit op state<br/>(op, hrs_off)"]
    H --> I["update_stress:<br/>accumulate wear<br/>see chart 3"]
    I --> J["Daily LTSA accrual<br/>(fixed, EOH reserve, overage)"]
    J --> K{"Inspection trigger?<br/>EOH hard-stop OR calendar"}
    K -->|yes| K1["Charge CI/MI cost,<br/>HR penalty, reset state<br/>see chart 6"]
    K -->|no| L["(no inspection)"]
    K1 --> Z
    L --> Z
```

---

## 3. Wear accumulation — what feeds each accumulator

`update_stress()` turns a day's running into damage. The key nuance from [ADR-006](../decisions/006-ambient-weighted-wear.md): the **hot-section** accumulators (`dc`, `tbc_time`) advance on *ambient-weighted* fired hours; the rest on raw fired hours / starts. Trips ([ADR-007](../decisions/007-creep-wiring-and-trip-wear.md)) inject extra `df` + `eoh`. **Field-by-field math, the accumulator→consequence map, the creep/fatigue laws, and where recovery is costed are in [`wear_mechanics.md`](wear_mechanics.md).**

```mermaid
flowchart LR
    FH["fired hours"]
    ST["starts<br/>(cold/warm/hot)"]
    AMB["ambient temp<br/>per fired hour"]
    TRIP["trip from load<br/>(ADR-007)"]

    AMB -->|"ambient_wear_factor()<br/>re-anchored, mean ~ 1.0"| FHW["ambient-weighted<br/>fired hours"]
    FH --> FHW

    FHW -->|creep rate| DC["dc (creep)"]
    FHW -->|+1/hr weighted| TBC["tbc_time (TBC life)"]
    FH -->|+ start EOH| EOH["eoh (contractual clock)"]
    FH -->|drift| HRR["hr_recov"]
    FH -->|approach asymptote 2.5%| FOUL["fouling"]
    FH -->|rotor rate| ROT["rotor_life"]
    ST -->|fatigue per type| DF["df (fatigue)"]
    ST -->|1 per start| HC["hrsg_cycles"]

    TRIP -->|"8x cold-start"| DF
    TRIP -->|"8x cold-start"| EOH

    classDef hot fill:#ffe6e6,stroke:#c00;
    class DC,TBC hot;
```

Pink = ambient-weighted hot-section accumulators. Note `eoh` stays on *raw* hours by design (it's the contractual clock; ambient is not a standard EOH driver — that's the deferred load half).

---

## 4. Wear → failure — how accumulators become forced-outage risk

Each accumulator maps to a component hazard; the hazards combine (independence) into a daily forced-outage probability. `P_creep(dc)` is new in [ADR-007](../decisions/007-creep-wiring-and-trip-wear.md) — it closed the gap where `dc` fed nothing.

```mermaid
flowchart TD
    DF["df (fatigue)"] -->|"hockey-stick<br/>above 0.60"| PC["P_combustion"]
    DC["dc (creep)"] -->|"hockey-stick<br/>above 0.50 (ADR-007)"| PCR["P_creep"]
    TBC["tbc_time"] -->|Weibull hazard| PT["P_TBC"]
    ROT["rotor_life"] -->|linear| PR["P_rotor"]

    PC --> PGT["P_GT = P_comb + P_TBC<br/>+ P_rotor + P_creep"]
    PCR --> PGT
    PT --> PGT
    PR --> PGT

    AGE["years elapsed<br/>(capped at 10)"] --> PH["P_HRSG (aged)"]
    AGE --> PB["P_BG (aged)"]

    PGT --> COMB["P_forced = 1 - (1-P_GT)(1-P_HRSG)(1-P_BG)<br/>capped 10%/day"]
    PH --> COMB
    PB --> COMB

    COMB --> DRAW{"Bernoulli<br/>draw"}
    DRAW -->|hit| OUT["Forced outage:<br/>lost MWh + owner cost<br/>+ trip wear if running"]
    DRAW -->|miss| RUN["Plant available<br/>to dispatch"]
```

For low-CF Lockport, `P_creep` and `P_combustion` sit near zero (sub-threshold) — the realized outages are driven by the HRSG/BoP baselines. The GT-side channels bite for high-CF / hot-running assets and across Monte Carlo paths.

---

## 5. The dispatch decision (one hour)

How an hour picks its operating mode. The **commitment hurdle** (the one principled dispatch-realism win, see [`extra/temperature_load_fidelity.md`](extra/temperature_load_fidelity.md) §9) only applies when starting from off. **The per-hour margin math (`spark → effective_spark → margin`) is decomposed with worked numbers in [`dispatch_economics.md`](dispatch_economics.md).**

```mermaid
flowchart TD
    H["Hour: LMP, ambient temp"] --> M["For each mode 3xCC/2xCC/1xCC:<br/>spark = LMP - (HR/1000)(gas+RGGI) - VOM"]
    M --> OFF{"Plant currently<br/>off?"}
    OFF -->|yes| HUR["effective spark = spark<br/>- commitment hurdle<br/>- policy wear hurdle"]
    OFF -->|no| NOH["effective spark = spark"]
    HUR --> PICK["margin = max(eff_spark,0) x capacity<br/>pick best mode"]
    NOH --> PICK
    PICK --> POS{"best margin<br/>&gt; 0?"}
    POS -->|yes| RUN["Run best mode<br/>(full capacity in v1)"]
    POS -->|no| MR{"Must-run /<br/>steam day?"}
    MR -->|yes| SO["1xCC or steam-only<br/>(run at a loss for heat)"]
    MR -->|no| OFFL["Offline"]
```

Note: v1 always dispatches at **full mode capacity** when it runs (price-taker). 3xCC dominates 2xCC (best HR + most MW), so 2xCC never wins economically — the economic 2xCC and part-load output are **Stream A** work (the behavioral dispatch rule).

---

## 6. Inspection trigger + state resets

Inspections are the only thing that *reduces* wear. They fire on EOH hard-stop or calendar.

```mermaid
flowchart TD
    T{"Trigger?"} -->|"EOH &gt; threshold + 1500<br/>(hard stop)"| FIRE["Fire inspection"]
    T -->|"today >= scheduled date<br/>(calendar)"| FIRE
    FIRE --> TYPE{"CI or MI?"}
    TYPE -->|CI| CI["dc x0.5, df x0.5,<br/>fouling x0.3, hr_recov x0.3"]
    TYPE -->|MI| MI["dc=0, df=0, tbc_time=0,<br/>tbc_thresh resampled,<br/>hrsg_cycles=0, rotor x0.5,<br/>fouling x0.3, hr_recov x0.25"]
    CI --> COST["Owner cost + HR penalty;<br/>plant offline for duration"]
    MI --> COST
```

> A calendar-triggered inspection legitimately fires **below** the EOH threshold (it's time-driven). The Sanity-6 check now exempts calendar triggers from the EOH-proximity test (see [`architecture.md`](architecture.md) §7.6).

---

## 7. The feedback loop, in one frame

The compressed mental model — how the "other side" (engineering/wear) reaches dispatch, EOH, and TBC. (The expanded narrative is in the local learning log `degradation_factors/09`.)

```mermaid
flowchart LR
    S["STATE<br/>(degraded HR, p_forced, EOH)"] -->|"degraded HR -> higher fuel cost<br/>wear hurdle near EOH limit"| D["DISPATCH<br/>(which hours/modes run)"]
    D -->|"fired hours, starts,<br/>ambient over those hours"| W["WEAR<br/>update_stress"]
    W --> S
    S -->|"hazard"| O["FORCED OUTAGE<br/>(+ trip wear)"]
    O --> W
    S -->|"EOH + calendar"| I["INSPECTION<br/>(resets state)"]
    I --> S
    D --> C["LTSA + P/L"]
    O --> C
    I --> C
```

---

## 8. Two meters, not one — the EOH vs physical-damage distinction

Why the model tracks both a contractual clock and a physical-damage state (from learning log `degradation_factors/01`).

```mermaid
flowchart TD
    OP["Operation:<br/>fired hours, starts, trips, ambient"]
    OP --> EOH["EOH<br/>(contractual clock)"]
    OP --> PD["dc + df<br/>(physical creep-fatigue damage)"]

    EOH --> M1["When is inspection<br/>due / billed?"]
    M1 --> LTSA["Inspection timing,<br/>fees, EOH reserve, overage"]

    PD --> CPL{"dc&gt;0.05 AND df&gt;0.05<br/>AND dc+df&gt;D_LIM(0.7)?"}
    CPL -->|yes| HALVE["creep-fatigue interaction:<br/>halve both (Miner coupling)"]
    PD --> M2["How risky is the<br/>hot section NOW?"]
    M2 --> RISK["Forced-outage probability<br/>(P_creep, P_combustion)"]
```

A plant can look fine on the EOH clock while `dc+df` quietly climbs — that hidden risk is exactly why the physical meter exists.

---

## 9. The forward scenario engine (`src/forward`)

How the *same* daily engine becomes a forward P10/P50/P90 valuation. Built (RT default, ~25 analog windows). Impl docs: [`implementation/forward/`](../implementation/forward/); design: [`plans/forward_engine_plan.md`](../plans/forward_engine_plan.md).

```mermaid
flowchart TD
    SEAS["SEAS5 ensemble forecast<br/>(weather_forecast_seas5.json)"] --> SEL
    HIST["Historical spine<br/>price (RT) / weather / gas<br/>1999-2026"] --> SEL

    subgraph S["select.py — temperature analog"]
        SEL["score each Apr-Mar window:<br/>z-anomaly vs SEAS5 (Apr-Oct)<br/>→ softmax → probability"]
    end
    SEL --> BUILD["build.py<br/>eligible windows → scenario specs<br/>(span + probability)"]
    BUILD --> RUN

    subgraph R["run.py — over each scenario"]
        RUN["slice market to window span<br/>→ gt_engine.run_path (charts 1-8)<br/>→ per-scenario Net P/L"]
    end
    RUN --> AGG["probability-weighted<br/>P10 / P50 / P90"]
    AGG --> OUT["per_path.parquet · quantiles.json<br/>· manifest · notebook 06 charts/card"]

    classDef eng fill:#e8f8f0,stroke:#16a085;
    class RUN eng;
```

**Key**: `run.py` calls the **same `gt_engine.run_path`** that charts 1–8 describe — once per analog window, then weights the outcomes by the temperature-analog probability. Each scenario starts from the **aged historical end-state** for that mode (`aged_start=True`, ADR-009) — not a fresh plant — so the A/B/C wear policy reflects realistic accumulated wear. RT's 25-window pool spans multiple gas regimes, surfacing the high-gas-year downside a DA-only 2017+ pool would miss. Basis is selectable (`basis="RT"` default). Caveat unchanged: absolute level isn't representative (energy-only + placeholder LTSA) — the *distribution shape* is the deliverable.

---

## Cross-references

- [`architecture.md`](architecture.md) — the prose: §2 (three-layer loop), §5 (daily loop, state vector, forced-outage, inspections), §7.6 (the Sanity-6 fix)
- [`pnl_ledger.md`](pnl_ledger.md) — the cost/revenue components behind "LTSA + P&L"
- [`dispatch_mechanics.md`](dispatch_mechanics.md) — operating mode × policy mode detail
- [`extra/temperature_load_fidelity.md`](extra/temperature_load_fidelity.md) — the commitment hurdle, ambient wear, and the deferred load half
- ADRs [006](../decisions/006-ambient-weighted-wear.md) (ambient wear) and [007](../decisions/007-creep-wiring-and-trip-wear.md) (creep wiring + trip wear)
