"""Evolución diferencial DE/rand/1/bin.

  mutante:  v_i = x_r1 + F*(x_r2 - x_r3),  r1,r2,r3 distintos entre sí y de i
  cruce:    u_ij = v_ij si rand<CR o j=j_rand, si no x_ij
  selección: x_i <- u_i si f(u_i) <= f(x_i)   (voraz, actualización síncrona)
"""
import numpy as np


def differential_evolution(obj, rng, pop_size=40, F=0.5, CR=0.9,
                          budget=10000, record=False):
    N, d = pop_size, obj.dim
    if N < 4:
        raise ValueError("DE/rand/1 requiere tam_pob >= 4")

    x = rng.uniform(obj.lo, obj.hi, (N, d))
    fx = obj.f_pop(x)
    gen = 0
    curve = [(obj.equivalent_cost, fx.min())]
    traj = []

    def save_frame(k):
        if record and d == 2:
            traj.extend(dict(generation=k, x1=p[0], x2=p[1], **{"f(x1,x2)": val})
                        for p, val in zip(x, fx))
    save_frame(0)

    while obj.n_f + N <= budget:
        # tres índices distintos entre sí y distintos de i
        R = rng.random((N, N))
        np.fill_diagonal(R, np.inf)
        r = np.argsort(R, axis=1)[:, :3]
        v = x[r[:, 0]] + F * (x[r[:, 1]] - x[r[:, 2]])

        cross_mask = rng.random((N, d)) < CR
        cross_mask[np.arange(N), rng.integers(0, d, N)] = True
        u = np.clip(np.where(cross_mask, v, x), obj.lo, obj.hi)

        fu = obj.f_pop(u)
        better = fu <= fx
        x[better], fx[better] = u[better], fu[better]

        gen += 1
        curve.append((obj.equivalent_cost, fx.min()))
        save_frame(gen)

    i = int(np.argmin(fx))
    return dict(best_x=x[i].copy(), best_f=float(fx[i]), curve=curve,
                trajectory=traj if record and d == 2 else None)
