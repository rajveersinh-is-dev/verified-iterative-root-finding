"""Symbolic verification of the convergence order of the proposed M4 method.

Uses sympy Taylor expansion to confirm the error recurrence e_{n+1} ~ C e_n^4.
"""


import sympy as sp

e, A2, A3 = sp.symbols('e A2 A3')

# Newton error: e_y = A2 e^2 + (2 A3 - 2 A2^2) e^3 + ...
e_y = A2*e**2 + (2*A3 - 2*A2**2)*e**3

# t = f(y)/f(x) ~ A2 e + (2 A3 - 3 A2^2) e^2
t = A2*e + (2*A3 - 3*A2**2)*e**2

# ratio f(y)/f'(x) ~ A2 e^2 + (2 A3 - 4 A2^2) e^3
ratio = A2*e**2 + (2*A3 - 4*A2**2)*e**3

# H(t) = 1 + 2 t  (h1=2, h2=0)
H = 1 + 2*t

err = sp.expand(e_y - ratio*H)
err = sp.series(err, e, 0, 5).removeO()
print("error expansion:", err)
print("coeff e^1:", sp.simplify(err.coeff(e, 1)))
print("coeff e^2:", sp.simplify(err.coeff(e, 2)))
print("coeff e^3:", sp.simplify(err.coeff(e, 3)))
print("coeff e^4:", sp.simplify(err.coeff(e, 4)))
assert err.coeff(e, 1) == 0
assert err.coeff(e, 2) == 0
assert err.coeff(e, 3) == 0
print("VERIFIED: terms up to e^3 vanish; leading term is O(e^4).")