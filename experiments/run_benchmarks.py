# -*- coding: utf-8 -*-
"""Reproducible benchmark comparing iterative methods on standard test functions.

The script executes a small benchmark suite for the Newton, Secant and the
fourth‑order *M4* method defined in :pymod:`iterative_methods`.  Results are
written to ``results/benchmark_results.{csv,json}`` and a convergence plot for
the ``poly5`` test case is saved under ``figures/``.

The implementation has been modernised for Python 3.10+:

*   Explicit type hints throughout the module.
*   Small helper dataclasses to make the test‑case definition self‑documenting.
*   A private ``_run_benchmark`` function that returns the collected rows – this
    makes the core logic testable without performing any I/O.
*   Cleaner imports and removal of the ``sys.path`` hack (the repository layout
    already places ``src`` on the import path when the package is installed).
*   Robust error handling for optional ``matplotlib`` usage.
*   Detailed docstrings and comments.
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

# The repository's ``src`` directory is added to ``PYTHONPATH`` during normal
# development and installation.  Importing directly keeps the module importable
# without mutating ``sys.path`` at runtime.
from iterative_methods import estimate_order, m4, newton, secant

# ---------------------------------------------------------------------------
# Constants & paths
# ---------------------------------------------------------------------------
OUT_DIR: Path = Path(__file__).resolve().parents[1] / "results"
OUT_DIR.mkdir(exist_ok=True)
FIG_DIR: Path = Path(__file__).resolve().parents[1] / "figures"
FIG_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Test‑case definition
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    """Container for a single benchmark problem.

    Attributes
    ----------
    name: Human readable identifier.
    f: Callable[[float], float] – the function whose root is sought.
    df: Callable[[float], float] – derivative of ``f`` (required for Newton/M4).
    x0: Initial guess for Newton/M4.
    sx0: First starting point for the Secant method.
    sx1: Second starting point for the Secant method.
    """

    name: str
    f: Callable[[float], float]
    df: Callable[[float], float]
    x0: float
    sx0: float
    sx1: float

# The benchmark suite – kept identical to the original behaviour.
TESTS: List[BenchmarkCase] = [
    BenchmarkCase(
        name="poly2",
        f=lambda x: x * x - 2.0,
        df=lambda x: 2.0 * x,
        x0=1.5,
        sx0=2.0,
        sx1=1.0,
    ),
    BenchmarkCase(
        name="exp",
        f=lambda x: math.exp(x) - 2.0,
        df=lambda x: math.exp(x),
        x0=1.0,
        sx0=2.0,
        sx1=1.0,
    ),
    BenchmarkCase(
        name="cos",
        f=lambda x: math.cos(x) - x,
        df=lambda x: -math.sin(x) - 1.0,
        x0=0.5,
        sx0=1.5,
        sx1=0.5,
    ),
    BenchmarkCase(
        name="poly5",
        f=lambda x: x ** 5 - x - 0.1,
        df=lambda x: 5 * x ** 4 - 1,
        x0=0.9,
        sx0=1.5,
        sx1=0.5,
    ),
]

# ---------------------------------------------------------------------------
# Core benchmark logic
# ---------------------------------------------------------------------------
def _run_benchmark() -> List[Dict[str, Any]]:
    """Execute the benchmark suite and return a list of result dictionaries.

    The function mirrors the original script's behaviour but isolates the data
    collection from file‑system side effects, making it straightforward to unit
    test.
    """
    rows: List[Dict[str, Any]] = []
    for case in TESTS:
        # Reference root obtained with the high‑order M4 method.
        ref = m4(case.f, case.df, case.x0, root=None, tol=1e-15, maxit=50)
        root: float = ref["root"]

        # Run each algorithm with the same tolerance/iteration limits.
        for method_name, result in [
            ("Newton", newton(case.f, case.df, case.x0, root=root, tol=1e-15, maxit=50)),
            ("M4", m4(case.f, case.df, case.x0, root=root, tol=1e-15, maxit=50)),
            (
                "Secant",
                secant(case.f, case.sx0, case.sx1, root=root, tol=1e-15, maxit=50),
            ),
        ]:
            rows.append(
                {
                    "function": case.name,
                    "method": method_name,
                    "root": result["root"],
                    "reference_root": root,
                    "iterations": result["iterations"],
                    "converged": result["converged"],
                    "final_error": abs(result["root"] - root),
                    "estimated_order": estimate_order(result["errors"]),
                }
            )
    return rows


def _write_results(rows: List[Dict[str, Any]]) -> None:
    """Persist benchmark data to CSV and JSON files.

    Parameters
    ----------
    rows:
        The list produced by :func:`_run_benchmark`.
    """
    if not rows:
        raise RuntimeError("No benchmark rows to write – the suite produced no data.")

    csv_path = OUT_DIR / "benchmark_results.csv"
    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path = OUT_DIR / "benchmark_results.json"
    json_path.write_text(json.dumps(rows, indent=2, default=str))

    print("Wrote", csv_path)


def _plot_convergence() -> None:
    """Generate a convergence plot for the ``poly5`` test case.

    The function is deliberately defensive – any import or runtime error is
    caught and reported without aborting the whole benchmark run.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")  # Ensure a non‑interactive backend.
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover – optional dependency.
        print("figure error: matplotlib not available or failed to initialise –", exc)
        return

    # Re‑use the same problem definition as in ``TESTS``.
    f = lambda x: x ** 5 - x - 0.1
    df = lambda x: 5 * x ** 4 - 1
    ref = m4(f, df, 0.9, root=None, tol=1e-15, maxit=50)
    root = ref["root"]

    r_newton = newton(f, df, 0.9, root=root, tol=1e-15, maxit=50)
    r_m4 = m4(f, df, 0.9, root=root, tol=1e-15, maxit=50)
    r_secant = secant(f, 0.5, 1.5, root=root, tol=1e-15, maxit=50)

    plt.figure(figsize=(7, 4.5))
    for label, result, marker in [
        ("Newton", r_newton, "o"),
        ("M4 (proposed)", r_m4, "s"),
        ("Secant", r_secant, "^"),
    ]:
        # ``errors`` may contain non‑positive entries (e.g., when the method
        # converged in fewer iterations).  Filter them out for a clean log‑plot.
        errors = [e for e in result["errors"] if e > 0]
        plt.semilogy(range(1, len(errors) + 1), errors, marker + "-", label=label)

    plt.xlabel("Iteration")
    plt.ylabel("Absolute error")
    plt.title("Convergence on $x^5 - x - 0.1 = 0$")
    plt.grid(True, which="both", linestyle=":")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "convergence_poly5.png", dpi=150)
    plt.close()


def run() -> None:
    """Entry‑point used by the ``__main__`` guard.

    The function orchestrates the benchmark execution, result persistence and
    optional plotting while preserving the original script's console output.
    """
    rows = _run_benchmark()
    _write_results(rows)
    _plot_convergence()

    # Echo a concise summary to stdout – identical to the original script.
    for row in rows:
        print(
            row["function"],
            row["method"],
            "iters=",
            row["iterations"],
            "order=",
            row["estimated_order"],
        )


if __name__ == "__main__":
    run()
