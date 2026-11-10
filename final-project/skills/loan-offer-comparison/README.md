# Loan Offer Comparison - reusable Skill

**What another person can reuse:** a tested, deterministic procedure (plus scripts
and checks) for comparing amortising loan offers that differ in rate, fees, term
and repayment structure, and for checking the result independently.

Community project: **https://github.com/openJiuwen-ai/jiuwenswarm**
(JiuwenSwarm / WorkSwarm). This link is also in the repository README.

---

## Finance user, task and supported scope

A borrower or credit analyst with 2-10 instalment-loan quotations, a monthly
budget cap and an income-based affordability ceiling, who needs a defensible
answer to "which offer is actually cheapest, and which can I afford?".
Supported: fixed nominal rates, monthly instalments, `annuity` and
`equal_principal` plans, fixed/percentage upfront fees, monthly fees, terms of
1-600 months. Not supported: variable rates, early repayment, live quotes,
multi-currency conversion, legal-APR compliance, investment advice.

## Required software and tested versions

- Python **3.9+**, standard library only. No `pip install`, no API key, no network.
- Tested: Python 3.13.14, Windows 11 / Git Bash, 2026-11-10.
- Optional: any text editor / browser to view `.md`, `.csv` and `.svg` outputs.

## Input files, fields, units and sources

See `SKILL.md` sections 2 and 4. In short:

- `examples/offers_case_A.csv` - 4 synthetic HKD personal-loan offers
  (HKD 180,000; 24-36 months).
- `examples/borrower_case_A.json` - HKD 6,000 monthly cap, HKD 30,000 income,
  35% payment-to-income ceiling.
- `examples/offers_case_B.csv` / `borrower_case_B.json` - a **different** synthetic
  case (CNY 600,000 SME equipment finance; 48-60 months) for the reuse test.

**All bundled inputs are synthetic teaching data, not real quotations.** Replace
them with your own lawful data; record provider, retrieval date, units and any
transformations in your `data_note`. Money is one currency per run; rates are
decimal fractions; terms are whole months. No personal data is bundled.

## How to start - exact commands

From this skill folder (or use absolute paths; helper paths resolve relative to
the loaded skill directory):

```
python scripts/loan_compare.py --offers examples/offers_case_A.csv \
  --config examples/borrower_case_A.json --out outputs/my_run

python scripts/verify.py --offers examples/offers_case_A.csv \
  --config examples/borrower_case_A.json --out outputs/my_run \
  --report outputs/my_run/verification.md --json outputs/my_run/verification.json
```

To run only the standalone evaluation battery:

```
python scripts/verify.py --battery-only --report battery.md
```

To use your own inputs, change `--offers`, `--config` and `--out`. CLI overrides:
`--case-id`, `--currency`, `--budget-cap`, `--monthly-income`, `--max-dti`,
`--tol`, `--no-charts`. Run `python scripts/loan_compare.py --help` for details.

In a fresh conversation, a WorkSwarm/JiuwenSwarm user can import this folder as
a regular Skill (import `SKILL.md` or the folder by absolute path), ask it to
show which skill files it read, plan a **new** case with a **new, unused** output
folder, then approve execution. `SKILL.md` section 5 contains the six-part
prompt to paste. The Skill must obtain its own inputs and decisions; it contains
no cached answers or approvals.

## One small example and its expected checks

With the bundled Case A inputs, expect:

| Offer | Peak monthly | All-in cost | Effective APR | Affordable |
|---|---:|---:|---:|:---:|
| A1_LOW_RATE_FEE | HKD 5,410.94 | HKD 19,293.82 | 6.900% | YES |
| A2_NO_FEE | HKD 5,500.45 | HKD 18,016.18 | 6.300% | YES |
| A3_SHORT_TERM | HKD 8,042.75 | HKD 13,026.09 | 6.800% | NO |
| A4_EQUAL_PRINCIPAL | HKD 5,915.00 | HKD 18,652.50 | 6.741% | YES |

Expected checks: 4 offers, 0 validation errors, 0 duplicate ids; 7/7 internal
identity checks per offer; `verify.py` reports **83/83 checks passed, 0 failed**;
the naive lowest-headline-rate pick (`A1_LOW_RATE_FEE`, 5.200%) **disagrees**
with the lowest effective APR (`A2_NO_FEE`).

## Output files and what they mean

| File | Meaning |
|---|---|
| `schedules/*.csv` | Auditable month-by-month amortisation for each offer |
| `summary.json` | All metrics, identity checks, ranking, naive baseline |
| `comparison.md` | Comparison, affordability detail, ranking, limitations |
| `balance_paths.svg` | Remaining balance curves |
| `cost_breakdown.svg` | Interest + upfront fee + monthly fees per offer |
| `run_log.txt` | Exact command, environment, input checks |
| `verification.md` / `.json` | Independent check record, pass/fail table |

## How to verify / reproduce the important result

1. Run the two commands above and inspect the actual stdout and the saved files;
   a chat message saying "done" is not evidence.
2. Open `verification.md` and confirm 83/83 pass. Two independent methods are
   used: bisection-on-balance (payment) and Newton (IRR), plus a spreadsheet
   PMT known-answer reference, changed-input cases and invalid-input cases.
3. To change a small input, edit one CSV cell (e.g. `A1` rate `0.0520` ->
   `0.0620`) and rerun into a new folder; the payment and APR must both rise.

## Known failures and limitations

See `SKILL.md` sections 7 and 9. In short: monthly-only; nominal all-in cost is
not time-value adjusted; fee-withholding is an assumption; inputs are synthetic;
bad inputs stop the run with exit code 3 rather than being silently dropped;
small floating-point residuals (~1e-10) remain after CSV round-tripping;
`verify.py` exits 5 if any check fails. A known development issue: the first
Newton IRR implementation broke on a tiny Newton step before accepting a small
NPV residual and raised a false failure; it was fixed with a relative
convergence criterion and a step-size return, then all 83 checks passed. This is
recorded in the project report rather than hidden.

## Reused work, AI assistance, licence and attribution

- No third-party code or datasets. Textbook annuity/IRR definitions only.
- Built with substantial AI assistance (WorkBuddy AI agent: read the course
  brief, wrote and executed the scripts, inspected outputs); the student is
  responsible for all choices and numerical claims, which come from saved files.
- MIT licence; inherits the course repository `LICENSE`.
- Author: Kaiming Tian, HKUST IEDA, Finance with AI Agents final project, 2026.
- openJiuwen / JiuwenSwarm: **https://github.com/openJiuwen-ai/jiuwenswarm**
- Public package: `final-project/` in `Kaiming5762/finance-ai-mini-demo`.
