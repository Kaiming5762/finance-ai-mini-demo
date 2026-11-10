# Community contribution record

Template: `final project_instructions.pdf`, Appendix F. All statements below are  
factual; optional routes that were not attempted are marked as such.

## Contribution type and what another person can reuse

- **Type:** public GitHub **regular Skill** package (Appendix D). A Team Skill is  
  not needed because no agent coordination is part of the reusable capability.
- **Title:** `loan-offer-comparison` (Loan Offer Compass), version **1.0.0**.
- **Reusable part:** a tested procedure plus runnable scripts and checks for  
  comparing amortising loan offers on an all-in cash-flow basis - input  
  validation, exact amortisation schedules, IRR-based effective APR/EAR,  
  affordability limits, a naive-baseline comparison and an independent  
  verification battery. A finished report is an output; the **procedure** is  
  the contribution.
- **Package location:** `skills/loan-offer-comparison/` in this repository  
  (`SKILL.md`, `README.md`, `scripts/loan_compare.py`, `scripts/verify.py`,  
  `examples/*.csv`, `examples/*.json`).

## Public GitHub URL and exact commit

- **Repository URL:** <https://github.com/Kaiming5762/finance-ai-mini-demo>  
  (public fork of `congw729/finance-ai-mini-demo`, folder `final-project/`).
- **Exact final commit URL:**  
  <https://github.com/Kaiming5762/finance-ai-mini-demo/commit/c50335ee82f42059086027b6dea897080af06254>
- **Commit hash:** `c50335ee82f42059086027b6dea897080af06254`
- **Commit message:** `feat: add Loan Offer Compass final project (Loans and financing)`  
  (signed off with `git commit -s`).
- **Package version:** 1.0.0
- **Source ZIP:** `final-project_source.zip` (submitted alongside the report;  
  generated from the final working tree; contains source, Skill, checks,  
  examples, report source/exports and docs; excludes secrets, caches and  
  environments).
- **README link to openJiuwen:** <https://github.com/openJiuwen-ai/jiuwenswarm>  
  appears in `final-project/README.md` (section "openJiuwen community link") and  
  in `skills/loan-offer-comparison/README.md` and `SKILL.md`.
- **GitHub publication date:** 2026-11-10 (UTC).
- **Access blocker:** none observed (GitHub reachable, stored credentials used).
- **Note on the follow-up commit:** a commit can only cite its predecessor, not  
  itself. The URL above is the commit that contains **all deliverables**. The  
  small commit immediately after it only writes this URL into this record and  
  refreshes the exported report; no calculation, evidence, example or numeric  
  result changed. Both commits were pushed to `main`. Later documentation-only
  commits (for example the verbatim demo narration and checklist) do not change
  any calculation, evidence, example or numeric result.

## Fresh-run case, invocation, output and verification

| Field        | Record                                                                                                                                                                          |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Fresh case   | `offers_case_B.csv` + `borrower_case_B.json` - CNY 600,000 SME equipment finance, 48/60-month terms, 4 lenders, different rates/fees/cap from Case A                            |
| Clean setup  | New shell; skill files listed and `SKILL.md` shown before execution; target folder `outputs/fresh_case_B/` confirmed **empty** immediately before the run                       |
| Invocation   | `python scripts/run_all.py --only case_B` (engine + independent checker), with `--case-b-out` available for a different new folder                                              |
| Output       | `outputs/fresh_case_B/` - 4 schedules, `summary.json`, `comparison.md`, 2 SVG charts, `run_log.txt`, `verification.md`, `verification.json`                                     |
| Core result  | Naive lowest-rate pick `B1_INDUSTRIAL` (4.350%) vs lowest effective APR `B2_CITY_BANK` (4.850%) - **disagree**; cheapest offers B3/B4 are unaffordable under the CNY 12,000 cap |
| Verification | **83/83 checks passed, 0 failed**; 7/7 internal identities per offer; independent bisection-payment and Newton-IRR recomputations agree                                         |
| Evidence     | `evidence/E3_fresh_case_B_run.txt`, `evidence/E4_changed_inputs_checks.txt`, `outputs/fresh_case_B/run_log.txt`                                                                 |
| Reuse type   | **Honest self-reproduction by the same author**, not a classmate's peer reuse test. No peer reuse is claimed.                                                                   |
| Label        | Loaded from source files in a clean setup; **full execution completed**, not merely a load-and-plan check (Appendix D explicitly requires checked execution).                   |

## Optional Hub / PR

- **Hub submission:** not attempted (optional, selected Team Skills only). No  
  status claimed; this package is a regular Skill, not a Team Skill.
- **Upstream PR:** not attempted (optional route, Appendix E). No PR was opened,  
  no CLA signed, no CI run. No status is claimed.
- GitHub package publication completes the normal course contribution route.

## Sharing notice

The teaching team may share the submitted GitHub URL with the openJiuwen team.  
No private data, credentials or personal financial information is contained in  
the public package. The examples are synthetic teaching data.
