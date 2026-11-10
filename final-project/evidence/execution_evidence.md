# Execution evidence index

The course brief allows **"Two to four readable screenshots or equivalent
compact records showing actual WorkSwarm/tool use and verification."** This
project uses four compact tool-output records rather than UI screenshots. Each
records a UTC timestamp, working directory, Python version, the exact command,
exit code, and the complete stdout/stderr captured from a real subprocess.

They were produced by `scripts/run_all.py`, which launches the engine and the
independent checker as subprocesses and writes their real output to these files.
A chat message saying "done" is not used as evidence.

| # | File | What it shows | Result |
|---|---|---|---|
| **E1** | `E1_case_A_run.txt` | Agent executing the calculation tool `loan_compare.py` on Case A: input checks (4 offers, 0 errors, 0 duplicates), binding ceiling, the four offers' peak payment / all-in cost / APR / EAR / affordability, 7/7 internal identity checks each, the naive-vs-APR disagreement and the output folder | exit 0 |
| **E2** | `E2_verification.txt` | Agent running the independent checker `verify.py` on the saved Case A output: **83/83 checks passed, 0 failed**, and the path of the written `verification.md` / `verification.json` | exit 0 |
| **E3** | `E3_fresh_case_B_run.txt` | Agent executing the **reused Skill** in a clean setup on a different case (CNY SME equipment finance) into a new, previously empty output folder; shows a different input set, output and verification path | exit 0 |
| **E4** | `E4_changed_inputs_checks.txt` | Independent verification of the fresh Case B run, including the known-answer, changed-input, invalid-input and error-behaviour battery: **83/83 checks passed, 0 failed** | exit 0 |

Supporting results (not uploaded as separate evidence): `outputs/case_A/` and
`outputs/fresh_case_B/` contain the schedules, `summary.json`, `comparison.md`,
`run_log.txt`, two SVG charts and the full `verification.md` tables. The failed
first verification (11/12, `Newton IRR did not converge`, `verify.py` exit 5)
and its correction are described honestly in `report/report.md` section 5.4 and
`docs/agent-workflow.md`; E2 shows the **final successful run**, as the brief
instructs.

## How to reproduce these records

```
cd final-project
python scripts/run_all.py                     # rewrites E1-E4
python scripts/run_all.py --only case_B --case-b-out outputs/a_new_folder
```

## Reading the records

- `Command` in E1-E4 is shown in portable form: all paths are relative to the
  project root and the locally resolved interpreter (`sys.executable`) is
  displayed as `python`. The header states this explicitly, and the stdout,
  stderr and exit codes are untouched real subprocess output. No absolute path
  is hard-coded in `SKILL.md`, `README.md`, the scripts or the generated logs.
- No API key, token, password or personal financial data appears in any record.
- Tool environment: these are the actual tool outputs of a WorkBuddy AI single
  agent using approved local tools (file read/write, terminal, Git), the same
  class of local tools described for WorkSwarm/JiuwenSwarm in T1-T3. See
  `report/report.md` section 3 for the honest labelling. If a WorkSwarm-specific
  UI screenshot is required, run the identical `run_all.py` command inside the
  classroom WorkSwarm app and capture its tool panel.
