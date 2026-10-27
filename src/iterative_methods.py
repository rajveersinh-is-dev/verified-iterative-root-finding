"""Iterative methods for solving scalar nonlinear equations f(x)=0.

This module implements several classical and a proposed fourth-order method.
All methods return a result dictionary with keys:
    root, iterations, converged, errors (list of absolute errors per iterate),
    x_history.
"""

from __future__ import annotations

import math
from typing import Callable, Dict, List, Optional, Any


def _is_valid(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return False
    if isinstance(v, complex):
        try:
            import cmath
            if cmath.isnan(v) or cmath.isinf(v):
                return False
        except Exception:
            if math.isnan(v.real) or math.isinf(v.real) or math.isnan(v.imag) or math.isinf(v.imag):
                return False
    if hasattr(v, 'ae'): # basic check for mpmath types
        try:
            import mpmath
            if mpmath.isnan(v) or mpmath.isinf(v):
                return False
        except Exception:
            pass
    return True

def _safe_call(f: Callable[[Any], Any], x: Any) -> Optional[Any]:
    try:
        v = f(x)
    except Exception:
        return None
    if not _is_valid(v):
        return None
    return v


def _get_real_type(x: Any) -> type:
    """Get the appropriate real-valued scalar type for setting tolerances."""
    if isinstance(x, complex) or isinstance(x, int):
        return float
    # for mpmath.mpc, the type of its absolute value is mpf
    if hasattr(x, 'real') and type(x) != type(x.real):
        return type(x.real)
    return type(x)


def newton(
    f: Callable[[Any], Any],
    df: Callable[[Any], Any],
    x0: Any,
    root: Optional[Any] = None,
    tol: float = 1e-14,
    maxit: int = 100,
) -> Dict:
    """Classical Newton-Raphson method."""
    if isinstance(x0, int):
        x0 = float(x0)
    T = _get_real_type(x0)
    xs = [x0]
    errors: List[Any] = []
    converged = False
    for _ in range(maxit):
        fx = _safe_call(f, xs[-1])
        dfx = _safe_call(df, xs[-1])
        if fx is None or dfx is None or abs(dfx) < T('1e-30'):
            break
        try:
            x_new = xs[-1] - fx / dfx
        except Exception:
            break
        if not _is_valid(x_new):
            break
        xs.append(x_new)
        if root is not None:
            errors.append(abs(x_new - root))
        if abs(x_new - xs[-2]) < T(str(tol)) or (root is not None and errors[-1] < T(str(tol))):
            converged = True
            break
    return {
        "method": "Newton",
        "root": xs[-1],
        "iterations": len(xs) - 1,
        "converged": converged,
        "errors": errors,
        "x_history": xs,
    }


def secant(
    f: Callable[[Any], Any],
    x0: Any,
    x1: Any,
    root: Optional[Any] = None,
    tol: float = 1e-14,
    maxit: int = 100,
) -> Dict:
    """Secant method (derivative-free)."""
    if isinstance(x0, int):
        x0 = float(x0)
    if isinstance(x1, int):
        x1 = float(x1)
    T = _get_real_type(x0)
    xs = [x0, x1]
    errors: List[Any] = []
    converged = False
    for _ in range(maxit):
        f0 = _safe_call(f, xs[-2])
        f1 = _safe_call(f, xs[-1])
        if f0 is None or f1 is None:
            break
        try:
            denom = f1 - f0
            if abs(denom) < T('1e-30'):
                break
            x_new = xs[-1] - f1 * (xs[-1] - xs[-2]) / denom
        except Exception:
            break
        if not _is_valid(x_new):
            break
        xs.append(x_new)
        if root is not None:
            errors.append(abs(x_new - root))
        if abs(xs[-1] - xs[-2]) < T(str(tol)) or (root is not None and errors and errors[-1] < T(str(tol))):
            converged = True
            break
    return {
        "method": "Secant",
        "root": xs[-1],
        "iterations": len(xs) - 2,
        "converged": converged,
        "errors": errors,
        "x_history": xs,
    }


def m4(
    f: Callable[[Any], Any],
    df: Callable[[Any], Any],
    x0: Any,
    root: Optional[Any] = None,
    tol: float = 1e-14,
    maxit: int = 100,
) -> Dict:
    """Proposed fourth-order method.

    Let y = x - f(x)/f'(x) (Newton step). Then

        x_{new} = y - (f(y)/f'(x)) * (1 + 2 * f(y)/f(x)).

    Convergence order 4 is established in the accompanying manuscript
    (paper/main.tex) via Taylor expansion; verified symbolically in
    experiments/symbolic_order.py.
    """
    if isinstance(x0, int):
        x0 = float(x0)
    T = _get_real_type(x0)
    TypeX = type(x0) if not isinstance(x0, complex) else complex
    xs = [x0]
    errors: List[Any] = []
    converged = False
    for _ in range(maxit):
        x = xs[-1]
        fx = _safe_call(f, x)
        dfx = _safe_call(df, x)
        if fx is None or dfx is None or abs(dfx) < T('1e-30'):
            break
        try:
            if abs(fx) < T('1e-300'):
                converged = True
                break
        except Exception:
            # Fallback for types where 1e-300 might cause issues (e.g. some decimals)
            # or if absolute value comparison fails
            pass

        try:
            y = x - fx / dfx
        except Exception:
            break
        if not _is_valid(y):
            break

        fy = _safe_call(f, y)
        if fy is None:
            break

        try:
            t = fy / fx
        except Exception:
            break
        if not _is_valid(t):
            break

        try:
            correction = (fy / dfx) * (TypeX('1.0') + TypeX('2.0') * t)
            x_new = y - correction
        except Exception:
            break
        if not _is_valid(x_new):
            break

        xs.append(x_new)
        if root is not None:
            errors.append(abs(x_new - root))
        if abs(x_new - xs[-2]) < T(str(tol)) or (root is not None and errors and errors[-1] < T(str(tol))):
            converged = True
            break
    return {
        "method": "M4 (proposed)",
        "root": xs[-1],
        "iterations": len(xs) - 1,
        "converged": converged,
        "errors": errors,
        "x_history": xs,
    }


def estimate_order(errors: List[Any]) -> Optional[float]:
    """Estimate convergence order from a list of absolute errors.

    Fits log(e_{n+1}) = p * log(e_n) + c over the last usable pairs.
    Returns None if not enough data.
    """
    if len(errors) < 3:
        return None
    import statistics

    is_std_float = all(isinstance(e, float) for e in errors)
    floor1 = 1e-12 if is_std_float else 1e-80
    floor2 = 1e-13 if is_std_float else 1e-90

    pts = []
    for i in range(len(errors) - 1):
        try:
            a, b = float(errors[i]), float(errors[i + 1])
        except (TypeError, ValueError):
            continue

        if a <= 0 or b <= 0:
            continue
        if not (math.isfinite(a) and math.isfinite(b)):
            continue
        # ignore pairs that have hit floating-point floor
        if a < floor1 or b < floor2:
            continue
        pts.append((math.log(a), math.log(b)))
    if len(pts) < 2:
        return None
    # use last min(4, len) points
    pts = pts[-4:]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return None
    return num / den
