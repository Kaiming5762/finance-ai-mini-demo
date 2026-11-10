#!/usr/bin/env python3
"""Loan Offer Compass -- compare amortising loan offers on an all-in cash-flow basis.

Pure Python standard library. No third-party packages, no network, no credentials.

Given a CSV of loan offers and a small borrower config, this engine
  * validates every input and stops with an explanation on bad data,
  * builds an exact month-by-month amortisation schedule per offer
    (level-payment "annuity" or declining-payment "equal_principal"),
  * computes the effective APR / EAR from the borrower's actual cash flows
    (IRR, so upfront and monthly fees are included),
  * applies a monthly affordability ceiling and a payment-to-income ceiling,
  * computes the largest principal the borrower could afford on each offer,
  * ranks offers and compares with the naive "lowest headline rate" shortcut,
  * writes schedules, JSON, Markdown, SVG charts and a run log.

Cash-flow convention (borrower's point of view), currency units, monthly periods:
    t = 0      + (principal - upfront_fee)          net amount received
    t = 1..n   - (interest + principal + monthly_fee)   instalment outflow
    APR  = periods_per_year * i_IRR   (nominal annual rate, monthly compounding)
    EAR  = (1 + i_IRR) ** periods_per_year - 1
    all-in cost = sum(outflows) - net_received = total interest + all fees

Usage:
    python loan_compare.py --offers offers.csv --config borrower.json --out outputs/run1
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ENGINE_VERSION = "1.0.0"
PERIODS_PER_YEAR = 12  # monthly instalments only; see LIMITATIONS in SKILL.md


def display_path(path: Path | str) -> str:
    """Render a path relative to the working directory so logs stay portable.

    Keeps machine-specific absolute paths out of committed run logs and evidence.
    """
    p = Path(path)
    try:
        return p.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except (ValueError, OSError):
        return p.as_posix()

REQUIRED_COLUMNS = (
    "offer_id",
    "lender",
    "principal",
    "annual_nominal_rate",
    "term_months",
    "repayment_type",
)
OPTIONAL_COLUMNS = {
    "fee_upfront_fixed": 0.0,
    "fee_upfront_pct": 0.0,
    "fee_monthly": 0.0,
}
REPAYMENT_TYPES = ("annuity", "equal_principal")
PALETTE = ("#2563eb", "#dc2626", "#059669", "#d97706", "#7c3aed", "#0891b2")


class InputError(ValueError):
    """Raised when the supplied inputs do not satisfy the declared rules."""


# --------------------------------------------------------------------------- #
# Input handling and validation
# --------------------------------------------------------------------------- #

def _finite_float(raw, field, row_label, errors, minimum=None, maximum=None):
    """Parse one numeric cell, accumulating errors instead of raising early."""
    if raw is None or str(raw).strip() == "":
        errors.append(f"{row_label}: '{field}' is missing")
        return None
    try:
        value = float(str(raw).strip())
    except (TypeError, ValueError):
        errors.append(f"{row_label}: '{field}' is not numeric (got {raw!r})")
        return None
    if not math.isfinite(value):
        errors.append(f"{row_label}: '{field}' is not finite (got {raw!r})")
        return None
    if minimum is not None and value < minimum:
        errors.append(f"{row_label}: '{field}' must be >= {minimum} (got {value})")
        return None
    if maximum is not None and value > maximum:
        errors.append(f"{row_label}: '{field}' must be <= {maximum} (got {value})")
        return None
    return value


def load_offers(path: Path):
    """Read and validate the offers CSV. Returns (offers, input_checks)."""
    if not path.is_file():
        raise InputError(f"offers file not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames or [])
        raw_rows = list(reader)

    checks = {
        "offers_file": path.name,
        "columns_found": fieldnames,
        "row_count": len(raw_rows),
        "duplicate_offer_ids": [],
        "missing_values": 0,
        "unknown_columns_ignored": [],
        "validation_errors": [],
    }
    errors = []
    if not fieldnames:
        raise InputError(f"offers CSV has no header row: {path}")
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in fieldnames]
    if missing_cols:
        raise InputError(f"offers CSV is missing required columns: {', '.join(missing_cols)}")
    known = set(REQUIRED_COLUMNS) | set(OPTIONAL_COLUMNS)
    checks["unknown_columns_ignored"] = [c for c in fieldnames if c not in known]
    if not raw_rows:
        raise InputError(f"offers CSV contains no data rows: {path}")

    offers = []
    seen = {}
    for idx, raw in enumerate(raw_rows, start=2):  # CSV line 1 is the header
        label = f"row {idx}"
        oid = (raw.get("offer_id") or "").strip()
        if not oid:
            errors.append(f"{label}: 'offer_id' is empty")
        elif oid in seen:
            checks["duplicate_offer_ids"].append(oid)
            errors.append(f"{label}: duplicate offer_id {oid!r} (first seen row {seen[oid]})")
        else:
            seen[oid] = idx
            label = f"row {idx} ({oid})"

        for col in fieldnames:
            if raw.get(col) is None or str(raw.get(col)).strip() == "":
                if col in REQUIRED_COLUMNS or col in OPTIONAL_COLUMNS:
                    checks["missing_values"] += 1

        principal = _finite_float(raw.get("principal"), "principal", label, errors, minimum=1e-9)
        rate = _finite_float(
            raw.get("annual_nominal_rate"), "annual_nominal_rate", label, errors,
            minimum=0.0, maximum=1.0,
        )
        term_raw = _finite_float(raw.get("term_months"), "term_months", label, errors, minimum=1)
        term = None
        if term_raw is not None:
            if abs(term_raw - round(term_raw)) > 1e-12:
                errors.append(f"{label}: 'term_months' must be a whole number (got {term_raw})")
            else:
                term = int(round(term_raw))
                if term > 600:
                    errors.append(f"{label}: 'term_months' must be <= 600 (got {term})")
                    term = None

        fixed = _finite_float(
            raw.get("fee_upfront_fixed") if raw.get("fee_upfront_fixed") not in (None, "") else 0.0,
            "fee_upfront_fixed", label, errors, minimum=0.0,
        )
        pct = _finite_float(
            raw.get("fee_upfront_pct") if raw.get("fee_upfront_pct") not in (None, "") else 0.0,
            "fee_upfront_pct", label, errors, minimum=0.0, maximum=0.5,
        )
        monthly = _finite_float(
            raw.get("fee_monthly") if raw.get("fee_monthly") not in (None, "") else 0.0,
            "fee_monthly", label, errors, minimum=0.0,
        )
        rtype = (raw.get("repayment_type") or "").strip()
        if rtype not in REPAYMENT_TYPES:
            errors.append(
                f"{label}: 'repayment_type' must be one of {', '.join(REPAYMENT_TYPES)} (got {rtype!r})"
            )
        lender = (raw.get("lender") or "").strip() or "(unnamed)"

        if None not in (principal, rate, term, fixed, pct, monthly) and rtype in REPAYMENT_TYPES:
            offers.append({
                "offer_id": oid,
                "lender": lender,
                "principal": principal,
                "annual_nominal_rate": rate,
                "term_months": term,
                "fee_upfront_fixed": fixed,
                "fee_upfront_pct": pct,
                "fee_monthly": monthly,
                "repayment_type": rtype,
            })

    checks["validation_errors"] = errors
    if errors:
        raise InputError(
            "Input validation failed; nothing was calculated. Fix the following:\n  - "
            + "\n  - ".join(errors)
        )
    return offers, checks


def load_config(path: Path | None, args) -> dict:
    """Read borrower settings, then apply explicit CLI overrides."""
    cfg = {
        "case_id": "unnamed_case",
        "currency": "HKD",
        "monthly_budget_cap": None,
        "monthly_income": None,
        "max_payment_to_income": 0.35,
        "periods_per_year": PERIODS_PER_YEAR,
        "data_note": "Synthetic teaching data; see data/source_notes.md.",
    }
    if path is not None:
        if not path.is_file():
            raise InputError(f"config file not found: {path}")
        with path.open("r", encoding="utf-8-sig") as fh:
            user = json.load(fh)
        if not isinstance(user, dict):
            raise InputError("config JSON must be an object")
        cfg.update(user)

    for key, cli_value in (
        ("case_id", args.case_id),
        ("currency", args.currency),
        ("monthly_budget_cap", args.budget_cap),
        ("monthly_income", args.monthly_income),
        ("max_payment_to_income", args.max_dti),
    ):
        if cli_value is not None:
            cfg[key] = cli_value

    errors = []
    for key in ("monthly_budget_cap", "monthly_income"):
        value = cfg.get(key)
        if value is None or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            errors.append(f"config '{key}' must be a positive finite number (got {value!r})")
    dti = cfg.get("max_payment_to_income")
    if not isinstance(dti, (int, float)) or not math.isfinite(dti) or not (0 < dti <= 1):
        errors.append(f"config 'max_payment_to_income' must be in (0, 1] (got {dti!r})")
    if int(cfg.get("periods_per_year", PERIODS_PER_YEAR)) != PERIODS_PER_YEAR:
        errors.append(
            f"config 'periods_per_year' must be {PERIODS_PER_YEAR}; "
            "this engine supports monthly instalments only"
        )
    cur = str(cfg.get("currency", "")).strip()
    if not (1 <= len(cur) <= 6):
        errors.append(f"config 'currency' looks wrong (got {cur!r})")
    if errors:
        raise InputError("Config validation failed; nothing was calculated:\n  - " + "\n  - ".join(errors))
    cfg["currency"] = cur
    cfg["periods_per_year"] = PERIODS_PER_YEAR
    return cfg


# --------------------------------------------------------------------------- #
# Financial mathematics
# --------------------------------------------------------------------------- #

def annuity_payment(principal: float, periodic_rate: float, n: int) -> float:
    """Level instalment (principal + interest) for an ordinary annuity."""
    if periodic_rate == 0.0:
        return principal / n
    return principal * periodic_rate / (1.0 - (1.0 + periodic_rate) ** (-n))


def build_schedule(offer: dict) -> list[dict]:
    """Exact month-by-month amortisation schedule. No rounding is applied internally."""
    principal = offer["principal"]
    n = offer["term_months"]
    i = offer["annual_nominal_rate"] / PERIODS_PER_YEAR
    fee_monthly = offer["fee_monthly"]
    rtype = offer["repayment_type"]
    level = annuity_payment(principal, i, n) if rtype == "annuity" else None

    balance = principal
    rows = []
    cumulative_interest = 0.0
    for t in range(1, n + 1):
        opening = balance
        interest = opening * i
        if t == n:
            # Final instalment clears the remaining balance exactly (no residual dust).
            principal_part = opening
            total_due = opening + interest
        elif rtype == "annuity":
            principal_part = level - interest
            total_due = level
        else:  # equal_principal: constant principal, declining total payment
            principal_part = principal / n
            total_due = principal_part + interest
        closing = opening - principal_part
        outflow = total_due + fee_monthly
        cumulative_interest += interest
        rows.append({
            "period": t,
            "opening_balance": opening,
            "interest": interest,
            "principal": principal_part,
            "monthly_fee": fee_monthly,
            "total_outflow": outflow,
            "closing_balance": closing,
            "cumulative_interest": cumulative_interest,
        })
        balance = closing
    return rows


def npv(periodic_rate: float, net_received: float, outflows: list[float]) -> float:
    """NPV of the borrower's cash flows at a candidate monthly discount rate."""
    if periodic_rate <= -1.0:
        return float("inf")
    discount = 1.0 + periodic_rate
    value = net_received
    for t, outflow in enumerate(outflows, start=1):
        value -= outflow / discount ** t
    return value


def irr_bisection(net_received: float, outflows: list[float], tol: float = 1e-13) -> float:
    """Monthly IRR by bisection. Different algorithm from verify.py's Newton solver."""
    if net_received <= 0:
        raise InputError("net disbursement (principal less upfront fees) must be positive")
    if abs(npv(0.0, net_received, outflows)) < tol * max(1.0, net_received):
        return 0.0  # zero-interest, zero-fee loan
    lo, hi = 0.0, 0.5
    for _ in range(200):
        if npv(hi, net_received, outflows) >= 0.0:
            break
        hi *= 2.0
        if hi > 1e6:
            raise InputError("could not bracket the IRR; check the cash flows")
    else:
        raise InputError("could not bracket the IRR; check the cash flows")
    for _ in range(300):
        mid = (lo + hi) / 2.0
        if npv(mid, net_received, outflows) > 0.0:
            hi = mid
        else:
            lo = mid
        if hi - lo < tol:
            break
    return (lo + hi) / 2.0


def peak_outflow_for(trial_principal: float, offer: dict) -> float:
    """Peak monthly outflow for a trial principal (used by the affordability solver)."""
    probe = dict(offer)
    probe["principal"] = trial_principal
    return max(row["total_outflow"] for row in build_schedule(probe))


def max_affordable_principal(offer: dict, ceiling: float) -> float:
    """Largest principal whose peak instalment fits the monthly ceiling (bisection)."""
    if peak_outflow_for(0.0, offer) > ceiling:
        return 0.0  # fixed monthly fees alone break the budget
    lo = 0.0
    hi = max(offer["principal"] * 2.0, 1.0)
    for _ in range(100):
        if peak_outflow_for(hi, offer) > ceiling:
            break
        hi *= 2.0
        if hi > offer["principal"] * 1e6:
            return float("inf")
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if peak_outflow_for(mid, offer) > ceiling:
            hi = mid
        else:
            lo = mid
        if hi - lo < 1e-7:
            break
    return lo


def offer_checks(offer: dict, rows: list[dict], metrics: dict, tol: float) -> dict:
    """Internal cash-flow identities. The independent checker is verify.py."""
    i = offer["annual_nominal_rate"] / PERIODS_PER_YEAR
    p = offer["principal"]
    err_interest = max(abs(r["interest"] - r["opening_balance"] * i) for r in rows)
    err_balance = max(abs(r["opening_balance"] - r["principal"] - r["closing_balance"]) for r in rows)
    sum_principal = sum(r["principal"] for r in rows)
    sum_outflow = sum(r["total_outflow"] for r in rows)
    sum_interest = sum(r["interest"] for r in rows)
    net = metrics["net_disbursement"]
    outflows = [r["total_outflow"] for r in rows]
    residual = npv(metrics["irr_monthly"], net, outflows)
    return {
        "interest_equals_opening_times_rate": {
            "max_abs_error": err_interest, "tolerance": tol, "pass": err_interest <= tol,
        },
        "balance_roll_forward": {
            "max_abs_error": err_balance, "tolerance": tol, "pass": err_balance <= tol,
        },
        "principal_repaid_equals_principal": {
            "difference": sum_principal - p, "tolerance": tol,
            "pass": abs(sum_principal - p) <= tol,
        },
        "final_balance_zero": {
            "value": rows[-1]["closing_balance"], "tolerance": tol,
            "pass": abs(rows[-1]["closing_balance"]) <= tol,
        },
        "payments_equal_interest_plus_principal_plus_fees": {
            "difference": sum_outflow - (sum_interest + p + offer["fee_monthly"] * len(rows)),
            "tolerance": tol,
            "pass": abs(sum_outflow - (sum_interest + p + offer["fee_monthly"] * len(rows))) <= tol,
        },
        "all_in_cost_equals_interest_plus_fees": {
            "difference": metrics["total_cost"] - (metrics["total_interest"] + metrics["total_fees"]),
            "tolerance": tol,
            "pass": abs(metrics["total_cost"] - (metrics["total_interest"] + metrics["total_fees"])) <= tol,
        },
        "npv_at_irr_is_zero": {
            "residual": residual, "tolerance": tol, "pass": abs(residual) <= tol,
        },
    }


def summarize(offer: dict, cfg: dict, tol: float) -> dict:
    """Compute every reported metric and the internal identities for one offer."""
    rows = build_schedule(offer)
    n = len(rows)
    upfront = offer["fee_upfront_fixed"] + offer["fee_upfront_pct"] * offer["principal"]
    net = offer["principal"] - upfront
    if net <= 0:
        raise InputError(f"{offer['offer_id']}: upfront fees exceed the principal")
    outflows = [r["total_outflow"] for r in rows]
    total_interest = sum(r["interest"] for r in rows)
    total_fees = upfront + offer["fee_monthly"] * n
    total_outflow = sum(outflows)
    total_cost = total_outflow - net
    irr = irr_bisection(net, outflows, tol=1e-13)
    peak = max(outflows)
    ceiling = min(cfg["monthly_budget_cap"], cfg["monthly_income"] * cfg["max_payment_to_income"])
    pti = peak / cfg["monthly_income"]
    budget_ok = peak <= cfg["monthly_budget_cap"] + tol
    dti_ok = pti <= cfg["max_payment_to_income"] + tol

    metrics = {
        "offer_id": offer["offer_id"],
        "lender": offer["lender"],
        "repayment_type": offer["repayment_type"],
        "principal": offer["principal"],
        "annual_nominal_rate": offer["annual_nominal_rate"],
        "term_months": n,
        "fee_upfront_fixed": offer["fee_upfront_fixed"],
        "fee_upfront_pct": offer["fee_upfront_pct"],
        "fee_monthly": offer["fee_monthly"],
        "upfront_fee_total": upfront,
        "net_disbursement": net,
        "periodic_rate": offer["annual_nominal_rate"] / PERIODS_PER_YEAR,
        "level_instalment_ex_fees": annuity_payment(
            offer["principal"], offer["annual_nominal_rate"] / PERIODS_PER_YEAR, n
        ) if offer["repayment_type"] == "annuity" else None,
        "first_instalment": outflows[0],
        "peak_monthly_outflow": peak,
        "final_monthly_outflow": outflows[-1],
        "total_outflow": total_outflow,
        "total_interest": total_interest,
        "total_fees": total_fees,
        "total_cost": total_cost,
        "irr_monthly": irr,
        "effective_apr": irr * PERIODS_PER_YEAR,
        "effective_ear": (1.0 + irr) ** PERIODS_PER_YEAR - 1.0,
        "npv_at_irr": npv(irr, net, outflows),
        "affordability_ceiling": ceiling,
        "payment_to_income": pti,
        "affordable_by_budget": budget_ok,
        "affordable_by_dti": dti_ok,
        "affordable": budget_ok and dti_ok,
        "headroom_vs_ceiling": ceiling - peak,
        "max_affordable_principal": max_affordable_principal(offer, ceiling),
        "schedule_file": f"schedules/{safe_id(offer['offer_id'])}.csv",
        "schedule": rows,
    }
    metrics["checks"] = offer_checks(offer, rows, metrics, tol)
    return metrics


def safe_id(value: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in str(value))


# --------------------------------------------------------------------------- #
# Output writers (all plain-text / SVG, no third-party libraries)
# --------------------------------------------------------------------------- #

SCHEDULE_FIELDS = (
    "period", "opening_balance", "interest", "principal", "monthly_fee",
    "total_outflow", "closing_balance", "cumulative_interest",
)


def write_schedule(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(SCHEDULE_FIELDS)
        for r in rows:
            writer.writerow(
                [str(r["period"])] + [f"{r[k]:.10f}" for k in SCHEDULE_FIELDS[1:]]
            )


def money(value: float, currency: str) -> str:
    return f"{currency} {value:,.2f}"


def pct(value: float) -> str:
    return f"{value * 100:.3f}%"


def write_comparison(path: Path, results: list[dict], cfg: dict, ranking: dict, baseline: dict) -> None:
    cur = cfg["currency"]
    lines = [
        f"# Loan Offer Compass - comparison ({cfg['case_id']})",
        "",
        f"Currency: **{cur}**. Monthly instalments; nominal annual rates are quoted as "
        "`rate / 12` per month. Generated by `loan_compare.py` "
        f"v{ENGINE_VERSION} at {datetime.now(timezone.utc).isoformat(timespec='seconds')}.",
        "",
        "## How to read this table",
        "",
        "- **Peak monthly outflow** includes interest, principal and any monthly fee. For "
        "`equal_principal` offers the outflow declines over time, so the peak (first month) "
        "is the binding affordability number.",
        "- **All-in cost** = total interest + upfront fee + all monthly fees. It is a nominal "
        "HKD amount and is *not* adjusted for the timing of cash flows.",
        "- **Effective APR / EAR** come from the IRR of the borrower's actual cash flows "
        "(net disbursement at t=0, instalments at t=1..n). They are the only figures here "
        "that put fees, rates and terms on one comparable footing.",
        "- **Affordable** means the peak instalment fits both the monthly budget cap and the "
        "payment-to-income ceiling.",
        "",
        "## Comparison",
        "",
        "| Offer | Lender | Plan | Nominal p.a. | Term (m) | Peak monthly | Upfront fee | "
        "Total interest | Total fees | All-in cost | Effective APR | EAR | Affordable |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for r in results:
        lines.append(
            f"| {r['offer_id']} | {r['lender']} | {r['repayment_type']} | "
            f"{pct(r['annual_nominal_rate'])} | {r['term_months']} | "
            f"{money(r['peak_monthly_outflow'], cur)} | {money(r['upfront_fee_total'], cur)} | "
            f"{money(r['total_interest'], cur)} | {money(r['total_fees'], cur)} | "
            f"{money(r['total_cost'], cur)} | {pct(r['effective_apr'])} | "
            f"{pct(r['effective_ear'])} | {'YES' if r['affordable'] else 'NO'} |"
        )
    lines += [
        "",
        "## Affordability detail",
        "",
        f"Monthly budget cap: {money(cfg['monthly_budget_cap'], cur)}; "
        f"monthly income: {money(cfg['monthly_income'], cur)}; "
        f"payment-to-income ceiling: {pct(cfg['max_payment_to_income'])}; "
        f"binding ceiling: {money(min(cfg['monthly_budget_cap'], cfg['monthly_income'] * cfg['max_payment_to_income']), cur)}.",
        "",
        "| Offer | Peak monthly | Headroom vs ceiling | Payment / income | Max affordable principal |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in results:
        lines.append(
            f"| {r['offer_id']} | {money(r['peak_monthly_outflow'], cur)} | "
            f"{money(r['headroom_vs_ceiling'], cur)} | {pct(r['payment_to_income'])} | "
            f"{money(r['max_affordable_principal'], cur)} |"
        )
    lines += [
        "",
        "## Ranking and the naive shortcut",
        "",
        f"- By all-in cost (affordable offers only): {', '.join(ranking['by_total_cost_affordable']) or '(none affordable)'}.",
        f"- By all-in cost (all offers): {', '.join(ranking['by_total_cost_all'])}.",
        f"- By effective APR (all offers): {', '.join(ranking['by_effective_apr'])}.",
        f"- Naive baseline - pick the lowest headline nominal rate: **{baseline['naive_pick']}**.",
        f"- Lowest effective APR: **{baseline['all_in_pick']}**. "
        + ("**They disagree** - the headline-rate shortcut is misleading here."
           if baseline["disagree"] else "They agree on this case."),
        "",
        "## Limitations",
        "",
        "Monthly instalments only; no compounding within a month, no early repayment, no "
        "variable rates, no default risk, no tax effects and no time value applied to the "
        "nominal all-in-cost figure. Fees are assumed to be withheld from the disbursement. "
        "Offers are synthetic teaching data, not real quotes. See `SKILL.md` and "
        "`data/source_notes.md`.",
        "",
        "## Files in this run",
        "",
        "- `summary.json` - all metrics and internal identity checks, machine readable.",
        "- `schedules/*.csv` - full month-by-month amortisation for each offer.",
        "- `balance_paths.svg`, `cost_breakdown.svg` - charts generated from the schedules.",
        "- `run_log.txt` - input checks, command and environment of this run.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _svg_header(w: int, h: int, title: str, subtitle: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="Segoe UI, Arial, sans-serif">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="30" y="34" font-size="19" font-weight="600" fill="#111827">{html.escape(title)}</text>',
        f'<text x="30" y="55" font-size="12" fill="#6b7280">{html.escape(subtitle)}</text>',
    ]


def write_balance_chart(path: Path, results: list[dict], cfg: dict) -> None:
    w, h = 940, 500
    left, right, top, bottom = 95, 30, 85, 70
    pw, ph = w - left - right, h - top - bottom
    out = _svg_header(
        w, h, "Remaining balance by month",
        f"{cfg['case_id']} - {cfg['currency']} - one curve per offer, from the generated schedules",
    )
    max_bal = max([r["principal"] for r in results] + [1.0])
    max_n = max(r["term_months"] for r in results)
    def X(t): return left + pw * (t / max_n)
    def Y(v): return top + ph * (1.0 - v / (max_bal * 1.05))
    for k in range(6):
        v = max_bal * 1.05 * k / 5
        y = Y(v)
        out.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left+pw}" y2="{y:.2f}" stroke="#e5e7eb" stroke-width="1"/>')
        out.append(f'<text x="{left-10}" y="{y+4:.2f}" font-size="11" fill="#6b7280" text-anchor="end">{v:,.0f}</text>')
    out.append(f'<line x1="{left}" y1="{top+ph}" x2="{left+pw}" y2="{top+ph}" stroke="#9ca3af" stroke-width="1"/>')
    for k in range(0, max_n + 1, max(1, max_n // 6)):
        x = X(k)
        out.append(f'<text x="{x:.2f}" y="{top+ph+20}" font-size="11" fill="#6b7280" text-anchor="middle">{k}</text>')
    out.append(f'<text x="{left+pw/2:.2f}" y="{h-14}" font-size="12" fill="#374151" text-anchor="middle">Month</text>')
    out.append(f'<text x="18" y="{top+ph/2:.2f}" font-size="12" fill="#374151" transform="rotate(-90 18 {top+ph/2:.2f})" text-anchor="middle">Balance ({cfg["currency"]})</text>')
    for idx, r in enumerate(results):
        color = PALETTE[idx % len(PALETTE)]
        pts = [f"{X(0):.2f},{Y(r['principal']):.2f}"]
        pts += [f"{X(row['period']):.2f},{Y(row['closing_balance']):.2f}" for row in r["schedule"]]
        out.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="2.4" stroke-linejoin="round"/>')
        ly = top + 6 + idx * 20
        out.append(f'<line x1="{left+pw-190}" y1="{ly}" x2="{left+pw-168}" y2="{ly}" stroke="{color}" stroke-width="3"/>')
        out.append(f'<text x="{left+pw-160}" y="{ly+4}" font-size="11" fill="#374151">{html.escape(r["offer_id"])}</text>')
    out.append("</svg>")
    path.write_text("\n".join(out), encoding="utf-8")


def write_cost_chart(path: Path, results: list[dict], cfg: dict) -> None:
    w = 940
    row_h, top, bottom = 54, 90, 55
    h = top + row_h * len(results) + bottom
    left, right = 210, 150
    pw = w - left - right
    out = _svg_header(
        w, h, "All-in cost breakdown",
        f"{cfg['case_id']} - {cfg['currency']} - interest + upfront fee + monthly fees (principal excluded)",
    )
    max_cost = max(r["total_cost"] for r in results) or 1.0
    scale = pw / (max_cost * 1.18)
    for k in range(5):
        v = max_cost * 1.18 * k / 4
        x = left + scale * v
        out.append(f'<line x1="{x:.2f}" y1="{top-14}" x2="{x:.2f}" y2="{top+row_h*len(results)}" stroke="#e5e7eb" stroke-width="1"/>')
        out.append(f'<text x="{x:.2f}" y="{top-22}" font-size="10" fill="#6b7280" text-anchor="middle">{v:,.0f}</text>')
    segments = (
        ("total_interest", "#2563eb", "Interest"),
        ("upfront_fee_total", "#d97706", "Upfront fee"),
        ("fee_monthly_total", "#dc2626", "Monthly fees"),
    )
    lx = left
    for key, color, label in segments:
        out.append(f'<rect x="{lx}" y="{top-52}" width="12" height="12" rx="2" fill="{color}"/>')
        out.append(f'<text x="{lx+17}" y="{top-42}" font-size="11" fill="#374151">{label}</text>')
        lx += 145
    for idx, r in enumerate(results):
        y = top + idx * row_h + 10
        out.append(f'<text x="{left-14}" y="{y+20}" font-size="12" fill="#111827" text-anchor="end">{html.escape(r["offer_id"])}</text>')
        x = left
        values = {
            "total_interest": r["total_interest"],
            "upfront_fee_total": r["upfront_fee_total"],
            "fee_monthly_total": r["fee_monthly"] * r["term_months"],
        }
        for key, color, _ in segments:
            bw = values[key] * scale
            if bw > 0:
                out.append(f'<rect x="{x:.2f}" y="{y}" width="{bw:.2f}" height="26" fill="{color}"/>')
            x += bw
        out.append(f'<text x="{x+8:.2f}" y="{y+18}" font-size="12" font-weight="600" fill="#111827">{r["total_cost"]:,.0f}</text>')
        if not r["affordable"]:
            out.append(f'<text x="{w-16}" y="{y+18}" font-size="10" fill="#b91c1c" text-anchor="end">OVER CAP</text>')
    out.append(f'<text x="{left+pw/2:.2f}" y="{h-16}" font-size="12" fill="#374151" text-anchor="middle">All-in cost ({cfg["currency"]}, nominal)</text>')
    out.append("</svg>")
    path.write_text("\n".join(out), encoding="utf-8")


def write_run_log(path: Path, argv, offers_path, config_path, checks, cfg, results, out_dir) -> None:
    lines = [
        "Loan Offer Compass - run log",
        "============================",
        f"UTC timestamp      : {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"Engine version     : {ENGINE_VERSION}",
        f"Python             : {sys.version.split()[0]} ({sys.platform})",
        f"Command            : {' '.join(str(a) for a in argv)}",
        f"Offers file        : {display_path(offers_path)}",
        f"Config file        : {display_path(config_path) if config_path else '(CLI defaults/overrides)'}",
        f"Output folder      : {display_path(out_dir)}",
        "",
        "Input checks",
        "------------",
        f"Rows read                : {checks['row_count']}",
        f"Columns                  : {', '.join(checks['columns_found'])}",
        f"Missing values           : {checks['missing_values']} (optional fee blanks default to 0)",
        f"Duplicate offer ids      : {checks['duplicate_offer_ids'] or 'none'}",
        f"Unknown columns ignored  : {checks['unknown_columns_ignored'] or 'none'}",
        f"Validation errors        : {checks['validation_errors'] or 'none'}",
        f"Currency                 : {cfg['currency']}",
        f"Periods per year         : {cfg['periods_per_year']} (monthly instalments)",
        f"Monthly budget cap       : {cfg['monthly_budget_cap']:.2f}",
        f"Monthly income           : {cfg['monthly_income']:.2f}",
        f"Max payment/income       : {cfg['max_payment_to_income']:.4f}",
        "",
        "Per-offer internal identity checks",
        "-----------------------------------",
    ]
    for r in results:
        failed = [k for k, v in r["checks"].items() if not v["pass"]]
        lines.append(f"{r['offer_id']}: {len(r['checks']) - len(failed)}/{len(r['checks'])} passed"
                     + (f"  FAILED: {', '.join(failed)}" if failed else ""))
    lines += [
        "",
        "Note: these are the engine's own self-checks. Independent verification is in verify.py",
        "and its output verification.md / evidence/E2_verification.txt.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Compare loan offers on an all-in cash-flow basis (pure stdlib).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--offers", required=True, type=Path, help="CSV of loan offers")
    p.add_argument("--config", type=Path, default=None, help="JSON borrower settings")
    p.add_argument("--out", required=True, type=Path, help="output folder (created if absent)")
    p.add_argument("--case-id", default=None, help="override config case_id")
    p.add_argument("--currency", default=None, help="override config currency label")
    p.add_argument("--budget-cap", type=float, default=None, help="override monthly budget cap")
    p.add_argument("--monthly-income", type=float, default=None, help="override monthly income")
    p.add_argument("--max-dti", type=float, default=None, help="override payment-to-income ceiling")
    p.add_argument("--tol", type=float, default=1e-6, help="absolute tolerance for identity checks")
    p.add_argument("--no-charts", action="store_true", help="skip SVG charts")
    return p


def run(args, argv=None) -> dict:
    """Execute one comparison. Returns the summary dict (also written to disk)."""
    offers, checks = load_offers(args.offers)
    cfg = load_config(args.config, args)
    out_dir = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    results = [summarize(o, cfg, args.tol) for o in offers]
    affordable = [r["offer_id"] for r in results if r["affordable"]]
    ranking = {
        "by_total_cost_all": [r["offer_id"] for r in sorted(results, key=lambda r: r["total_cost"])],
        "by_total_cost_affordable": [
            r["offer_id"] for r in sorted(
                (r for r in results if r["affordable"]), key=lambda r: r["total_cost"]
            )
        ],
        "by_effective_apr": [r["offer_id"] for r in sorted(results, key=lambda r: r["effective_apr"])],
        "affordable_offers": affordable,
    }
    naive_pick = min(results, key=lambda r: (r["annual_nominal_rate"], r["offer_id"]))["offer_id"]
    all_in_pick = ranking["by_effective_apr"][0]
    baseline = {
        "description": "Naive shortcut: pick the offer with the lowest headline nominal rate.",
        "naive_pick": naive_pick,
        "all_in_pick": all_in_pick,
        "disagree": naive_pick != all_in_pick,
    }

    public = []
    for r in results:
        item = {k: v for k, v in r.items() if k != "schedule"}
        public.append(item)
        write_schedule(out_dir / r["schedule_file"], r["schedule"])

    summary = {
        "engine": "loan-offer-comparison",
        "engine_version": ENGINE_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python_version": sys.version.split()[0],
        "case": cfg,
        "cash_flow_convention": (
            "t=0: +(principal - upfront fees); t=1..n: -(interest + principal + monthly fee); "
            "APR = 12 * monthly IRR; EAR = (1 + monthly IRR)^12 - 1; "
            "all-in cost = sum(outflows) - net disbursement"
        ),
        "input_checks": checks,
        "offers": public,
        "ranking": ranking,
        "naive_baseline": baseline,
        "tolerance": args.tol,
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8"
    )
    write_comparison(out_dir / "comparison.md", results, cfg, ranking, baseline)
    if not args.no_charts:
        write_balance_chart(out_dir / "balance_paths.svg", results, cfg)
        write_cost_chart(out_dir / "cost_breakdown.svg", results, cfg)
    write_run_log(
        out_dir / "run_log.txt", argv or sys.argv, args.offers, args.config,
        checks, cfg, results, out_dir,
    )
    return summary


def main(argv=None) -> int:
    argv = list(sys.argv if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv[1:])
    try:
        summary = run(args, argv)
    except InputError as exc:
        print(f"INPUT ERROR: {exc}", file=sys.stderr)
        return 3
    except (OSError, json.JSONDecodeError) as exc:
        print(f"IO/JSON ERROR: {exc}", file=sys.stderr)
        return 4

    cur = summary["case"]["currency"]
    print(f"Loan Offer Compass v{ENGINE_VERSION} | case: {summary['case']['case_id']} | currency: {cur}")
    print(f"Input checks: {summary['input_checks']['row_count']} offers, "
          f"{len(summary['input_checks']['validation_errors'])} validation errors, "
          f"{len(summary['input_checks']['duplicate_offer_ids'])} duplicate ids")
    print(f"Binding monthly ceiling: {summary['offers'][0]['affordability_ceiling']:,.2f} {cur}")
    print()
    print(f"{'offer':<14}{'peak/m':>12}{'all-in cost':>16}{'APR':>10}{'EAR':>10}  affordable  checks")
    for r in summary["offers"]:
        n_pass = sum(1 for c in r["checks"].values() if c["pass"])
        print(f"{r['offer_id']:<14}{r['peak_monthly_outflow']:>12,.2f}{r['total_cost']:>16,.2f}"
              f"{r['effective_apr']*100:>9.3f}%{r['effective_ear']*100:>9.3f}%  "
              f"{'YES' if r['affordable'] else 'NO ':<11} {n_pass}/{len(r['checks'])}")
    print()
    print(f"Naive lowest-rate pick : {summary['naive_baseline']['naive_pick']}")
    print(f"Lowest effective APR   : {summary['naive_baseline']['all_in_pick']}"
          + ("  -> DISAGREE (headline rates mislead)" if summary["naive_baseline"]["disagree"] else "  -> agree"))
    print(f"Ranking by all-in cost (affordable only): "
          f"{', '.join(summary['ranking']['by_total_cost_affordable']) or '(none affordable)'}")
    print()
    print(f"Outputs -> {display_path(args.out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
