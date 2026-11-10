# Independent verification and evaluation record

Generated: 2026-11-10T08:17:22+00:00 | Checker: `verify.py` | Engine: `loan_compare.py` v1.0.0

**Result: 83/83 checks passed, 0 failed.**

Two different checking methods were used, as the project brief asks:

1. **Independent recomputation** - the checker re-reads the saved schedule CSVs and the original offers CSV, finds the level payment by bisection on a recursive balance equation (not the annuity closed form), and solves the IRR by Newton's method with an analytic derivative (not the engine's bisection). It then checks the cash-flow identities and NPV=0 on the saved numbers.
2. **External reference / changed-input / error battery** - a known-answer 12-month, 12% p.a. loan compared with a spreadsheet PMT reference, six changed-input cases, eight invalid-input cases and one CLI error-behaviour case.

The naive baseline (pick the lowest headline nominal rate) is recorded so the ranking can be compared with a simple heuristic.

| Case / input | Method / baseline | Expected / reference | Actual | Pass | Note |
|---|---|---|---|:---:|---|
| run integrity | summary.json offer count == offers CSV row count | 4 | 4 | PASS |  |
| run integrity | all engine self-checks pass | True | True | PASS | Engine self-checks are not independent; see the recomputations below. |
| A1_LOW_RATE_FEE | schedule row count == term_months | 36 | 36 | PASS | Re-read from the saved schedule CSV. |
| A1_LOW_RATE_FEE | interest_t = opening_t * monthly rate | max abs error <= 1e-06 | 5.002e-11 | PASS |  |
| A1_LOW_RATE_FEE | closing_t = opening_t - principal_t | max abs error <= 1e-06 | 1.164e-10 | PASS |  |
| A1_LOW_RATE_FEE | outflow_t = interest + principal + monthly fee | max abs error <= 1e-06 | 1.000e-10 | PASS |  |
| A1_LOW_RATE_FEE | sum of principal == original principal | 180000.000000 | 180000.000000 | PASS |  |
| A1_LOW_RATE_FEE | final closing balance == 0 | 0 | 0.000e+00 | PASS |  |
| A1_LOW_RATE_FEE | sum(outflows) = interest + principal + all monthly fees | 194793.823282 | 194793.823282 | PASS |  |
| A1_LOW_RATE_FEE | level instalment: bisection on balance recursion vs engine closed form | 5410.939536 | 5410.939536 | PASS | Independent algorithm; equality supports the annuity formula. |
| A1_LOW_RATE_FEE | first schedule outflow == level instalment + monthly fee | 5410.939536 | 5410.939536 | PASS |  |
| A1_LOW_RATE_FEE | effective APR: Newton IRR vs engine bisection IRR | 0.069003688 | 0.069003688 | PASS | Different root-finding method on the same saved cash flows. |
| A1_LOW_RATE_FEE | NPV of saved cash flows at independently solved IRR == 0 | \|NPV\| <= 1e-06 | 4.420e-10 | PASS |  |
| A1_LOW_RATE_FEE | all-in cost == total interest + all fees | 19293.823282 | 19293.823282 | PASS |  |
| A1_LOW_RATE_FEE | all-in cost == sum(outflows) - net disbursement | 19293.823282 | 19293.823282 | PASS |  |
| A1_LOW_RATE_FEE | peak outflow == max of saved outflows | 5410.939536 | 5410.939536 | PASS |  |
| A1_LOW_RATE_FEE | affordability flag matches saved peak vs binding ceiling | True | True | PASS |  |
| A2_NO_FEE | schedule row count == term_months | 36 | 36 | PASS | Re-read from the saved schedule CSV. |
| A2_NO_FEE | interest_t = opening_t * monthly rate | max abs error <= 1e-06 | 4.883e-11 | PASS |  |
| A2_NO_FEE | closing_t = opening_t - principal_t | max abs error <= 1e-06 | 1.164e-10 | PASS |  |
| A2_NO_FEE | outflow_t = interest + principal + monthly fee | max abs error <= 1e-06 | 1.010e-10 | PASS |  |
| A2_NO_FEE | sum of principal == original principal | 180000.000000 | 180000.000000 | PASS |  |
| A2_NO_FEE | final closing balance == 0 | 0 | 0.000e+00 | PASS |  |
| A2_NO_FEE | sum(outflows) = interest + principal + all monthly fees | 198016.184800 | 198016.184800 | PASS |  |
| A2_NO_FEE | level instalment: bisection on balance recursion vs engine closed form | 5500.449578 | 5500.449578 | PASS | Independent algorithm; equality supports the annuity formula. |
| A2_NO_FEE | first schedule outflow == level instalment + monthly fee | 5500.449578 | 5500.449578 | PASS |  |
| A2_NO_FEE | effective APR: Newton IRR vs engine bisection IRR | 0.063000000 | 0.063000000 | PASS | Different root-finding method on the same saved cash flows. |
| A2_NO_FEE | NPV of saved cash flows at independently solved IRR == 0 | \|NPV\| <= 1e-06 | 4.702e-10 | PASS |  |
| A2_NO_FEE | all-in cost == total interest + all fees | 18016.184800 | 18016.184800 | PASS |  |
| A2_NO_FEE | all-in cost == sum(outflows) - net disbursement | 18016.184800 | 18016.184800 | PASS |  |
| A2_NO_FEE | peak outflow == max of saved outflows | 5500.449578 | 5500.449578 | PASS |  |
| A2_NO_FEE | affordability flag matches saved peak vs binding ceiling | True | True | PASS |  |
| A3_SHORT_TERM | schedule row count == term_months | 24 | 24 | PASS | Re-read from the saved schedule CSV. |
| A3_SHORT_TERM | interest_t = opening_t * monthly rate | max abs error <= 1e-06 | 4.934e-11 | PASS |  |
| A3_SHORT_TERM | closing_t = opening_t - principal_t | max abs error <= 1e-06 | 1.019e-10 | PASS |  |
| A3_SHORT_TERM | outflow_t = interest + principal + monthly fee | max abs error <= 1e-06 | 1.000e-10 | PASS |  |
| A3_SHORT_TERM | sum of principal == original principal | 180000.000000 | 180000.000000 | PASS |  |
| A3_SHORT_TERM | final closing balance == 0 | 0 | 0.000e+00 | PASS |  |
| A3_SHORT_TERM | sum(outflows) = interest + principal + all monthly fees | 193026.091804 | 193026.091804 | PASS |  |
| A3_SHORT_TERM | level instalment: bisection on balance recursion vs engine closed form | 8042.753825 | 8042.753825 | PASS | Independent algorithm; equality supports the annuity formula. |
| A3_SHORT_TERM | first schedule outflow == level instalment + monthly fee | 8042.753825 | 8042.753825 | PASS |  |
| A3_SHORT_TERM | effective APR: Newton IRR vs engine bisection IRR | 0.068000000 | 0.068000000 | PASS | Different root-finding method on the same saved cash flows. |
| A3_SHORT_TERM | NPV of saved cash flows at independently solved IRR == 0 | \|NPV\| <= 1e-06 | 1.146e-10 | PASS |  |
| A3_SHORT_TERM | all-in cost == total interest + all fees | 13026.091804 | 13026.091804 | PASS |  |
| A3_SHORT_TERM | all-in cost == sum(outflows) - net disbursement | 13026.091804 | 13026.091804 | PASS |  |
| A3_SHORT_TERM | peak outflow == max of saved outflows | 8042.753825 | 8042.753825 | PASS |  |
| A3_SHORT_TERM | affordability flag matches saved peak vs binding ceiling | False | False | PASS |  |
| A4_EQUAL_PRINCIPAL | schedule row count == term_months | 36 | 36 | PASS | Re-read from the saved schedule CSV. |
| A4_EQUAL_PRINCIPAL | interest_t = opening_t * monthly rate | max abs error <= 1e-06 | 3.342e-11 | PASS |  |
| A4_EQUAL_PRINCIPAL | closing_t = opening_t - principal_t | max abs error <= 1e-06 | 0.000e+00 | PASS |  |
| A4_EQUAL_PRINCIPAL | outflow_t = interest + principal + monthly fee | max abs error <= 1e-06 | 0.000e+00 | PASS |  |
| A4_EQUAL_PRINCIPAL | sum of principal == original principal | 180000.000000 | 180000.000000 | PASS |  |
| A4_EQUAL_PRINCIPAL | final closing balance == 0 | 0 | 0.000e+00 | PASS |  |
| A4_EQUAL_PRINCIPAL | sum(outflows) = interest + principal + all monthly fees | 197452.500000 | 197452.500000 | PASS |  |
| A4_EQUAL_PRINCIPAL | equal-principal first outflow | 5915.000000 | 5915.000000 | PASS |  |
| A4_EQUAL_PRINCIPAL | equal-principal outflow is strictly declining | first > last | 5915.00 > 5054.58 | PASS |  |
| A4_EQUAL_PRINCIPAL | effective APR: Newton IRR vs engine bisection IRR | 0.067405788 | 0.067405788 | PASS | Different root-finding method on the same saved cash flows. |
| A4_EQUAL_PRINCIPAL | NPV of saved cash flows at independently solved IRR == 0 | \|NPV\| <= 1e-06 | 1.410e-10 | PASS |  |
| A4_EQUAL_PRINCIPAL | all-in cost == total interest + all fees | 18652.500000 | 18652.500000 | PASS |  |
| A4_EQUAL_PRINCIPAL | all-in cost == sum(outflows) - net disbursement | 18652.500000 | 18652.500000 | PASS |  |
| A4_EQUAL_PRINCIPAL | peak outflow == max of saved outflows | 5915.000000 | 5915.000000 | PASS |  |
| A4_EQUAL_PRINCIPAL | affordability flag matches saved peak vs binding ceiling | True | True | PASS |  |
| baseline | naive lowest-headline-rate pick (from saved summary) | recorded | A1_LOW_RATE_FEE | PASS | Simple heuristic used as the comparison reference. |
| baseline | lowest effective APR among all offers | A2_NO_FEE | A2_NO_FEE | PASS |  |
| K1 known answer | reference level payment | 888.487886783 | 888.487886783 | PASS | closed-form ordinary annuity / =PMT(1%,12,10000) in Excel or Google Sheets |
| K1 known answer | reference total paid | 10661.854641401 | 10661.854641401 | PASS |  |
| K1 known answer | reference total interest | 661.854641401 | 661.854641401 | PASS |  |
| K1 known answer | independent bisection payment vs external reference | 888.487886783 | 888.487886783 | PASS |  |
| C1 changed input | +1 percentage point on the nominal rate | higher payment and higher APR | 3650.09 -> 3704.70; APR 5.990% -> 6.990% | PASS |  |
| C2 changed input | +2% upfront fee (HKD 2,400) | payment unchanged; APR up; all-in cost up by exactly 2,400 | payment 3650.09 -> 3650.09; cost 11403.20 -> 13803.20; APR 5.990% -> 7.352% | PASS | Shows why a headline rate alone cannot rank fee-bearing offers. |
| C3 changed input | term 36 -> 48 months | lower monthly payment, higher total interest | payment 3650.09 -> 2817.65; interest 11403.20 -> 15247.36 | PASS |  |
| C4 changed input | +HKD 50 monthly fee | peak outflow up by exactly 50; total fees up by 50 * 36 | peak +50.00; fees +1800.00 | PASS |  |
| C5 changed input | budget cap 3,000 vs 5,000 | affordability flips NO -> YES | 3,000: False; 5,000: True | PASS |  |
| C6 changed input | annuity -> equal-principal plan | declining outflow and lower total interest | first 3932.33 > last 3349.97; interest 11403.20 -> 11081.50 | PASS |  |
| E1 invalid input | negative principal | clear InputError, no calculation | InputError: Input validation failed; nothing was calculated. Fix the following: | PASS |  |
| E1 invalid input | zero term | clear InputError, no calculation | InputError: Input validation failed; nothing was calculated. Fix the following: | PASS |  |
| E1 invalid input | unknown repayment type | clear InputError, no calculation | InputError: Input validation failed; nothing was calculated. Fix the following: | PASS |  |
| E1 invalid input | non-numeric rate | clear InputError, no calculation | InputError: Input validation failed; nothing was calculated. Fix the following: | PASS |  |
| E1 invalid input | rate above 100% | clear InputError, no calculation | InputError: Input validation failed; nothing was calculated. Fix the following: | PASS |  |
| E1 invalid input | duplicate offer id | clear InputError, no calculation | InputError: Input validation failed; nothing was calculated. Fix the following: | PASS |  |
| E1 invalid input | missing offer id | clear InputError, no calculation | InputError: Input validation failed; nothing was calculated. Fix the following: | PASS |  |
| E1 invalid input | fractional term | clear InputError, no calculation | InputError: Input validation failed; nothing was calculated. Fix the following: | PASS |  |
| E2 error behaviour | CLI on invalid input exits nonzero and writes nothing | returncode 3 + 'INPUT ERROR' on stderr | returncode 3; stderr="INPUT ERROR: Input validation failed; nothing was calculated. Fix the following:\n  - row 2 (A): 'principal' mu"; output folder created=False | PASS |  |

## What these checks establish - and what they do not

- They establish internal arithmetic consistency, agreement between two different implementations of the payment and IRR, and correct rejection of malformed inputs.
- They do **not** establish that the synthetic offer data are real bank quotes, that any lender's quotation uses this fee timing, or that a real borrower's rate would stay fixed. The fee-withholding convention is an assumption, stated in SKILL.md.
- All-in cost is a nominal sum and is not discounted; APR/EAR is the time-value-adjusted measure. Ranking by these two can differ, which is expected.
- The known-answer reference was derived from the standard annuity formula, which is also the basis of the engine's payment formula; the independent bisection payment and the spreadsheet PMT value provide the cross-check.

Verified run folder: `outputs/case_A`

Original offers file: `skills/loan-offer-comparison/examples/offers_case_A.csv`
