# Agent workflow and tool-use record

This is the working record of the single Agent that built and executed the
project. It follows the six-part GOAL / INPUTS / METHOD / OUTPUT / BOUNDARIES /
CHECKS pattern from T2/T3 and Appendix B of the final project brief. No separate
specification document was used.

## 1. The six-part prompt actually used

```
GOAL
For a borrower comparing instalment-loan quotations, build a reproducible
"Loan Offer Compass" that compares repayment plans with different rates, fees,
terms and affordability limits, and produces an auditable, checkable result.
Single Agent; keep the scope laptop-sized.

INPUTS
~/Downloads/final project_instructions.pdf (course brief),
HKUST T1/T2/T3 Student Guides (from Downloads), the existing course fork
~/Documents/finance-ai-mini-demo, and the local Python/Git/Word
environment. All loan offers are to be author-constructed SYNTHETIC teaching
data; record provenance, units and validation rules.

METHOD
Use Python 3 standard library only (no pip, no network, no API key). Monthly
periods; i = nominal_rate / 12. Cash flows from the borrower's view:
t=0 +(principal - upfront fees); t=1..n -(interest + principal + monthly fee).
Support annuity and equal_principal plans. Effective APR = 12 * IRR found by
bisection; EAR = (1+IRR)^12 - 1. All-in cost = total interest + all fees.
Affordability uses the PEAK monthly outflow against
min(budget_cap, income * max_payment_to_income); solve max affordable principal
by bisection. Record the naive "lowest headline rate" baseline. Check before
analysing: reject malformed inputs with an explicit error, never silently drop.
Independent checker must re-read SAVED schedules and use DIFFERENT algorithms
(bisection-on-balance for the payment, Newton for the IRR).

OUTPUT
New folder final-project/ inside the existing fork (preserve T1-T3 work and the
three pre-existing untracked files). Deliver README.md, requirements.txt,
scripts/, skills/loan-offer-comparison/ (SKILL.md, README.md, scripts/,
examples/), data/source_notes.md, outputs/case_A/, outputs/fresh_case_B/,
evidence/ E1-E4, report/report.pdf (.docx/.html/.md), demo/, community/,
docs/, and a source ZIP.

BOUNDARIES
Do not modify existing tutorial files or the three untracked files. Do not
install packages, browse, change credentials, or invent numbers. Ask before the
two external actions: pushing to a public GitHub repository and generating a
report PDF with the locally installed Word. Do not overwrite an earlier output
folder without asking. No secrets, private data or personal absolute paths in
the reusable package.

CHECKS
Show real tool output (not chat claims) for: input validation, 7 internal cash-
flow identities per offer, a known-answer 12%/12-month schedule, an independent
second implementation, six changed-input cases, eight invalid-input cases, one
CLI error-behaviour case, and a fresh-case execution in a new output folder.
Open the saved files. Any failed check must be shown and fixed, not hidden.
```

## 2. Tool-use log (compact)

| Step | Tool action | Observed result |
|---|---|---|
| 1 | Read 9-page brief + T1/T2/T3 guides via local PDF extraction | Requirements, Loans-and-financing topic, six-part prompt, Git flow, Skill packaging, "no extra packages" |
| 2 | Inspect environment | Python 3.13.14 (no numpy/pandas), Git 2.55 (`Kaiming5762 <ktianac@connect.ust.hk>`), no `gh`, Word 16.0, GitHub credentials stored, network 200 |
| 3 | Inspect existing fork | `origin = https://github.com/Kaiming5762/finance-ai-mini-demo.git`, branch `main`, clean tracked tree; untracked `app.py`, `backtest.py`, `run_output.txt` left untouched |
| 4 | Ask user to approve the two external actions | Both approved: commit+push to the fork; Word-native PDF/DOCX/HTML export |
| 5 | Write `loan_compare.py` and run it on Case A | exit 0; 4 offers, 0 validation errors, 7/7 identities each; naive pick A1 disagrees with lowest APR A2 |
| 6 | Write `verify.py` and run it | **First run FAILED**: 11/12, `AssertionError: Newton IRR did not converge` |
| 7 | Debug with a printed Newton iterate trace | NPV fell ~12,590 -> ~1e-11 in 3-4 steps; the solver broke on `abs(step) <= 1e-15` before accepting the residual |
| 8 | Fix convergence rule, rerun | **83/83 passed, 0 failed** |
| 9 | Write `run_all.py`, execute Case A capture | `E1`, `E2` written with real stdout/exit codes |
| 10 | Package the regular Skill (`SKILL.md`, `README.md`, examples) | No absolute paths, secrets or cached answers; openJiuwen link added |
| 11 | Clean-setup fresh Case B: list skill files, show `SKILL.md`, confirm empty output folder, execute | `E3`, `E4`: engine exit 0, **83/83** checks |
| 12 | Write report Markdown, convert to print HTML, export with Word | `report.pdf` 9 pages, `report.docx`, `report.html` verified by reading the PDF back |
| 13 | Write demo, community and evidence records | Files listed in `README.md` |
| 14 | Local `git commit -s`, push to public fork, build source ZIP | See `community/contribution-record.md` |

Roles: one Agent, no team. The brief explicitly welcomes single-agent projects;
a team would not have helped because there is no parallelizable research split,
and "another agent repeating the same script is not automatically independent
verification" (Appendix B). Independence here comes from **different algorithms
and saved-file rereads**, not from a second agent.

## 3. Troubleshooting record (Appendix C pattern)

- **Goal:** independently solve the IRR with Newton's method in `verify.py`.
- **Symptom / exact error:** `AssertionError: Newton IRR did not converge`;
  `verify.py` exited 5 with 11/12 checks passed.
- **Tried:** printed `NPV`, derivative and rate for 12 iterations on all four
  offers. Observed rapid convergence to ~1e-11 residual, then a break on the
  step-size condition.
- **Smallest reversible fix:** use a **relative** convergence tolerance
  `tol * net_disbursement` (NPV is in currency units, so an absolute 1e-12
  epsilon is unrealistic), and return the iterate when the Newton step becomes
  tiny instead of treating it as a failure. Keep the analytic derivative.
- **Verification:** reran `verify.py` on Case A (83/83) and on fresh Case B
  (83/83), and confirmed the saved `verification.md` tables contain no FAIL rows.
- No credentials, history rewrites or unrelated files were touched.

## 4. Boundaries and honest labelling

- The three pre-existing untracked files in the fork were never modified, staged
  or deleted. T1-T3 tracked files are unchanged.
- The two external actions were approved explicitly before execution.
- No API key, token, password, model output or personal financial data is stored
  in the project. Before publication the harness was changed to pass project-
  relative paths and to show the interpreter as `python`, so even the evidence
  logs, `run_log.txt` and `verification.md` contain no machine-specific path.
- **Tool environment:** the agent runtime was WorkBuddy AI, using approved local
  tools (file read/write, terminal, Git) of the same class as WorkSwarm /
  JiuwenSwarm in the T1-T3 guides. No WorkSwarm UI screenshot is claimed. The
  calculation is plain Python, so `python scripts/run_all.py` inside the
  classroom WorkSwarm app reproduces identical outputs; capture that tool panel
  if a platform-specific screenshot is required.
- AI assistance is attributed in `report/report.md` section 8 and in both
  `README.md` files. All numbers come from saved outputs and executable checks.
