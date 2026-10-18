"""Reproducible benchmark comparing iterative methods on standard test functions."""

import csv
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from iterative_methods import newton, secant, m4, estimate_order

OUT = Path(__file__).resolve().parents[1] / "results"
OUT.mkdir(exist_ok=True)
FIG = Path(__file__).resolve().parents[1] / "figures"
FIG.mkdir(exist_ok=True)

TESTS = [
    ("poly2", lambda x: x * x - 2.0, lambda x: 2.0 * x, 1.5, 2.0, 1.0),
    ("exp", lambda x: math.exp(x) - 2.0, lambda x: math.exp(x), 1.0, 2.0, 1.0),
    ("cos", lambda x: math.cos(x) - x, lambda x: -math.sin(x) - 1.0, 0.5, 1.5, 0.5),
    ("poly5", lambda x: x ** 5 - x - 0.1, lambda x: 5 * x ** 4 - 1, 0.9, 1.5, 0.5),
]


def run():
    rows = []
    for name, f, df, x0, sx0, sx1 in TESTS:
        # reference root via m4
        ref = m4(f, df, x0, root=None, tol=1e-15, maxit=50)
        root = ref["root"]
        for method_name, res in [
            ("Newton", newton(f, df, x0, root=root, tol=1e-15, maxit=50)),
            ("M4", m4(f, df, x0, root=root, tol=1e-15, maxit=50)),
            ("Secant", secant(f, sx0, sx1, root=root, tol=1e-15, maxit=50)),
        ]:
            rows.append({
                "function": name,
                "method": method_name,
                "root": res["root"],
                "reference_root": root,
                "iterations": res["iterations"],
                "converged": res["converged"],
                "final_error": abs(res["root"] - root),
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
        f = lambda x: x ** 5 - x - 0.1
        df = lambda x: 5 * x ** 4 - 1
        ref = m4(f, df, 0.9, root=None, tol=1e-15, maxit=50)
        root = ref["root"]
        rN = newton(f, df, 0.9, root=root, tol=1e-15, maxit=50)
        rM = m4(f, df, 0.9, root=root, tol=1e-15, maxit=50)
        rS = secant(f, 0.5, 1.5, root=root, tol=1e-15, maxit=50)
        plt.figure(figsize=(7, 4.5))
        for label, r, marker in [("Newton", rN, "o"), ("M4 (proposed)", rM, "s"), ("Secant", rS, "^")]:
            errs = [e for e in r["errors"] if e > 0]
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
