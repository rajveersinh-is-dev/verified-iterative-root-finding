"""Reproducible benchmark comparing iterative methods on standard test functions."""

import csv
import json
import math
import mpmath
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from iterative_methods import newton, secant, m4, estimate_order

mpmath.mp.dps = 100

OUT = Path(__file__).resolve().parents[1] / "results"
OUT.mkdir(exist_ok=True)
FIG = Path(__file__).resolve().parents[1] / "figures"
FIG.mkdir(exist_ok=True)

TESTS = [
    ("poly2", lambda x: x * x - mpmath.mpf('2.0'), lambda x: mpmath.mpf('2.0') * x, mpmath.mpf('1.5'), mpmath.mpf('2.0'), mpmath.mpf('1.0')),
    ("exp", lambda x: mpmath.exp(x) - mpmath.mpf('2.0'), lambda x: mpmath.exp(x), mpmath.mpf('1.0'), mpmath.mpf('2.0'), mpmath.mpf('1.0')),
    ("cos", lambda x: mpmath.cos(x) - x, lambda x: -mpmath.sin(x) - mpmath.mpf('1.0'), mpmath.mpf('0.5'), mpmath.mpf('1.5'), mpmath.mpf('0.5')),
    ("poly5", lambda x: x ** 5 - x - mpmath.mpf('0.1'), lambda x: mpmath.mpf('5.0') * x ** 4 - mpmath.mpf('1.0'), mpmath.mpf('0.9'), mpmath.mpf('1.5'), mpmath.mpf('0.5')),
]


def run():
    rows = []
    for name, f, df, x0, sx0, sx1 in TESTS:
        # Find reference root for each method individually, since they might converge to different roots (e.g. poly5 secant)
        ref_n = newton(f, df, x0, root=None, tol=1e-80, maxit=50)
        root_n = ref_n["root"]
        res_n = newton(f, df, x0, root=root_n, tol=1e-80, maxit=50)

        ref_m = m4(f, df, x0, root=None, tol=1e-80, maxit=50)
        root_m = ref_m["root"]
        res_m = m4(f, df, x0, root=root_m, tol=1e-80, maxit=50)

        ref_s = secant(f, sx0, sx1, root=None, tol=1e-80, maxit=50)
        root_s = ref_s["root"]
        res_s = secant(f, sx0, sx1, root=root_s, tol=1e-80, maxit=50)

        for method_name, res, target_root in [
            ("Newton", res_n, root_n),
            ("M4", res_m, root_m),
            ("Secant", res_s, root_s),
        ]:
            rows.append({
                "function": name,
                "method": method_name,
                "root": float(res["root"]),
                "reference_root": float(target_root),
                "iterations": res["iterations"],
                "converged": res["converged"],
                "final_error": float(abs(res["root"] - target_root)),
                "estimated_order": estimate_order(res["errors"]),
            })
    # write csv
    csv_path = OUT / "benchmark_results.csv"
    with csv_path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    # write json
    (OUT / "benchmark_results.json").write_text(json.dumps(rows, indent=2, default=str))

    # figure: convergence of errors for 'poly5'
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        name = "poly5"
        f = lambda x: x ** 5 - x - mpmath.mpf('0.1')
        df = lambda x: mpmath.mpf('5.0') * x ** 4 - mpmath.mpf('1.0')
        # Use individual reference roots for error convergence plotting
        ref_N = newton(f, df, mpmath.mpf('0.9'), root=None, tol=1e-80, maxit=50)
        rN = newton(f, df, mpmath.mpf('0.9'), root=ref_N["root"], tol=1e-80, maxit=50)

        ref_M = m4(f, df, mpmath.mpf('0.9'), root=None, tol=1e-80, maxit=50)
        rM = m4(f, df, mpmath.mpf('0.9'), root=ref_M["root"], tol=1e-80, maxit=50)

        ref_S = secant(f, mpmath.mpf('0.5'), mpmath.mpf('1.5'), root=None, tol=1e-80, maxit=50)
        rS = secant(f, mpmath.mpf('0.5'), mpmath.mpf('1.5'), root=ref_S["root"], tol=1e-80, maxit=50)
        plt.figure(figsize=(7, 4.5))
        for label, r, marker in [("Newton", rN, "o"), ("M4 (proposed)", rM, "s"), ("Secant", rS, "^")]:
            errs = [float(e) for e in r["errors"] if e > 0]
            plt.semilogy(range(1, len(errs) + 1), errs, marker + "-", label=label)
        plt.xlabel("Iteration")
        plt.ylabel("Absolute error")
        plt.title("Convergence on $x^5 - x - 0.1 = 0$")
        plt.grid(True, which="both", linestyle=":")
        plt.legend()
        plt.tight_layout()
        plt.savefig(FIG / "convergence_poly5.png", dpi=150)
        plt.close()
    except Exception as e:
        print("figure error:", e)

    print("Wrote", csv_path)
    for row in rows:
        print(row["function"], row["method"], "iters=", row["iterations"], "order=", row["estimated_order"])


if __name__ == "__main__":
    run()
