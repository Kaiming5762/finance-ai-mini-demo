# Loan Offer Compass - Finance with AI Agents Final Project

**Topic: Loans and financing** (Appendix A of the course brief): *"Compare  
repayment plans with different rates, fees, terms, and affordability limits.  
Known-answer schedules, cash-flow identities, and changed inputs."*

> For a borrower comparing instalment-loan quotations, this project takes a CSV  
> of offers plus a borrower affordability config, produces exact amortisation  
> schedules, an IRR-based effective APR/EAR, an affordability verdict and a  
> ranking, and is useful because headline nominal rates hide fees and term  
> effects; I check it with a known-answer reference, an independent second  
> implementation, cash-flow identities, changed-input and invalid-input cases.

## openJiuwen community link

This reusable Skill is contributed to the openJiuwen community:

**<https://github.com/openJiuwen-ai/jiuwenswarm>** (JiuwenSwarm / WorkSwarm)

Course repository (public): `https://github.com/Kaiming5762/finance-ai-mini-demo`,  
folder `final-project/`. Exact final deliverables commit:  
<https://github.com/Kaiming5762/finance-ai-mini-demo/commit/c50335ee82f42059086027b6dea897080af06254>  
(full publication details in `community/contribution-record.md`).

## What a new user needs

|                       |                                                                                                                                                                                                                             |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Finance user / task   | A borrower or analyst comparing 2-10 fixed-rate instalment loans under a monthly affordability ceiling                                                                                                                      |
| Software / versions   | Python 3.9+ standard library only (tested 3.13.14, Windows 11 / Git Bash, 2026-11-10). No installs, no API key, no network                                                                                                  |
| Inputs                | `skills/loan-offer-comparison/examples/offers_case_A.csv` and `borrower_case_A.json` (synthetic HKD personal loans). Fields, units and validation rules: `data/source_notes.md` and `SKILL.md`                              |
| How to start          | `python scripts/run_all.py` (one command, both cases, writes evidence)                                                                                                                                                      |
| Small example         | `python skills/loan-offer-comparison/scripts/loan_compare.py --offers skills/loan-offer-comparison/examples/offers_case_A.csv --config skills/loan-offer-comparison/examples/borrower_case_A.json --out outputs/my_new_run` |
| Expected checks       | 4 offers, 0 validation errors, 7/7 internal identities per offer, `verify.py` reports **83/83 checks passed**; naive lowest-rate pick `A1_LOW_RATE_FEE` disagrees with lowest APR `A2_NO_FEE`                               |
| Outputs               | `outputs/case_A/` and `outputs/fresh_case_B/` - schedules CSV, `summary.json`, `comparison.md`, two SVG charts, `run_log.txt`, `verification.md`                                                                            |
| Verify                | `python scripts/run_all.py` then open `evidence/` and `outputs/*/verification.md`                                                                                                                                           |
| Limitations           | Monthly only; nominal all-in cost is undiscounted; fee-withholding is an assumption; synthetic inputs; see `SKILL.md` section 9                                                                                             |
| Attribution / licence | Original work, MIT; built with substantial AI assistance (WorkBuddy AI agent); no third-party code or data                                                                                                                  |

## One-command reproduction

```
cd final-project
python scripts/run_all.py
```

This runs the engine and the independent checker for Case A and the fresh Case B,  
and writes four compact execution-evidence records into `evidence/`.  
`python scripts/run_all.py --only case_B --case-b-out outputs/a_new_folder`  
runs the reuse case alone into a new, unused folder.

## Folder map

```
final-project/
  README.md                  <- this file (includes the openJiuwen link)
  requirements.txt           <- standard library only
  scripts/run_all.py         <- one-command reproduction + evidence capture
  skills/loan-offer-comparison/
    SKILL.md                 <- the REUSABLE CONTRIBUTION (regular Skill)
    README.md                <- how a new user loads and runs it
    scripts/loan_compare.py  <- engine (pure stdlib)
    scripts/verify.py        <- independent checker + evaluation battery
    examples/                <- two lawful synthetic cases (CSV + JSON)
  data/source_notes.md       <- provenance, units, validation rules, limitations
  outputs/case_A/            <- primary run results
  outputs/fresh_case_B/      <- fresh-case reuse run results
  evidence/                  <- E1-E4 execution records, evaluation + evidence index
  report/                    <- report.pdf (submission), report.docx, report.html/md
  demo/                      <- 5-minute demonstration script and slides
  community/contribution-record.md
  docs/agent-workflow.md     <- six-part prompt and actual agent-use record
```

## Core result (Case A, HKD 180,000 personal loan)

| Offer              | Nominal p.a. | Peak/month | All-in cost | Effective APR | Affordable |
| ------------------ | -----------: | ---------: | ----------: | ------------: | :--------: |
| A1_LOW_RATE_FEE    |       5.200% |   5,410.94 |   19,293.82 |        6.900% |     YES    |
| A2_NO_FEE          |       6.300% |   5,500.45 |   18,016.18 |        6.300% |     YES    |
| A3_SHORT_TERM      |       6.800% |   8,042.75 |   13,026.09 |        6.800% |     NO     |
| A4_EQUAL_PRINCIPAL |       5.900% |   5,915.00 |   18,652.50 |        6.741% |     YES    |

The naive shortcut picks A1 (lowest headline rate, 5.200%), but its 2.5%  
arrangement fee lifts the effective APR to 6.900%; the genuinely cheapest  
**affordable** offer is A2 (HKD 18,016.18 all-in cost, 6.300% APR). A3 has the  
lowest nominal all-in cost of all four but is unaffordable: its HKD 8,042.75  
peak instalment exceeds the HKD 6,000 monthly cap. This is the finance problem  
the tool solves.

## Submission items

| Course requirement                                  | Where                                                                      |
| --------------------------------------------------- | -------------------------------------------------------------------------- |
| Report PDF (>= 3 pages)                             | `report/report.pdf`                                                        |
| Repository URL + exact Commit URL + source ZIP      | `community/contribution-record.md`, `final-project_source.zip`             |
| 5-minute demonstration                              | `demo/demo-script.md`, `demo/demo-slides.html`                             |
| Execution evidence (2-4 compact records)            | `evidence/E1`-`E4` + `evidence/execution_evidence.md`                      |
| Community record + fresh-run evidence               | `community/contribution-record.md`, `outputs/fresh_case_B/`, `evidence/E3` |
| Runnable code, Skill files, checks, lawful examples | `skills/loan-offer-comparison/`, `scripts/`, `data/`                       |

## Reused work and AI assistance

No third-party code, datasets or tutorial outputs are reused. The annuity and  
IRR definitions are textbook finance. The course's T1/T2/T3 guides supplied the  
six-part prompt pattern, the "check before analysing" rule, the standard-library  
constraint and the Git workflow; they are cited in `report/report.md`. Substantial  
AI assistance came from a WorkBuddy AI agent that read the brief, wrote and  
executed the scripts, inspected saved outputs and drafted and exported this  
report. Every numerical claim is traceable to a saved output file and an  
executable calculation or check - see `evidence/` and `docs/agent-workflow.md`.
