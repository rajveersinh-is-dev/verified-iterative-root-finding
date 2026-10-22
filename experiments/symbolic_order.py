"""Symbolic verification of the convergence order of the proposed M4 method.

Uses sympy Taylor expansion to confirm the error recurrence e_{n+1} ~ C e_n^4.
"""

import sympy as sp

e, lam = sp.symbols('e lam')
A2, A3, A4, A5 = sp.symbols('A2 A3 A4 A5')

f_expr = lam * (e + A2*e**2 + A3*e**3 + A4*e**4 + A5*e**5)
df_expr = sp.diff(f_expr, e)

# Newton error: e_y = e - f(x)/f'(x)
e_y = sp.series(e - f_expr / df_expr, e, 0, 6).removeO()

# f(y)
fy_expr = sp.series(f_expr.subs(e, e_y), e, 0, 6).removeO()

# ratio f(y)/f'(x)
ratio_expr = sp.series(fy_expr / df_expr, e, 0, 6).removeO()

# t = f(y)/f(x)
t_expr = sp.series(fy_expr / f_expr, e, 0, 6).removeO()

# H(t) = 1 + 2 t
H_expr = 1 + 2*t_expr

err = sp.series(e_y - ratio_expr * H_expr, e, 0, 6).removeO()
print("error expansion:", err)
print("coeff e^1:", sp.simplify(err.coeff(e, 1)))
print("coeff e^2:", sp.simplify(err.coeff(e, 2)))
print("coeff e^3:", sp.simplify(err.coeff(e, 3)))
coeff_e4 = sp.simplify(err.coeff(e, 4))
print("coeff e^4:", coeff_e4)
assert err.coeff(e, 1) == 0
assert err.coeff(e, 2) == 0
assert err.coeff(e, 3) == 0
print(f"VERIFIED: terms up to e^3 vanish; leading term is O(e^4) with coeff {coeff_e4}.")
