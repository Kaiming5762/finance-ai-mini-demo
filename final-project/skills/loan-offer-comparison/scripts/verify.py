#!/usr/bin/env python3
"""Independent verification and evaluation battery for Loan Offer Compass.

This program is deliberately NOT a re-run of loan_compare.py. Where the engine
uses a closed-form annuity formula and bisection for the IRR, this checker uses
  * a bisection search on a recursive balance equation for the level payment,
  * Newton's method with an analytic derivative for the IRR,
  * the SAVED schedule CSV files as the only source of per-period numbers.

It also runs a small evaluation battery: a known-answer reference case,
changed-input sensitivity checks, invalid-input/error-behaviour checks, and a
comparison with the naive "lowest headline rate" baseline.

Usage:
    python verify.py --offers offers.csv --config borrower.json --out outputs/run1
    python verify.py --battery-only            # just the evaluation battery
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def display_path(path: Path | str) -> str:
    """Render a path relative to the working directory so reports stay portable."""
    p = Path(path)
    try:
        return p.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except (ValueError, OSError):
        return p.as_posix()


def _load_engine():
    spec = importlib.util.spec_from_file_location("loan_compare", HERE / "loan_compare.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ENGINE = _load_engine()
PPY = 12

# External reference: spreadsheet =PMT(0.01, 12, 10000) and the standard
# ordinary-annuity formula, independently evaluated before coding the engine.
KNOWN_ANSWER = {
    "principal": 10000.0,
    "annual_nominal_rate": 0.12,
    "term_months": 12,
    "reference_payment": 888.4878867834161,
    "reference_total_paid": 10661.854641400994,
    "reference_total_interest": 661.8546414009943,
    "source": "closed-form ordinary annuity / =PMT(1%,12,10000) in Excel or Google Sheets",
}


def npv_newton(rate: float, net: float, outflows: list[float]) -> tuple[float, float]:
    """NPV and its analytic derivative at a monthly rate."""
    value = net
    deriv = 0.0
    for t, o in enumerate(outflows, start=1):
        discount = 1.0 + rate
        value -= o / discount ** t
        deriv += t * o / discount ** (t + 1)
    return value, deriv


def irr_newton(net: float, outflows: list[float], tol: float = 1e-12) -> float:
    """Monthly IRR by Newton's method -- different algorithm from the engine's bisection.

    The NPV residual is measured in currency units, so convergence uses a
    relative criterion. A tiny Newton step is itself a converged result: it is
    returned rather than treated as a failure (a plain absolute epsilon on NPV
    can oscillate at the last bit of floating-point precision).
    """
    r = 0.01
    value_tol = tol * max(1.0, net)  # relative to the size of the disbursement
    for _ in range(200):
        value, deriv = npv_newton(r, net, outflows)
        if abs(value) <= value_tol:
            return r
        if deriv <= 0 or not math.isfinite(deriv):
            break
        step = value / deriv
        r_new = r - step
        if r_new <= -0.9:
            r_new = (r - 0.9) / 2.0  # keep the iterate in the valid domain
        if abs(r_new - r) <= 1e-15:
            return r_new
        r = r_new
    raise AssertionError("Newton IRR did not converge")


def payment_by_balance_bisection(principal: float, i: float, n: int) -> float:
    """Level payment found by driving a recursive balance to zero (no annuity formula)."""
    lo, hi = 0.0, principal * (1.0 + i)  # payment cannot exceed one-period debt
    for _ in range(300):
        mid = (lo + hi) / 2.0
        balance = principal
        for _ in range(n):
            balance = balance * (1.0 + i) - mid
        if balance > 0:
            lo = mid  # payment too small -> debt remains
        else:
            hi = mid
        if hi - lo < 1e-10:
            break
    return (lo + hi) / 2.0


def read_schedule(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return [
            {k: (int(v) if k == "period" else float(v)) for k, v in row.items()}
            for row in csv.DictReader(fh)
        ]


def read_offers_raw(path: Path) -> list[dict]:
    """Re-read the ORIGINAL offers CSV independently of summary.json."""
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def approx(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol


class Recorder:
    def __init__(self):
        self.rows = []

    def add(self, case, method, expected, actual, passed, note=""):
        self.rows.append({
            "case": case, "method": method, "expected": str(expected),
            "actual": str(actual), "pass": bool(passed), "note": note,
        })

    @property
    def failed(self):
        return [r for r in self.rows if not r["pass"]]


def verify_run(offers_path: Path, config_path: Path | None, out_dir: Path, tol: float, rec: Recorder) -> None:
    """Independently recompute the saved run from the saved files."""
    summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
    raw_offers = read_offers_raw(offers_path)
    cfg = summary["case"]

    rec.add(
        "run integrity", "summary.json offer count == offers CSV row count",
        len(raw_offers), len(summary["offers"]),
        len(raw_offers) == len(summary["offers"]),
    )
    all_internal = all(
        check["pass"] for offer in summary["offers"] for check in offer["checks"].values()
    )
    rec.add(
        "run integrity", "all engine self-checks pass",
        "True", str(all_internal), all_internal,
        "Engine self-checks are not independent; see the recomputations below.",
    )

    for raw, saved in zip(raw_offers, summary["offers"]):
        oid = raw["offer_id"]
        P = float(raw["principal"])
        rate = float(raw["annual_nominal_rate"])
        n = int(float(raw["term_months"]))
        i = rate / PPY
        fee_fixed = float(raw.get("fee_upfront_fixed") or 0.0)
        fee_pct = float(raw.get("fee_upfront_pct") or 0.0)
        fee_monthly = float(raw.get("fee_monthly") or 0.0)
        rtype = raw["repayment_type"]
        upfront = fee_fixed + fee_pct * P
        net = P - upfront

        rows = read_schedule(out_dir / saved["schedule_file"])
        outflows = [r["total_outflow"] for r in rows]
        rec.add(
            oid, "schedule row count == term_months", n, len(rows), len(rows) == n,
            "Re-read from the saved schedule CSV.",
        )

        # --- identity checks computed from the saved CSV ---------------------
        e_interest = max(abs(r["interest"] - r["opening_balance"] * i) for r in rows)
        e_balance = max(abs(r["opening_balance"] - r["principal"] - r["closing_balance"]) for r in rows)
        e_flow = max(abs(r["total_outflow"] - (r["interest"] + r["principal"] + r["monthly_fee"])) for r in rows)
        sum_principal = sum(r["principal"] for r in rows)
        sum_interest = sum(r["interest"] for r in rows)
        sum_outflow = sum(outflows)
        for label, err in (
            ("interest_t = opening_t * monthly rate", e_interest),
            ("closing_t = opening_t - principal_t", e_balance),
            ("outflow_t = interest + principal + monthly fee", e_flow),
        ):
            rec.add(oid, label, f"max abs error <= {tol}", f"{err:.3e}", err <= tol)
        rec.add(oid, "sum of principal == original principal", f"{P:.6f}",
                f"{sum_principal:.6f}", approx(sum_principal, P, tol))
        rec.add(oid, "final closing balance == 0", "0", f"{rows[-1]['closing_balance']:.3e}",
                abs(rows[-1]["closing_balance"]) <= tol)
        rec.add(oid, "sum(outflows) = interest + principal + all monthly fees",
                f"{sum_interest + P + fee_monthly * n:.6f}", f"{sum_outflow:.6f}",
                approx(sum_outflow, sum_interest + P + fee_monthly * n, tol))

        # --- independent payment -------------------------------------------
        if rtype == "annuity":
            indep_pmt = payment_by_balance_bisection(P, i, n)
            engine_pmt = saved["level_instalment_ex_fees"]
            rec.add(oid, "level instalment: bisection on balance recursion vs engine closed form",
                    f"{indep_pmt:.6f}", f"{engine_pmt:.6f}",
                    approx(indep_pmt, engine_pmt, tol),
                    "Independent algorithm; equality supports the annuity formula.")
            rec.add(oid, "first schedule outflow == level instalment + monthly fee",
                    f"{indep_pmt + fee_monthly:.6f}", f"{outflows[0]:.6f}",
                    approx(outflows[0], indep_pmt + fee_monthly, tol))
        else:
            # straight-line plan: constant principal, declining total payment
            first = P / n + P * i + fee_monthly
            rec.add(oid, "equal-principal first outflow",
                    f"{first:.6f}", f"{outflows[0]:.6f}", approx(outflows[0], first, tol))
            rec.add(oid, "equal-principal outflow is strictly declining",
                    "first > last", f"{outflows[0]:.2f} > {outflows[-1]:.2f}",
                    outflows[0] > outflows[-1])

        # --- independent IRR (Newton) ---------------------------------------
        indep_irr = irr_newton(net, outflows)
        indep_apr = indep_irr * PPY
        rec.add(oid, "effective APR: Newton IRR vs engine bisection IRR",
                f"{indep_apr:.9f}", f"{saved['effective_apr']:.9f}",
                approx(indep_apr, saved["effective_apr"], 1e-8),
                "Different root-finding method on the same saved cash flows.")
        resid, _ = npv_newton(indep_irr, net, outflows)
        rec.add(oid, "NPV of saved cash flows at independently solved IRR == 0",
                f"|NPV| <= {tol}", f"{abs(resid):.3e}", abs(resid) <= tol)

        # --- cost and affordability identities ------------------------------
        total_fees = upfront + fee_monthly * n
        rec.add(oid, "all-in cost == total interest + all fees",
                f"{sum_interest + total_fees:.6f}", f"{saved['total_cost']:.6f}",
                approx(saved["total_cost"], sum_interest + total_fees, tol))
        rec.add(oid, "all-in cost == sum(outflows) - net disbursement",
                f"{sum_outflow - net:.6f}", f"{saved['total_cost']:.6f}",
                approx(saved["total_cost"], sum_outflow - net, tol))
        rec.add(oid, "peak outflow == max of saved outflows",
                f"{max(outflows):.6f}", f"{saved['peak_monthly_outflow']:.6f}",
                approx(saved["peak_monthly_outflow"], max(outflows), tol))
        ceiling = min(cfg["monthly_budget_cap"], cfg["monthly_income"] * cfg["max_payment_to_income"])
        expected_affordable = max(outflows) <= ceiling + tol
        rec.add(oid, "affordability flag matches saved peak vs binding ceiling",
                str(expected_affordable), str(saved["affordable"]),
                expected_affordable == saved["affordable"])

    # --- baseline comparison -------------------------------------------------
    naive = min(summary["offers"], key=lambda r: (r["annual_nominal_rate"], r["offer_id"]))
    rec.add("baseline", "naive lowest-headline-rate pick (from saved summary)",
            "recorded", naive["offer_id"], True,
            "Simple heuristic used as the comparison reference.")
    rec.add("baseline", "lowest effective APR among all offers",
            summary["ranking"]["by_effective_apr"][0],
            summary["naive_baseline"]["all_in_pick"],
            summary["ranking"]["by_effective_apr"][0] == summary["naive_baseline"]["all_in_pick"])


def _offer(**kw) -> dict:
    base = {
        "offer_id": "BASE", "lender": "Synthetic Bank", "principal": 120000.0,
        "annual_nominal_rate": 0.0599, "term_months": 36,
        "fee_upfront_fixed": 0.0, "fee_upfront_pct": 0.0, "fee_monthly": 0.0,
        "repayment_type": "annuity",
    }
    base.update(kw)
    return base


def _cfg(**kw) -> dict:
    base = {
        "case_id": "battery", "currency": "HKD", "monthly_budget_cap": 4000.0,
        "monthly_income": 30000.0, "max_payment_to_income": 0.35,
        "periods_per_year": 12,
    }
    base.update(kw)
    return base


def evaluation_battery(rec: Recorder) -> None:
    """Small, hand-checkable evaluation: reference case, changed inputs, error behaviour."""
    tol = 1e-6

    # 1. Known-answer schedule -------------------------------------------------
    k = KNOWN_ANSWER
    ref_offer = _offer(
        principal=k["principal"], annual_nominal_rate=k["annual_nominal_rate"],
        term_months=k["term_months"],
    )
    rows = ENGINE.build_schedule(ref_offer)
    pmt = rows[0]["total_outflow"]
    total_paid = sum(r["total_outflow"] for r in rows)
    total_interest = sum(r["interest"] for r in rows)
    rec.add("K1 known answer", "reference level payment", f"{k['reference_payment']:.9f}",
            f"{pmt:.9f}", approx(pmt, k["reference_payment"], 1e-8), k["source"])
    rec.add("K1 known answer", "reference total paid", f"{k['reference_total_paid']:.9f}",
            f"{total_paid:.9f}", approx(total_paid, k["reference_total_paid"], 1e-7))
    rec.add("K1 known answer", "reference total interest", f"{k['reference_total_interest']:.9f}",
            f"{total_interest:.9f}", approx(total_interest, k["reference_total_interest"], 1e-7))
    indep_pmt = payment_by_balance_bisection(k["principal"], 0.01, k["term_months"])
    rec.add("K1 known answer", "independent bisection payment vs external reference",
            f"{k['reference_payment']:.9f}", f"{indep_pmt:.9f}",
            approx(indep_pmt, k["reference_payment"], 1e-8))

    # 2. Changed inputs --------------------------------------------------------
    base = ENGINE.summarize(_offer(), _cfg(), tol)
    higher_rate = ENGINE.summarize(_offer(annual_nominal_rate=0.0699), _cfg(), tol)
    rec.add("C1 changed input", "+1 percentage point on the nominal rate",
            "higher payment and higher APR",
            f"{base['peak_monthly_outflow']:.2f} -> {higher_rate['peak_monthly_outflow']:.2f}; "
            f"APR {base['effective_apr']*100:.3f}% -> {higher_rate['effective_apr']*100:.3f}%",
            higher_rate["peak_monthly_outflow"] > base["peak_monthly_outflow"]
            and higher_rate["effective_apr"] > base["effective_apr"])

    fee_offer = _offer(fee_upfront_pct=0.02)
    with_fee = ENGINE.summarize(fee_offer, _cfg(), tol)
    rec.add("C2 changed input", "+2% upfront fee (HKD 2,400)",
            "payment unchanged; APR up; all-in cost up by exactly 2,400",
            f"payment {base['peak_monthly_outflow']:.2f} -> {with_fee['peak_monthly_outflow']:.2f}; "
            f"cost {base['total_cost']:.2f} -> {with_fee['total_cost']:.2f}; "
            f"APR {base['effective_apr']*100:.3f}% -> {with_fee['effective_apr']*100:.3f}%",
            approx(with_fee["peak_monthly_outflow"], base["peak_monthly_outflow"], tol)
            and with_fee["effective_apr"] > base["effective_apr"]
            and approx(with_fee["total_cost"] - base["total_cost"], 2400.0, tol),
            "Shows why a headline rate alone cannot rank fee-bearing offers.")

    longer = ENGINE.summarize(_offer(term_months=48), _cfg(), tol)
    rec.add("C3 changed input", "term 36 -> 48 months",
            "lower monthly payment, higher total interest",
            f"payment {base['peak_monthly_outflow']:.2f} -> {longer['peak_monthly_outflow']:.2f}; "
            f"interest {base['total_interest']:.2f} -> {longer['total_interest']:.2f}",
            longer["peak_monthly_outflow"] < base["peak_monthly_outflow"]
            and longer["total_interest"] > base["total_interest"])

    monthly = ENGINE.summarize(_offer(fee_monthly=50.0), _cfg(), tol)
    rec.add("C4 changed input", "+HKD 50 monthly fee",
            "peak outflow up by exactly 50; total fees up by 50 * 36",
            f"peak +{monthly['peak_monthly_outflow'] - base['peak_monthly_outflow']:.2f}; "
            f"fees +{monthly['total_fees'] - base['total_fees']:.2f}",
            approx(monthly["peak_monthly_outflow"] - base["peak_monthly_outflow"], 50.0, tol)
            and approx(monthly["total_fees"] - base["total_fees"], 1800.0, tol))

    tight = ENGINE.summarize(_offer(), _cfg(monthly_budget_cap=3000.0), tol)
    loose = ENGINE.summarize(_offer(), _cfg(monthly_budget_cap=5000.0), tol)
    rec.add("C5 changed input", "budget cap 3,000 vs 5,000",
            "affordability flips NO -> YES",
            f"3,000: {tight['affordable']}; 5,000: {loose['affordable']}",
            (not tight["affordable"]) and loose["affordable"])

    linear = ENGINE.summarize(_offer(repayment_type="equal_principal"), _cfg(), tol)
    rec.add("C6 changed input", "annuity -> equal-principal plan",
            "declining outflow and lower total interest",
            f"first {linear['first_instalment']:.2f} > last {linear['final_monthly_outflow']:.2f}; "
            f"interest {base['total_interest']:.2f} -> {linear['total_interest']:.2f}",
            linear["first_instalment"] > linear["final_monthly_outflow"]
            and linear["total_interest"] < base["total_interest"])

    # 3. Invalid inputs / error behaviour -------------------------------------
    header = ("offer_id,lender,principal,annual_nominal_rate,term_months,"
              "repayment_type,fee_upfront_fixed,fee_upfront_pct,fee_monthly")
    good = "A,Bank,120000,0.0599,36,annuity,0,0,0"
    bad_cases = {
        "negative principal": "A,Bank,-120000,0.0599,36,annuity,0,0,0",
        "zero term": "A,Bank,120000,0.0599,0,annuity,0,0,0",
        "unknown repayment type": "A,Bank,120000,0.0599,36,bullet,0,0,0",
        "non-numeric rate": "A,Bank,120000,cheap,36,annuity,0,0,0",
        "rate above 100%": "A,Bank,120000,1.5,36,annuity,0,0,0",
        "duplicate offer id": good + "\n" + good,
        "missing offer id": ",Bank,120000,0.0599,36,annuity,0,0,0",
        "fractional term": "A,Bank,120000,0.0599,36.5,annuity,0,0,0",
    }
    with tempfile.TemporaryDirectory(prefix="loan-invalid-") as tmp:
        tmpdir = Path(tmp)
        for label, body in bad_cases.items():
            p = tmpdir / "bad.csv"
            p.write_text(header + "\n" + body + "\n", encoding="utf-8")
            try:
                ENGINE.load_offers(p)
                outcome = "NO ERROR (bad)"
                passed = False
            except ENGINE.InputError as exc:
                outcome = "InputError: " + str(exc).splitlines()[0][:90]
                passed = True
            rec.add("E1 invalid input", label, "clear InputError, no calculation", outcome, passed)

        p = tmpdir / "bad.csv"
        p.write_text(header + "\n" + "A,Bank,-120000,0.0599,36,annuity,0,0,0\n", encoding="utf-8")
        cfgp = tmpdir / "cfg.json"
        cfgp.write_text(json.dumps(_cfg()), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(HERE / "loan_compare.py"), "--offers", str(p),
             "--config", str(cfgp), "--out", str(tmpdir / "should_not_exist")],
            capture_output=True, text=True,
        )
        rec.add("E2 error behaviour", "CLI on invalid input exits nonzero and writes nothing",
                "returncode 3 + 'INPUT ERROR' on stderr",
                f"returncode {proc.returncode}; stderr={proc.stderr.strip()[:110]!r}; "
                f"output folder created={(tmpdir / 'should_not_exist').exists()}",
                proc.returncode == 3 and "INPUT ERROR" in proc.stderr
                and not (tmpdir / "should_not_exist").exists())


def write_report(path: Path, rec: Recorder, out_dir: Path | None, offers_path: Path | None) -> None:
    n_pass = sum(1 for r in rec.rows if r["pass"])
    lines = [
        "# Independent verification and evaluation record",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')} | "
        f"Checker: `verify.py` | Engine: `loan_compare.py` v{ENGINE.ENGINE_VERSION}",
        "",
        f"**Result: {n_pass}/{len(rec.rows)} checks passed, {len(rec.failed)} failed.**",
        "",
        "Two different checking methods were used, as the project brief asks:",
        "",
        "1. **Independent recomputation** - the checker re-reads the saved schedule CSVs "
        "and the original offers CSV, finds the level payment by bisection on a recursive "
        "balance equation (not the annuity closed form), and solves the IRR by Newton's "
        "method with an analytic derivative (not the engine's bisection). It then checks "
        "the cash-flow identities and NPV=0 on the saved numbers.",
        "2. **External reference / changed-input / error battery** - a known-answer "
        "12-month, 12% p.a. loan compared with a spreadsheet PMT reference, six changed-input "
        "cases, eight invalid-input cases and one CLI error-behaviour case.",
        "",
        "The naive baseline (pick the lowest headline nominal rate) is recorded so the "
        "ranking can be compared with a simple heuristic.",
        "",
        "| Case / input | Method / baseline | Expected / reference | Actual | Pass | Note |",
        "|---|---|---|---|:---:|---|",
    ]
    for r in rec.rows:
        clean = lambda s: str(s).replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {clean(r['case'])} | {clean(r['method'])} | {clean(r['expected'])} | "
            f"{clean(r['actual'])} | {'PASS' if r['pass'] else '**FAIL**'} | {clean(r['note'])} |"
        )
    lines += [
        "",
        "## What these checks establish - and what they do not",
        "",
        "- They establish internal arithmetic consistency, agreement between two different "
        "implementations of the payment and IRR, and correct rejection of malformed inputs.",
        "- They do **not** establish that the synthetic offer data are real bank quotes, that "
        "any lender's quotation uses this fee timing, or that a real borrower's rate would "
        "stay fixed. The fee-withholding convention is an assumption, stated in SKILL.md.",
        "- All-in cost is a nominal sum and is not discounted; APR/EAR is the time-value-"
        "adjusted measure. Ranking by these two can differ, which is expected.",
        "- The known-answer reference was derived from the standard annuity formula, which "
        "is also the basis of the engine's payment formula; the independent bisection "
        "payment and the spreadsheet PMT value provide the cross-check.",
        "",
    ]
    if out_dir is not None:
        lines += [f"Verified run folder: `{display_path(out_dir)}`", ""]
    if offers_path is not None:
        lines += [f"Original offers file: `{display_path(offers_path)}`", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def build_parser():
    p = argparse.ArgumentParser(description="Independent verification of Loan Offer Compass")
    p.add_argument("--offers", type=Path, default=None)
    p.add_argument("--config", type=Path, default=None)
    p.add_argument("--out", type=Path, default=None, help="folder containing a completed run")
    p.add_argument("--report", type=Path, default=None, help="where to write verification.md")
    p.add_argument("--json", type=Path, default=None, help="where to write verification.json")
    p.add_argument("--tol", type=float, default=1e-6)
    p.add_argument("--battery-only", action="store_true")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    rec = Recorder()
    if not args.battery_only and (args.offers is None or args.out is None):
        print("INPUT ERROR: --offers and --out are required unless --battery-only", file=sys.stderr)
        return 2
    # Each stage is isolated: a crash in one stage is recorded as a failed check
    # but must not silently skip the rest of the evaluation.
    for label, stage in (
        ("run verification", lambda: verify_run(args.offers, args.config, args.out, args.tol, rec)),
        ("evaluation battery", lambda: evaluation_battery(rec)),
    ):
        if label == "run verification" and args.battery_only:
            continue
        try:
            stage()
        except Exception as exc:
            rec.add("checker", f"{label} completed without exception", "no exception",
                    f"{type(exc).__name__}: {exc}", False)

    report_path = args.report or (args.out / "verification.md" if args.out else Path("verification.md"))
    report_path.parent.mkdir(parents=True, exist_ok=True)
    write_report(report_path, rec, None if args.battery_only else args.out, args.offers)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(rec.rows, indent=2), encoding="utf-8")

    n_pass = sum(1 for r in rec.rows if r["pass"])
    print(f"Independent verification: {n_pass}/{len(rec.rows)} checks passed, {len(rec.failed)} failed")
    if args.out and not args.battery_only:
        print(f"Verified run: {display_path(args.out)}")
    for r in rec.failed:
        print(f"  FAIL | {r['case']} | {r['method']} | expected {r['expected']} | got {r['actual']}")
    print(f"Report: {display_path(report_path)}")
    return 0 if not rec.failed else 5


if __name__ == "__main__":
    raise SystemExit(main())
