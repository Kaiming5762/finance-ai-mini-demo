# Compact evaluation record (Appendix F template)

Reference: `final project_instructions.pdf`, Appendix F. Full 83-row tables:
`outputs/case_A/verification.md` and `outputs/fresh_case_B/verification.md`.
Run records: `E1`-`E4` in this folder. Totals are from `verify.py`, not from chat.

| Case / input version | Method / baseline | Expected / reference result | Actual result | Pass / fail | Correction or limitation |
|---|---|---|:---:|---|---|
| Case A, `offers_case_A.csv` + `borrower_case_A.json`, 10 Nov 2026 | Run integrity: saved summary vs source CSV | 4 offers, 0 validation errors | 4 offers, 0 errors, 0 duplicates | PASS | - |
| Case A | Engine's 7 internal identities per offer | 28/28 pass | 28/28 pass | PASS | Self-check; not independent |
| K1 known answer: 10,000 @ 12% p.a., 12 months, no fees | External spreadsheet reference `=PMT(1%,12,10000)` | PMT 888.487886783; total paid 10,661.854641401; interest 661.854641401 | identical to 9 dp | PASS | Reference shares the textbook annuity formula; the independent bisection payment is the cross-check |
| Case A offers A1-A4 | Independent level payment: bisection on balance recursion vs engine closed form | equal within 1e-6 | equal (A2: 5,500.449578 both) | PASS | - |
| Case A offers A1-A4 | Independent IRR: Newton with analytic derivative vs engine bisection | equal within 1e-8 | equal (A1: 0.069003688 both) | PASS | Newton initially failed on its stopping rule; fixed, see below |
| Case A offers A1-A4 | Cash-flow identities + NPV=0 on saved schedule CSVs | max abs error <= 1e-6 | max ~5e-11 | PASS | CSV written at 10 decimals |
| C1 rate +1 pp | Changed input | payment and APR rise | 3,650.09 -> 3,704.70; APR 5.990% -> 6.990% | PASS | 6 changed-input cases only |
| C2 +2% upfront fee (2,400) | Changed input | payment unchanged; cost +2,400; APR up | payment unchanged; cost 11,403.20 -> 13,803.20; APR 5.990% -> 7.352% | PASS | Demonstrates the headline-rate trap |
| C3 term 36 -> 48 months | Changed input | payment down, total interest up | 3,650.09 -> 2,817.65; interest 11,403.20 -> 15,247.36 | PASS | - |
| C4 +50 monthly fee | Changed input | peak +50 exactly; fees +1,800 | +50.00 and +1,800.00 | PASS | - |
| C5 budget cap 3,000 vs 5,000 | Changed input | affordability flips NO -> YES | False -> True | PASS | - |
| C6 annuity -> equal_principal | Changed input | declining outflow; lower total interest | 3,932.33 > 3,349.97; interest 11,403.20 -> 11,081.50 | PASS | Same principal/rate/term |
| E1 eight malformed CSVs | Invalid-input handling | clear `InputError`, no calculation | 8/8 rejected | PASS | - |
| E2 CLI on bad CSV | Error behaviour | exit 3, `INPUT ERROR`, no output folder | exactly as expected | PASS | - |
| Naive baseline | Lowest headline nominal rate vs lowest effective APR | disagreement expected on a fee-bearing offer | Case A: A1 vs A2; Case B: B1 vs B2 | PASS | Heuristic, not a gold standard |
| Case B, `offers_case_B.csv` (fresh run) | Full `verify.py` on the reused Skill, new output folder | 83/83 pass | 83/83 passed, 0 failed | PASS | Self-reproduction, not peer reuse |
| **Total, Case A** | `verify.py` | - | **83/83 passed, 0 failed** | PASS | - |
| **Total, Case B** | `verify.py` | - | **83/83 passed, 0 failed** | PASS | - |

## Failure and correction (recorded, not hidden)

| Attempt | Result | Cause | Fix | Verification |
|---|---|---|---|---|
| First `verify.py` run | 11/12, exit 5, `AssertionError: Newton IRR did not converge` | Newton converged in 3-4 steps (NPV ~1e-11) but the stopping rule broke on a tiny step before accepting a small NPV residual, then raised | Relative convergence criterion `tol * net_disbursement` (NPV is in currency units) and return the iterate when the Newton step is tiny | Re-run: 83/83 pass on both cases |

## Conditions kept consistent

Units (one currency per case), periods (monthly), price/cost basis (nominal
all-in cost vs IRR-based APR/EAR), constraints (binding affordability ceiling)
and information timing (fees at t = 0) are fixed and documented in `SKILL.md`.
No rule was tuned after seeing test results. Cases are small and self-constructed;
this is a short, clearly defined comparison, not a benchmark suite. No timing
or token measurements were instrumented, so none are reported.
