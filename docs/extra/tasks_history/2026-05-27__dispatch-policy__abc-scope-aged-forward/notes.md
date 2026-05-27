# Notes — A/B/C scope + aged-state forward (2026-05-27)

## The mechanism, in one place

`wear_penalty_mult(mode, eoh_headroom)` (engine.py:296) is the ONLY thing distinguishing A/B/C. The base start economics (commitment hurdle = full Kumar start C&M; wear hurdle = 0.42 × that, amortized — engine.py:677/686) is **identical for all three modes and already derived/defensible**. A/B/C differ only in a near-threshold preservation premium:

```
wear_mult by EOH headroom (= threshold − current EOH):
  headroom   B      C
   4000     1.00   1.00
   3000     1.50   1.75
   2000     2.00   2.50
   1000     2.50   3.25     <- B clamps at 2.5 here; C keeps climbing
      0     2.50   4.00
```
The premium only ramps below ~4,000 headroom → it's a **plant-state-gated** lever. Where you start the sim decides whether A/B/C can differ at all.

## Implementation

### engine.py — `run_path`
```python
def run_path(..., init_state_override=None) -> dict:
    state = init_state(seed=seed) if init_state_override is None else replace(init_state_override)
```
`replace()` (dataclasses, already imported line 82) takes a defensive copy so a shared aged-state object isn't mutated across scenarios. All `PlantState` fields are scalars → shallow copy is safe. Default `None` → byte-identical historical path.

### run.py — `run_forward`
```python
def run_forward(mode="A", ..., aged_start=True):
    ...
    init_override = None
    if aged_start:
        with contextlib.redirect_stdout(io.StringIO()):
            init_override = eng.run_mode(mode)["final_state"]   # one historical replay/mode
    ...
    r = eng.run_path(..., init_state_override=init_override)
```
Manifest now records `init_state` ("aged_historical_end_state"/"fresh") + `init_eoh`.

## Commands used
```bash
# Regression (byte-identical gate) — MUST pass
source .venv/bin/activate && python -m pytest tests/test_gt_engine_regression.py -q
#   -> 6 passed

# A/B/C under aged vs fresh start (the proof)
python -c "from forward.run import run_forward; ...  # loop A/B/C x aged/fresh, print P10/P50/P90"

# Diagnostic: aged EOH per mode + is B==C at path level?
python -c "import gt_engine.engine as eng; ... run_mode(m)['final_state'].eoh ; np.allclose(B,C)"
```

## Verification / results

**Regression**: 6/6 byte-identical (default `init_state_override=None` path untouched).

**Forward Net P&L P50 ($M)**:
| start | A | B | C |
|---|---:|---:|---:|
| fresh (EOH 24k, 1-yr) | −16.15 | −16.15 | −16.15 (byte-identical) |
| aged (each mode's history, 1-yr) | −16.35 | −16.58 | −16.58* |

\* B vs C are NOT identical — max path diff: fired_hours 4, total_mwh ~916, net ~$0.14M (below $M rounding).

**Aged-start state per mode** (the key to reading the result):
| mode | aged EOH | insp_done | rotor |
|---|---:|---:|---:|
| A | 42,138 | 1 | 0.176 |
| B | 42,370 | 0 | 0.351 |
| C | 42,370 | 0 | 0.351 |

## Key insights

1. **The "forward A=B=C" was a self-imposed assumption, not a model property.** Fresh-start + 1-yr horizon parks EOH ~20k from the 48k threshold → `wear_mult` pinned at 1.0 for all → identical. Fixed by carrying aged state.

2. **A's separation is mostly INHERITED state, not in-forward policy.** A took its MI in 2025 history → enters the forward freshly overhauled (EOH 42,138, rotor 0.176, 1 inspection done). B/C deferred the MI → enter mid-life (EOH 42,370, rotor 0.351). That inherited difference drives most of A's ~$0.2M edge — not divergent in-forward dispatch.

3. **B ≈ C is a definition/operating-regime mismatch.** C's distinctive behavior lives at headroom < 1,000 (where B clamps at 2.5× but C climbs to 4.0×). A 1-yr forward from EOH ~42k keeps headroom ~5,630 → ~1,630 — **never enters that region** — so C's extra conservatism stays dormant. The policy difference exists where the asset never operates.

4. **No mode reaches the 48k MI threshold in the 1-yr window** (ends ~46k). So the in-forward policy effect is genuinely weak; it would only bite with a **multi-year forward** that crosses the threshold in-window.

5. **Corrected a wrong first-draft finding.** Initially wrote "the MI fires in-window regardless of policy" — false. Verified against the numbers and rewrote. Trust-but-verify the model's own output before documenting it.

6. **The base wear cost is already derived** (Kumar start C&M × 0.42). Only the *premium magnitudes* (2.5/4.0, geometry) are invented — that's the narrow thing ADR-009 §4 defers, not the whole hurdle.
