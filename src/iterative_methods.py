"""Iterative methods for solving scalar nonlinear equations f(x)=0.

This module implements several classical and a proposed fourth-order method.
All methods return a result dictionary with keys:
    root, iterations, converged, errors (list of absolute errors per iterate),
    x_history.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional
import math



def _safe_call(f: Callable[[float], float], x: float) -> Optional[float]:
    """Safe call.
    
    Args:
        f:
        x:
    
    Returns:
        float: Result of type float
    
    """
    try:
        v = f(x)
    except Exception:
        return None
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return None
    return float(v)


def newton(
    f: Callable[[float], float],
    df: Callable[[float], float],
    x0: float,
    root: Optional[float] = None,
    tol: float = 1e-14,
    maxit: int = 100,
) -> Dict:
    """Classical Newton-Raphson method."""
    xs = [float(x0)]
    errors: List[float] = []
    converged = False
    for _ in range(maxit):
        fx = _safe_call(f, xs[-1])
        dfx = _safe_call(df, xs[-1])
        if fx is None or dfx is None or abs(dfx) < 1e-30:
            break
        x_new = xs[-1] - fx / dfx
        xs.append(x_new)
        if root is not None:
            errors.append(abs(x_new - root))
        if abs(x_new - xs[-2]) < tol or (root is not None and errors[-1] < tol):
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
    f: Callable[[float], float],
    x0: float,
    x1: float,
    root: Optional[float] = None,
    tol: float = 1e-14,
    maxit: int = 100,
) -> Dict:
    """Secant method (derivative-free)."""
    xs = [float(x0), float(x1)]
    errors: List[float] = []
    converged = False
    for _ in range(maxit):
        f0 = _safe_call(f, xs[-2])
        f1 = _safe_call(f, xs[-1])
        if f0 is None or f1 is None:
            break
        denom = f1 - f0
        if abs(denom) < 1e-30:
            break
        x_new = xs[-1] - f1 * (xs[-1] - xs[-2]) / denom
        xs.append(x_new)
        if root is not None:
            errors.append(abs(x_new - root))
        if abs(xs[-1] - xs[-2]) < tol or (root is not None and errors and errors[-1] < tol):
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
    f: Callable[[float], float],
    df: Callable[[float], float],
    x0: float,
    root: Optional[float] = None,
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
    xs = [float(x0)]
    errors: List[float] = []
    converged = False
    for _ in range(maxit):
        x = xs[-1]
        fx = _safe_call(f, x)
        dfx = _safe_call(df, x)
        if fx is None or dfx is None or abs(dfx) < 1e-30 or abs(fx) < 1e-300:
            break
        y = x - fx / dfx
        fy = _safe_call(f, y)
        if fy is None:
            break
        t = fy / fx
        # guard against overflow
        if not math.isfinite(t):
            break
        correction = (fy / dfx) * (1.0 + 2.0 * t)
        x_new = y - correction
        xs.append(x_new)
        if root is not None:
            errors.append(abs(x_new - root))
        if abs(x_new - xs[-2]) < tol or (root is not None and errors and errors[-1] < tol):
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


def estimate_order(errors: List[float]) -> Optional[float]:
    """Estimate convergence order from a list of absolute errors.

    Fits log(e_{n+1}) = p * log(e_n) + c over the last usable pairs.
    Returns None if not enough data.
    """
    if len(errors) < 3:
        return None
    pts = []
    for i in range(len(errors) - 1):
        a, b = errors[i], errors[i + 1]
        if a <= 0 or b <= 0:
            continue
        if not (math.isfinite(a) and math.isfinite(b)):
            continue
        # ignore pairs that have hit floating-point floor
        if a < 1e-12 or b < 1e-13:
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
