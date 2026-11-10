# 5-minute demonstration script

**Format:** live, single take, no edits. If recorded instead, label the file
`recorded` and state the recording date; do not present a recorded run as live.
**Platform:** any terminal with Python 3.9+ in `final-project/`. No installs, no
network, no API key.
**Slides:** `demo/demo-slides.html` (open in a browser; contains the two charts).

| Time | What to show | Exact action / words |
|---|---|---|
| **0:00 - 0:45** | **The user task** | Slide 1. "A borrower has four HKD 180,000 personal-loan offers with different rates, arrangement fees, terms and repayment structures, and a HKD 6,000 monthly ceiling. Which is cheapest among the ones they can actually afford?" Show `offers_case_A.csv` and `borrower_case_A.json` for 10 seconds. State that data are synthetic teaching inputs. |
| **0:45 - 1:45** | **Core output** | Run `python scripts/run_all.py --only case_A`. While it runs, point at the real stdout: input checks (4 offers, 0 errors), the four offers' peak/month, all-in cost, APR, affordability and **7/7** identity checks. Then open `outputs/case_A/comparison.md` and show the table. Highlight: naive lowest-rate pick `A1` (5.200%) but its effective APR is 6.900%; `A2` (6.300% headline) is the cheapest **affordable** offer at HKD 18,016.18; `A3` is cheapest overall but unaffordable (HKD 8,042.75 > HKD 6,000). Show `balance_paths.svg` / `cost_breakdown.svg` on slide 2. |
| **1:45 - 3:00** | **An important check** | Run `python skills/loan-offer-comparison/scripts/verify.py --offers skills/loan-offer-comparison/examples/offers_case_A.csv --config skills/loan-offer-comparison/examples/borrower_case_A.json --out outputs/case_A --report outputs/case_A/verification.md`. Show **83/83 checks passed**. Open `outputs/case_A/verification.md` and point at three rows: the known-answer `=PMT(1%,12,10000)` = 888.487886783; the independent bisection payment vs the closed form (both 5,500.449578 for A2); the Newton IRR vs the bisection IRR (both 0.069003688 for A1). Explain these are **different algorithms reading saved CSVs**, not a repeat of the same script. Mention the honest failure: the first run was 11/12 with a Newton convergence bug, fixed, then 83/83. |
| **3:00 - 4:00** | **Changed-input check** | Edit one CSV cell in a **copy** of the offers file: change A1 rate from `0.0520` to `0.0620`. Run `python skills/loan-offer-comparison/scripts/loan_compare.py --offers <copy> --config skills/loan-offer-comparison/examples/borrower_case_A.json --out outputs/demo_changed`. Show that A1's payment and effective APR both rise. Alternatively run `python skills/loan-offer-comparison/scripts/verify.py --battery-only --report demo/battery.md` and show the six changed-input and eight invalid-input rows. State that bad inputs stop the run with exit code 3 rather than being silently dropped. |
| **4:00 - 4:45** | **The reusable component** | Slide 3. Show `skills/loan-offer-comparison/SKILL.md` (YAML name/description, inputs/outputs, procedure, checks, failure handling) and the `README.md`. Then run `python scripts/run_all.py --only case_B --case-b-out outputs/demo_fresh` into a **new, unused folder** with a different case (CNY 600,000 SME equipment finance). Show its stdout: 4 offers, 83/83 checks, and the same headline-rate trap on different inputs. Say: "This is labelled self-reproduction, not a classmate's reuse test." |
| **4:45 - 5:00** | **Where it lives** | Slide 4. Show the public repository URL, the exact commit URL from `community/contribution-record.md`, and the openJiuwen link https://github.com/openJiuwen-ai/jiuwenswarm in the README. Close with one limitation: monthly instalments only, synthetic data, nominal all-in cost is not discounted. |

## Pre-flight checklist (do before starting the clock)

```
cd final-project
python --version
python scripts/run_all.py            # confirm both cases pass and E1-E4 exist
```

- Close unrelated windows; no credentials, tokens or key files on screen.
- If capturing screenshots for the submission, keep them **outside** the repo
  and make sure the repository owner, file path and commit are readable.
- Recorded vs live: state it out loud at 0:00 and write it in the submission
  text. Do not relabel a recorded run as live.

## What the grader should be able to see

1. The user task and the documented inputs (CSV + JSON).
2. The core output actually produced by a tool run (not chat text).
3. One important check with an independent method and its pass/fail result.
4. The reusable component invoked on a new case with a new output folder.
5. An honest limitation and a labelled failure/correction.
