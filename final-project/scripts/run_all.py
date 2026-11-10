#!/usr/bin/env python3
"""One-command reproduction of the Loan Offer Compass final project.

Runs the engine and the independent checker for Case A and/or the fresh Case B,
captures the REAL stdout/stderr/exit code of each subprocess, and writes compact
execution-evidence records into evidence/ (the brief allows "two to four readable
screenshots or equivalent compact records").

Usage (from any working directory):
    python scripts/run_all.py                 # both cases
    python scripts/run_all.py --only case_A
    python scripts/run_all.py --only case_B  # fresh-case reuse run
    python scripts/run_all.py --case-b-out outputs/my_new_folder

All spawned commands use paths relative to the project root, and the evidence
records show the interpreter as the portable token "python". No machine-specific
absolute path is baked into the project. Pure standard library.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "loan-offer-comparison"
ENGINE = SKILL / "scripts" / "loan_compare.py"
CHECKER = SKILL / "scripts" / "verify.py"
EXAMPLES = SKILL / "examples"
EVIDENCE = ROOT / "evidence"

CASES = {
    "case_A": {
        "offers": EXAMPLES / "offers_case_A.csv",
        "config": EXAMPLES / "borrower_case_A.json",
        "out": ROOT / "outputs" / "case_A",
        "engine_log": "E1_case_A_run.txt",
        "check_log": "E2_verification.txt",
    },
    "case_B": {
        "offers": EXAMPLES / "offers_case_B.csv",
        "config": EXAMPLES / "borrower_case_B.json",
        "out": ROOT / "outputs" / "fresh_case_B",
        "engine_log": "E3_fresh_case_B_run.txt",
        "check_log": "E4_changed_inputs_checks.txt",
    },
}


def rel(path: Path | str) -> str:
    """Display paths relative to the project root, portable across machines."""
    p = Path(path)
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except (ValueError, OSError):
        return p.as_posix()


def command_for(key: str, kind: str) -> tuple[list[str], str]:
    """Return (actual argv, portable command shown in the evidence record)."""
    c = CASES[key]
    script = ENGINE if kind == "engine" else CHECKER
    tokens = [rel(script), "--offers", rel(c["offers"]), "--config", rel(c["config"]),
              "--out", rel(c["out"])]
    if kind == "check":
        tokens += ["--report", rel(c["out"] / "verification.md"),
                   "--json", rel(c["out"] / "verification.json")]
    return [sys.executable] + tokens, "python " + " ".join(tokens)


def execute(cmd: list[str], shown: str, log_path: Path, title: str) -> bool:
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    header = [
        "=" * 78,
        title,
        "=" * 78,
        f"UTC timestamp : {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "Working dir   : project root (parent of scripts/)",
        f"Python        : {sys.version.split()[0]} on {sys.platform}",
        "Interpreter   : sys.executable resolved locally; shown as 'python' below",
        f"Command       : {shown}",
        f"Exit code     : {proc.returncode}",
        "-" * 78,
        "STDOUT",
        "-" * 78,
    ]
    body = [proc.stdout.rstrip()]
    if proc.stderr.strip():
        body += ["", "-" * 78, "STDERR", "-" * 78, proc.stderr.rstrip()]
    body += ["", "-" * 78, "END OF RECORD", "-" * 78, ""]
    log_path.write_text("\n".join(header + body), encoding="utf-8")
    print(f"[{title}] exit={proc.returncode} -> {rel(log_path)}")
    if proc.stdout.strip():
        print("    " + proc.stdout.strip().splitlines()[0])
    return proc.returncode == 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Reproduce the final-project runs and capture evidence")
    ap.add_argument("--only", choices=("case_A", "case_B", "all"), default="all")
    ap.add_argument("--case-b-out", type=Path, default=None,
                    help="new output folder for the fresh-case reuse run")
    args = ap.parse_args()

    if args.case_b_out is not None:
        CASES["case_B"]["out"] = (ROOT / args.case_b_out).resolve()

    keys = ("case_A", "case_B") if args.only == "all" else (args.only,)
    results = []
    for key in keys:
        c = CASES[key]
        engine_cmd, engine_shown = command_for(key, "engine")
        check_cmd, check_shown = command_for(key, "check")
        ok1 = execute(engine_cmd, engine_shown, EVIDENCE / c["engine_log"],
                      f"EXECUTION EVIDENCE | {key} | engine run (loan_compare.py)")
        ok2 = execute(check_cmd, check_shown, EVIDENCE / c["check_log"],
                      f"EXECUTION EVIDENCE | {key} | independent verification + evaluation battery")
        results.append((key, ok1, ok2))

    print()
    print("Reproduction summary")
    for key, ok1, ok2 in results:
        print(f"  {key}: engine={'PASS' if ok1 else 'FAIL'}  verification={'PASS' if ok2 else 'FAIL'}")
    print(f"  Outputs : {rel(ROOT / 'outputs')}")
    print(f"  Evidence: {rel(EVIDENCE)}")
    return 0 if all(o1 and o2 for _, o1, o2 in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
