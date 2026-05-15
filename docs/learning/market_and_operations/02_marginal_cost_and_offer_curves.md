# Marginal Cost And Offer Curves

## What This Guide Is

This guide explains how heat-rate curves become market-facing offer prices.

Read these first:

- [Heat Rate](../basics/02_heat_rate.md)
- [Start Costs And VOM](../basics/04_start_costs_and_vom.md)
- [Dispatch And The Daily Loop](../basics/05_dispatch_and_daily_loop.md)
- [Operating Range: Pmin And Pmax](./01_operating_range_pmin_pmax.md)

> Plant-Type Note
> Marginal cost and offer curves are market/operations concepts. The formulas are broad, but the right curve depends on plant type, operating mode, market rules, fuel basis, emissions costs, start costs, and whether the plant is simple-cycle, CCGT, aeroderivative, frame, or CHP.

## First-Time Reader Map

If this topic is new, start with the basic chain:

```text
fuel curve
  |
  v
incremental heat rate
  |
  v
marginal fuel cost
  |
  v
total marginal cost
  |
  v
offer curve
```

Key terms:

| Term | First-time meaning |
| :--- | :--- |
| Fuel curve | Relationship between MW output and fuel burn. |
| Average heat rate | Total fuel divided by total MWh. |
| Incremental heat rate | Extra fuel needed for the next extra MWh. |
| Marginal cost | Cost to produce one more MWh at a given output level. |
| VOM | Variable operating and maintenance cost per MWh. |
| Emissions cost | Cost from CO2, NOx, or other emissions programs if applicable. |
| Offer curve | MW/price schedule offered to a market or used internally for dispatch. |
| Step offer | Offer with flat price blocks. |
| Piecewise-linear offer | Offer where price changes smoothly between MW breakpoints. |
| Pmin/Pmax | Feasible online MW range. |

## Why This Matters

The dispatch model needs to know whether a MWh is profitable.

```text
power price
  compared with
fuel cost + VOM + emissions + wear / start economics
```

Heat rate tells the fuel cost side. Offer curves turn that cost into market-ready MW/price blocks.

For Step 2, this matters because:

| Question | Why marginal cost helps |
| :--- | :--- |
| Should the plant run? | Compare expected price to cost. |
| How many MW should it produce? | Higher MW may have different incremental heat rate. |
| How should offers be priced? | Offer blocks need cost-based prices. |
| Where does Pmin/Pmax matter? | Offer MW blocks must stay inside feasible range. |
| How does gas price change dispatch? | Gas price multiplies heat rate directly. |

## Average Vs Incremental Heat Rate

Average heat rate answers:

```text
How much fuel did the plant use per MWh overall?
```

Incremental heat rate answers:

```text
How much extra fuel is needed for the next extra MWh?
```

Offer curves usually need incremental heat rate.

| Heat-rate type | Formula idea | Common use |
| :--- | :--- | :--- |
| Average heat rate | total fuel / total MWh | Reporting, performance comparison, simple examples. |
| Incremental heat rate | slope of fuel curve | Marginal cost, offer blocks, economic dispatch. |

Beginner warning:

```text
average heat rate is not automatically the right offer price basis
```

## Fuel Curve

A common simple fuel curve is:

```text
F(P) = a * P^2 + b * P + c
```

Where:

| Symbol | Meaning |
| :--- | :--- |
| `F(P)` | Fuel burn at output `P`, usually MMBtu/h. |
| `P` | Power output, MW. |
| `a`, `b`, `c` | Fitted curve parameters from operating data or OEM curves. |

Average heat rate:

```text
HR_avg(P) = F(P) / P
```

Incremental heat rate:

```text
HR_inc(P) = 2 * a * P + b
```

The local plant-model reference uses this structure for offer-curve work. For the InfraSure docs, treat it as a practical market-operations method, not as a universal OEM model.

## Marginal Cost Formula

Core marginal cost:

```text
MC(P,t) =
  gas_price(t) * HR_inc(P)
  + VOM
  + emissions_cost
```

Where:

| Item | Unit | Meaning |
| :--- | :--- | :--- |
| `MC(P,t)` | $/MWh | Marginal cost at output P and time t. |
| `gas_price(t)` | $/MMBtu | Delivered gas price for the relevant time. |
| `HR_inc(P)` | MMBtu/MWh | Incremental heat rate at output P. |
| `VOM` | $/MWh | Variable O&M cost. |
| `emissions_cost` | $/MWh | Emissions adder if applicable. |

Simple example:

| Item | Value |
| :--- | ---: |
| Incremental heat rate | 8.2 MMBtu/MWh |
| Gas price | $4.00/MMBtu |
| VOM | $3.00/MWh |
| Emissions cost | $0.00/MWh |

```text
fuel marginal cost = 8.2 * 4.00
fuel marginal cost = $32.80/MWh

total marginal cost = 32.80 + 3.00 + 0.00
total marginal cost = $35.80/MWh
```

## What About Start Cost?

Start cost is real, but it is not the same as marginal fuel cost.

| Cost type | Trigger | Natural treatment |
| :--- | :--- | :--- |
| Fuel marginal cost | Each additional MWh | Marginal cost / offer price. |
| VOM | Each MWh | Marginal cost / offer price. |
| Emissions cost | Each MWh or fuel burn | Marginal cost / offer price. |
| Start cost | Start event | Commitment cost or spread across expected MWh. |
| EOH/wear cost | Operation or starts | Dispatch penalty, reserve, or wear adder depending model design. |

For learning:

```text
marginal cost prices energy MWh
start cost affects whether the plant should commit
```

In a simplified offer curve, start cost may be converted into a $/MWh premium across an expected run. That is useful for quick screening, but it can mislead if the actual run length is uncertain.

## Offer Curve Basics

An offer curve is a set of MW and price points.

```text
MW range from Pmin to Pmax
        |
        v
split into blocks
        |
        v
price each block using marginal cost
```

Example:

| Block | MW range | Price basis |
| :--- | :--- | :--- |
| 1 | 100 to 200 MW | MC at 200 MW. |
| 2 | 200 to 300 MW | MC at 300 MW. |
| 3 | 300 to 400 MW | MC at 400 MW. |

Why right-edge pricing is common in simple examples:

```text
if marginal cost rises with MW,
right-edge pricing avoids underpricing the last MW in the block
```

## Step Vs Piecewise-Linear Offers

Two common shapes:

| Offer type | Plain meaning | When useful |
| :--- | :--- | :--- |
| Step offer | Price is flat inside each block. | Simple, transparent, conservative when priced at right edge. |
| Piecewise-linear offer | Price slopes between breakpoints. | Smoother approximation of a rising marginal-cost curve. |

Step offer:

```text
Price
 $70 |              ______ block 3
 $55 |        _____|
 $40 |  _____|
     +-----------------------------
        Pmin        MW        Pmax
```

Piecewise-linear offer:

```text
Price
 $70 |             /
 $55 |        ____/
 $40 |  _____/
     +-----------------------------
        Pmin        MW        Pmax
```

Guardrails:

| Guardrail | Why |
| :--- | :--- |
| MW breakpoints must increase. | Market blocks must be physically valid. |
| Prices should not decrease if marginal cost rises. | Avoids incoherent offers. |
| Blocks must fit within Pmin/Pmax. | Avoids impossible MW offers. |
| Curve must stay within fitted data domain. | Avoids extrapolating beyond observed/OEM support. |

## Worked Example: Three Offer Blocks

Assume:

| Item | Value |
| :--- | ---: |
| Pmin | 100 MW |
| Pmax | 400 MW |
| Gas price | $4.00/MMBtu |
| VOM | $3/MWh |
| Emissions | $0/MWh |

Assume incremental heat rates at right edge:

| Block | Right-edge MW | HR_inc | Fuel MC | Total MC |
| :--- | ---: | ---: | ---: | ---: |
| 1 | 200 MW | 8.0 | $32.00/MWh | $35.00/MWh |
| 2 | 300 MW | 8.4 | $33.60/MWh | $36.60/MWh |
| 3 | 400 MW | 9.0 | $36.00/MWh | $39.00/MWh |

Offer structure:

```text
0 MW        100        200        300        400
|-----------|----------|----------|----------|
 offline      block 1    block 2    block 3
             $35.00    $36.60    $39.00
```

## Plant-Type Variations

| Plant type | Offer-curve issue |
| :--- | :--- |
| Simple-cycle GT | Often high heat rate and high start-cost sensitivity; short-run economics matter. |
| Aeroderivative GT | Fast-start and reserve value may matter as much as energy offer price. |
| Frame simple-cycle GT | Larger MW blocks and start/ramp constraints can shape offers. |
| 1x1 CCGT | Heat rate and Pmin/Pmax differ from full 2x1 operation. |
| 2x1 CCGT | May need separate mode curves and blocky operating ranges. |
| CHP / cogeneration | Steam/heat obligations can change marginal opportunity cost. |

## Historical Calibration Vs Forward Offer

The offer model may use historical inputs:

```text
historical fuel curve
historical Pmin/Pmax
historical heat-rate behavior
```

But the actual offer for a future day also needs forward inputs:

```text
gas price for the bid period
expected weather if using weather adjustment
availability / outage state
plant state and degradation
market rules
```

Do not call a historical fuel curve a forecast by itself.

## How This Feeds Step 2

Step 2 dispatch uses offer/marginal-cost logic this way:

```text
hourly price
  |
  v
compare with marginal cost curve
  |
  v
respect Pmin/Pmax and commitment constraints
  |
  v
choose online/offline and MW
```

The daily state update then records:

- MWh
- fuel burn
- fired hours
- starts
- load swings
- EOH
- degradation increments
- cashflow outputs

## What The Framework Includes

| Included item | Why it matters |
| :--- | :--- |
| Heat-rate basics | Converts gas price into fuel cost. |
| Average vs incremental heat-rate warning | Helps avoid using the wrong cost basis. |
| Start cost and VOM guide | Separates fuel, VOM, start, reserve, and overage concepts. |
| Pmin/Pmax guide | Defines MW range for offers. |
| Step 2 blueprint plan | Explains where dispatch and operating economics belong. |

## What The Framework Leaves Out

| Missing detail | Why it matters |
| :--- | :--- |
| Exact fuel-curve coefficients by plant/mode | Needed for actual marginal cost. |
| Market-specific offer format | PJM, NYISO, bilateral, and internal dispatch formats differ. |
| Start-cost allocation method | Commitment cost should not be casually buried in marginal cost. |
| Emissions price treatment | CO2/NOx adders may matter in some markets. |
| Mode-specific curves | CCGT 1x1 and 2x1 operation can have different curves. |
| Validation against cleared dispatch | Needed before relying on offers for investment decisions. |

## Source Basis And Certainty

| Source | Use in this guide | Certainty |
| :--- | :--- | :--- |
| [Heat Rate](../basics/02_heat_rate.md) | Average vs incremental heat-rate foundation. | Green for concept. |
| [Start Costs And VOM](../basics/04_start_costs_and_vom.md) | Cost buckets and start-cost distinction. | Green for structure; values are plant-specific. |
| [Operating Range: Pmin And Pmax](./01_operating_range_pmin_pmax.md) | MW boundary for offer blocks. | Green for concept. |
| `plant model/production_planning_simple_plant_model.md` | Fuel curve, marginal cost, and offer-block workflow. | Green as local method; plant data needed. |
| `plant model/offer_curve_info/OFFER_CURVE_STEP_VS_LINEAR.md` | Step vs piecewise-linear offer framing. | Green for offer-shape concept. |

## Open Questions Before Implementation

| Question | Why it matters |
| :--- | :--- |
| Which market format is required? | Determines MW/price fields and constraints. |
| Are offers for energy only or also reserves/capacity? | Products have different pricing logic. |
| Are fuel curves unit-level, plant-level, or mode-level? | Prevents mixing 1x1 and 2x1 behavior. |
| How should start costs enter dispatch? | Event cost vs $/MWh premium changes decisions. |
| Which gas price basis should be used? | Delivered gas cost may differ from hub price. |
| Should wear or EOH penalty be included in offers? | Depends on market rules and internal dispatch policy. |
| How will curves be validated? | Backtesting is needed before investor use. |

## Quick Recap

```text
fuel curve -> incremental heat rate -> marginal cost -> offer blocks
```

Use average heat rate for simple performance understanding. Use incremental heat rate for marginal cost and offer pricing.
