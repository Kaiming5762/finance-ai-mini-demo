# Independent verification and evaluation record

Generated: 2026-11-10T08:17:23+00:00 | Checker: `verify.py` | Engine: `loan_compare.py` v1.0.0

**Result: 83/83 checks passed, 0 failed.**

Two different checking methods were used, as the project brief asks:

1. **Independent recomputation** - the checker re-reads the saved schedule CSVs and the original offers CSV, finds the level payment by bisection on a recursive balance equation (not the annuity closed form), and solves the IRR by Newton's method with an analytic derivative (not the engine's bisection). It then checks the cash-flow identities and NPV=0 on the saved numbers.
2. **External reference / changed-input / error battery** - a known-answer 12-month, 12% p.a. loan compared with a spreadsheet PMT reference, six changed-input cases, eight invalid-input cases and one CLI error-behaviour case.

The naive baseline (pick the lowest headline nominal rate) is recorded so the ranking can be compared with a simple heuristic.

| Case / input | Method / baseline | Expected / reference | Actual | Pass | Note |
|---|---|---|---|:---:|---|
| run integrity | summary.json offer count == offers CSV row count | 4 | 4 | PASS |  |
| run integrity | all engine self-checks pass | True | True | PASS | Engine self-checks are not independent; see the recomputations below. |
| B1_INDUSTRIAL | schedule row count == term_months | 60 | 60 | PASS | Re-read from the saved schedule CSV. |
| B1_INDUSTRIAL | interest_t = opening_t * monthly rate | max abs error <= 1e-06 | 4.957e-11 | PASS |  |
| B1_INDUSTRIAL | closing_t = opening_t - principal_t | max abs error <= 1e-06 | 1.746e-10 | PASS |  |
| B1_INDUSTRIAL | outflow_t = interest + principal + monthly fee | max abs error <= 1e-06 | 1.000e-10 | PASS |  |
| B1_INDUSTRIAL | sum of principal == original principal | 600000.000000 | 600000.000000 | PASS |  |
| B1_INDUSTRIAL | final closing balance == 0 | 0 | 0.000e+00 | PASS |  |
| B1_INDUSTRIAL | sum(outflows) = interest + principal + all monthly fees | 668696.027136 | 668696.027136 | PASS |  |
| B1_INDUSTRIAL | level instalment: bisection on balance recursion vs engine closed form | 11144.933786 | 11144.933786 | PASS | Independent algorithm; equality supports the annuity formula. |
| B1_INDUSTRIAL | first schedule outflow == level instalment + monthly fee | 11144.933786 | 11144.933786 | PASS |  |
| B1_INDUSTRIAL | effective APR: Newton IRR vs engine bisection IRR | 0.049705756 | 0.049705756 | PASS | Different root-finding method on the same saved cash flows. |
| B1_INDUSTRIAL | NPV of saved cash flows at independently solved IRR == 0 | \|NPV\| <= 1e-06 | 1.120e-09 | PASS |  |
| B1_INDUSTRIAL | all-in cost == total interest + all fees | 77696.027136 | 77696.027136 | PASS |  |
| B1_INDUSTRIAL | all-in cost == sum(outflows) - net disbursement | 77696.027136 | 77696.027136 | PASS |  |
| B1_INDUSTRIAL | peak outflow == max of saved outflows | 11144.933786 | 11144.933786 | PASS |  |
| B1_INDUSTRIAL | affordability flag matches saved peak vs binding ceiling | True | True | PASS |  |
| B2_CITY_BANK | schedule row count == term_months | 60 | 60 | PASS | Re-read from the saved schedule CSV. |
| B2_CITY_BANK | interest_t = opening_t * monthly rate | max abs error <= 1e-06 | 4.957e-11 | PASS |  |
| B2_CITY_BANK | closing_t = opening_t - principal_t | max abs error <= 1e-06 | 1.164e-10 | PASS |  |
| B2_CITY_BANK | outflow_t = interest + principal + monthly fee | max abs error <= 1e-06 | 1.019e-10 | PASS |  |
| B2_CITY_BANK | sum of principal == original principal | 600000.000000 | 600000.000000 | PASS |  |
| B2_CITY_BANK | final closing balance == 0 | 0 | 0.000e+00 | PASS |  |
| B2_CITY_BANK | sum(outflows) = interest + principal + all monthly fees | 676893.211038 | 676893.211038 | PASS |  |
| B2_CITY_BANK | level instalment: bisection on balance recursion vs engine closed form | 11281.553517 | 11281.553517 | PASS | Independent algorithm; equality supports the annuity formula. |
| B2_CITY_BANK | first schedule outflow == level instalment + monthly fee | 11281.553517 | 11281.553517 | PASS |  |
| B2_CITY_BANK | effective APR: Newton IRR vs engine bisection IRR | 0.048500000 | 0.048500000 | PASS | Different root-finding method on the same saved cash flows. |
| B2_CITY_BANK | NPV of saved cash flows at independently solved IRR == 0 | \|NPV\| <= 1e-06 | 8.167e-10 | PASS |  |
| B2_CITY_BANK | all-in cost == total interest + all fees | 76893.211038 | 76893.211038 | PASS |  |
| B2_CITY_BANK | all-in cost == sum(outflows) - net disbursement | 76893.211038 | 76893.211038 | PASS |  |
| B2_CITY_BANK | peak outflow == max of saved outflows | 11281.553517 | 11281.553517 | PASS |  |
| B2_CITY_BANK | affordability flag matches saved peak vs binding ceiling | True | True | PASS |  |
| B3_LESSOR | schedule row count == term_months | 48 | 48 | PASS | Re-read from the saved schedule CSV. |
| B3_LESSOR | interest_t = opening_t * monthly rate | max abs error <= 1e-06 | 4.547e-13 | PASS |  |
| B3_LESSOR | closing_t = opening_t - principal_t | max abs error <= 1e-06 | 0.000e+00 | PASS |  |
| B3_LESSOR | outflow_t = interest + principal + monthly fee | max abs error <= 1e-06 | 0.000e+00 | PASS |  |
| B3_LESSOR | sum of principal == original principal | 600000.000000 | 600000.000000 | PASS |  |
| B3_LESSOR | final closing balance == 0 | 0 | 0.000e+00 | PASS |  |
| B3_LESSOR | sum(outflows) = interest + principal + all monthly fees | 662475.000000 | 662475.000000 | PASS |  |
| B3_LESSOR | equal-principal first outflow | 15050.000000 | 15050.000000 | PASS |  |
| B3_LESSOR | equal-principal outflow is strictly declining | first > last | 15050.00 > 12553.12 | PASS |  |
| B3_LESSOR | effective APR: Newton IRR vs engine bisection IRR | 0.056287779 | 0.056287779 | PASS | Different root-finding method on the same saved cash flows. |
| B3_LESSOR | NPV of saved cash flows at independently solved IRR == 0 | \|NPV\| <= 1e-06 | 1.668e-09 | PASS |  |
| B3_LESSOR | all-in cost == total interest + all fees | 68475.000000 | 68475.000000 | PASS |  |
| B3_LESSOR | all-in cost == sum(outflows) - net disbursement | 68475.000000 | 68475.000000 | PASS |  |
| B3_LESSOR | peak outflow == max of saved outflows | 15050.000000 | 15050.000000 | PASS |  |
| B3_LESSOR | affordability flag matches saved peak vs binding ceiling | False | False | PASS |  |
| B4_DIGITAL | schedule row count == term_months | 48 | 48 | PASS | Re-read from the saved schedule CSV. |
| B4_DIGITAL | interest_t = opening_t * monthly rate | max abs error <= 1e-06 | 4.957e-11 | PASS |  |
| B4_DIGITAL | closing_t = opening_t - principal_t | max abs error <= 1e-06 | 1.164e-10 | PASS |  |
| B4_DIGITAL | outflow_t = interest + principal + monthly fee | max abs error <= 1e-06 | 1.019e-10 | PASS |  |
| B4_DIGITAL | sum of principal == original principal | 600000.000000 | 600000.000000 | PASS |  |
| B4_DIGITAL | final closing balance == 0 | 0 | 0.000e+00 | PASS |  |
| B4_DIGITAL | sum(outflows) = interest + principal + all monthly fees | 660917.881456 | 660917.881456 | PASS |  |
| B4_DIGITAL | level instalment: bisection on balance recursion vs engine closed form | 13709.122530 | 13709.122530 | PASS | Independent algorithm; equality supports the annuity formula. |
| B4_DIGITAL | first schedule outflow == level instalment + monthly fee | 13769.122530 | 13769.122530 | PASS |  |
| B4_DIGITAL | effective APR: Newton IRR vs engine bisection IRR | 0.050762650 | 0.050762650 | PASS | Different root-finding method on the same saved cash flows. |
| B4_DIGITAL | NPV of saved cash flows at independently solved IRR == 0 | \|NPV\| <= 1e-06 | 1.055e-10 | PASS |  |
| B4_DIGITAL | all-in cost == total interest + all fees | 63917.881456 | 63917.881456 | PASS |  |
| B4_DIGITAL | all-in cost == sum(outflows) - net disbursement | 63917.881456 | 63917.881456 | PASS |  |
| B4_DIGITAL | peak outflow == max of saved outflows | 13769.122530 | 13769.122530 | PASS |  |
| B4_DIGITAL | affordability flag matches saved peak vs binding ceiling | False | False | PASS |  |
| baseline | naive lowest-headline-rate pick (from saved summary) | recorded | B1_INDUSTRIAL | PASS | Simple heuristic used as the comparison reference. |
| baseline | lowest effective APR among all offers | B2_CITY_BANK | B2_CITY_BANK | PASS |  |
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

Verified run folder: `outputs/fresh_case_B`

Original offers file: `skills/loan-offer-comparison/examples/offers_case_B.csv`
