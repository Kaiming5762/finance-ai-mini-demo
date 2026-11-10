---
name: loan-offer-comparison
description: >-
  Compare amortising loan offers that differ in nominal rate, upfront and monthly fees,
  term and repayment structure on one all-in cash-flow basis. Use when a borrower or
  analyst needs an auditable schedule, an effective APR/EAR from actual cash flows,
  an affordability check against a monthly ceiling, and a ranking that exposes the
  "lowest headline rate" trap. Produces deterministic CSV/JSON/Markdown/SVG outputs
  and an independent verification record. Pure Python standard library.
version: 1.0.0
license: MIT
author: Kaiming Tian (HKUST IEDA, Finance with AI Agents final project)
---

# Loan Offer Comparison (Loan Offer Compass)

A regular Skill, not a Team Skill: no agent coordination is part of the reusable
capability. Everything needed to rerun it lives in this folder.

## 1. Scope

**User / task.** An individual borrower (or a credit analyst advising one) who has
several instalment-loan quotations and must decide which to take, subject to a
monthly affordability limit. Headline nominal rates hide arrangement fees, monthly
administration fees, term effects and repayment structure, so a spreadsheet built
by hand is easy to get wrong and hard to check.

**What this Skill does.** Given a CSV of offers and a small borrower config, it
validates the inputs, builds an exact month-by-month amortisation schedule for
each offer, computes the effective APR / EAR from the borrower's real cash flows,
applies affordability limits, computes the largest affordable principal, ranks
offers, and writes machine-readable results plus an independent check record.

**What it does not do.** It does not fetch live quotes, recommend a purchase,
handle variable rates, early repayment, default risk, taxes, inflation or
cross-currency comparison. It is a reproducible calculation and checking
procedure, not financial advice.

## 2. Inputs

All inputs are supplied by the user. No network, credentials, API keys or paid
data are used. Paths are resolved by the caller; scripts resolve their own
helpers relative to the loaded skill directory.

### `offers.csv` (required)

One row per offer. Rates are decimal fractions (`0.0520` = 5.20% p.a.), money is
in the single `currency` declared in the config, and terms are whole months.

| Column | Required | Meaning / rule |
|---|---|---|
| `offer_id` | yes | Unique, non-empty identifier |
| `lender` | yes | Free-text label |
| `principal` | yes | Amount borrowed, > 0 |
| `annual_nominal_rate` | yes | Decimal in [0, 1] |
| `term_months` | yes | Whole number in [1, 600] |
| `repayment_type` | yes | `annuity` (level payment) or `equal_principal` (declining payment) |
| `fee_upfront_fixed` | no (default 0) | Fixed arrangement fee, >= 0 |
| `fee_upfront_pct` | no (default 0) | Fraction of principal, in [0, 0.5] |
| `fee_monthly` | no (default 0) | Per-month administration fee, >= 0 |

Unknown columns are reported and ignored. Blank optional fee cells default to 0.

### `borrower.json` (required unless every value is passed on the CLI)

```json
{
  "case_id": "my_case",
  "currency": "HKD",
  "monthly_budget_cap": 6000.0,
  "monthly_income": 30000.0,
  "max_payment_to_income": 0.35,
  "periods_per_year": 12,
  "data_note": "where the numbers came from"
}
```

`currency` is a **display label only**; no FX conversion happens.
`periods_per_year` must be 12 (monthly instalments only).

## 3. Outputs (written into `--out`, created if absent)

| File | Content |
|---|---|
| `schedules/<offer_id>.csv` | Full amortisation: opening balance, interest, principal, monthly fee, total outflow, closing balance, cumulative interest (10 decimals) |
| `summary.json` | Every metric, all internal identity checks, ranking and the naive baseline |
| `comparison.md` | Human-readable comparison, affordability detail, ranking, limitations |
| `balance_paths.svg`, `cost_breakdown.svg` | Charts generated from the schedules, pure SVG |
| `run_log.txt` | Input checks, exact command, environment, per-offer check counts |
| `verification.md` / `verification.json` | Written by `verify.py`, the independent check record |

## 4. Financial definitions (do not change these silently)

Monthly periods; `i = annual_nominal_rate / 12`.

- **Cash flows, borrower's view.** `t=0: +(principal - upfront_fee)` where
  `upfront_fee = fee_upfront_fixed + fee_upfront_pct * principal`;
  `t=1..n: -(interest_t + principal_t + fee_monthly)`.
  Fees are assumed withheld from the disbursement (paying them separately at t=0
  gives the same net cash flow).
- **Level instalment.** `PMT = P*i / (1 - (1+i)^-n)`, or `P/n` when `i = 0`.
- **Period identities.** `interest_t = opening_t * i`;
  `closing_t = opening_t - principal_t`;
  `outflow_t = interest_t + principal_t + fee_monthly`. The final instalment
  clears the remaining balance exactly.
- **Effective APR / EAR.** Solve `NPV(i_IRR) = 0` on those cash flows by bisection.
  `APR = 12 * i_IRR` (nominal annual, monthly compounding);
  `EAR = (1 + i_IRR)^12 - 1`.
- **All-in cost (nominal).** `sum(outflows) - net_disbursement`
  `= total interest + upfront fee + n * fee_monthly`. Not discounted.
- **Affordability.** Binding ceiling `= min(monthly_budget_cap, monthly_income *
  max_payment_to_income)`. An offer is affordable iff its **peak** monthly
  outflow fits the ceiling; the peak is used because `equal_principal` plans are
  front-loaded. `max_affordable_principal` is found by bisection on the principal.
- **Naive baseline.** The offer with the lowest headline nominal rate. Recorded
  so the all-in ranking can be compared with a simple heuristic.

All-in cost and APR can rank offers differently: cost ignores timing, APR does
not. Report both; do not present one as "the" answer.

## 5. Procedure (six-part prompt a new user can paste)

**GOAL** - Compare my loan offers on an all-in, auditable basis and tell me which
ones I can afford. **INPUTS** - `<path to offers.csv>` and `<path to borrower.json>`;
state whether they are real or synthetic. **METHOD** - Use `scripts/loan_compare.py`
exactly as documented in this SKILL.md; do not invent data or change the
financial definitions. **OUTPUT** - Write all results into a **new, unused**
folder `<path to output folder>`. **BOUNDARIES** - Do not modify the input files,
do not install packages, do not browse, do not change credentials, do not
overwrite an existing output folder without asking. **CHECKS** - Show me the
input-check summary, the 7 internal identity checks per offer, and the output of
`scripts/verify.py`; stop and explain if any check fails.

### Commands (run from the loaded skill folder, or use absolute paths)

```
python scripts/loan_compare.py --offers examples/offers_case_A.csv \
  --config examples/borrower_case_A.json --out outputs/my_run

python scripts/verify.py --offers examples/offers_case_A.csv \
  --config examples/borrower_case_A.json --out outputs/my_run \
  --report outputs/my_run/verification.md --json outputs/my_run/verification.json
```

CLI overrides: `--case-id`, `--currency`, `--budget-cap`, `--monthly-income`,
`--max-dti`, `--tol`, `--no-charts`. `verify.py --battery-only` runs just the
known-answer, changed-input and invalid-input battery.

## 6. Checks (keep all of them when reusing)

The engine performs 7 **self-checks** per offer (they are not independent):
interest-equals-opening-times-rate, balance roll-forward, principal repaid
equals principal, final balance zero, payments equal interest + principal +
fees, all-in cost equals interest + fees, and NPV at the engine's IRR is zero.

`verify.py` is the **independent** check. It re-reads the **saved schedule CSVs**
and the original offers CSV (not `summary.json` values) and uses deliberately
different algorithms:

1. Level payment by **bisection on a recursive balance equation** instead of the
   closed-form annuity formula.
2. IRR by **Newton's method with an analytic derivative** instead of bisection.
3. Cash-flow identities and `NPV = 0` evaluated on the saved numbers.

It also runs a small evaluation battery:

- **Known answer.** `P = 10,000`, 12% p.a., 12 months, no fees, compared with the
  spreadsheet reference `=PMT(1%,12,10000)` = `888.487886783`, total paid
  `10,661.854641401`, total interest `661.854641401`.
- **Changed inputs.** Rate +1 pp; +2% upfront fee; term 36 -> 48; +50 monthly
  fee; budget cap 3,000 vs 5,000; annuity -> equal-principal.
- **Error behaviour.** Eight malformed CSVs plus one CLI test that must exit 3
  with `INPUT ERROR` and write no output folder.

Expected result for the bundled `offers_case_A.csv` + `borrower_case_A.json`:
**83/83 checks pass**. The naive lowest-rate pick is `A1_LOW_RATE_FEE` (5.200%
headline) while the lowest effective APR is `A2_NO_FEE` (6.300%) - they
**disagree**, because A1 hides a 2.5% arrangement fee that lifts its APR to
6.900%. `A3_SHORT_TERM` has the lowest nominal all-in cost but is unaffordable
(peak HKD 8,042.75 > HKD 6,000 cap).

## 7. Failure handling

| Situation | Behaviour |
|---|---|
| Missing file, missing column, empty CSV | Stop with `INPUT ERROR`, no output written, exit code 3 |
| Non-numeric / non-finite / out-of-range value | Accumulate **all** row errors and stop; do not silently drop or fill |
| Duplicate `offer_id`, empty id | Stop with an explicit row reference |
| Unknown `repayment_type` | Stop; only `annuity` and `equal_principal` are supported |
| `periods_per_year != 12` | Stop; monthly instalments only |
| Upfront fees >= principal | Stop (net disbursement would be non-positive) |
| IRR cannot be bracketed | Stop with an explicit message rather than returning a number |
| Any identity check fails | Reported in `summary.json` and `run_log.txt`; treat the run as failed |
| A verification check fails | `verify.py` exits 5 and lists every failure |
| Output folder already has files | Ask before replacing; prefer a new folder |

Never invent a missing input, never claim a check passed without its output,
never round internally (round only for display), and never publish credentials.

## 8. Dependencies and tested versions

- Python 3.9+ **standard library only** (`argparse`, `csv`, `json`, `math`,
  `datetime`, `pathlib`, `html`). No `pip install`, no model API, no network.
- Tested on Python 3.13.14 / Windows (Git Bash), 2026-11-10.
- The course requirement of "no extra packages" is satisfied by design.

## 9. Known limitations

Monthly instalments only; no intra-month compounding, no variable rates, no
early repayment or refinancing, no default/prepayment risk, no tax or insurance
effects, no inflation. All-in cost is undiscounted, so it is not comparable
across different terms without the APR/EAR. Fee withholding is an assumption
about quotation timing, not a fact about any lender. Bundled offers are
**synthetic teaching data** with no real-world provenance; the tool cannot
establish that any input is an authentic quote. APR here is the IRR-based
borrower cost, which is not necessarily the legally defined APR in any
jurisdiction. Small floating-point residuals (~1e-10 currency units) remain
after CSV round-tripping at 10 decimals; the checks use a 1e-6 tolerance.

## 10. Attribution, licence and community

- Original work for the HKUST IEDA "AI Agents and Financial Optimization"
  final project (Loans and financing topic, Appendix A of the project brief).
  Built with substantial AI assistance (WorkBuddy AI agent reading the brief,
  writing and executing the scripts, checking the outputs); all numerical
  claims come from the executable scripts and saved output files, not from chat text.
- No third-party code or data is reused. The standard annuity and IRR
  definitions are textbook finance, not copied implementation.
- Licensed MIT (inherits the course repository's licence; see repository `LICENSE`).
- Community project: **https://github.com/openJiuwen-ai/jiuwenswarm**
  (JiuwenSwarm / WorkSwarm), linked from the repository README as required.
- Course repository: the public fork `Kaiming5762/finance-ai-mini-demo`,
  folder `final-project/`. See `../../README.md` and `../../community/contribution-record.md`.
