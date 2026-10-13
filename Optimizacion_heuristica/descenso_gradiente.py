"""Descenso por gradiente proyectado, con paso fijo o búsqueda de línea de Armijo.

    x_{k+1} = P( x_k - t_k * grad f(x_k) ),   P = proyección a la caja [lo, hi]^n

Armijo (backtracking): se reduce t <- beta*t hasta que
    f(x_new) <= f(x_k) - c * grad f(x_k) . (x_k - x_new)
Todas las evaluaciones de f de la búsqueda de línea se cuentan.
"""
import numpy as np


def gradient_descent(obj, rng, lr=1.0, line_search="armijo", c=1e-4, beta=0.5,
                       max_backtrack=30, grad_tol=1e-8, budget=10000,
                       record=False, x0=None):
    x = rng.uniform(obj.lo, obj.hi, obj.dim) if x0 is None else np.asarray(x0, float)
    fx = obj.f(x)
    curve = [(obj.equivalent_cost, fx)]
    traj = [dict(x1=x[0], x2=x[1], **{"f(x1,x2)": fx})] if record and obj.dim == 2 else None

    while obj.equivalent_cost < budget:
        g = obj.grad(x)
        if np.linalg.norm(g) < grad_tol:
            break
        t = lr
        if line_search == "armijo":
            accepted = False
            for _ in range(max_backtrack):
                x_new = np.clip(x - t * g, obj.lo, obj.hi)
                f_new = obj.f(x_new)
                if f_new <= fx - c * g @ (x - x_new):
                    accepted = True
                    break
                t *= beta
            if not accepted:      # no hay dirección de descenso útil
                break
        else:                     # paso fijo
            x_new = np.clip(x - t * g, obj.lo, obj.hi)
            f_new = obj.f(x_new)
        x, fx = x_new, f_new
        curve.append((obj.equivalent_cost, fx))
        if traj is not None:
            traj.append(dict(x1=x[0], x2=x[1], **{"f(x1,x2)": fx}))

    return dict(best_x=x, best_f=fx, curve=curve, trajectory=traj)
