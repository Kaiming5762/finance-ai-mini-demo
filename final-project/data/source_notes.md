# Input provenance and data notes

## Declaration

**Every loan offer used in this project is synthetic teaching data.** No real
bank quotations, no paid data, no downloaded market data and no personal
financial information were used. The offers were constructed by the author to
make the comparison interesting: a headline-rate trap (Case A offer A1), a
fee-free comparator (A2), an unaffordable short-term offer (A3), and a
front-loaded equal-principal plan (A4).

| Item | Value |
|---|---|
| Input files | `skills/loan-offer-comparison/examples/offers_case_A.csv`, `borrower_case_A.json`, `offers_case_B.csv`, `borrower_case_B.json` |
| Provider | Author-constructed synthetic examples |
| Created / used on | 2026-11-10 (UTC+8) |
| Real or synthetic | **Synthetic** |
| Currency | Case A: HKD; Case B: CNY (display label only, no FX conversion) |
| Units | Money: currency units; rates: decimal fraction per annum; terms: whole months |
| Period / frequency | Monthly instalments; `i = annual_nominal_rate / 12` |
| Retrieval | None; files are versioned in the repository and require no download |
| Transformations | None. Values are read directly from the CSV/JSON and validated on load |

## Why synthetic data is lawful and appropriate here

The project brief (Appendix B) allows "course CSVs or synthetic examples" as an
alternative to downloaded data. The core claim of this project is about
**calculation and checking**, not about any particular lender's quotation, so
constructed inputs are sufficient and avoid redistribution or licensing issues.
Nothing here is redistributed from a data provider.

## Declared validation rules (Appendix B step 2)

`loan_compare.py` checks, before calculating: header presence and required
columns; non-empty file; unique non-empty `offer_id`; numeric and finite values;
principal > 0; rate in [0, 1]; whole-number term in [1, 600]; fees >= 0;
percentage fee <= 0.5; recognised `repayment_type`; `periods_per_year == 12`;
positive budget cap and income; payment-to-income ceiling in (0, 1].
Missing optional fee cells default to 0 (a declared rule, not a silent fill).
Any other missing value, duplicate, or out-of-range value **stops the run with
an explicit error list** and exit code 3; no row is silently dropped or imputed.
See `outputs/case_A/run_log.txt` for the actual input-check result of the
primary run, and `outputs/case_A/verification.md` for the eight invalid-input
tests.

## Financial conventions

- Fees are assumed withheld from the disbursement at t = 0 (equivalent to paying
  them separately at t = 0).
- Interest accrues monthly on the opening balance at `rate / 12`.
- The final instalment clears the remaining balance exactly.
- Effective APR/EAR come from the IRR of the borrower's cash flows; they are
  **not** asserted to be any jurisdiction's legally defined APR.
- All-in cost is an undiscounted nominal sum; it is not discounted for timing.

## What these inputs cannot establish

They cannot establish that any lender quotes these rates, that fees are actually
withheld, that a borrower's income is stable, or that a chosen offer is the best
available product. Recalculation and independent verification establish
internal arithmetic correctness only, not the authenticity of the source data.
