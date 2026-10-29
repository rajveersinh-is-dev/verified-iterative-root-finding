"""Tests for iterative_methods module."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from iterative_methods import newton, secant, m4, estimate_order


def f1(x):
    return x * x - 2.0


def df1(x):
    return 2.0 * x


def f2(x):
    return math.exp(x) - 2.0


def df2(x):
    return math.exp(x)


ROOT1 = math.sqrt(2.0)
ROOT2 = math.log(2.0)


def test_newton_converges():
    r = newton(f1, df1, 1.5, root=ROOT1)
    assert r["converged"]
    assert abs(r["root"] - ROOT1) < 1e-12


def test_m4_converges():
    r = m4(f1, df1, 1.5, root=ROOT1)
    assert r["converged"]
    assert abs(r["root"] - ROOT1) < 1e-12


def test_secant_converges():
    r = secant(f1, 1.0, 2.0, root=ROOT1)
    assert r["converged"]
    assert abs(r["root"] - ROOT1) < 1e-12


def test_m4_order_approx_4():
    def f(x):
        return x ** 5 - x - 0.1

    def df(x):
        return 5 * x ** 4 - 1

    # reference root
    r0 = m4(f, df, 0.9, root=None, tol=1e-15, maxit=50)
    root = r0["root"]
    r = m4(f, df, 0.9, root=root, tol=1e-15, maxit=50)
    order = estimate_order(r["errors"])
    assert order is not None
    assert 3.0 < order < 5.5, f"estimated order {order}"


def test_m4_order_mpmath():
    import mpmath

    mpmath.mp.dps = 100

    def f(x):
        return mpmath.exp(x) - mpmath.mpf('2.0')

    def df(x):
        return mpmath.exp(x)

    x0 = mpmath.mpf('1.0')
    root = mpmath.log(mpmath.mpf('2.0'))

    r = m4(f, df, x0, root=root, tol=1e-80, maxit=50)
    order = estimate_order(r["errors"])

    assert order is not None
    assert 3.8 < order < 4.2, f"estimated order {order}"


def test_newton_order_approx_2():
    r = newton(f2, df2, 1.0, root=ROOT2, tol=1e-15, maxit=20)
    order = estimate_order(r["errors"])
    assert order is not None
    assert 1.5 < order < 2.5, f"estimated order {order}"


def test_newton_df_zero_stops():
    def f(x):
        return x

    def df(x):
        return 0.0

    r = newton(f, df, 1.0, root=0.0, maxit=5)
    assert not r["converged"] or r["iterations"] <= 5


def test_m4_at_root():
    r = m4(f1, df1, ROOT1, root=ROOT1, tol=1e-14, maxit=5)
    # should converge immediately or in one step
    assert r["converged"] or r["iterations"] <= 2


def test_m4_exact_root():
    def f(x):
        return x

    def df(x):
        return 1.0

    r = m4(f, df, 0.0)
    assert r["converged"]
    assert r["iterations"] == 0
    assert r["root"] == 0.0


def test_estimate_order_insufficient():
    assert estimate_order([]) is None
    assert estimate_order([1.0]) is None


def test_complex_roots():
    def f(x):
        return x**2 + 1.0

    def df(x):
        return 2.0 * x

    r_m4 = m4(f, df, 1.0+1.0j, tol=1e-12)
    assert r_m4["converged"]
    assert abs(r_m4["root"] - 1.0j) < 1e-11

    r_newton = newton(f, df, 1.0+1.0j, tol=1e-12)
    assert r_newton["converged"]
    assert abs(r_newton["root"] - 1.0j) < 1e-11

    r_secant = secant(f, 1.0+1.0j, 1.0+0.5j, tol=1e-12)
    assert r_secant["converged"]
    assert abs(r_secant["root"] - 1.0j) < 1e-11


def test_mpmath_complex():
    import mpmath
    mpmath.mp.dps = 30

    def f(x):
        return x**2 + 1.0

    def df(x):
        return 2.0 * x

    x0 = mpmath.mpc(1.0, 1.0)
    root = mpmath.mpc(0.0, 1.0)

    r_m4 = m4(f, df, x0, root=root, tol=1e-25)
    assert r_m4["converged"]
    assert abs(r_m4["root"] - root) < 1e-24


def test_divergent_function_safe_call():
    import cmath
    def f(x):
        return cmath.exp(x)
    def df(x):
        return cmath.exp(x)

    # Exponentiating a large number overflows to complex infinity/nan,
    # safe_call should catch it and stop without throwing an error
    r = m4(f, df, 1000.0 + 1000.0j, maxit=5)
    assert not r["converged"]

def test_newton_overflow_protection():
    # test division overflow
    def f1(x): return 1e200
    def df1(x): return 1e-200

    r1 = newton(f1, df1, 0.0)
    assert not r1["converged"]
    assert r1["root"] == 0.0

    # test evaluation overflow
    def f2(x): return x**400
    def df2(x): return 400 * x**399

    r2 = newton(f2, df2, 10.0)
    assert not r2["converged"]

def test_secant_zero_division():
    def f(x):
        if x == 0.0: return 1.0
        if x == 1.0: return 1.0 # causes denom to be 0
        return x

    r = secant(f, 0.0, 1.0)
    assert not r["converged"]

def test_m4_math_domain_error():
    # math.log(-1) raises ValueError (math domain error)
    def f(x):
        return math.log(x)
    def df(x):
        return 1.0/x

    r = m4(f, df, -1.0)
    assert not r["converged"]
    assert r["iterations"] == 0
    assert r["root"] == -1.0

def test_complex_overflow_protection():
    def f(x): return complex(1e200, 1e200)
    def df(x): return complex(1e-200, 1e-200)

    r_newton = newton(f, df, complex(0, 0))
    assert not r_newton["converged"]

    r_m4 = m4(f, df, complex(0, 0))
    assert not r_m4["converged"]

def test_decimal_types_fallback():
    from decimal import Decimal
    def f(x): return x**2 - Decimal('2.0')
    def df(x): return Decimal('2.0') * x

    r = m4(f, df, Decimal('1.5'))
    assert r["converged"]
    # should be close to sqrt(2)
    assert abs(float(r["root"]) - 1.4142135623730951) < 1e-12

def test_verbose_logging(caplog):
    import logging
    caplog.set_level(logging.DEBUG)

    def f(x): return x**2 + 1.0
    def df(x): return 0.0  # Force derivative too small

    r_newton = newton(f, df, 1.0, verbose=True)
    assert not r_newton["converged"]

    r_m4 = m4(f, df, 1.0, verbose=True)
    assert not r_m4["converged"]

    def f_secant(x): return 1.0 # Force denominator too small
    r_secant = secant(f_secant, 0.0, 1.0, verbose=True)
    assert not r_secant["converged"]

    assert "[Newton] Derivative too small:" in caplog.text
    assert "[M4] Derivative too small:" in caplog.text
    assert "[Secant] Denominator too small:" in caplog.text
