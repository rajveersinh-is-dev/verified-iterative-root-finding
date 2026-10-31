import pytest
"""Tests for iterative_methods module."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from iterative_methods import _is_valid, _safe_call, newton, secant, m4, estimate_order


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
    mpmath = pytest.importorskip("mpmath")

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
    mpmath = pytest.importorskip("mpmath")
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
def test_is_valid_none():
    assert not _is_valid(None)

def test_is_valid_float_nan_inf():
    assert not _is_valid(float('nan'))
    assert not _is_valid(float('inf'))

def test_is_valid_complex_nan_inf():
    assert not _is_valid(complex(float('nan'), 1.0))
    assert not _is_valid(complex(1.0, float('inf')))

def test_is_valid_mpmath_nan_inf():
    mpmath = pytest.importorskip("mpmath")
    assert not _is_valid(mpmath.nan)
    assert not _is_valid(mpmath.inf)

def test_is_valid_mpmath_exception():
    class BadMpmath:
        ae = True
        @property
        def real(self): return float('nan')
    assert _is_valid(BadMpmath())

def test_safe_call_exception(caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    def f(x): raise ValueError("test")
    assert _safe_call(f, 1.0, verbose=True, context="test") is None
    assert "[test] Exception during evaluation: test" in caplog.text

def test_safe_call_invalid(caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    def f(x): return None
    assert _safe_call(f, 1.0, verbose=True, context="test") is None
    assert "[test] Invalid value returned: None" in caplog.text

def test_newton_int_input():
    def f(x): return x - 2.0
    def df(x): return 1.0
    res = newton(f, df, 2)
    assert res["converged"]
    assert res["root"] == 2.0

def test_newton_invalid_f(caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    def f(x): return None
    def df(x): return 1.0
    res = newton(f, df, 2.0, verbose=True)
    assert not res["converged"]

def test_newton_invalid_x_new(caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    def f(x): return float('inf')
    def df(x): return 1.0
    res = newton(f, df, 2.0, verbose=True)
    assert not res["converged"]

def test_newton_exception_step(caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    class BadType(float):
        def __sub__(self, other):
            raise ValueError("bad sub")
        def __abs__(self):
            return 1.0
        def __lt__(self, other):
            return False
    def f(x): return 1.0
    def df(x): return 1.0
    res = newton(f, df, BadType(1.0), verbose=True)
    assert not res["converged"]

def test_secant_int_input():
    def f(x): return x - 2.0
    res = secant(f, 0, 3)
    assert res["converged"]

def test_secant_invalid_f(caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    def f(x): return None
    res = secant(f, 0.0, 3.0, verbose=True)
    assert not res["converged"]

def test_secant_exception_step(caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    class BadType(float):
        def __sub__(self, other):
            if isinstance(other, BadType):
                return self
            raise ValueError("bad sub")
        def __abs__(self):
            return 1.0
        def __lt__(self, other):
            return False
    def f(x): return 1.0 if x == 1.0 else 0.0
    res = secant(f, BadType(1.0), BadType(2.0), verbose=True)
    assert not res["converged"]

def test_secant_invalid_x_new(caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    class InvalidValType(float):
        def __sub__(self, other):
            return float('inf')
        def __abs__(self):
            return 1.0
        def __lt__(self, other):
            return False
    def f(x): return 1.0 if x == 1.0 else 0.0
    res = secant(f, InvalidValType(1.0), InvalidValType(2.0), verbose=True)
    assert not res["converged"]

def test_m4_int_input():
    def f(x): return x - 2.0
    def df(x): return 1.0
    res = m4(f, df, 2)
    assert res["converged"]

def test_m4_invalid_f():
    def f(x): return None
    def df(x): return 1.0
    res = m4(f, df, 2.0, verbose=True)
    assert not res["converged"]

def test_m4_exception_y(caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    class BadType(float):
        def __sub__(self, other):
            raise ValueError("bad sub")
        def __abs__(self):
            return 1.0
        def __lt__(self, other):
            return False
    def f(x): return 1.0
    def df(x): return 1.0
    res = m4(f, df, BadType(1.0), verbose=True)
    assert not res["converged"]

def test_m4_invalid_y(caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    class InvalidValType(float):
        def __sub__(self, other):
            return float('inf')
        def __abs__(self):
            return 1.0
        def __lt__(self, other):
            return False
    def f(x): return 1.0
    def df(x): return 1.0
    res = m4(f, df, InvalidValType(1.0), verbose=True)
    assert not res["converged"]


def test_m4_invalid_fy(caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    def f(x):
        if x == 2.0: return 1.0
        return None
    def df(x): return 1.0
    res = m4(f, df, 2.0, verbose=True)
    assert not res["converged"]

def test_m4_exception_ratio(caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    def f(x): return 1.0
    def df(x): return 1.0
    class BadRatioType(float):
        def __sub__(self, other): return self
        def __truediv__(self, other): raise ValueError("bad div")
        def __abs__(self): return 1.0
        def __lt__(self, other): return False
    res = m4(f, df, BadRatioType(1.0), verbose=True)
    assert not res["converged"]

def test_m4_invalid_ratio(caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    def f(x): return 1.0
    def df(x): return 1.0
    class InvalidRatioType(float):
        def __sub__(self, other): return self
        def __truediv__(self, other): return float('inf')
        def __abs__(self): return 1.0
        def __lt__(self, other): return False
    res = m4(f, df, InvalidRatioType(1.0), verbose=True)
    assert not res["converged"]

def test_m4_exception_correction(caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    def f(x): return 1.0
    def df(x): return 1.0
    class BadCorrType(float):
        def __sub__(self, other):
            if isinstance(other, float) and other == float('inf'):
                raise ValueError("bad sub2")
            return float('inf') # y becomes inf? No, y is just next call
        def __truediv__(self, other): return self
        def __mul__(self, other): raise ValueError("bad mul")
        def __add__(self, other): return self
        def __abs__(self): return 1.0
        def __lt__(self, other): return False
    # Let y be computed, then when correcting:
    # correction = (fy / dfx) * (TypeX('1.0') + TypeX('2.0') * t)
    res = m4(f, df, BadCorrType(1.0), verbose=True)
    assert not res["converged"]


def test_m4_invalid_x_new(caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    def f(x): return 1.0
    def df(x): return 1.0
    class BadCorrType(float):
        def __sub__(self, other): return float('inf')
        def __truediv__(self, other): return self
        def __mul__(self, other): return self
        def __add__(self, other): return self
        def __abs__(self): return 1.0
        def __lt__(self, other): return False
    res = m4(f, df, BadCorrType(1.0), verbose=True)
    assert not res["converged"]


def test_m4_abs_exception():
    class BadType(float):
        def __abs__(self): raise ValueError("bad abs")
        def __sub__(self, other): return self
        def __truediv__(self, other): return self
        def __mul__(self, other): return self
        def __add__(self, other): return self

    def f(x): return BadType(1.0)
    def df(x): return 1.0
    res = m4(f, df, 1.0)
    assert not res["converged"]

def test_estimate_order_typeerror():
    assert estimate_order([None, None, None, None]) is None
    assert estimate_order([-1.0, -1.0, -1.0, -1.0]) is None

def test_estimate_order_not_finite():
    assert estimate_order([float('inf'), float('inf'), float('inf'), float('inf')]) is None

def test_estimate_order_zero_den():
    assert estimate_order([0.5, 0.5, 0.5, 0.5]) is None

def test_newton_invalid_x_new2(caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    class BadType(float):
        def __sub__(self, other):
            return float('nan')
        def __abs__(self):
            return 1.0
        def __lt__(self, other):
            return False
    def f(x): return 1.0
    def df(x): return 1.0
    res = newton(f, df, BadType(1.0), verbose=True)
    assert not res["converged"]

def test_m4_ratio_exception(caplog):
    import logging
    caplog.set_level(logging.DEBUG)

    class BadDivType(float):
        def __sub__(self, other): return self
        def __truediv__(self, other):
            if getattr(self, '_is_y', False):
                raise ValueError("bad div")
            return self
        def __abs__(self): return 1.0
        def __lt__(self, other): return False

    def f(x):
        return x
    def df(x): return 1.0

    x0 = BadDivType(1.0)
    x0._is_y = False

    # We need fy / fx to raise exception. fy is f(y).
    # Since f(x) = x, fy = y. y = x - fx/dfx.
    # fx = x0. dfx = 1.0. fx/dfx = x0.
    # y = x0 - x0 = x0.
    # fy = y = x0.
    # t = fy / fx = x0 / x0.
    # We want this to raise exception.

    # Let's use a function that returns an object whose division raises an error
    class RetObj(float):
        def __truediv__(self, other):
            raise ValueError("bad div")
        def __abs__(self): return 1.0
        def __lt__(self, other): return False

    class XObj(float):
        def __sub__(self, other): return self
        def __truediv__(self, other): return self
        def __abs__(self): return 1.0
        def __lt__(self, other): return False
        def __add__(self, other): return self
        def __mul__(self, other): return self

    call_count = 0
    def f(x):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return XObj(1.0)
        return RetObj(1.0)

    def df(x): return XObj(1.0)

    res = m4(f, df, XObj(1.0), verbose=True)
    assert not res["converged"]

def test_m4_ratio_invalid(caplog):
    import logging
    caplog.set_level(logging.DEBUG)

    class RetObj(float):
        def __truediv__(self, other):
            return float('inf')
        def __abs__(self): return 1.0
        def __lt__(self, other): return False

    class XObj(float):
        def __sub__(self, other): return self
        def __truediv__(self, other): return self
        def __abs__(self): return 1.0
        def __lt__(self, other): return False
        def __add__(self, other): return self
        def __mul__(self, other): return self

    call_count = 0
    def f(x):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return XObj(1.0)
        return RetObj(1.0)

    def df(x): return XObj(1.0)

    res = m4(f, df, XObj(1.0), verbose=True)
    assert not res["converged"]


def test_m4_correction_exception(caplog):
    import logging
    caplog.set_level(logging.DEBUG)

    class RetObj(float):
        def __truediv__(self, other):
            return XObj(1.0)
        def __abs__(self): return 1.0
        def __lt__(self, other): return False

    class XObj(float):
        def __sub__(self, other):
            raise ValueError("bad sub3")
        def __truediv__(self, other): return self
        def __abs__(self): return 1.0
        def __lt__(self, other): return False
        def __add__(self, other): return self
        def __mul__(self, other): return self

    call_count = 0
    def f(x):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return XObj(1.0)
        return RetObj(1.0)

    def df(x): return XObj(1.0)

    res = m4(f, df, XObj(1.0), verbose=True)
    assert not res["converged"]

def test_m4_invalid_x_new2(caplog):
    import logging
    caplog.set_level(logging.DEBUG)

    class RetObj(float):
        def __truediv__(self, other):
            return XObj(1.0)
        def __abs__(self): return 1.0
        def __lt__(self, other): return False

    class XObj(float):
        def __sub__(self, other):
            return float('inf')
        def __truediv__(self, other): return self
        def __abs__(self): return 1.0
        def __lt__(self, other): return False
        def __add__(self, other): return self
        def __mul__(self, other): return self

    call_count = 0
    def f(x):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return XObj(1.0)
        return RetObj(1.0)

    def df(x): return XObj(1.0)

    res = m4(f, df, XObj(1.0), verbose=True)
    assert not res["converged"]

def test_m4_correction_real_exception(caplog):
    import logging
    caplog.set_level(logging.DEBUG)

    class XObj(float):
        def __sub__(self, other):
            if isinstance(other, float) and float(other) == float('1.0'):
                raise ValueError("bad cor")
            return self
        def __truediv__(self, other): return self
        def __abs__(self): return 1.0
        def __lt__(self, other): return False
        def __add__(self, other): return self
        def __mul__(self, other):
            # This is called during correction calculation
            if float(self) == 2.0:
                raise ValueError("bad mul")
            return self

    call_count = 0
    def f(x):
        nonlocal call_count
        call_count += 1
        return XObj(1.0)

    def df(x): return XObj(1.0)

    res = m4(f, df, XObj(1.0), verbose=True)
    assert not res["converged"]

def test_m4_correction_invalid(caplog):
    import logging
    caplog.set_level(logging.DEBUG)

    class XObj(float):
        def __sub__(self, other):
            # when computing x_new = y - correction
            if isinstance(other, float) and float(other) == float('1.0'):
                return float('nan')
            return self
        def __truediv__(self, other): return self
        def __abs__(self): return 1.0
        def __lt__(self, other): return False
        def __add__(self, other): return self
        def __mul__(self, other):
            if float(self) == 2.0:
                return self
            return self

    call_count = 0
    def f(x):
        nonlocal call_count
        call_count += 1
        return XObj(1.0)

    def df(x): return XObj(1.0)

    res = m4(f, df, XObj(1.0), verbose=True)
    assert not res["converged"]

def test_m4_correction_invalid2(caplog):
    import logging
    caplog.set_level(logging.DEBUG)

    class XObj(float):
        def __sub__(self, other):
            if type(other) is type(self):
                # When doing x_new = y - correction
                return float('nan')
            return self
        def __truediv__(self, other): return self
        def __abs__(self): return 1.0
        def __lt__(self, other): return False
        def __add__(self, other): return self
        def __mul__(self, other): return self

    def f(x): return XObj(1.0)
    def df(x): return XObj(1.0)

    res = m4(f, df, XObj(1.0), verbose=True)
    assert not res["converged"]

def test_m4_correction_exception2(caplog):
    import logging
    caplog.set_level(logging.DEBUG)

    class XObj(float):
        def __sub__(self, other):
            if type(other) is type(self):
                # When doing x_new = y - correction
                raise ValueError("bad cor2")
            return self
        def __truediv__(self, other): return self
        def __abs__(self): return 1.0
        def __lt__(self, other): return False
        def __add__(self, other): return self
        def __mul__(self, other): return self

    def f(x): return XObj(1.0)
    def df(x): return XObj(1.0)

    res = m4(f, df, XObj(1.0), verbose=True)
    assert not res["converged"]

def test_m4_correction_invalid3(caplog):
    import logging
    caplog.set_level(logging.DEBUG)

    class XObj(float):
        def __sub__(self, other): return float('nan')
        def __truediv__(self, other): return self
        def __abs__(self): return 1.0
        def __lt__(self, other): return False
        def __add__(self, other): return self
        def __mul__(self, other): return self

    # For m4 to reach correction, it needs y to be valid, and fy to be valid, and t to be valid
    # y = x - fx/dfx
    # we need this to be a valid XObj

    class YObj(float):
        def __sub__(self, other): return float('nan')

    class FYObj(float):
        def __truediv__(self, other): return self # for t and correction
        def __mul__(self, other): return self

    call_count = 0
    def f(x):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return XObj(1.0)
        return FYObj(1.0)

    def df(x): return XObj(1.0)

    res = m4(f, df, XObj(1.0), verbose=True)
    assert not res["converged"]

def test_m4_correction_exception3(caplog):
    import logging
    caplog.set_level(logging.DEBUG)

    class XObj(float):
        def __sub__(self, other): return self
        def __truediv__(self, other): return self
        def __abs__(self): return 1.0
        def __lt__(self, other): return False
        def __add__(self, other): return self
        def __mul__(self, other): return self

    class FYObj(float):
        def __truediv__(self, other): return self # for t and correction
        def __mul__(self, other):
            raise ValueError("bad mul3")

    call_count = 0
    def f(x):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return XObj(1.0)
        return FYObj(1.0)

    def df(x): return XObj(1.0)

    res = m4(f, df, XObj(1.0), verbose=True)
    assert not res["converged"]

def test_m4_invalid_x_new4(caplog):
    import logging
    caplog.set_level(logging.DEBUG)

    class XObj(float):
        def __sub__(self, other): return float('nan')
        def __truediv__(self, other): return self
        def __abs__(self): return 1.0
        def __lt__(self, other): return False
        def __add__(self, other): return self
        def __mul__(self, other): return self

    class FYObj(float):
        def __truediv__(self, other): return self
        def __mul__(self, other): return self

    call_count = 0
    def f(x):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return XObj(1.0)
        return FYObj(1.0)

    def df(x): return XObj(1.0)

    res = m4(f, df, XObj(1.0), verbose=True)
    assert not res["converged"]

def test_m4_invalid_x_new5(caplog):
    import logging
    caplog.set_level(logging.DEBUG)

    class XObj(float):
        def __sub__(self, other):
            if isinstance(other, float) and float(other) == float('1.0'):
                # We want _is_valid(x_new) to be False, but we need x_new to be computed successfully
                return float('nan')
            return self
        def __truediv__(self, other): return self
        def __abs__(self): return 1.0
        def __lt__(self, other): return False
        def __add__(self, other): return self
        def __mul__(self, other): return self

    class FYObj(float):
        def __truediv__(self, other): return self
        def __mul__(self, other): return self

    call_count = 0
    def f(x):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return XObj(1.0)
        return FYObj(1.0)

    def df(x): return XObj(1.0)

    res = m4(f, df, XObj(1.0), verbose=True)
    assert not res["converged"]

def test_m4_invalid_x_new6(caplog):
    import logging
    caplog.set_level(logging.DEBUG)

    class XObj(float):
        def __sub__(self, other):
            if type(other) is FYObj: # let's just make it return inf
                return float('inf')
            return self
        def __truediv__(self, other): return self
        def __abs__(self): return 1.0
        def __lt__(self, other): return False
        def __add__(self, other): return self
        def __mul__(self, other): return self

    class FYObj(float):
        def __truediv__(self, other): return self
        def __mul__(self, other): return self

    call_count = 0
    def f(x):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return XObj(1.0)
        return FYObj(1.0)

    def df(x): return XObj(1.0)

    res = m4(f, df, XObj(1.0), verbose=True)
    assert not res["converged"]

def test_is_valid_complex_exception():
    from unittest.mock import patch
    with patch('cmath.isnan', side_effect=ValueError("mocked error")):
        assert not _is_valid(complex(float('nan'), 1.0))
        assert not _is_valid(complex(1.0, float('inf')))
