# Placeholder Caveats — Known Issues and How They'll Be Resolved

> Tracks values currently flagged `status: placeholder` in the data spine — what's there now (the seed value), why it's wrong-by-design, what the real value will look like, and the validation path to get there.
>
> This doc is the "what model results to NOT trust until extraction completes" reference. Every model_card output (per consolidation plan §10) should reproduce the relevant subset of this doc.

---

## Why this doc exists

The assumption-tracking discipline (consolidation plan §6 + `status_taxonomy.md`) gives us nine status codes. Of those, `placeholder` is the one that requires the most explicit user-facing handling — the value in the YAML is **not** an honest estimate; it's a seed that lets the model run while the real value is pending.

If a stakeholder runs the model and reads an output without context, they might conclude that a placeholder value is a model assumption we stand behind. **It isn't.** This doc is the place to discover what's a placeholder and what its real-vs-seed delta is likely to look like.

---

## Active placeholders

### 1. `data/assets/lockport/ltsa_terms.yaml` — entire file (~40 values)

**Status**: Every leaf value in this file is `status: placeholder` (verified by `tests/test_lockport_static_profile.py::test_ltsa_all_values_placeholder`).

**Seed values**: All values are seeded from the Athens prototype `[ASSUME]` defaults documented in `docs/extra/gas-turbine-digital-twin/LTSAContract.py`.

**Why the seed is wrong-by-magnitude for Lockport**:

| Aspect | Athens (the seed) | Lockport (the actual asset) |
|---|---|---|
| Configuration | 2x1 CCGT | 3-on-1 CCGT (one more CT) |
| Vintage | Modern merchant | 1992 F-class PURPA-era |
| Counterparty type | Merchant CCGT in NYISO Zone F | Cogen in NYISO Zone A with industrial steam host |
| Likely OEM relationship | Modern GE CSA | 1992-vintage maintenance services (predates modern CSA conventions) |

**Specific seed-vs-likely-reality flags**:

- **Fixed monthly fee** (seed: $850K/month): A 1992 cogen with established maintenance practices may have a materially different fee structure — possibly lower fixed plus higher event-based, or a totally different contract architecture (PURPA-era contracts often look unlike modern CSAs).
- **CI/MI inspection costs** (seed: $3.75M / $30M total): Scale with capacity and turbine model. Lockport's 3 × 48.7 MW CTs are smaller than Athens's 2 × ~200 MW CCGT, so inspection costs likely scale down. But cogen-specific scope (steam-side coordination) may add cost.
- **OEM coverage fractions** (seed: 75% CI / 65% MI): Modern CSA assumption. 1992 vintage contract may have very different coverage.
- **Start overage baselines** (seed: 150 hot / 35 warm / 5 cold / 3 trip per year): Athens annual figures. Lockport's actual baseline depends on contract; the MOR data shows Lockport runs much fewer cycles than Athens-class merchant assets.

**What will be true post-extraction**:

- Real values from data room `3.2.6.4 Lockport Trial Balances 2024-Feb 2026.xlsx` (LTSA invoice line items) and original PURPA contract filings (NYS PSC, 1990–1992 era).
- `status` flips from `placeholder` to `real_reported` (contract terms) or `real_observed` (historical invoice averages).
- Validation: cycle-end HR guarantee, availability guarantee, escalation clauses — all should be discoverable.

**Until then — model_card disclosure**:

Every run that consumes `ltsa_terms.yaml` MUST output a banner at the top of `model_card.md`:

```
⚠ LTSA TERMS ARE PLACEHOLDERS (NOT LOCKPORT-SPECIFIC)
- Values seeded from Athens 2x1 CCGT prototype defaults
- Lockport is 3-on-1 1992 F-class cogen — different scale, vintage, counterparty
- All LTSA outputs (fixed_fee accrual, CI/MI events, overage charges, penalties) are numerically valid but deal-irrelevant
- Real values pending data room extraction (see data/assets/lockport/ltsa_terms.yaml validation_path fields)
```

The `tests/test_lockport_static_profile.py::test_ltsa_all_values_placeholder` test is intentionally fragile — it will fail the moment any value gets a real status. That failure is the signal to update this doc + flip the model_card banner.

---

### 2. `data/assets/lockport/operating_profile.yaml` → `annual_generation.yearly_summary_table`

**Status**: One field placeholder (the rest of the file is `real_observed` from MOR).

**Seed value**: `null`.

**Why placeholder**: The MOR notebook has a Stage 1 annual summary cell that aggregates daily MOR data into per-year totals (annual generation, fired hours, capacity factor, mean ambient temp) for 2021–2025. I have the 2024 correction value (192,494 MWh) explicitly from the notebook, but not the full 5-year breakdown.

**What will be true post-extraction**: When Notebook 1 (Phase G) runs the MOR loader, it should extract the yearly summary DataFrame and populate this field. Status flips to `real_observed`.

**Until then**: Not a blocker. v1 dispatch model can run without the full annual breakdown.

---

### 3. `data/assets/lockport/ltsa_terms.yaml` → `hr_penalty.guarantee_btu_per_kwh`

**Status**: `placeholder` with `value: null` (no seed even from Athens — depends on plant-specific contract).

**Why placeholder**: The HR guarantee is a contract-specific value that should be close to the plant's design heat rate. Lockport's 1992 F-class design HR is **not** in EIA-860 (boiler 6_2 reporting gap for this plant — see `engineering.yaml.generators.GEN1.has_hrsg` caveats).

**What will be true post-extraction**: Real value from contract. Status flips to `real_reported`.

**Until then**: HR penalty mechanism won't fire in v1 runs because the threshold is null. This is an honest no-op rather than a false signal.

---

## Pending placeholders (will appear later)

Future phases may add more placeholders. Examples expected:

- **Hourly observed dispatch / starts / ramps / outages** (Phase 2c of natural-gas-thermal expansion at the renewablesinfo side) — would land as additional `real_observed` rows in `operating_profile.yaml` once CEMS data is in. Until then, ramp / hot-start values stay as `assumed_techclass` from the dispatch_params lookup.
- **NYISO ICAP capacity revenue** — currently `not_applicable` in v1 per `market_context.yaml.capacity_market.modeled_in_v1 = false`. When v2 adds capacity modeling, this becomes a populated field; the DMNC test data room file is the source.
- **Forced outage rate (EFORd)** — NERC GADS data; currently completely absent from the data spine. May land as `placeholder` if/when we incorporate it.

This doc gets updated as new placeholders appear.

---

## Resolved placeholders (historical record)

(None yet. When data room extraction completes, the LTSA section above moves here with a "resolved" note + diff of seed vs real values.)

---

## How to use this doc

- **Reading a model output**: cross-reference `model_card.md` placeholder counts against this doc. Anything that affects an LTSA cost stream is not trustworthy until §1 resolves.
- **Reading a YAML file**: any `status: placeholder` value carries a `validation_path` pointing to the data room. Use that path; don't assume the seed.
- **After data room extraction**: update this doc — move the resolved section to "historical record", update the relevant YAML, regenerate model_card.

## See also

- [`status_taxonomy.md`](./status_taxonomy.md) — the 9-status definitions
- [`README.md`](./README.md) — assumption-tracking discipline overview
- [`data/assets/lockport/ltsa_terms.yaml`](../../data/assets/lockport/ltsa_terms.yaml) — the placeholder file itself
- [Consolidation plan §6](../plans/consolidation_plan.md#6-assumption-tracking-schema-first-class-principle)
- [Consolidation plan §10 anti-patterns](../plans/consolidation_plan.md#10-anti-patterns-ulysses-pact-against-future-self) — "Don't run a model and call it valid because it doesn't crash"
